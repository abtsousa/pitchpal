"""
Last fixtures tool for retrieving past matches.
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


class GetLastFixturesTool:
    """Tool for retrieving past football fixtures."""
    
    @staticmethod
    def get_last_fixtures(
        league_name: str | None = None,
        season: int | None = None,
        team_name: str | None = None,
        last_count: int = 5,
        date_from: str | None = None,
        date_to: str | None = None
    ) -> Response:
        """
        Get the last fixtures for a league, team, or date range.
        
        Args:
            league_name: Name of the league or cup (e.g., "Premier League", "La Liga")
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            team_name: Optional team name to filter fixtures for specific team
            last_count: Optional number of last fixtures to retrieve (max 20)
            date_from: Optional start date in YYYY-MM-DD format
            date_to: Optional end date in YYYY-MM-DD format
            
        Returns:
            ValidResponse with fixtures data or ErrorResponse with error details
        """
        params = {}
        
        # Add league parameter if provided
        if league_name:
            league_id = get_league_id_by_name(league_name)
            if league_id is None:
                logger.error(f"League '{league_name}' not found")
                return ErrorResponse(error=f"League '{league_name}' not found")
            params["league"] = league_id
        
        # Add season parameter if provided
        if season:
            params["season"] = season
        
        # Add team parameter if provided
        if team_name:
            team_id = get_team_id_by_name(team_name)
            if team_id is None:
                logger.error(f"Team '{team_name}' not found")
                return ErrorResponse(error=f"Team '{team_name}' not found")
            params["team"] = team_id
        
        # Add last parameter (number of last fixtures)
        if last_count and last_count > 0:
            params["last"] = min(last_count, 20)  # API limit is 20
        
        # Add date range parameters if provided
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to
        
        writer = get_stream_writer()
        writer(f"Fetching last {last_count} fixtures")
        if league_name:
            writer(f" for {league_name}")
        if team_name:
            writer(f" for team {team_name}")
        writer("...\n")
        
        # Make the API call
        try:
            response = call_football_api("GET", "fixtures", params=params)
            
            if isinstance(response, ValidResponse) and "response" in response.data:
                logger.info(f"Successfully retrieved {len(response.data['response'])} fixtures")
                return response
            elif isinstance(response, ValidResponse):
                logger.warning(f"No fixtures found")
                return ErrorResponse(error="No fixtures found")
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error fetching fixtures: {str(e)}")
            return ErrorResponse(error=f"Error fetching fixtures: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetLastFixturesInput(BaseModel):
            league_name: Optional[str] = Field(None, description="Name of the league or cup (e.g., 'Premier League', 'La Liga')")
            season: Optional[int] = Field(None, description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            team_name: Optional[str] = Field(None, description="Optional team name to filter fixtures for specific team")
            last_count: int = Field(5, description="Number of last fixtures to retrieve (max 20)")
            date_from: Optional[str] = Field(None, description="Optional start date in YYYY-MM-DD format")
            date_to: Optional[str] = Field(None, description="Optional end date in YYYY-MM-DD format")

        return StructuredTool.from_function(
            self.get_last_fixtures,
            name="get_last_fixtures",
            description="Get the last fixtures for a league, team, or date range.",
            args_schema=GetLastFixturesInput,
            return_direct=False
        )
