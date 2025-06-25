from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from agent.nodes import call_model, tool_node
from agent.state import State

def get_agent():
    """
    Get our LangGraph agent with the given model and tools.
    """
   
    class GraphConfig(TypedDict):
        model_name: Literal["google", "openai"]
        prompt: str | None

    graph = StateGraph(State, config_schema=GraphConfig)
    
    # Add nodes
    graph.add_node("chatbot_with_tools", call_model)
    graph.add_node("tools", tool_node)
    
    # Add edges
    graph.add_edge(START, "chatbot_with_tools")
    graph.add_conditional_edges("chatbot_with_tools", tools_condition)
    graph.add_edge("tools", "chatbot_with_tools")
        
    return graph.compile()