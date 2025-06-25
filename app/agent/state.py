from typing import Literal, TypedDict, Sequence, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    about_sports: bool # TODO test prompt injection that mentions sports
    sports_mentioned: list[Literal["soccer", "basketball", "rugby", "F1", "other_sport", "offtopic"]]