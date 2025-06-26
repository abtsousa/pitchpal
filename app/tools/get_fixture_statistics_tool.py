"""
Fixture statistics tool for retrieving match statistics.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from utils.football_api_utils import (
    call_football_api, Response, ValidResponse, ErrorResponse
)
from utils.getters import get_team_id_by_name

logger = logging.getLogger(__name__)


class GetFixtureStatisticsTool:
    """Tool for retrieving fixture statistics."""
    
    @staticmethod
    def get_fixture_statistics(
        fixture_id: int,
        team_name: str | None = None,
        stats_type: str | None = None,
        half: bool = False
    ) -> Response:
        """
        Get statistics for a specific fixture.
        
        Args:
            fixture_id: The ID of the fixture
            team_name: Optional team name to filter statistics for specific team
            stats_type: Optional type of statistics to filter
            half: Whether to include halftime statistics (available from 2024 season)
            
        Returns:
            ValidResponse with fixture statistics data or ErrorResponse with error details
        """
        params: dict = {
            "fixture": fixture_id
        }
        
        # Add team parameter if provided
        if team_name:
            team_id = get_team_id_by_name(team_name)
            if team_id is None:
                logger.error(f"Team '{team_name}' not found")
                return ErrorResponse(error=f"Team '{team_name}' not found")
            params["team"] = team_id
        
        # Add type parameter if provided
        if stats_type:
            params["type"] = stats_type
        
        # Add half parameter if requested
        if half:
            params["half"] = "true"
        
        writer = get_stream_writer()
        writer(f"Fetching statistics for fixture {fixture_id}")
        if team_name:
            writer(f" for team {team_name}")
        if half:
            writer(" (including halftime stats)")
        writer("...\n")
        
        # Make the API call
        try:
            response = call_football_api("GET", "fixtures/statistics", params=params)
            
            if isinstance(response, ValidResponse) and "response" in response.data:
                logger.info(f"Successfully retrieved statistics for fixture {fixture_id}")
                return response
            elif isinstance(response, ValidResponse):
                logger.warning(f"No statistics found for fixture {fixture_id}")
                return ErrorResponse(error=f"No statistics found for fixture {fixture_id}")
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error fetching fixture statistics: {str(e)}")
            return ErrorResponse(error=f"Error fetching fixture statistics: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetFixtureStatisticsInput(BaseModel):
            fixture_id: int = Field(..., description="The ID of the fixture")
            team_name: Optional[str] = Field(None, description="Optional team name to filter statistics for specific team")
            stats_type: Optional[str] = Field(None, description="Optional type of statistics to filter")
            half: bool = Field(False, description="Whether to include halftime statistics (available from 2024 season)")

        return StructuredTool.from_function(
            self.get_fixture_statistics,
            name="get_fixture_statistics",
            description="Get statistics for a specific fixture, optionally filtered by team or statistics type.",
            args_schema=GetFixtureStatisticsInput,
            return_direct=False
        )
