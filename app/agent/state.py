from typing import TypedDict, Sequence, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]