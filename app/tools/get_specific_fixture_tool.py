"""
Specific fixture tool for retrieving fixtures between two specific teams.
"""

import logging
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from utils.football_api_utils import (
    call_football_api, Response, ValidResponse, ErrorResponse
)
from utils.getters import get_league_id_by_name, get_team_id_by_name

logger = logging.getLogger(__name__)


class GetSpecificFixtureTool:
    """Tool for retrieving specific fixtures between two teams."""
    
    @staticmethod
    def get_specific_fixture(
        league_name: str,
        season: int,
        home_team: str,
        away_team: str
    ) -> Response:
        """
        Get a specific fixture between two teams in a given league and season.
        
        Args:
            league_name: Name of the league or cup (e.g., "Premier League", "La Liga")
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            home_team: Name of the home team
            away_team: Name of the away team
            
        Returns:
            ValidResponse with fixture data or ErrorResponse with error details
        """
        # Get league ID
        league_id = get_league_id_by_name(league_name)
        if league_id is None:
            logger.error(f"League '{league_name}' not found")
            return ErrorResponse(error=f"League '{league_name}' not found")
        
        # Get team IDs
        home_team_id = get_team_id_by_name(home_team)
        if home_team_id is None:
            logger.error(f"Home team '{home_team}' not found")
            return ErrorResponse(error=f"Home team '{home_team}' not found")
        
        away_team_id = get_team_id_by_name(away_team)
        if away_team_id is None:
            logger.error(f"Away team '{away_team}' not found")
            return ErrorResponse(error=f"Away team '{away_team}' not found")
        
        writer = get_stream_writer()
        writer(f"Searching for fixture: {home_team} vs {away_team} in {league_name} season {season}...\n")
        
        # First, try to get all fixtures for the home team in that league/season
        params = {
            "league": league_id,
            "season": season,
            "team": home_team_id
        }
        
        try:
            response = call_football_api("GET", "fixtures", params=params)
            
            if isinstance(response, ValidResponse) and "response" in response.data:
                fixtures = response.data["response"]
                
                # Filter for matches against the away team
                matching_fixtures = []
                for fixture in fixtures:
                    home_id = fixture["teams"]["home"]["id"]
                    away_id = fixture["teams"]["away"]["id"]
                    
                    # Check if this is the specific match we're looking for
                    if home_id == home_team_id and away_id == away_team_id:
                        matching_fixtures.append(fixture)
                
                if matching_fixtures:
                    logger.info(f"Found {len(matching_fixtures)} fixture(s) between {home_team} and {away_team}")
                    # Return the fixtures in the same format as the API
                    return ValidResponse(data={"response": matching_fixtures})
                else:
                    # Try the reverse (away team as home team parameter)
                    params["team"] = away_team_id
                    response2 = call_football_api("GET", "fixtures", params=params)
                    
                    if isinstance(response2, ValidResponse) and "response" in response2.data:
                        fixtures2 = response2.data["response"]
                        
                        # Filter for matches against the home team (but with teams swapped)
                        for fixture in fixtures2:
                            home_id = fixture["teams"]["home"]["id"]
                            away_id = fixture["teams"]["away"]["id"]
                            
                            if home_id == home_team_id and away_id == away_team_id:
                                matching_fixtures.append(fixture)
                    
                    if matching_fixtures:
                        logger.info(f"Found {len(matching_fixtures)} fixture(s) between {home_team} and {away_team}")
                        return ValidResponse(data={"response": matching_fixtures})
                    else:
                        error_msg = f"No fixture found between {home_team} (home) and {away_team} (away) in {league_name} season {season}"
                        logger.warning(error_msg)
                        return ErrorResponse(error=error_msg)
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error searching for fixture: {str(e)}")
            return ErrorResponse(error=f"Error searching for fixture: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetSpecificFixtureInput(BaseModel):
            league_name: str = Field(..., description="Name of the league or cup (e.g., 'Premier League', 'La Liga')")
            season: int = Field(..., description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            home_team: str = Field(..., description="Name of the home team")
            away_team: str = Field(..., description="Name of the away team")

        return StructuredTool.from_function(
            self.get_specific_fixture,
            name="get_specific_fixture",
            description="Get a specific fixture between two teams in a given league and season.",
            args_schema=GetSpecificFixtureInput,
            return_direct=False
        )
