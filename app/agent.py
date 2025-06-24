from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

class State(TypedDict):
    messages: Annotated[list, add_messages]

def get_agent(model, tools=None, name="Agent", prompt=None):
    """
    Get our LangGraph agent with the given model and tools.
    
    Args:
        model: The language model to use
        tools: List of tools to bind to the model (optional)
        name: Name of the agent (optional)
        prompt: System prompt for the agent (optional)
    
    Returns:
        Compiled LangGraph agent
    """
    graph_builder = StateGraph(State)
    
    if tools:
        # Agent with tools
        model_with_tools = model.bind_tools(tools)
        
        def chatbot_with_tools(state: State):
            messages = state["messages"]
            
            # Add system prompt if provided
            if prompt and (not messages or messages[0].type != "system"):
                messages = [SystemMessage(content=prompt)] + messages
            
            return {"messages": [model_with_tools.invoke(messages)]}
        
        # Add nodes
        graph_builder.add_node("chatbot_with_tools", chatbot_with_tools)
        tool_node = ToolNode(tools=tools)
        graph_builder.add_node("tools", tool_node)
        
        # Add edges
        graph_builder.add_edge(START, "chatbot_with_tools")
        graph_builder.add_conditional_edges("chatbot_with_tools", tools_condition)
        graph_builder.add_edge("tools", "chatbot_with_tools")
        
    else:
        # Simple chatbot without tools
        def chatbot(state: State):
            messages = state["messages"]
            
            # Add system prompt if provided
            if prompt and (not messages or messages[0].type != "system"):
                messages = [SystemMessage(content=prompt)] + messages
            
            return {"messages": [model.invoke(messages)]}
        
        graph_builder.add_node("chatbot", chatbot)
        graph_builder.add_edge(START, "chatbot")
    
    return graph_builder.compile()