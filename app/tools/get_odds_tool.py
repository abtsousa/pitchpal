"""
Odds tool for retrieving betting odds for a fixture or league.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer

from utils.football_api_utils import (
    call_football_api, Response, ValidResponse, ErrorResponse
)
from utils.getters import get_league_id_by_name

logger = logging.getLogger(__name__)


class GetOddsTool:
    """Tool for retrieving odds for a fixture or league."""
    
    @staticmethod
    def get_odds(
        fixture_id: int | None = None,
        league_name: str | None = None,
        season: int | None = None,
        date: str | None = None,
        timezone: str | None = None,
        page: int = 1,
        bookmaker_id: int | None = None,
        bet_id: int | None = None
    ) -> Response:
        """
        Get odds for a fixture, league, or other parameters.
        
        Args:
            fixture_id: The ID of the fixture
            league_name: Name of the league (e.g., "Premier League", "La Liga")
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            date: A valid date in YYYY-MM-DD format
            timezone: A valid timezone string
            page: Page number for pagination
            bookmaker_id: The ID of the bookmaker
            bet_id: The ID of the bet
        Returns:
            ValidResponse with odds data or ErrorResponse with error details
        """
        params: dict = {}
        if fixture_id is not None:
            params["fixture"] = fixture_id
        if league_name:
            league_id = get_league_id_by_name(league_name)
            if league_id is None:
                logger.error(f"League '{league_name}' not found")
                return ErrorResponse(error=f"League '{league_name}' not found")
            params["league"] = league_id
        if season:
            params["season"] = season
        if date:
            params["date"] = date
        if timezone:
            params["timezone"] = timezone
        if page:
            params["page"] = page
        if bookmaker_id:
            params["bookmaker"] = bookmaker_id
        if bet_id:
            params["bet"] = bet_id
        
        writer = get_stream_writer()
        writer(f"Fetching odds")
        if fixture_id:
            writer(f" for fixture {fixture_id}")
        if league_name:
            writer(f" in league {league_name}")
        if bookmaker_id:
            writer(f" (bookmaker {bookmaker_id})")
        writer("...\n")
        
        try:
            response = call_football_api("GET", "odds", params=params)
            if isinstance(response, ValidResponse) and "response" in response.data:
                logger.info(f"Successfully retrieved odds")
                return response
            elif isinstance(response, ValidResponse):
                logger.warning(f"No odds found")
                return ErrorResponse(error="No odds found")
            else:
                return response  # Already an ErrorResponse
        except Exception as e:
            logger.error(f"Error fetching odds: {str(e)}")
            return ErrorResponse(error=f"Error fetching odds: {str(e)}")

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetOddsInput(BaseModel):
            fixture_id: Optional[int] = Field(None, description="The ID of the fixture")
            league_name: Optional[str] = Field(None, description="Name of the league (e.g., 'Premier League', 'La Liga')")
            season: Optional[int] = Field(None, description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            date: Optional[str] = Field(None, description="A valid date in YYYY-MM-DD format")
            timezone: Optional[str] = Field(None, description="A valid timezone string")
            page: int = Field(1, description="Page number for pagination")
            bookmaker_id: Optional[int] = Field(None, description="The ID of the bookmaker")
            bet_id: Optional[int] = Field(None, description="The ID of the bet")

        return StructuredTool.from_function(
            self.get_odds,
            name="get_odds",
            description="Get odds for a fixture, league, or other parameters.",
            args_schema=GetOddsInput,
            return_direct=False
        )
