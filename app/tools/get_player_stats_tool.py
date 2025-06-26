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
    
    @staticmethod
    def format_player_stats(stats_response: Response) -> str:
        """
        Format the player statistics response into a readable string.
        
        Args:
            stats_response: Response from get_player_stats function
            
        Returns:
            Formatted string with player statistics
        """
        if not isinstance(stats_response, ValidResponse):
            return f"Error: {stats_response.error}" #type: ignore
        
        data = stats_response.data
        if "response" not in data or not data["response"]:
            return "No player data found"
        
        players = data["response"]
        
        # If multiple players found, show summary and loop through all
        if len(players) > 1:
            result = f"**{len(players)} players found:**\n\n"
            
            for i, player_data in enumerate(players, 1):
                result += f"**Player {i}:**\n"
                result += GetPlayerStatsTool.format_single_player_stats(player_data)
                result += "\n" + "="*60 + "\n\n"
            
            return result
        else:
            # Single player - use existing format
            return GetPlayerStatsTool.format_single_player_stats(players[0])

    @staticmethod
    def format_single_player_stats(player_data: dict) -> str:
        """
        Format statistics for a single player.
        
        Args:
            player_data: Single player data dictionary from API response
            
        Returns:
            Formatted string with player statistics
        """
        player_info = player_data["player"]
        statistics = player_data["statistics"]
        
        # Format player basic info
        result = f"**{player_info['name']}** (Age: {player_info['age']})\n"
        result += f"Born: {player_info['birth']['date']} in {player_info['birth']['place']}, {player_info['birth']['country']}\n"
        result += f"Nationality: {player_info['nationality']}\n"
        result += f"Height: {player_info['height']}, Weight: {player_info['weight']}\n"
        result += f"Injured: {'Yes' if player_info['injured'] else 'No'}\n\n"
        
        # Calculate totals across all seasons/competitions
        total_games = sum(stat['games']['appearences'] or 0 for stat in statistics)
        total_starts = sum(stat['games']['lineups'] or 0 for stat in statistics)
        total_minutes = sum(stat['games']['minutes'] or 0 for stat in statistics)
        total_goals = sum(stat['goals']['total'] or 0 for stat in statistics)
        total_assists = sum(stat['goals']['assists'] or 0 for stat in statistics)
        total_yellow = sum(stat['cards']['yellow'] or 0 for stat in statistics)
        total_red = sum(stat['cards']['red'] or 0 for stat in statistics)
        
        # Calculate additional totals
        total_shots = sum(stat['shots']['total'] or 0 for stat in statistics)
        total_shots_on_target = sum(stat['shots']['on'] or 0 for stat in statistics)
        total_penalties_scored = sum(stat['penalty']['scored'] or 0 for stat in statistics)
        total_penalties_missed = sum(stat['penalty']['missed'] or 0 for stat in statistics)
        total_passes = sum(stat['passes']['total'] or 0 for stat in statistics)
        total_key_passes = sum(stat['passes']['key'] or 0 for stat in statistics)
        total_duels = sum(stat['duels']['total'] or 0 for stat in statistics)
        total_duels_won = sum(stat['duels']['won'] or 0 for stat in statistics)
        total_dribbles = sum(stat['dribbles']['attempts'] or 0 for stat in statistics)
        total_dribbles_success = sum(stat['dribbles']['success'] or 0 for stat in statistics)
        
        # Calculate average rating (only from seasons where rating exists)
        ratings = [float(stat['games']['rating']) for stat in statistics if stat['games']['rating'] is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Add totals section
        result += "**Total statistics:**\n"
        result += f"Games: {total_games} appearances, {total_starts} starts, {total_minutes} minutes\n"
        result += f"Goals: {total_goals}, Assists: {total_assists}\n"
        if total_shots > 0:
            result += f"Shots: {total_shots} total, {total_shots_on_target} on target\n"
        if total_penalties_scored > 0 or total_penalties_missed > 0:
            result += f"Penalties: {total_penalties_scored} scored, {total_penalties_missed} missed\n"
        if avg_rating:
            result += f"Average rating: {avg_rating:.2f}\n"
        if total_yellow > 0 or total_red > 0:
            result += f"Cards: {total_yellow} yellow, {total_red} red\n"
        
        # Add other stats if they exist
        other_total_stats = []
        if total_passes > 0:
            other_total_stats.append(f"Passes: {total_passes}")
        if total_key_passes > 0:
            other_total_stats.append(f"Key passes: {total_key_passes}")
        if total_duels > 0:
            other_total_stats.append(f"Duels: {total_duels_won}/{total_duels} won")
        if total_dribbles > 0:
            other_total_stats.append(f"Dribbles: {total_dribbles_success}/{total_dribbles} successful")
        
        if other_total_stats:
            result += f"Other: {', '.join(other_total_stats)}\n"
        
        result += "\n"
        
        # Group statistics by season and league
        result += "**Statistics by Season and Competition:**\n\n"
        
        # Sort statistics by season (descending) and then by league
        sorted_stats = sorted(statistics, key=lambda x: (
            x['league']['season'] or 0, 
            x['league']['name'] or ''
        ), reverse=True)
        
        for stat in sorted_stats:
            team = stat['team']
            league = stat['league']
            games = stat['games']
            goals = stat['goals']
            
            # Skip entries with no appearances
            if games['appearences'] == 0:
                continue
                
            season = league['season'] if league['season'] else 'Unknown'
            league_name = league['name'] if league['name'] else 'Unknown League'
            
            result += f"**{season} - {league_name}** ({team['name']})\n"
            
            # Game statistics
            result += f"  Games: {games['appearences']} appearances, {games['lineups']} starts, {games['minutes']} minutes"
            if games['rating']:
                result += f", Rating: {games['rating']}"
            result += "\n"
            
            # Goals and assists
            if goals['total'] is not None or goals['assists'] is not None:
                goals_str = f"  Goals: {goals['total'] if goals['total'] is not None else 0}"
                if goals['assists'] is not None:
                    goals_str += f", Assists: {goals['assists']}"
                result += goals_str + "\n"
            
            # Shots
            shots = stat['shots']
            if shots['total'] is not None:
                result += f"  Shots: {shots['total']} total, {shots['on']} on target\n"
            
            # Cards
            cards = stat['cards']
            if cards['yellow'] > 0 or cards['red'] > 0:
                result += f"  Cards: {cards['yellow']} yellow, {cards['red']} red\n"
            
            # Penalties
            penalty = stat['penalty']
            if penalty['scored'] is not None or penalty['missed'] is not None:
                pen_str = "  Penalties:"
                if penalty['scored'] is not None:
                    pen_str += f" {penalty['scored']} scored"
                if penalty['missed'] is not None:
                    pen_str += f", {penalty['missed']} missed"
                result += pen_str + "\n"
            
            # Other notable stats
            passes = stat['passes']
            duels = stat['duels']
            dribbles = stat['dribbles']
            
            other_stats = []
            if passes['total'] is not None:
                other_stats.append(f"Passes: {passes['total']}")
            if passes['key'] is not None:
                other_stats.append(f"Key passes: {passes['key']}")
            if duels['total'] is not None and duels['won'] is not None:
                other_stats.append(f"Duels: {duels['won']}/{duels['total']} won")
            if dribbles['attempts'] is not None and dribbles['success'] is not None:
                other_stats.append(f"Dribbles: {dribbles['success']}/{dribbles['attempts']} successful")
            
            if other_stats:
                result += f"  Other: {', '.join(other_stats)}\n"
            
            result += "\n"
        
        return result
    
    @staticmethod
    def get_player_stats_formatted(
        player_name: str,
        team_name: str | None = None,
        league_name: str | None = None,
        season: int | None = None,
        page: int = 1
    ) -> str:
        """
        Get detailed statistics for a player by name, formatted for readability.
        Can be filtered by team, league, and season.

        Args:
            player_name: Name of the player (minimum 4 characters required by API)
            team_name: Optional team name to filter players by team
            league_name: Optional league name to filter players by league
            season: Optional season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            page: Optional page number for pagination (default 1)

        Returns:
            Compact formatted string with player statistics or error message
        """
        # Get the raw stats
        stats_response = GetPlayerStatsTool.get_player_stats(player_name, team_name, league_name, season, page)
        
        # Format and return using compact format (much less verbose than raw JSON)
        return GetPlayerStatsTool.format_player_stats(stats_response)

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
            self.get_player_stats_formatted,
            name="get_player_stats",
            description="Returns comprehensive stats for a player in a specified team (club or national team) or league: games, goals, assists, shots, passes, tackles, cards, penalties, fouls, and dribbles.",
            args_schema=GetPlayerStatsInput,
            return_direct=False
        )
