from getpass import getpass
import os
from typing import Literal, TypedDict
from langchain_core.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage
from langchain_core.language_models.base import LanguageModelInput
from pydantic import BaseModel, Field
from agent.state import State
from langchain_core.messages import SystemMessage
from tools import get_all_tools
from langgraph.prebuilt import ToolNode

### Helper functions ###

def _get_model(model_name: Literal["google", "openai"]) -> BaseChatModel:
    if model_name == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = getpass("Enter API key for Google Gemini: ")
        
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    elif model_name == "openai":
        from langchain_openai import ChatOpenAI
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = getpass("Enter API key for OpenAI: ")

        return ChatOpenAI(model="gpt-4.1-mini-2025-04-14", stream_usage=True)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

def _get_tools() -> list[StructuredTool]:
    from tools import get_all_tools
    return get_all_tools()

def _bind_model(model: BaseChatModel) -> Runnable[LanguageModelInput, BaseMessage]:
    return model.bind_tools(_get_tools())

### NODES ###

# Call model node
def call_model(state: State, config) -> dict[str, list[BaseMessage]]:
    messages = state["messages"]
    model_name = config.get('configurable', {}).get("model_name", "openai")
    system_prompt = config.get('configurable', {}).get("system_prompt", None)
    
    # Add system prompt if provided
    if system_prompt and (not messages or messages[0].type != "system"):
        system_message: BaseMessage = SystemMessage(content=system_prompt)
        messages = [system_message] + list(messages)
    
    model = _get_model(model_name)
    model = _bind_model(model)
    response = model.invoke(messages)
    
    return {"messages": [response]}

# Tool node
tool_node = ToolNode(tools=_get_tools())

# Guardrail node
class AboutSportsGuardrailNode(TypedDict):
    """Is the user's question about sports?"""
    about_sports: bool

class AboutSportsGuardrailSchema(BaseModel):
    """Is the user's question about sports?"""
    about_sports: bool = Field(description="Whether the user's question is about sports")

about_sports_prompt = "Determine whether the user's most recent question is about sports."

def sports_guardrail(state: State, config) -> AboutSportsGuardrailNode:
    """
    Check if the user's question is about sports.
    """
    messages = state["messages"]
    model_name = config.get('configurable', {}).get("model_name", "openai")
    messages = [about_sports_prompt] + list(messages)
    
    model = _get_model(model_name).with_structured_output(
        AboutSportsGuardrailSchema
    )
    response = model.invoke(messages)
    
    return {"about_sports": response.about_sports} # type: ignore