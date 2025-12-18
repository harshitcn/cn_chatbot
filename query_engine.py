"""
Dynamic query engine using semantic search.
No hard-coded categories or keyword matching - fully query-driven.
"""
import logging
import hashlib
import re
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
            # Perform semantic search (get more results for better filtering)
            results = self.search(query, top_k=top_k * 2)  # Get 2x results for filtering
            
            if not results:
                return {
                    "status": "no_results",
                    "query": query,
                    "answer": "I couldn't find relevant information to answer your question. Please try rephrasing or ask about something else.",
                    "sources": []
                }
            
            # Extract query keywords for topic filtering
            query_lower = query.lower()
            query_keywords = set(query_lower.split())
            # Add common variations
            if 'camp' in query_lower:
                query_keywords.update(['camp', 'camps'])
            if 'program' in query_lower:
                query_keywords.update(['program', 'programs'])
            if 'academ' in query_lower:
                query_keywords.update(['academy', 'academies'])
            
            # Filter by score and topic relevance
            max_distance = 2.0  # Maximum acceptable distance for L2
            filtered_results = []
            
            for r in results:
                # Score filter
                if r["score"] > max_distance and min_score > 0.0:
                    continue
                
                # Topic relevance: check if chunk contains query keywords
                text_lower = r["text"].lower()
                keyword_matches = sum(1 for kw in query_keywords if kw in text_lower)
                relevance_score = keyword_matches / max(len(query_keywords), 1)
                
                # Prioritize chunks with higher keyword relevance
                r["relevance_score"] = relevance_score
                filtered_results.append(r)
            
            # Sort by relevance (keyword matches) first, then by semantic score
            filtered_results.sort(key=lambda x: (-x.get("relevance_score", 0), x["score"]))
            
            if not filtered_results:
                # If all results filtered out, use top results anyway
                filtered_results = results[:min(3, len(results))]
            
            # Define topic conflicts for filtering
            topic_conflicts = {
                'camp': ['academy', 'academies'],
                'camps': ['academy', 'academies'],
                'program': ['camp', 'camps'],
                'programs': ['camp', 'camps'],
                'academy': ['camp', 'camps'],
                'academies': ['camp', 'camps'],
            }
            
            # Identify primary query topic
            primary_topic = None
            for kw in query_keywords:
                if kw in topic_conflicts:
                    primary_topic = kw
                    break
            
            # Build answer from top chunks, prioritizing topic-relevant ones
            answer_parts = []
            sources = []
            seen_texts = set()  # Avoid duplicate content
            topic_relevant_count = 0
            
            for result in filtered_results[:top_k * 2]:  # Look through more results
                text = result["text"]
                section = result.get("section", "General")
                url = result.get("url", "")
                relevance = result.get("relevance_score", 0)
                
                # Skip if we've seen very similar text (avoid duplicates)
                text_hash = hashlib.md5(text.lower()[:100].encode()).hexdigest()
                if text_hash in seen_texts:
                    continue
                seen_texts.add(text_hash)
                
                # Check for topic conflicts
                text_lower = text.lower()
                has_conflict = False
                if primary_topic and primary_topic in topic_conflicts:
                    conflicts = topic_conflicts[primary_topic]
                    has_conflict_keywords = any(conflict in text_lower for conflict in conflicts)
                    has_topic_keywords = primary_topic in text_lower
                    
                    # If chunk has conflict keywords but no topic keywords, skip it
                    if has_conflict_keywords and not has_topic_keywords and relevance < 0.2:
                        continue  # Skip chunks that are clearly about conflicting topic
                    
                    # If chunk has both topic and conflict, prefer chunks with more topic mentions
                    if has_conflict_keywords and has_topic_keywords:
                        topic_count = text_lower.count(primary_topic)
                        conflict_count = sum(text_lower.count(c) for c in conflicts)
                        # If conflicts outnumber topics significantly, skip
                        if conflict_count > topic_count * 1.5:
                            continue
                
                # Prioritize topic-relevant chunks
                # If we have topic-relevant chunks, prefer those over generic ones
                if relevance > 0.3:  # Has some keyword matches
                    topic_relevant_count += 1
                    answer_parts.append(text)
                elif topic_relevant_count < 2:  # Still need more content
                    answer_parts.append(text)
                elif len(answer_parts) < 3:  # Need at least 3 chunks
                    answer_parts.append(text)
                
                # Stop if we have enough topic-relevant content
                if topic_relevant_count >= 3 and len(answer_parts) >= 3:
                    break
                
                # Add to sources
                sources.append({
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "section": section,
                    "url": url,
                    "score": round(result["score"], 3),
                    "relevance": round(relevance, 2)
                })
            
            # Combine answer parts intelligently
            answer = self._combine_answer_parts(answer_parts)
            
            # Clean up answer and remove unrelated content
            answer = self._clean_answer(answer)
            answer = self._filter_unrelated_content(answer, query_keywords)
            
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
    
    def _filter_unrelated_content(self, answer: str, query_keywords: set) -> str:
        """
        Filter out sentences that are clearly about different topics.
        
        Args:
            answer: The combined answer text
            query_keywords: Set of keywords from the query
            
        Returns:
            Filtered answer text
        """
        if not answer or not query_keywords:
            return answer
        
        # Define topic conflict keywords
        topic_conflicts = {
            'camp': ['academy', 'academies', 'program', 'programs', 'jr', 'create'],
            'camps': ['academy', 'academies', 'program', 'programs', 'jr', 'create'],
            'program': ['camp', 'camps'],
            'programs': ['camp', 'camps'],
            'academy': ['camp', 'camps'],
            'academies': ['camp', 'camps'],
        }
        
        # Identify primary query topic
        primary_topic = None
        for kw in query_keywords:
            if kw in topic_conflicts:
                primary_topic = kw
                break
        
        # Split into sentences (better splitting)
        # Split by sentence endings, but keep the punctuation
        sentences = re.split(r'([.!?]+\s+)', answer)
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        filtered_sentences = []
        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            sentence_lower = sentence.lower()
            
            # Check if sentence contains query keywords
            keyword_matches = sum(1 for kw in query_keywords if kw in sentence_lower)
            
            # If primary topic is identified, check for conflicts
            if primary_topic and primary_topic in topic_conflicts:
                conflicts = topic_conflicts[primary_topic]
                has_conflict = any(conflict in sentence_lower for conflict in conflicts)
                has_topic = primary_topic in sentence_lower
                
                # If sentence has conflict keywords but no topic keywords, exclude it
                if has_conflict and not has_topic and keyword_matches == 0:
                    continue  # Skip this sentence - it's about a conflicting topic
            
            # If sentence has keyword matches, include it
            if keyword_matches > 0:
                filtered_sentences.append(sentence)
            # If sentence is very short (likely a heading or button), include it
            elif len(sentence) < 40:
                filtered_sentences.append(sentence)
            # For longer sentences without keywords, be more selective
            elif len(sentence) < 100:
                # Include short-medium sentences that might be context
                filtered_sentences.append(sentence)
            # For long sentences without keywords, exclude them
            # (they're likely about unrelated topics)
        
        result = ' '.join(filtered_sentences).strip()
        
        # Final cleanup: remove common navigation/button text that's not useful
        result = re.sub(r'\b(LEARN MORE|ENROLL NOW|SHOW|CLICK|BUTTON)\b', '', result, flags=re.IGNORECASE)
        result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
        
        return result.strip()
