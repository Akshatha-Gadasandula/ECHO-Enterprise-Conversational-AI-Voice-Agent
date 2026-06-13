import logging
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq
from agent.state import EchoState
from agent.prompts import ECHO_SYSTEM_PROMPT, INTENT_CLASSIFIER_PROMPT
from rag.retriever import get_retriever
from config import get_settings
from latency_tracker import LatencyTracker

logger = logging.getLogger(__name__)

settings = get_settings()


def classify_intent_node(state: EchoState) -> dict:
    """
    Classify the user's intent using Groq.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state dict with intent field
    """
    try:
        query = state.get("user_transcript", "")
        if not query:
            return {"intent": "other"}
        
        # Format prompt
        prompt = INTENT_CLASSIFIER_PROMPT.format(query=query)
        
        # Call Groq
        llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.3,
            max_tokens=10
        )
        
        response = llm.invoke([HumanMessage(content=prompt)])
        
        intent = response.content.strip().lower()
        logger.info(f"Classified intent: {intent}")
        
        return {"intent": intent}
    
    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return {"intent": "other"}


def retrieve_context_node(state: EchoState) -> dict:
    """
    Retrieve relevant knowledge base context for the user query.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state dict with rag_context field
    """
    try:
        query = state.get("user_transcript", "")
        if not query:
            return {"rag_context": ""}
        
        retriever = get_retriever()
        context = retriever.retrieve(query)
        
        logger.info(f"Retrieved context: {len(context)} chars")
        
        return {"rag_context": context}
    
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        return {"rag_context": ""}


def generate_response_node(state: EchoState) -> dict:
    """
    Generate LLM response using conversation history and context.
    
    Args:
        state: Current agent state with full message history
    
    Returns:
        Updated state dict with agent_response
    """
    try:
        # Build system prompt with context and turn count
        rag_context = state.get("rag_context", "No context retrieved.")
        turn_count = state.get("turn_count", 0)
        
        system_prompt = ECHO_SYSTEM_PROMPT.format(
            rag_context=rag_context,
            turn_count=turn_count
        )
        
        # Build messages list from state (keep last N turns for memory efficiency)
        messages_list = state.get("messages", [])
        conversation_memory_turns = settings.conversation_memory_turns
        
        # Keep only recent messages to manage context window
        if len(messages_list) > conversation_memory_turns * 2:
            messages_list = messages_list[-(conversation_memory_turns * 2):]
        
        # Create Groq LLM with system prompt
        llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.3,
            max_tokens=settings.max_tokens
        )
        
        # Prepare messages with system prompt
        messages_to_send = [HumanMessage(content=system_prompt)]
        messages_to_send.extend(messages_list)
        
        # Call Groq
        response = llm.invoke(messages_to_send)
        
        response_text = response.content.strip()
        logger.info(f"Generated response: '{response_text}'")
        
        # Return response and incremented turn count
        return {
            "agent_response": response_text,
            "turn_count": turn_count + 1,
            "messages": [AIMessage(content=response_text)]
        }
    
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return {
            "agent_response": "I'm having trouble understanding. Could you please repeat that?",
            "turn_count": state.get("turn_count", 0) + 1,
            "messages": [AIMessage(content="I'm having trouble understanding. Could you please repeat that?")]
        }


def check_end_node(state: EchoState) -> dict:
    """
    Check if conversation should end based on intent or turn count.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state dict with should_end flag
    """
    intent = state.get("intent", "other")
    turn_count = state.get("turn_count", 0)
    
    # End conversation if user explicitly says goodbye or turn limit reached
    should_end = intent == "conversation_end" or turn_count > 20
    
    if should_end:
        logger.info(f"Conversation end triggered (intent: {intent}, turns: {turn_count})")
    
    return {"should_end": should_end}
