"""
Top scorers tool for retrieving top goal scorers in a league.
"""

import logging
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from utils.football_api_utils import (
    call_football_api, Response, ValidResponse, ErrorResponse
)
from utils.getters import get_league_id_by_name

logger = logging.getLogger(__name__)


class GetTopScorersTool:
    """Tool for retrieving top scorers in a league."""
    
    @staticmethod
    def get_top_scorers(
        league_name: str,
        season: int
    ) -> Response:
        """
        Get the top scorers for a specific league and season.
        
        Args:
            league_name: Name of the league (e.g., "Premier League", "La Liga")
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            
        Returns:
            ValidResponse with top scorers data or ErrorResponse with error details
        """
        # Get league ID from name
        league_id = get_league_id_by_name(league_name)
        if league_id is None:
            logger.error(f"League '{league_name}' not found")
            return ErrorResponse(error=f"League '{league_name}' not found")
        
        params = {
            "league": league_id,
            "season": season
        }
        
        writer = get_stream_writer()
        writer(f"Fetching top scorers for {league_name} season {season}...\n")
        
        # Make the API call
        try:
            response = call_football_api("GET", "players/topscorers", params=params)
            
            if isinstance(response, ValidResponse) and "response" in response.data:
                logger.info(f"Successfully retrieved {len(response.data['response'])} top scorers")
                return response
            elif isinstance(response, ValidResponse):
                logger.warning(f"No top scorers found")
                return ErrorResponse(error="No top scorers found")
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error fetching top scorers: {str(e)}")
            return ErrorResponse(error=f"Error fetching top scorers: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetTopScorersInput(BaseModel):
            league_name: str = Field(..., description="Name of the league (e.g., 'Premier League', 'La Liga')")
            season: int = Field(..., description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")

        return StructuredTool.from_function(
            self.get_top_scorers,
            name="get_top_scorers",
            description="Get the top scorers for a specific league and season.",
            args_schema=GetTopScorersInput,
            return_direct=False
        )
