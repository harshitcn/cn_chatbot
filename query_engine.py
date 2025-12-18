"""
Dynamic query engine using semantic search.
No hard-coded categories or keyword matching - fully query-driven.
"""
import logging
import hashlib
from typing import Dict, List, Any, Optional
import numpy as np

from embeddings import get_embeddings, load_or_build_vector_store
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)


class DynamicQueryEngine:
    """
    Fully dynamic query engine using semantic search.
    Works for any query without hard-coded categories.
    """
    
    def __init__(self, vector_store: Optional[FAISS] = None, chunks: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the query engine.
        
        Args:
            vector_store: Optional pre-built FAISS vector store
            chunks: Optional list of chunks to build vector store from
        """
        self.vector_store = vector_store
        self.chunks = chunks or []
        self.embeddings = None
        
        if self.vector_store is None and self.chunks:
            logger.info("Building vector store from chunks...")
            self.embeddings = get_embeddings()
            self.vector_store = load_or_build_vector_store(self.chunks)
            logger.info(f"Vector store built with {len(self.chunks)} chunks")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search for a query.
        
        Args:
            query: User query string
            top_k: Number of top results to return
            
        Returns:
            List of relevant chunks with similarity scores
        """
        if not self.vector_store:
            logger.warning("No vector store available for search")
            return []
        
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                # Find original chunk data
                chunk_metadata = doc.metadata
                
                result = {
                    "text": doc.page_content,
                    "score": float(score),
                    "metadata": chunk_metadata,
                    "section": chunk_metadata.get('section', 'Unknown')
                }
                
                # Try to find original chunk by matching text or using index
                chunk_index = chunk_metadata.get('chunk_index')
                element_index = chunk_metadata.get('element_index')
                
                # Find matching chunk from original chunks list
                matching_chunk = None
                if chunk_index is not None:
                    # Try direct index lookup
                    for chunk in self.chunks:
                        if chunk.get("chunk_id") == chunk_metadata.get("chunk_id"):
                            matching_chunk = chunk
                            break
                
                # Fallback: search by text similarity
                if not matching_chunk:
                    doc_text = doc.page_content[:100].lower()
                    for chunk in self.chunks:
                        chunk_text = chunk.get("text", "")[:100].lower()
                        if doc_text in chunk_text or chunk_text in doc_text:
                            matching_chunk = chunk
                            break
                
                if matching_chunk:
                    result["url"] = matching_chunk.get("url")
                    result["chunk_id"] = matching_chunk.get("chunk_id")
                    result["section"] = matching_chunk.get("section", result["section"])
                
                formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} relevant chunks for query: {query[:50]}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}", exc_info=True)
            return []
    
    def answer_query(self, query: str, top_k: int = 5, min_score: float = 0.0) -> Dict[str, Any]:
        """
        Answer a user query using semantic search.
        
        Args:
            query: User query string
            top_k: Number of top chunks to retrieve
            min_score: Minimum similarity score threshold (lower is more similar for distance-based scores)
            
        Returns:
            Dictionary with answer and sources
        """
        try:
            # Perform semantic search
            results = self.search(query, top_k=top_k)
            
            if not results:
                return {
                    "status": "no_results",
                    "query": query,
                    "answer": "I couldn't find relevant information to answer your question. Please try rephrasing or ask about something else.",
                    "sources": []
                }
            
            # Filter by score (for distance-based scores, lower is better)
            # FAISS typically returns L2 distance, so we want scores close to 0
            # For cosine similarity (normalized), scores are typically 0-1, higher is better
            # But FAISS with L2 distance means lower scores are more similar
            # Adjust threshold based on score distribution
            max_distance = 2.0  # Maximum acceptable distance for L2
            filtered_results = [
                r for r in results 
                if (r["score"] <= max_distance) or (min_score == 0.0 and r["score"] <= 5.0)
            ]
            
            if not filtered_results:
                # If all results filtered out, use top results anyway
                filtered_results = results[:min(3, len(results))]
            
            # Build answer from top chunks (use top 3-5 most relevant)
            answer_parts = []
            sources = []
            seen_texts = set()  # Avoid duplicate content
            
            for result in filtered_results[:5]:  # Use top 5 chunks for comprehensive answer
                text = result["text"]
                section = result.get("section", "General")
                url = result.get("url", "")
                
                # Skip if we've seen very similar text (avoid duplicates)
                text_hash = hashlib.md5(text.lower()[:100].encode()).hexdigest()
                if text_hash in seen_texts:
                    continue
                seen_texts.add(text_hash)
                
                # Add to answer (avoid too much repetition)
                if len(answer_parts) < 3 or len(text) > 100:
                    answer_parts.append(text)
                
                # Add to sources
                sources.append({
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "section": section,
                    "url": url,
                    "score": round(result["score"], 3)
                })
            
            # Combine answer parts intelligently
            answer = self._combine_answer_parts(answer_parts)
            
            # Clean up answer
            answer = self._clean_answer(answer)
            
            return {
                "status": "success",
                "query": query,
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error answering query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "answer": f"I encountered an error processing your query: {str(e)}",
                "sources": []
            }
    
    def _combine_answer_parts(self, answer_parts: List[str]) -> str:
        """
        Intelligently combine answer parts, removing redundancy.
        """
        if not answer_parts:
            return ""
        
        if len(answer_parts) == 1:
            return answer_parts[0]
        
        # Combine parts, avoiding excessive repetition
        combined = []
        seen_phrases = set()
        
        for part in answer_parts:
            part = part.strip()
            if not part:
                continue
            
            # Check for significant overlap with already included text
            part_words = set(part.lower().split())
            is_redundant = False
            
            for existing in combined:
                existing_words = set(existing.lower().split())
                # If more than 70% word overlap, consider redundant
                if part_words and existing_words:
                    overlap = len(part_words & existing_words) / len(part_words)
                    if overlap > 0.7:
                        is_redundant = True
                        break
            
            if not is_redundant:
                combined.append(part)
        
        return " ".join(combined)
    
    def _clean_answer(self, answer: str) -> str:
        """Clean and format the answer text."""
        if not answer:
            return ""
        
        # Remove excessive whitespace
        answer = " ".join(answer.split())
        
        # Remove duplicate sentences (simple check)
        sentences = answer.split('. ')
        seen = set()
        unique_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sentence_lower = sentence.lower().strip()
            # Skip if we've seen this exact sentence (allowing for minor variations)
            if sentence_lower and sentence_lower not in seen:
                seen.add(sentence_lower)
                unique_sentences.append(sentence)
        
        answer = '. '.join(unique_sentences)
        
        # Ensure proper ending
        if answer and not answer.endswith(('.', '!', '?')):
            answer += "."
        
        return answer.strip()
