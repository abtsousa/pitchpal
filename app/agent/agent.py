from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from agent.nodes import call_model, sports_guardrail, tool_node
from agent.state import State
from langchain_core.messages import AIMessage

def is_about_sports(state: State) -> Literal["hardcoded_response", "agent"]:
    if not state["about_sports"]:
        return "hardcoded_response"
    return "agent"

def hardcoded_response(state: State):
    return {
        "messages": [
            AIMessage(
            "I am not able to answer that. "
            "Please ask me something else."
            )
        ]
    }

def get_agent():
    """
    Get our LangGraph agent with the given model and tools.
    """
   
    class GraphConfig(TypedDict):
        model_name: Literal["google", "openai"]
        system_prompt: str | None

    graph = StateGraph(State, config_schema=GraphConfig)
    
    # Add nodes
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_node(sports_guardrail)
    graph.add_node(hardcoded_response)
    
    # Add edges
    graph.add_edge(START, "sports_guardrail")
    graph.add_conditional_edges("sports_guardrail", is_about_sports)
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    graph.add_edge("hardcoded_response", END)
        
    return graph.compile()