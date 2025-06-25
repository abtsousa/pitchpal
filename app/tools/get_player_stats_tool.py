"""
Player statistics tool for retrieving player performance data.
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


class GetPlayerStatsTool:
    """Tool for retrieving player statistics."""
    
    @staticmethod
    def get_player_stats(
        player_name: str,
        team_name: str | None = None,
        league_name: str | None = None,
        season: int | None = None,
        page: int = 1
    ) -> Response:
        """
        Returns comprehensive career-wide stats for a player in a specified team (club or national team) or league: games, goals, assists, shots, passes, tackles, cards, penalties, fouls, and dribbles.

        Args:
            player_name: Name of the player (minimum 4 characters)
            team_name: Team name to filter players by team (either this or league_name is required)
            league_name: League name to filter players by league (either this or team_name is required)
            season: Optional season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            page: Optional page number for pagination (default 1)

        Returns:
            ValidResponse with players statistics data or ErrorResponse with error details
        """
        # The API requires at least 4 characters for search in the statistics endpoint
        if len(player_name) < 4:
            logger.error(f"Player name '{player_name}' is too short. Minimum 4 characters required.")
            return ErrorResponse(error=f"Player name '{player_name}' is too short. Minimum 4 characters required.")
        
        writer = get_stream_writer()
        writer(f"Searching for player: {player_name}")
        if team_name:
            writer(f" (team: {team_name})")
        if league_name:
            writer(f" (league: {league_name})")
        if season:
            writer(f" (season: {season})")
        writer("...\n")
        
        # Prepare parameters for the API call
        params = {"search": player_name, "page": page}
        
        # Add optional team parameter
        if team_name:
            team_id = get_team_id_by_name(team_name)
            if team_id is None:
                logger.error(f"Team '{team_name}' not found")
                return ErrorResponse(error=f"Team '{team_name}' not found")
            params["team"] = team_id
        
        # Add optional league parameter
        if league_name:
            league_id = get_league_id_by_name(league_name)
            if league_id is None:
                logger.error(f"League '{league_name}' not found")
                return ErrorResponse(error=f"League '{league_name}' not found")
            params["league"] = league_id
        
        # Add optional season parameter
        if season:
            params["season"] = season
        
        # Search for the player using the statistics API endpoint
        response = call_football_api("GET", "players", params=params)
        
        if isinstance(response, ValidResponse) and "response" in response.data:
            logger.info(f"Found {len(response.data['response'])} players")
            return response
        
        else:
            error_msg = f"Error searching for players '{player_name}': {response.error if isinstance(response, ErrorResponse) else 'Unknown error'}"
            logger.error(error_msg)
            return ErrorResponse(error=error_msg)

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetPlayerStatsInput(BaseModel):
            player_name: str = Field(..., description="Name of the player (minimum 4 characters)")
            team_name: Optional[str] = Field(None, description="Team name to filter players by team (either team_name or league_name is required)")
            league_name: Optional[str] = Field(None, description="League name to filter players by league (either team_name or league_name is required)")
            season: Optional[int] = Field(None, description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            page: int = Field(1, description="Page number for pagination (default 1)")

        return StructuredTool.from_function(
            self.get_player_stats,
            name="get_player_stats",
            description="Returns comprehensive career-wide stats for a player in a specified team (club or national team) or league: games, goals, assists, shots, passes, tackles, cards, penalties, fouls, and dribbles.",
            args_schema=GetPlayerStatsInput,
            return_direct=False
        )
