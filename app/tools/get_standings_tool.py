"""
Standings tool for retrieving league standings data.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from utils.football_api_utils import (
    call_football_api, Response, ValidResponse, ErrorResponse
)
from utils.getters import get_league_id_by_name, get_team_id_by_name

logger = logging.getLogger(__name__)


class GetStandingsTool:
    """Tool for retrieving football league standings."""
    
    @staticmethod
    def get_standings(league_name: str, season: int, team_name: str | None = None) -> Response:
        """
        Get the standings for a league or specific team in a league.
        
        Args:
            league_name: Name of the league (e.g., "Premier League", "La Liga")
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            team_name: Optional team name to filter standings for specific team
            
        Returns:
            ValidResponse with standings data or ErrorResponse with error details
        """
        # Get league ID from the league name
        league_id = get_league_id_by_name(league_name)
        if league_id is None:
            logger.error(f"League '{league_name}' not found")
            return ErrorResponse(error=f"League '{league_name}' not found")
        
        # Prepare parameters for the API call
        params = {
            "league": league_id,
            "season": season
        }
        
        # If team name is provided, get team ID and add to params
        if team_name:
            team_id = get_team_id_by_name(team_name)
            if team_id is None:
                logger.error(f"Team '{team_name}' not found")
                return ErrorResponse(error=f"Team '{team_name}' not found")
            params["team"] = team_id
        
        writer = get_stream_writer()
        if not team_name:
            writer(f"Fetching standings for {league_name} season {season}...\n")
        else:
            writer(f"Fetching standings for team {team_name} in {league_name} season {season}...\n")
        
        # Make the API call
        try:
            response = call_football_api("GET", "standings", params=params)
            
            if isinstance(response, ValidResponse) and "response" in response.data and response.data["response"]:
                logger.info(f"Successfully retrieved standings data")
                return response
            elif isinstance(response, ValidResponse):
                logger.warning(f"No standings data found for {league_name} season {season}")
                return ErrorResponse(error=f"No standings data found for {league_name} season {season}")
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error fetching standings: {str(e)}")
            return ErrorResponse(error=f"Error fetching standings: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetStandingsInput(BaseModel):
            league_name: str = Field(..., description="Name of the league or cup (e.g., 'Premier League', 'La Liga')")
            season: int = Field(..., description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            team_name: Optional[str] = Field(None, description="Optional team name to filter standings for specific team")

        return StructuredTool.from_function(
            self.get_standings,
            name="get_standings",
            description="Get the standings for a league or specific team in a league.",
            args_schema=GetStandingsInput,
            return_direct=False
        )
