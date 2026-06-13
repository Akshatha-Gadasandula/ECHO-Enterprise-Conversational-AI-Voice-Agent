import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from websocket_handler import WebSocketHandler
from config import get_settings
from rag.indexer import RAGIndexer
from stt_engine import get_stt_engine
from rag.retriever import get_retriever

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context: startup and shutdown hooks."""
    
    logger.info("=" * 60)
    logger.info("ECHO Voice AI - Startup Sequence")
    logger.info("=" * 60)
    
    # Startup: Build RAG index
    logger.info("[1/3] Building RAG index...")
    try:
        indexer = RAGIndexer()
        indexer.build_index()
        logger.info("✓ RAG index built successfully")
    except Exception as e:
        logger.error(f"✗ RAG indexing failed: {e}")
        logger.info("Continuing with empty index...")
    
    # Startup: Warm up Whisper model
    logger.info("[2/3] Loading Whisper STT model...")
    try:
        stt_engine = get_stt_engine()
        logger.info(f"✓ Whisper model loaded ({settings.whisper_model_size})")
    except Exception as e:
        logger.error(f"✗ Whisper model load failed: {e}")
        raise
    
    # Startup: Warm up sentence transformer
    logger.info("[3/3] Initializing RAG retriever...")
    try:
        retriever = get_retriever()
        logger.info("✓ RAG retriever initialized")
    except Exception as e:
        logger.error(f"✗ RAG retriever initialization failed: {e}")
        logger.info("Continuing without RAG...")
    
    logger.info("=" * 60)
    logger.info("✓ ECHO Voice AI Ready!")
    logger.info(f"  Listening on {settings.host}:{settings.port}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("ECHO Voice AI shutting down...")


# Create FastAPI app
app = FastAPI(
    title="ECHO Voice AI",
    description="Enterprise Voice AI Agent for FinServ Bank",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ECHO Voice AI",
        "timestamp": time.time()
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Return aggregate metrics."""
    return {
        "service": "ECHO Voice AI",
        "status": "operational",
        "models": {
            "stt": settings.whisper_model_size,
            "llm": settings.claude_model,
            "embedding": settings.embedding_model
        },
        "rag": {
            "index_path": settings.faiss_index_path,
            "top_k": settings.rag_top_k
        }
    }


# WebSocket endpoint
@app.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice interaction."""
    handler = WebSocketHandler()
    await handler.handle_connection(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )
