from typing import Literal
from datetime import datetime

# Default system prompt for the football assistant
DEFAULT_FOOTBALL_PROMPT = (
    "You are {app_name}, a helpful football assistant. "
    "Today is {date}. "
    "Club World Cup is ongoing, but all the other European events have finished. "
    "If the user query does not specify a season, assume it is the latest "
    "(2024/25 for European leagues and 2025 for cups). "
    "If the user does not specify a league, assume it is the national league "
    "for the teams in the query. If any tool fails, figure out the correct "
    "parameters (e.g. for team name, 'FCP' should be 'FC Porto') and try again."
)

def create_agent_config(model_name: Literal["google", "openai"] = "google", 
                       app_name: str = "Tonibot",
                       custom_prompt: str | None = None) -> dict:
    """
    Create configuration for the agent.
    
    Args:
        model_name: The model to use ("google" or "openai")
        app_name: Name of the application
        custom_prompt: Custom system prompt (if None, uses default football assistant prompt)
    
    Returns:
        Configuration dictionary for the agent
    """
    if custom_prompt is None:
        prompt = DEFAULT_FOOTBALL_PROMPT.format(
            app_name=app_name,
            date=datetime.today().strftime('%Y-%m-%d')
        )
    else:
        prompt = custom_prompt
    
    return {
        "configurable": {
            "model_name": model_name,
            "prompt": prompt
        }
    }
