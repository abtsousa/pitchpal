from .get_standings_tool import GetStandingsTool

def get_all_tools():
    """
    Get all available tools as a list of LangChain StructuredTool instances.
    
    Returns:
        List of StructuredTool instances ready for use with LangChain agents
    """
    tools = []
    
    # Add standings tool
    standings_tool = GetStandingsTool()
    tools.append(standings_tool.as_tool())
    
    # TODO add more tools
    
    return tools