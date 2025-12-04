"""
Embeddings utility module.
Handles initialization and management of HuggingFace embeddings and FAISS vector store.
"""
from typing import List, Optional
from pathlib import Path
import hashlib
import json

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import get_settings

# Model name for sentence transformers
# Using the smallest viable model for 512MB memory limit
# paraphrase-MiniLM-L3-v2 is ~60MB vs all-MiniLM-L6-v2 which is ~80MB
EMBEDDING_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"


def get_faiss_index_path() -> Path:
    """
    Get the FAISS index path from settings.
    Creates the directory if it doesn't exist.
    
    Returns:
        Path: Path to the FAISS index directory
    """
    settings = get_settings()
    index_path = Path(settings.vector_store_path)
    
    # Ensure parent directory exists
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    return index_path


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Initialize and return HuggingFace embeddings model.
    Optimized for memory usage on free tier platforms (512MB limit).
    
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
            "device": "cpu",  # Use CPU for free tier compatibility
            "trust_remote_code": False
        },
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 1,  # Process one at a time to save memory
            "show_progress_bar": False,
            "convert_to_numpy": True,  # Use numpy instead of torch tensors
        }
    )


def _compute_faq_hash(faq_data: List[dict]) -> str:
    """
    Compute a hash of the FAQ data to detect changes.
    
    Args:
        faq_data: List of dictionaries with 'question' and 'answer' keys
    
    Returns:
        str: SHA256 hash of the FAQ data
    """
    # Sort FAQ data by question to ensure consistent hashing
    sorted_faq = sorted(faq_data, key=lambda x: x.get("question", ""))
    # Convert to JSON string for hashing
    faq_json = json.dumps(sorted_faq, sort_keys=True)
    return hashlib.sha256(faq_json.encode()).hexdigest()


def build_faiss_index(faq_data: List[dict], embeddings: Optional[HuggingFaceEmbeddings] = None) -> FAISS:
    """
    Build FAISS vector store from FAQ data.
    Optimized for memory usage on free tier platforms.
    
    Args:
        faq_data: List of dictionaries with 'question' and 'answer' keys
        embeddings: Optional embeddings model (will create if not provided)
    
    Returns:
        FAISS: Vector store containing FAQ documents
    """
    import gc
    
    if embeddings is None:
        embeddings = get_embeddings()
    
    # Create Document objects from FAQ data (minimize memory)
    documents = []
    for idx, faq in enumerate(faq_data):
        # Store only question in page_content, answer in metadata to save memory
        doc = Document(
            page_content=faq["question"],
            metadata={"answer": faq["answer"], "index": idx}  # Removed duplicate question
        )
        documents.append(doc)
    
    # Build FAISS vector store
    # For memory optimization, build directly (FAISS is already memory efficient)
    vector_store = FAISS.from_documents(documents, embeddings)
    
    # Save to disk for future use
    faiss_index_path = get_faiss_index_path()
    vector_store.save_local(str(faiss_index_path))
    
    # Save the FAQ hash to detect changes in future loads
    current_hash = _compute_faq_hash(faq_data)
    hash_file = faiss_index_path / "faq_hash.txt"
    hash_file.write_text(current_hash)
    
    # Force garbage collection after building
    gc.collect()
    
    return vector_store


def load_or_build_faiss_index(faq_data: List[dict]) -> FAISS:
    """
    Load existing FAISS index or build a new one if it doesn't exist or FAQ data has changed.
    
    Args:
        faq_data: List of dictionaries with 'question' and 'answer' keys
    
    Returns:
        FAISS: Vector store containing FAQ documents
    """
    embeddings = get_embeddings()
    
    # Get the FAISS index path from settings
    faiss_index_path = get_faiss_index_path()
    
    # Compute current FAQ data hash
    current_hash = _compute_faq_hash(faq_data)
    
    # Check if index exists and hash matches
    hash_file = faiss_index_path / "faq_hash.txt"
    index_exists = faiss_index_path.exists() and (faiss_index_path / "index.faiss").exists()
    
    if index_exists:
        # Check if FAQ data has changed
        if hash_file.exists():
            stored_hash = hash_file.read_text().strip()
            if stored_hash == current_hash:
                # Hash matches, load existing index
                try:
                    vector_store = FAISS.load_local(
                        str(faiss_index_path),
                        embeddings,
                        allow_dangerous_deserialization=True  # Required for FAISS loading
                    )
                    return vector_store
                except Exception as e:
                    print(f"Error loading existing FAISS index: {e}. Rebuilding...")
            else:
                print(f"FAQ data has changed (hash mismatch). Rebuilding index...")
        else:
            # Hash file doesn't exist, rebuild to create it
            print("FAQ hash file not found. Rebuilding index...")
    
    # Build new index if loading fails, index doesn't exist, or FAQ data changed
    return build_faiss_index(faq_data, embeddings)

