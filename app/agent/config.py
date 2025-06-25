from typing import Literal

def create_agent_config(app_name: str,
                       model_name: Literal["google", "openai"] = "openai") -> dict:
    """
    Create configuration for the agent.
    
    Args:
        model_name: The model to use ("google" or "openai")
        app_name: Name of the application
    
    Returns:
        Configuration dictionary for the agent
    """
    return {
        "configurable": {
            "model_name": model_name,
            "app_name": app_name
        }
    }
