from .get_standings_tool import GetStandingsTool
from .get_next_fixtures_tool import GetNextFixturesTool
from .get_last_fixtures_tool import GetLastFixturesTool
from .get_specific_fixture_tool import GetSpecificFixtureTool
from .get_match_events_tool import GetMatchEventsTool
from .get_specific_player_stats_tool import GetPlayerStatsTool
from .get_head_to_head_fixtures_tool import GetHeadToHeadFixturesTool
from .get_top_scorers_tool import GetTopScorersTool
from .get_fixture_statistics_tool import GetFixtureStatisticsTool
from .get_odds_tool import GetOddsTool
from .helper_tools import HelperTools
from langchain_core.tools import StructuredTool

def get_all_tools() -> list[StructuredTool]:
    """
    Get all available tools as a list of LangChain StructuredTool instances.
    
    Returns:
        List of StructuredTool instances ready for use with LangChain agents
    """
    tools = []
    
    # Add standings tool
    standings_tool = GetStandingsTool()
    tools.append(standings_tool.as_tool())
    
    # Add next fixtures tool
    next_fixtures_tool = GetNextFixturesTool()
    tools.append(next_fixtures_tool.as_tool())
    
    # Add last fixtures tool
    last_fixtures_tool = GetLastFixturesTool()
    tools.append(last_fixtures_tool.as_tool())
    
    # Add specific fixture tool
    specific_fixture_tool = GetSpecificFixtureTool()
    tools.append(specific_fixture_tool.as_tool())
    
    # Add match events tool
    match_events_tool = GetMatchEventsTool()
    tools.append(match_events_tool.as_tool())
    
    # Add player stats tool
    player_stats_tool = GetPlayerStatsTool()
    tools.append(player_stats_tool.as_tool())

    # Add head-to-head fixtures tool
    h2h_fixtures_tool = GetHeadToHeadFixturesTool()
    tools.append(h2h_fixtures_tool.as_tool())
    
    # Add top scorers tool
    top_scorers_tool = GetTopScorersTool()
    tools.append(top_scorers_tool.as_tool())

    # Add fixture statistics tool
    fixture_statistics_tool = GetFixtureStatisticsTool()
    tools.append(fixture_statistics_tool.as_tool())
    
    # Add odds tool
    odds_tool = GetOddsTool()
    tools.append(odds_tool.as_tool())
    
    # Add helper tools
    # helper_tools = HelperTools()
    # tools.extend(helper_tools.as_tools())
    
    return tools