"""
Head-to-head fixtures tool for retrieving fixtures between two specific teams.
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


class GetHeadToHeadFixturesTool:
    """Tool for retrieving head-to-head fixtures between two teams."""
    
    @staticmethod
    def get_head_to_head_fixtures(
        team1_name: str,
        team2_name: str,
        date: str | None = None,
        league_name: str | None = None,
        season: int | None = None,
        last: int | None = None,
        next: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        status: str | None = None,
        venue_id: int | None = None,
        timezone: str | None = None
    ) -> Response:
        """
        Get head-to-head fixtures between two teams.
        
        Args:
            team1_name: Name of the first team
            team2_name: Name of the second team
            date: Specific date in YYYY-MM-DD format
            league_name: Name of the league (optional)
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            last: For the X last fixtures
            next: For the X next fixtures
            from_date: From date in YYYY-MM-DD format
            to_date: To date in YYYY-MM-DD format
            status: Fixture status (NS, NS-PST-FT, etc.)
            venue_id: The venue id of the fixture
            timezone: A valid timezone
            
        Returns:
            ValidResponse with head-to-head fixtures data or ErrorResponse with error details
        """
        # Get team IDs
        team1_id = get_team_id_by_name(team1_name)
        if team1_id is None:
            logger.error(f"Team '{team1_name}' not found")
            return ErrorResponse(error=f"Team '{team1_name}' not found")
        
        team2_id = get_team_id_by_name(team2_name)
        if team2_id is None:
            logger.error(f"Team '{team2_name}' not found")
            return ErrorResponse(error=f"Team '{team2_name}' not found")
        
        writer = get_stream_writer()
        writer(f"Getting head-to-head fixtures between {team1_name} and {team2_name}...\n")
        
        logger.info(f"Getting head-to-head fixtures between {team1_name} and {team2_name}")
        
        # Build the h2h parameter (team1_id-team2_id)
        h2h_param = f"{team1_id}-{team2_id}"
        
        # Build parameters dictionary
        params: dict[str, str | int] = {
            "h2h": h2h_param
        }
        
        # Add league parameter if provided
        if league_name:
            league_id = get_league_id_by_name(league_name)
            if league_id is None:
                logger.error(f"League '{league_name}' not found")
                return ErrorResponse(error=f"League '{league_name}' not found")
            params["league"] = league_id
        
        # Add optional parameters if provided
        if date:
            params["date"] = date
        if season:
            params["season"] = season
        if last:
            params["last"] = last
        if next:
            params["next"] = next
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if status:
            params["status"] = status
        if venue_id:
            params["venue"] = venue_id
        if timezone:
            params["timezone"] = timezone
        
        try:
            response = call_football_api("GET", "fixtures/headtohead", params=params)
            
            if isinstance(response, ValidResponse):
                logger.info(f"Successfully retrieved head-to-head fixtures between {team1_name} and {team2_name}")
                return response
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error getting head-to-head fixtures: {str(e)}")
            return ErrorResponse(error=f"Error getting head-to-head fixtures: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetHeadToHeadFixturesInput(BaseModel):
            team1_name: str = Field(..., description="Name of the first team")
            team2_name: str = Field(..., description="Name of the second team")
            date: Optional[str] = Field(None, description="Specific date in YYYY-MM-DD format")
            league_name: Optional[str] = Field(None, description="Name of the league")
            season: Optional[int] = Field(None, description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            last: Optional[int] = Field(None, description="For the X last fixtures")
            next: Optional[int] = Field(None, description="For the X next fixtures")
            from_date: Optional[str] = Field(None, description="From date in YYYY-MM-DD format")
            to_date: Optional[str] = Field(None, description="To date in YYYY-MM-DD format")
            status: Optional[str] = Field(None, description="Fixture status (NS, NS-PST-FT, etc.)")
            venue_id: Optional[int] = Field(None, description="The venue id of the fixture")
            timezone: Optional[str] = Field(None, description="A valid timezone")

        return StructuredTool.from_function(
            self.get_head_to_head_fixtures,
            name="get_head_to_head_fixtures",
            description="Get head-to-head fixtures between two teams with optional filters for date, league, season, etc.",
            args_schema=GetHeadToHeadFixturesInput,
            return_direct=False
        )
