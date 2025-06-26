from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from agent.nodes import call_model, sports_guardrail, sports_classifier, tool_node
from agent.state import State
from agent.prompts import get_non_sports_response, get_future_sports_response, get_unsupported_sports_response
from langchain_core.messages import AIMessage

def triage_action(state: State) -> Literal["hardcoded_response", "agent", "future_sports_response", "unsupported_sports_response"]:
    """Determine what to do based on whether it's about sports and which sports are mentioned"""
    
    # Check if it's not about sports first
    if not state.get("about_sports", True):
        return "hardcoded_response"
    
    sports_mentioned = state.get("sports_mentioned", [])
    
    # If soccer is NOT mentioned, use existing behavior
    if "soccer" not in sports_mentioned:
        # If only future sports are mentioned
        future_sports = [s for s in sports_mentioned if s in ["basketball", "rugby", "F1"]]
        if future_sports and not ("other_sport" in sports_mentioned):
            return "future_sports_response"
        # If no sports are mentioned, call agent to handle it
        if not future_sports and not ("other_sport" in sports_mentioned):
            return "agent"
        # If other sports
        return "unsupported_sports_response"
    
    # If soccer IS mentioned, always proceed to agent
    return "agent"

def hardcoded_response(state: State, app_name: str):
    """Response for non-sports queries"""
    return {
        "messages": [
            AIMessage(get_non_sports_response(app_name))
        ]
    }

def future_sports_response(state: State, app_name: str):
    """Response for sports that will be added in the future"""
    sports_mentioned = state.get("sports_mentioned", [])
    future_sports = [s for s in sports_mentioned if s in ["basketball", "rugby", "F1"]]
    
    # Map internal names to display names
    sports_display_map = {
        "basketball": "basketball",
        "rugby": "rugby", 
        "F1": "Formula 1"
    }
    
    display_names = [sports_display_map.get(sport, sport) for sport in future_sports]
    
    return {
        "messages": [
            AIMessage(get_future_sports_response(app_name, display_names))
        ]
    }

def unsupported_sports_response(state: State, app_name: str):
    """Response for unsupported sports"""
    sports_mentioned = state.get("sports_mentioned", [])
    other_sports = [s for s in sports_mentioned if s == "other_sport"]
    
    if other_sports:
        display_names = ["other sports"]
    else:
        display_names = ["the requested topic"]
    
    return {
        "messages": [
            AIMessage(get_unsupported_sports_response(app_name, display_names))
        ]
    }

def get_agent():
    """
    Get our LangGraph agent with the given model and tools.
    """
   
    class GraphConfig(TypedDict):
        model_name: Literal["google", "openai"]
        app_name: str

    graph = StateGraph(State, config_schema=GraphConfig)
    
    # Add nodes
    graph.add_node("sports_guardrail", sports_guardrail)
    graph.add_node("sports_classifier", sports_classifier)
    graph.add_node("hardcoded_response", lambda state, config: hardcoded_response(state, app_name=config.get("app_name", "PitchPal")))
    graph.add_node("future_sports_response", lambda state, config: future_sports_response(state, app_name=config.get("app_name", "PitchPal")))
    graph.add_node("unsupported_sports_response", lambda state, config: unsupported_sports_response(state, app_name=config.get("app_name", "PitchPal")))
    graph.add_node("triage", lambda state: state, defer=True) # Dummy no-op node for triage
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    
    # Add edges
    graph.add_edge(START, "sports_guardrail")
    graph.add_edge(START, "sports_classifier")
    graph.add_edge("sports_guardrail", "triage")
    graph.add_edge("sports_classifier", "triage")
    graph.add_conditional_edges("triage", triage_action)
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    graph.add_edge("hardcoded_response", END)
    graph.add_edge("future_sports_response", END)
    graph.add_edge("unsupported_sports_response", END)
        
    return graph.compile()