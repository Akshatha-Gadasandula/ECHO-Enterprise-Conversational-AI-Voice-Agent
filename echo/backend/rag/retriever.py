import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from rag.indexer import RAGIndexer
from config import get_settings

logger = logging.getLogger(__name__)

# Global singleton instances
_retriever = None


class RAGRetriever:
    """
    Retrieves relevant knowledge base context for queries using semantic search.
    """
    
    def __init__(self):
        settings = get_settings()
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.top_k = settings.rag_top_k
        self.similarity_threshold = 1.5  # L2 distance threshold (higher = less similar)
        
        logger.info("Loading RAG index...")
        indexer = RAGIndexer()
        self.index, self.metadata = indexer.load_index()
        
        if self.index is None:
            logger.warning("FAISS index not found. Building new index...")
            indexer.build_index()
            self.index, self.metadata = indexer.load_index()
        
        logger.info(f"RAG Retriever initialized with {len(self.metadata)} chunks")
    
    def retrieve(self, query: str, top_k: int = None) -> str:
        """
        Retrieve relevant chunks from knowledge base for a query.
        
        Args:
            query: User query string
            top_k: Number of top results to return (uses settings default if None)
        
        Returns:
            Formatted context string with retrieved chunks
        """
        if self.index is None:
            logger.warning("FAISS index not available for retrieval")
            return ""
        
        try:
            k = top_k or self.top_k
            
            # Encode query
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False)
            query_embedding = np.array(query_embedding).astype(np.float32)
            
            # Search FAISS
            distances, indices = self.index.search(query_embedding, k=min(k, self.index.ntotal))
            
            # Collect matching chunks, filtering by similarity threshold
            relevant_chunks = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                # L2 distance: lower is better, 0 = perfect match, ~1.5 = starting to be dissimilar
                if distance > self.similarity_threshold:
                    logger.debug(f"Skipping chunk {idx} (distance {distance:.3f} > threshold {self.similarity_threshold})")
                    break  # FAISS returns sorted by distance, so stop when threshold exceeded
                
                chunk = self.metadata[idx]
                relevant_chunks.append(chunk)
                logger.debug(f"Retrieved chunk from {chunk['source']} (distance: {distance:.3f})")
            
            if not relevant_chunks:
                logger.info("No relevant chunks found above similarity threshold")
                return ""
            
            # Format context string
            context_parts = []
            current_source = None
            
            for chunk in relevant_chunks:
                source = chunk["source"]
                text = chunk["text"]
                
                # Add source header if it changed
                if source != current_source:
                    context_parts.append(f"\n[Source: {source}]")
                    current_source = source
                
                context_parts.append(text)
            
            context_string = "\n".join(context_parts)
            logger.info(f"Retrieved {len(relevant_chunks)} chunks for query (total length: {len(context_string)} chars)")
            
            return context_string
        
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return ""


def get_retriever() -> RAGRetriever:
    """Get or create the singleton RAG retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
