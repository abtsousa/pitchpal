from .get_standings_tool import GetStandingsTool
from .get_next_fixtures_tool import GetNextFixturesTool
from .get_last_fixtures_tool import GetLastFixturesTool
from .get_specific_fixture_tool import GetSpecificFixtureTool
from .get_match_events_tool import GetMatchEventsTool
from .get_specific_player_stats_tool import GetPlayerStatsTool
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
    
    # Add helper tools
    # helper_tools = HelperTools()
    # tools.extend(helper_tools.as_tools())
    
    return tools