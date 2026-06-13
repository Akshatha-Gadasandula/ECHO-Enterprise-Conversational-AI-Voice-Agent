import json
import logging
import os
from pathlib import Path
from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import get_settings

logger = logging.getLogger(__name__)


class RAGIndexer:
    """
    Builds and manages FAISS vector indices for enterprise knowledge base.
    """
    
    def __init__(self):
        settings = get_settings()
        self.docs_dir = "rag/docs"
        self.index_path = settings.faiss_index_path
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        # Ensure index directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk document text intelligently:
        - First split on double newlines (section breaks)
        - Then split long chunks on ". " (sentence breaks)
        - Target chunk size: 200-400 characters
        """
        chunks = []
        
        # Split on double newlines first (high-level sections)
        sections = text.split("\n\n")
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # If section is short enough, keep as-is
            if len(section) <= 400:
                chunks.append(section)
            else:
                # Split on ". " (sentence boundaries)
                sentences = section.split(". ")
                current_chunk = ""
                
                for sentence in sentences:
                    test_chunk = current_chunk + sentence + ". " if current_chunk else sentence + ". "
                    
                    # If adding this sentence keeps us under 400 chars, add it
                    if len(test_chunk) <= 400:
                        current_chunk = test_chunk
                    else:
                        # If we have content, save current chunk
                        if current_chunk:
                            chunks.append(current_chunk.rstrip(". "))
                        # Start new chunk with this sentence
                        current_chunk = sentence + ". "
                
                # Add remaining chunk
                if current_chunk:
                    chunks.append(current_chunk.rstrip(". "))
        
        return [c for c in chunks if c.strip()]
    
    def build_index(self) -> None:
        """
        Build FAISS index from all documents in docs_dir.
        """
        logger.info("Building RAG index...")
        
        if not os.path.exists(self.docs_dir):
            logger.warning(f"Docs directory not found: {self.docs_dir}")
            return
        
        chunks_metadata = []
        all_texts = []
        
        # Read and chunk all documents
        doc_files = sorted(Path(self.docs_dir).glob("*.txt"))
        logger.info(f"Found {len(doc_files)} document files")
        
        for doc_path in doc_files:
            filename = doc_path.name
            logger.info(f"Processing: {filename}")
            
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_text = f.read()
            
            # Chunk the document
            chunks = self._chunk_text(doc_text)
            logger.info(f"  → {len(chunks)} chunks extracted")
            
            # Add metadata for each chunk
            for chunk_id, chunk_text in enumerate(chunks):
                all_texts.append(chunk_text)
                chunks_metadata.append({
                    "text": chunk_text,
                    "source": filename,
                    "chunk_id": chunk_id
                })
        
        if not all_texts:
            logger.warning("No chunks found in documents")
            return
        
        logger.info(f"Total chunks to index: {len(all_texts)}")
        
        # Encode all chunks with sentence transformer
        logger.info("Encoding chunks with sentence transformer...")
        embeddings = self.embedding_model.encode(
            all_texts,
            show_progress_bar=True,
            batch_size=32
        )
        embeddings = np.array(embeddings).astype(np.float32)
        
        logger.info(f"Embedding dimension: {embeddings.shape[1]}")
        
        # Build FAISS index
        logger.info("Building FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        logger.info(f"FAISS index built: {index.ntotal} vectors")
        
        # Save index and metadata
        logger.info(f"Saving index to: {self.index_path}")
        faiss.write_index(index, f"{self.index_path}.faiss")
        
        with open(f"{self.index_path}_meta.json", "w") as f:
            json.dump(chunks_metadata, f, indent=2)
        
        logger.info(f"Index saved successfully. Metadata: {len(chunks_metadata)} chunks")
    
    def load_index(self) -> Tuple[faiss.Index, List[dict]]:
        """
        Load saved FAISS index and metadata.
        
        Returns:
            Tuple of (FAISS index, chunks metadata list)
        """
        index_file = f"{self.index_path}.faiss"
        meta_file = f"{self.index_path}_meta.json"
        
        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            logger.error(f"Index files not found. Run build_index() first.")
            return None, None
        
        logger.info(f"Loading FAISS index from: {index_file}")
        index = faiss.read_index(index_file)
        
        with open(meta_file, "r") as f:
            metadata = json.load(f)
        
        logger.info(f"Loaded index with {index.ntotal} vectors and {len(metadata)} chunks")
        return index, metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexer = RAGIndexer()
    indexer.build_index()
