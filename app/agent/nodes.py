from getpass import getpass
import os
from typing import Literal, TypedDict, cast
from langchain_core.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage
from langchain_core.language_models.base import LanguageModelInput
from pydantic import BaseModel, Field
from agent.state import State
from agent.prompts import SPORTS_GUARDRAIL_PROMPT, SPORTS_CLASSIFIER_PROMPT, get_system_prompt, get_dynamic_system_prompt
from langchain_core.messages import SystemMessage, HumanMessage
from tools import get_all_tools
from langgraph.prebuilt import ToolNode

### Helper functions ###

def _get_model(model_name: Literal["google", "openai"], nano_model: bool = False) -> BaseChatModel:
    if model_name == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = getpass("Enter API key for Google Gemini: ")
        
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash") if not nano_model else ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite-preview-06-17")
    elif model_name == "openai":
        from langchain_openai import ChatOpenAI
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = getpass("Enter API key for OpenAI: ")

        return ChatOpenAI(model="gpt-4.1-mini-2025-04-14", stream_usage=True) if not nano_model else ChatOpenAI(model="gpt-4.1-nano-2025-04-14", stream_usage=True)
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
    app_name = config.get('configurable', {}).get("app_name", "Tonibot")
    
    # Add system prompt if not already present
    if not messages or messages[0].type != "system":
        # Use dynamic system prompt if sports are mentioned
        sports_mentioned = state.get("sports_mentioned", [])
        system_prompt = get_dynamic_system_prompt(app_name, sports_mentioned)
        system_message: BaseMessage = SystemMessage(content=system_prompt)
        messages = [system_message] + list(messages)
    
    model = _get_model(model_name)
    model = _bind_model(model)
    response = model.invoke(messages)
    
    return {"messages": [response]}

# Tool node
tool_node = ToolNode(tools=_get_tools())

# Guardrail node
class AboutSportsGuardrailSchema(BaseModel):
    """Classification of whether the query is genuinely about sports"""
    about_sports: bool = Field(description="Whether the query is genuinely about sports")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation of the classification")


class SportsClassifierSchema(BaseModel):
    """Classification of which specific sports are mentioned in the query"""
    sports_mentioned: list[Literal["soccer", "basketball", "rugby", "F1", "other"]] = Field(
        description="List of sports mentioned in the query"
    )


def sports_guardrail(state: State, config) -> dict:
    """
    Check if the user's question is about sports.
    """
    last_message = state["messages"][-1] if state["messages"] else None
    if isinstance(last_message, HumanMessage):
        if not last_message.content:
            return {"about_sports": False, "reasoning": "Empty query"}
    else:
        return {"about_sports": False, "reasoning": "Last message is not a user query"}
    
    model_name = config.get('configurable', {}).get("model_name", "openai")

    # Create the message with proper content
    messages = [SPORTS_GUARDRAIL_PROMPT, last_message]
    
    model = _get_model(model_name).with_structured_output(
        AboutSportsGuardrailSchema
    )

    try:
        response = model.invoke(messages)
        response = cast(AboutSportsGuardrailSchema, response)
        
        # Apply confidence threshold for additional safety
        # If confidence is low and the model says it's about sports, be conservative
        if response.about_sports and response.confidence < 0.6:
            return {
                "about_sports": False,
                "guardrail_confidence": response.confidence,
                "guardrail_reasoning": f"Low confidence ({response.confidence}): {response.reasoning}"
            }
        
        return {
            "about_sports": response.about_sports,
            "guardrail_confidence": response.confidence,
            "guardrail_reasoning": response.reasoning
        }
        
    except Exception as e:
        # Fail closed - assume not about sports if classification fails
        return {
            "about_sports": False,
            "guardrail_confidence": 0.0,
            "guardrail_reasoning": f"Classification error: {str(e)}"
        }

def sports_classifier(state: State, config) -> dict:
    """
    Classify which specific sports are mentioned in the user's question.
    """
    last_message = state["messages"][-1] if state["messages"] else None
    if isinstance(last_message, HumanMessage):
        if not last_message.content:
            return {"sports_mentioned": []}
    else:
        return {"sports_mentioned": []}
    
    model_name = config.get('configurable', {}).get("model_name", "openai")

    # Create the message with proper content
    messages = [SPORTS_CLASSIFIER_PROMPT, last_message]
    
    model = _get_model(model_name, nano_model=True).with_structured_output(
        SportsClassifierSchema
    )

    try:
        response = model.invoke(messages)
        response = cast(SportsClassifierSchema, response)
        
        return {
            "sports_mentioned": response.sports_mentioned,
        }
        
    except Exception as e:
        # Fail closed - assume offtopic if classification fails
        return {
            "sports_mentioned": [],
        }