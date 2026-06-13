import logging
import json
import base64
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from vad_processor import VADProcessor
from stt_engine import get_stt_engine
from tts_engine import get_tts_engine
from latency_tracker import LatencyTracker
from agent.graph import ConversationManager
from config import get_settings

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Manages WebSocket connections and orchestrates the full ECHO voice pipeline.
    """
    
    # Message types (client → server)
    MSG_START_SESSION = "start_session"
    MSG_AUDIO_CHUNK = "audio_chunk"
    MSG_END_SESSION = "end_session"
    
    # Message types (server → client)
    MSG_SESSION_READY = "session_ready"
    MSG_TRANSCRIPT = "transcript"
    MSG_AUDIO_RESPONSE = "audio_response"
    MSG_LATENCY = "latency"
    MSG_STATUS = "status"
    MSG_ERROR = "error"
    
    # Agent states
    STATUS_LISTENING = "listening"
    STATUS_PROCESSING = "processing"
    STATUS_SPEAKING = "speaking"
    STATUS_IDLE = "idle"
    STATUS_ERROR = "error"
    
    async def handle_connection(self, websocket: WebSocket) -> None:
        """
        Handle a full WebSocket connection lifecycle.
        
        Args:
            websocket: FastAPI WebSocket connection
        """
        connection_id = str(uuid.uuid4())[:8]
        conversation_manager = None
        vad_processor = None
        latency_tracker = LatencyTracker()
        stt_engine = get_stt_engine()
        tts_engine = get_tts_engine()
        
        logger.info(f"[{connection_id}] New WebSocket connection")
        
        try:
            # Accept connection
            await websocket.accept()
            logger.info(f"[{connection_id}] Connection accepted")
            
            while True:
                # Receive message
                message_str = await websocket.receive_text()
                
                try:
                    message = json.loads(message_str)
                    msg_type = message.get("type", "unknown")
                    
                    # --- START SESSION ---
                    if msg_type == self.MSG_START_SESSION:
                        conv_id = message.get("conversation_id", str(uuid.uuid4()))
                        
                        # Initialize session components
                        conversation_manager = ConversationManager(conv_id)
                        vad_processor = VADProcessor()
                        latency_tracker.reset()
                        
                        # Send ready message
                        await websocket.send_text(json.dumps({
                            "type": self.MSG_SESSION_READY,
                            "conversation_id": conv_id
                        }))
                        
                        # Send initial status
                        await websocket.send_text(json.dumps({
                            "type": self.MSG_STATUS,
                            "state": self.STATUS_LISTENING
                        }))
                        
                        logger.info(f"[{connection_id}] Session started: {conv_id}")
                    
                    # --- AUDIO CHUNK ---
                    elif msg_type == self.MSG_AUDIO_CHUNK:
                        if not vad_processor or not conversation_manager:
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_ERROR,
                                "message": "Session not initialized. Send start_session first."
                            }))
                            continue
                        
                        # Decode base64 audio chunk
                        audio_data = message.get("data", "")
                        try:
                            audio_bytes = base64.b64decode(audio_data)
                        except Exception as e:
                            logger.error(f"[{connection_id}] Audio decode error: {e}")
                            continue
                        
                        # Process chunk through VAD
                        turn_complete, complete_audio = vad_processor.process_chunk(audio_bytes)
                        
                        if not turn_complete:
                            # Still accumulating audio, continue
                            continue
                        
                        # --- TURN COMPLETE: Process full speech ---
                        logger.info(f"[{connection_id}] Turn complete, processing...")
                        
                        try:
                            # Send status: processing
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_STATUS,
                                "state": self.STATUS_PROCESSING
                            }))
                            
                            # 1. TRANSCRIBE (STT)
                            latency_tracker.start("stt")
                            user_text = stt_engine.transcribe(complete_audio)
                            stt_duration = latency_tracker.end("stt")
                            
                            if not user_text:
                                logger.info(f"[{connection_id}] Empty transcription, reset")
                                vad_processor.reset()
                                await websocket.send_text(json.dumps({
                                    "type": self.MSG_STATUS,
                                    "state": self.STATUS_LISTENING
                                }))
                                continue
                            
                            logger.info(f"[{connection_id}] STT: '{user_text}' ({stt_duration:.1f}ms)")
                            
                            # Send user transcript
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_TRANSCRIPT,
                                "text": user_text,
                                "role": "user"
                            }))
                            
                            # 2. AGENT PROCESSING (LLM)
                            latency_tracker.start("llm")
                            agent_response = await conversation_manager.process_turn(user_text)
                            llm_duration = latency_tracker.end("llm")
                            
                            logger.info(f"[{connection_id}] LLM: '{agent_response}' ({llm_duration:.1f}ms)")
                            
                            # Send agent transcript
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_TRANSCRIPT,
                                "text": agent_response,
                                "role": "assistant"
                            }))
                            
                            # Send status: speaking
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_STATUS,
                                "state": self.STATUS_SPEAKING
                            }))
                            
                            # 3. SYNTHESIZE (TTS)
                            latency_tracker.start("tts")
                            audio_response = await tts_engine.synthesize(agent_response)
                            tts_duration = latency_tracker.end("tts")
                            
                            logger.info(f"[{connection_id}] TTS: {len(audio_response)} bytes ({tts_duration:.1f}ms)")
                            
                            # Send audio response
                            audio_b64 = base64.b64encode(audio_response).decode("utf-8")
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_AUDIO_RESPONSE,
                                "data": audio_b64,
                                "format": "mp3"
                            }))
                            
                            # Send latency metrics
                            metrics = latency_tracker.summary()
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_LATENCY,
                                **metrics
                            }))
                            
                            logger.info(f"[{connection_id}] Latency summary: {metrics}")
                            
                            # Reset VAD for next turn
                            vad_processor.reset()
                            
                            # Check if conversation should end
                            if conversation_manager.should_end():
                                logger.info(f"[{connection_id}] Conversation end flagged")
                                await websocket.send_text(json.dumps({
                                    "type": self.MSG_STATUS,
                                    "state": self.STATUS_IDLE
                                }))
                            else:
                                # Send status: back to listening
                                await websocket.send_text(json.dumps({
                                    "type": self.MSG_STATUS,
                                    "state": self.STATUS_LISTENING
                                }))
                        
                        except Exception as e:
                            logger.error(f"[{connection_id}] Turn processing error: {e}", exc_info=True)
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_ERROR,
                                "message": f"Processing error: {str(e)}"
                            }))
                            await websocket.send_text(json.dumps({
                                "type": self.MSG_STATUS,
                                "state": self.STATUS_LISTENING
                            }))
                            vad_processor.reset()
                    
                    # --- END SESSION ---
                    elif msg_type == self.MSG_END_SESSION:
                        logger.info(f"[{connection_id}] Session end requested")
                        if conversation_manager:
                            logger.info(f"[{connection_id}] Final turn count: {conversation_manager.get_turn_count()}")
                        break
                
                except json.JSONDecodeError as e:
                    logger.error(f"[{connection_id}] JSON decode error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": self.MSG_ERROR,
                        "message": "Invalid JSON"
                    }))
                except Exception as e:
                    logger.error(f"[{connection_id}] Message handling error: {e}", exc_info=True)
                    await websocket.send_text(json.dumps({
                        "type": self.MSG_ERROR,
                        "message": f"Error: {str(e)}"
                    }))
        
        except WebSocketDisconnect:
            logger.info(f"[{connection_id}] Client disconnected")
        except Exception as e:
            logger.error(f"[{connection_id}] Connection error: {e}", exc_info=True)
            try:
                await websocket.send_text(json.dumps({
                    "type": self.MSG_ERROR,
                    "message": f"Connection error: {str(e)}"
                }))
            except:
                pass
        finally:
            logger.info(f"[{connection_id}] Connection closed")
