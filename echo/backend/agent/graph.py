import logging
import uuid
from typing import Optional
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage
from agent.state import EchoState
from agent.nodes import (
    classify_intent_node,
    retrieve_context_node,
    generate_response_node,
    check_end_node
)

logger = logging.getLogger(__name__)

# Build the LangGraph graph
def _build_graph() -> any:
    """Build and compile the ECHO agent graph."""
    graph = StateGraph(EchoState)
    
    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("check_end", check_end_node)
    
    # Define edges (linear flow for v1)
    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_response")
    graph.add_edge("generate_response", "check_end")
    graph.add_edge("check_end", END)
    
    # Compile
    echo_graph = graph.compile()
    
    logger.info("ECHO agent graph compiled successfully")
    return echo_graph


# Singleton graph instance
_echo_graph = None


def get_agent_graph():
    """Get or create the singleton ECHO agent graph."""
    global _echo_graph
    if _echo_graph is None:
        _echo_graph = _build_graph()
    return _echo_graph


class ConversationManager:
    """
    Manages conversation state and turn processing for ECHO agent.
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize a new conversation.
        
        Args:
            conversation_id: Optional ID for tracking. Generated if not provided.
        """
        self.conversation_id = conversation_id or str(uuid.uuid4())
        
        # Initialize state
        self.state: EchoState = {
            "messages": [],
            "user_transcript": "",
            "rag_context": "",
            "agent_response": "",
            "intent": "",
            "conversation_id": self.conversation_id,
            "turn_count": 0,
            "should_end": False
        }
        
        logger.info(f"Created conversation: {self.conversation_id}")
    
    async def process_turn(self, user_text: str) -> str:
        """
        Process a single user input turn through the agent graph.
        
        Args:
            user_text: User's transcribed speech
        
        Returns:
            Agent's response text (ready for TTS)
        """
        try:
            # Add user message to history
            self.state["messages"].append(HumanMessage(content=user_text))
            self.state["user_transcript"] = user_text
            
            logger.info(f"Processing turn {self.state['turn_count']} for {self.conversation_id}: '{user_text}'")
            
            # Run agent graph
            graph = get_agent_graph()
            result = graph.invoke(self.state)
            
            # Update internal state with result
            self.state = result
            
            agent_response = self.state.get("agent_response", "")
            logger.info(f"Agent response: '{agent_response}' (turn_count: {self.state['turn_count']})")
            
            return agent_response
        
        except Exception as e:
            logger.error(f"Turn processing error: {e}")
            return "I encountered an error. Please try again."
    
    def reset(self) -> None:
        """Reset conversation state."""
        logger.info(f"Resetting conversation: {self.conversation_id}")
        self.state = {
            "messages": [],
            "user_transcript": "",
            "rag_context": "",
            "agent_response": "",
            "intent": "",
            "conversation_id": self.conversation_id,
            "turn_count": 0,
            "should_end": False
        }
    
    def should_end(self) -> bool:
        """Check if conversation should end."""
        return self.state.get("should_end", False)
    
    def get_turn_count(self) -> int:
        """Get current turn count."""
        return self.state.get("turn_count", 0)
