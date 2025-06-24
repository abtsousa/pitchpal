"""
Helper functions for getting league and team IDs by name.
"""

import json
import logging
from .football_api_utils import call_football_api, ValidResponse

logger = logging.getLogger(__name__)


def get_league_id_by_name(league_name: str) -> int | None:
    """
    Get the league ID by its name.

    Args:
        league_name: Name of the league

    Returns:
        League ID if found, otherwise None
    """
    try:
        leagues = json.load(open("cache/top_leagues.json"))
    except FileNotFoundError:
        logger.warning("top_leagues.json not found. Will fetch from API...")
        leagues = {}

    # Exact match first
    if league_name in leagues:
        return leagues[league_name]

    # If no match is found, fetch it from the API:
    logger.warning(
        f"League '{league_name}' not found in selected leagues. Fetching from API..."
    )
    response = call_football_api("GET", "leagues", params={"search": league_name})
    if isinstance(response, ValidResponse):
        # Work directly with the API response data
        if 'response' in response.data:
            for item in response.data['response']:
                league = item.get('league', {})
                league_api_name = league.get('name', '')
                league_id = league.get('id')
                
                # Check if this league matches what we're looking for
                if (league_api_name.lower() in league_name.lower() or 
                    league_name.lower() in league_api_name.lower()):
                    return league_id
        
        logger.error(f"League '{league_name}' not found in API response.")

    return None


def get_team_id_by_name(team_name: str, league_name: str | None = None) -> int | None:
    """
    Get the team ID by its name.

    Args:
        team_name: Name of the team
        league_name: Optional league name to filter teams by league

    Returns:
        Team ID if found, otherwise None
    """
    try:
        teams = json.load(open("cache/top_teams.json"))
    except FileNotFoundError:
        logger.warning("top_teams.json not found. Will fetch from API...")
        teams = {}

    # Exact match first
    if team_name in teams:
        team_data = teams[team_name]
        # If league filter is specified, check if team participates in that league
        if league_name:
            team_leagues = team_data.get("leagues", [])
            if league_name not in team_leagues:
                logger.warning(f"Team '{team_name}' found but does not participate in '{league_name}'")
                # Continue to partial match or API search
            else:
                return team_data["id"]
        else:
            return team_data["id"]

    # If the team is not found, try partial match
    for team_key, team_data in teams.items():
        if team_name.lower() in team_key.lower() or team_key.lower() in team_name.lower():
            # If league filter is specified, check if team participates in that league
            if league_name:
                team_leagues = team_data.get("leagues", [])
                if league_name not in team_leagues:
                    continue
            return team_data["id"]

    # If no match is found, fetch it from the API:
    filter_msg = f" in league '{league_name}'" if league_name else ""
    logger.warning(
        f"Team '{team_name}'{filter_msg} not found in cached teams. Fetching from API..."
    )
    response = call_football_api("GET", "teams", params={"search": team_name})

    if isinstance(response, ValidResponse):
        for team_data in response.data["response"]:
            team = team_data["team"]
            if team["name"].lower() == team_name.lower():
                return team["id"]

    return None
