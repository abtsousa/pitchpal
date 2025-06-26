"""
Match events tool for retrieving match events (goals, cards, substitutions, etc.).
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


class GetMatchEventsTool:
    """Tool for retrieving match events."""
    
    @staticmethod
    def get_match_events(
        fixture_id: int,
        team_name: str | None = None,
        player_name: str | None = None,
        event_type: str | None = None
    ) -> Response:
        """
        Get the events from a fixture.
        
        Available event types:
        - Goal: Normal Goal, Own Goal, Penalty, Missed Penalty
        - Card: Yellow Card, Red Card
        - Subst: Substitution [1, 2, 3...]
        - VAR: Goal cancelled, Penalty confirmed (available from 2020-2021 season)
        
        Args:
            fixture_id: The ID of the fixture (required)
            team_name: Optional team name to filter events by team
            player_name: Optional player name to filter events by player
            event_type: Optional event type to filter by (Goal, Card, Subst, VAR)
            
        Returns:
            ValidResponse with events data or ErrorResponse with error details
        """
        # Prepare parameters for the API call
        params = {
            "fixture": fixture_id
        }
        
        # Add team parameter if provided
        if team_name:
            team_id = get_team_id_by_name(team_name)
            if team_id is None:
                logger.error(f"Team '{team_name}' not found")
                return ErrorResponse(error=f"Team '{team_name}' not found")
            params["team"] = team_id
        
        # Add event type parameter if provided
        if event_type:
            # Validate event type
            valid_types = ["Goal", "Card", "Subst", "VAR"]
            if event_type not in valid_types:
                logger.error(f"Invalid event type '{event_type}'. Valid types: {valid_types}")
                return ErrorResponse(error=f"Invalid event type '{event_type}'. Valid types: {valid_types}")
            params["type"] = event_type
        
        writer = get_stream_writer()
        writer(f"Fetching events for fixture {fixture_id}")
        if team_name:
            writer(f" (filtering for team: {team_name})")
        if event_type:
            writer(f" (filtering for event type: {event_type})")
        writer("...\n")
        
        # Make the API call
        try:
            response = call_football_api("GET", "fixtures/events", params=params)
            
            if isinstance(response, ValidResponse) and "response" in response.data:
                events = response.data["response"]
                
                # Additional filtering by player name if provided (API doesn't support this directly)
                if player_name and events:
                    filtered_events = []
                    for event in events:
                        player = event.get("player", {})
                        if player and player.get("name"):
                            if player_name.lower() in player["name"].lower() or player["name"].lower() in player_name.lower():
                                filtered_events.append(event)
                    
                    logger.info(f"Filtered {len(filtered_events)} events for player '{player_name}'")
                    return ValidResponse(data={"response": filtered_events})
                
                logger.info(f"Successfully retrieved {len(events)} events")
                return response
            elif isinstance(response, ValidResponse):
                logger.warning(f"No events found for fixture {fixture_id}")
                return ErrorResponse(error=f"No events found for fixture {fixture_id}")
            else:
                return response  # Already an ErrorResponse
                
        except Exception as e:
            logger.error(f"Error fetching match events: {str(e)}")
            return ErrorResponse(error=f"Error fetching match events: {str(e)}")

    @staticmethod
    def get_match_events_by_teams(
        league_name: str,
        season: int,
        home_team: str,
        away_team: str,
        team_name: str | None = None,
        player_name: str | None = None,
        event_type: str | None = None
    ) -> Response:
        """
        Get the events from a match between two specific teams.
        
        This is a wrapper function that first finds the fixture between the teams,
        then retrieves the events for that fixture.
        
        Available event types:
        - Goal: Normal Goal, Own Goal, Penalty, Missed Penalty
        - Card: Yellow Card, Red Card
        - Subst: Substitution [1, 2, 3...]
        - VAR: Goal cancelled, Penalty confirmed (available from 2020-2021 season)
        
        Args:
            league_name: Name of the league or cup (e.g., "Premier League", "La Liga")
            season: Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)
            home_team: Name of the home team
            away_team: Name of the away team
            team_name: Optional team name to filter events by team
            player_name: Optional player name to filter events by player
            event_type: Optional event type to filter by (Goal, Card, Subst, VAR)
            
        Returns:
            ValidResponse with events data or ErrorResponse with error details
        """
        from .get_specific_fixture_tool import GetSpecificFixtureTool
        
        # First, find the fixture between the two teams
        logger.info(f"Looking for fixture: {home_team} vs {away_team} in {league_name} season {season}")
        
        fixture_response = GetSpecificFixtureTool.get_specific_fixture(league_name, season, home_team, away_team)
        
        if isinstance(fixture_response, ErrorResponse):
            return fixture_response
        
        if not isinstance(fixture_response, ValidResponse) or not fixture_response.data.get("response"):
            return ErrorResponse(error=f"No fixture found between {home_team} and {away_team} in {league_name} season {season}")
        
        fixtures = fixture_response.data["response"]
        
        # Use the first fixture if multiple matches found
        if len(fixtures) > 1:
            logger.info(f"Found {len(fixtures)} fixtures between these teams. Using the first one.")
        
        fixture = fixtures[0]
        fixture_id = fixture["fixture"]["id"]
        
        logger.info(f"Found fixture ID {fixture_id}, now getting events...")
        
        # Now get the events for this fixture
        return GetMatchEventsTool.get_match_events(fixture_id, team_name, player_name, event_type)

    def as_tool(self) -> StructuredTool:
        """
        Return the function as a LangChain StructuredTool.
        
        Returns:
            StructuredTool instance for use with LangChain agents
        """
        class GetMatchEventsByTeamsInput(BaseModel):
            league_name: str = Field(..., description="Name of the league or cup (e.g., 'Premier League', 'La Liga')")
            season: int = Field(..., description="Season FIRST year (4 digits, e.g., 2024 for 2024/2025 season)")
            home_team: str = Field(..., description="Name of the home team")
            away_team: str = Field(..., description="Name of the away team")
            team_name: Optional[str] = Field(None, description="Optional team name to filter events by team")
            player_name: Optional[str] = Field(None, description="Optional player name to filter events by player")
            event_type: Optional[str] = Field(None, description="Optional event type to filter by (Goal, Card, Subst, VAR)")

        return StructuredTool.from_function(
            self.get_match_events_by_teams,
            name="get_match_events_by_teams",
            description="Get the events from a match between two specific teams (automatically finds the fixture and retrieves events).",
            args_schema=GetMatchEventsByTeamsInput,
            return_direct=False
        )
