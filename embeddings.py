"""
Embedding-based vector store for scraped text chunks.
Uses sentence-transformers to create embeddings and FAISS for vector storage.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import json
import numpy as np

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Model name for sentence transformers
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Initialize and return HuggingFace embeddings model.
    Optimized for memory usage.
    
    Returns:
        HuggingFaceEmbeddings: Initialized embeddings model
    """
    import os
    import gc
    
    # Set environment variables to reduce memory usage
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    
    # Force garbage collection before loading model
    gc.collect()
    
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu",  # Use CPU for compatibility
            "trust_remote_code": False
        },
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 8,  # Process in batches
            "convert_to_numpy": True,  # Use numpy instead of torch tensors
        }
    )


def _compute_chunks_hash(chunks: List[Dict[str, Any]]) -> str:
    """
    Compute a hash of the chunks data to detect changes.
    
    Args:
        chunks: List of text chunk dictionaries
    
    Returns:
        str: SHA256 hash of the chunks data
    """
    # Sort chunks by text to ensure consistent hashing
    sorted_chunks = sorted(chunks, key=lambda x: x.get("text", ""))
    # Convert to JSON string for hashing
    chunks_json = json.dumps(sorted_chunks, sort_keys=True)
    return hashlib.sha256(chunks_json.encode()).hexdigest()


def build_vector_store(
    chunks: List[Dict[str, Any]], 
    embeddings: Optional[HuggingFaceEmbeddings] = None,
    vector_store_path: Optional[str] = None
) -> FAISS:
    """
    Build FAISS vector store from text chunks.
    
    Args:
        chunks: List of text chunk dictionaries
        embeddings: Optional embeddings model (will create if not provided)
        vector_store_path: Optional path to save/load vector store
    
    Returns:
        FAISS: Vector store containing chunk documents
    """
    import gc
    
    if embeddings is None:
        embeddings = get_embeddings()
    
    # Create Document objects from chunks
    documents = []
    for idx, chunk in enumerate(chunks):
        # Store text in page_content, metadata contains type and other info
        chunk_metadata = chunk.get("metadata", {})
        doc = Document(
            page_content=chunk.get("text", ""),
            metadata={
                "chunk_index": idx,
                "chunk_id": chunk.get("chunk_id", ""),
                "section": chunk.get("section", "General"),
                "url": chunk.get("url", ""),
                "type": chunk_metadata.get("type", chunk.get("type", "text_content")),
                **chunk_metadata  # Include all metadata from chunk
            }
        )
        documents.append(doc)
    
    # Build FAISS vector store
    vector_store = FAISS.from_documents(documents, embeddings)
    
    # Save to disk if path provided
    if vector_store_path:
        vector_store_path_obj = Path(vector_store_path)
        vector_store_path_obj.parent.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(vector_store_path_obj))
        
        # Save the chunks hash to detect changes in future loads
        current_hash = _compute_chunks_hash(chunks)
        hash_file = vector_store_path_obj / "chunks_hash.txt"
        hash_file.write_text(current_hash)
        
        logger.info(f"Saved vector store to {vector_store_path}")
    
    # Force garbage collection after building
    gc.collect()
    
    return vector_store


def load_or_build_vector_store(
    chunks: List[Dict[str, Any]],
    vector_store_path: Optional[str] = None
) -> FAISS:
    """
    Load existing FAISS index or build a new one if it doesn't exist or chunks have changed.
    
    Args:
        chunks: List of text chunk dictionaries
        vector_store_path: Path to vector store directory
    
    Returns:
        FAISS: Vector store containing chunk documents
    """
    embeddings = get_embeddings()
    
    if not vector_store_path:
        # No path provided, build new store
        return build_vector_store(chunks, embeddings)
    
    vector_store_path_obj = Path(vector_store_path)
    
    # Compute current chunks hash
    current_hash = _compute_chunks_hash(chunks)
    
    # Check if index exists and hash matches
    hash_file = vector_store_path_obj / "chunks_hash.txt"
    index_exists = vector_store_path_obj.exists() and (vector_store_path_obj / "index.faiss").exists()
    
    if index_exists:
        # Check if chunks data has changed
        if hash_file.exists():
            stored_hash = hash_file.read_text().strip()
            if stored_hash == current_hash:
                # Hash matches, load existing index
                try:
                    vector_store = FAISS.load_local(
                        str(vector_store_path_obj),
                        embeddings,
                        allow_dangerous_deserialization=True
                    )
                    logger.info(f"Loaded existing vector store from {vector_store_path}")
                    return vector_store
                except Exception as e:
                    logger.warning(f"Error loading existing FAISS index: {e}. Rebuilding...")
            else:
                logger.info("Chunks data has changed (hash mismatch). Rebuilding index...")
        else:
            # Hash file doesn't exist, rebuild to create it
            logger.info("Chunks hash file not found. Rebuilding index...")
    
    # Build new index if loading fails, index doesn't exist, or chunks changed
    return build_vector_store(chunks, embeddings, vector_store_path)


def embed_query(query: str, embeddings: Optional[HuggingFaceEmbeddings] = None) -> np.ndarray:
    """
    Embed a query string.
    
    Args:
        query: Query string to embed
        embeddings: Optional embeddings model (will create if not provided)
    
    Returns:
        np.ndarray: Query embedding vector
    """
    if embeddings is None:
        embeddings = get_embeddings()
    
    # Embed the query
    query_embedding = embeddings.embed_query(query)
    
    return np.array(query_embedding)

