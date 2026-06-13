from typing import TypedDict, List, Annotated, Optional
from langchain_core.messages import BaseMessage
import operator


class EchoState(TypedDict):
    """
    State schema for the ECHO agent conversation graph.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_transcript: str              # Latest user utterance from STT
    rag_context: str                  # Retrieved knowledge base context
    agent_response: str               # Final text response to synthesize
    intent: str                       # Classified intent
    conversation_id: str              # Session identifier
    turn_count: int                   # Number of turns in conversation
    should_end: bool                  # Graceful conversation end flag
