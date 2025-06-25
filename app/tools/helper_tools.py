"""
Helper tools for listing leagues and teams, and searching teams by code.
"""

import json
import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


class HelperTools:
    """Collection of helper tools for league and team discovery."""
    
    @staticmethod
    def list_leagues() -> list[str]:
        """
        List all available leagues.

        Returns:
            List of league names
        """
        try:
            leagues = json.load(open("cache/top_leagues.json"))
            return list(leagues.keys())
        except FileNotFoundError:
            logger.warning("top_leagues.json not found.")
            return []

    @staticmethod
    def list_teams(league_name: str | None = None) -> list[str]:
        """
        List all available teams from cached data.

        Args:
            league_name: Optional league name to filter teams by league

        Returns:
            List of team names
        """
        try:
            teams = json.load(open("cache/top_teams.json"))
            if league_name:
                # Filter teams by league if specified
                filtered_teams = [
                    team_name for team_name, team_data in teams.items()
                    if league_name in team_data.get("leagues", [])
                ]
                return filtered_teams
            return list(teams.keys())
        except FileNotFoundError:
            logger.warning("top_teams.json not found.")
            return []

    @staticmethod
    def search_teams_by_code(team_code: str, league_name: str | None = None) -> list[dict]:
        """
        Search for all teams with a specific code.

        Args:
            team_code: Code of the team (e.g., "MUN", "LIV")
            league_name: Optional league name to filter teams by league

        Returns:
            List of team dictionaries with name, id, code, and leagues
        """
        try:
            teams = json.load(open("cache/top_teams.json"))
        except FileNotFoundError:
            logger.warning("top_teams.json not found.")
            return []

        matching_teams = []
        for team_name, team_data in teams.items():
            if team_data.get("code") and team_data["code"].upper() == team_code.upper():
                # If league filter is specified, check if team participates in that league
                if league_name:
                    team_leagues = team_data.get("leagues", [])
                    if league_name not in team_leagues:
                        continue
                
                team_info = {
                    "name": team_name,
                    "id": team_data["id"],
                    "code": team_data["code"],
                    "leagues": team_data.get("leagues", [])
                }
                matching_teams.append(team_info)

        return matching_teams

    def as_tools(self) -> list[StructuredTool]:
        """
        Return all helper functions as LangChain StructuredTools.
        
        Returns:
            List of StructuredTool instances for use with LangChain agents
        """
        # Create tools for helper functions
        class ListLeaguesInput(BaseModel):
            pass  # No parameters needed

        class ListTeamsInput(BaseModel):
            league_name: Optional[str] = Field(None, description="Optional league name to filter teams by league")

        class SearchTeamsByCodeInput(BaseModel):
            team_code: str = Field(..., description="Code of the team (e.g., 'MUN', 'LIV', 'SLB')")
            league_name: Optional[str] = Field(None, description="Optional league name to filter teams by league")

        # Create the tools
        list_leagues_tool = StructuredTool.from_function(
            self.list_leagues,
            name="list_leagues",
            description="List all available leagues from cached data.",
            args_schema=ListLeaguesInput,
            return_direct=False
        )

        list_teams_tool = StructuredTool.from_function(
            self.list_teams,
            name="list_teams",
            description="List all available teams, optionally filtered by league.",
            args_schema=ListTeamsInput,
            return_direct=False
        )

        search_teams_by_code_tool = StructuredTool.from_function(
            self.search_teams_by_code,
            name="search_teams_by_code",
            description="Search for teams by their code (e.g., 'MUN' for Manchester United, 'SLB' for Benfica).",
            args_schema=SearchTeamsByCodeInput,
            return_direct=False
        )

        return [list_leagues_tool, list_teams_tool, search_teams_by_code_tool]
