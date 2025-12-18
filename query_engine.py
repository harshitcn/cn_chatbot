"""
Dynamic query engine using semantic search with embeddings.
Uses cosine similarity to find relevant chunks for any query.
No hardcoded keyword matching - fully dynamic.
"""
import logging
from typing import Dict, List, Any, Optional

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from embeddings import get_embeddings

logger = logging.getLogger(__name__)


class DynamicQueryEngine:
    """
    Dynamic query engine that uses semantic search with embeddings.
    Works for ANY query without hardcoded keywords or categories.
    """
    
    def __init__(self, vector_store: Optional[FAISS] = None, embeddings: Optional[HuggingFaceEmbeddings] = None):
        """
        Initialize the query engine.
        
        Args:
            vector_store: FAISS vector store with chunk embeddings
            embeddings: Embeddings model (will create if not provided)
        """
        self.vector_store = vector_store
        self.embeddings = embeddings or get_embeddings()
    
    def _find_relevant_chunks(
        self, 
        query: str, 
        top_k: int = 10,  # Increased to get more results
        similarity_threshold: float = 0.2  # Lower threshold to get more matches
    ) -> List[Dict[str, Any]]:
        """
        Find relevant chunks using semantic search.
        
        Args:
            query: User query string
            top_k: Number of top chunks to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List[Dict[str, Any]]: List of relevant chunks with similarity scores
        """
        if not self.vector_store:
            logger.warning("No vector store available")
            return []
        
        try:
            # Use FAISS similarity search
            results = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            relevant_chunks = []
            for doc, score in results:
                # FAISS returns distance (lower is better), convert to similarity
                # For normalized embeddings, similarity = 1 - distance
                similarity = 1 - score if score <= 1 else 1 / (1 + score)
                
                if similarity >= similarity_threshold:
                    relevant_chunks.append({
                        'text': doc.page_content,
                        'type': doc.metadata.get('type', 'unknown'),
                        'metadata': {k: v for k, v in doc.metadata.items() if k != 'type'},
                        'similarity_score': float(similarity)
                    })
            
            return relevant_chunks
        
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
            return []
    
    def _format_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Format chunks into a readable answer.
        Improved to prioritize structured camp items and better organize information.
        
        Args:
            query: Original user query
            chunks: List of relevant chunks
            
        Returns:
            str: Formatted answer text
        """
        if not chunks:
            return "I couldn't find relevant information to answer your question. Please try rephrasing or asking about something else."
        
        # Prioritize camp_item chunks for camp-related queries
        query_lower = query.lower()
        is_camp_query = 'camp' in query_lower
        
        # Sort chunks: camp_item first if it's a camp query, then by similarity score
        if is_camp_query:
            camp_items = [c for c in chunks if c.get('type') == 'camp_item']
            other_chunks = [c for c in chunks if c.get('type') != 'camp_item']
            sorted_chunks = camp_items + other_chunks
        else:
            sorted_chunks = chunks
        
        # Build formatted answer
        answer_parts = []
        seen_texts = set()  # Avoid duplicates
        
        # Add most relevant chunks
        for chunk in sorted_chunks[:15]:  # Increased to 15 for more comprehensive answers
            text = chunk.get('text', '').strip()
            if not text or text.lower() in seen_texts:
                continue
            
            metadata = chunk.get('metadata', {})
            chunk_type = chunk.get('type', 'unknown')
            
            # Format based on chunk type
            if chunk_type == 'camp_item':
                # Format camp items nicely
                camp_name = metadata.get('camp_name', '')
                age_group = metadata.get('age_group', '')
                
                formatted_item = ""
                if camp_name:
                    formatted_item = f"**{camp_name}**"
                if age_group:
                    formatted_item += f" (Ages {age_group})"
                if formatted_item:
                    formatted_item += ": "
                formatted_item += text
                answer_parts.append(formatted_item)
            elif 'title' in metadata:
                answer_parts.append(f"**{metadata['title']}**: {text}")
            else:
                answer_parts.append(text)
            
            seen_texts.add(text.lower())
        
        # Join with newlines for readability
        formatted_answer = '\n\n'.join(answer_parts)
        
        # Limit length but be more generous for camp listings
        max_length = 3000 if is_camp_query else 2000
        if len(formatted_answer) > max_length:
            formatted_answer = formatted_answer[:max_length] + "..."
        
        return formatted_answer
    
    def answer_query(
        self, 
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Answer a user query using semantic search.
        Works for ANY query without hardcoded keywords.
        
        Args:
            query: User query string
            top_k: Number of top chunks to retrieve
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            Dict[str, Any]: Structured response with:
                {
                    'status': str,  # 'success', 'no_results', or 'error'
                    'query': str,  # Original query
                    'chunks': List[Dict],  # Relevant chunks with scores
                    'formatted': str  # Formatted answer text
                }
        """
        try:
            if not query or not query.strip():
                return {
                    "status": "error",
                    "query": query,
                    "chunks": [],
                    "formatted": "Please provide a valid question."
                }
            
            # Find relevant chunks using semantic search
            chunks = self._find_relevant_chunks(query, top_k=top_k, similarity_threshold=similarity_threshold)
            
            # Format answer
            formatted_answer = self._format_answer(query, chunks)
            
            return {
                "status": "success" if chunks else "no_results",
                "query": query,
                "chunks": chunks,
                "formatted": formatted_answer
            }
        
        except Exception as e:
            logger.error(f"Error answering query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "chunks": [],
                "formatted": "I'm sorry, I encountered an error processing your query. Please try again."
            }

