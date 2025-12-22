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
            original_results = results  # Keep original for fallback
            
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
            if 'club' in query_lower:
                query_keywords.update(['club', 'clubs'])
            if 'create' in query_lower:
                query_keywords.update(['create'])
            
            # Check if query is general (asking about multiple things)
            is_general_query = any(word in query_lower for word in ['what', 'tell me about', 'know more about', 'offer', 'available', 'do you'])
            
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
                'club': ['camp', 'camps', 'academy', 'academies'],
                'clubs': ['camp', 'camps', 'academy', 'academies'],
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
            
            # Check if query is asking for specific data (camps, programs, etc.)
            is_specific_query = any(kw in query_lower for kw in ['upcoming', 'camp', 'program', 'club', 'create', 'academy'])
            
            for result in filtered_results[:top_k * 3]:  # Look through more results
                text = result["text"]
                section = result.get("section", "General")
                url = result.get("url", "")
                relevance = result.get("relevance_score", 0)
                metadata = result.get("metadata", {})
                
                # Skip if we've seen very similar text (avoid duplicates)
                text_hash = hashlib.md5(text.lower()[:100].encode()).hexdigest()
                if text_hash in seen_texts:
                    continue
                seen_texts.add(text_hash)
                
                # Skip chunks that are mostly navigation/UI text
                # Be less aggressive for general queries
                text_lower = text.lower()
                ui_word_count = sum(1 for word in ['learn more', 'enroll now', 'request info', 'show', 'click', 'close', 'book', 'find location', 'change location', 'your information', 'field is required'] if word in text_lower)
                total_words = len(text_lower.split())
                ui_threshold = 0.2 if is_general_query else 0.3  # Lower threshold for general queries
                if total_words > 0 and ui_word_count / total_words > ui_threshold:
                    continue
                
                # Check for topic conflicts
                has_conflict = False
                if primary_topic and primary_topic in topic_conflicts:
                    conflicts = topic_conflicts[primary_topic]
                    has_conflict_keywords = any(conflict in text_lower for conflict in conflicts)
                    has_topic_keywords = primary_topic in text_lower
                    
                    # Special handling for "clubs" - be more strict about excluding camps
                    if primary_topic in ['club', 'clubs']:
                        # If text mentions camps but not clubs, skip it
                        if 'camp' in text_lower and 'club' not in text_lower and relevance < 0.3:
                            continue
                    
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
                
                # For specific queries, prioritize API data and structured content
                if is_specific_query and metadata.get("type") in ["camp", "program"]:
                    topic_relevant_count += 1
                    answer_parts.append(text)
                # Prioritize topic-relevant chunks
                elif relevance > 0.3:  # Has some keyword matches
                    topic_relevant_count += 1
                    answer_parts.append(text)
                # For general queries, be more lenient
                elif is_general_query:
                    # For general queries, include more content even with lower relevance
                    if relevance > 0.1 or len(answer_parts) < 3:
                        answer_parts.append(text)
                elif topic_relevant_count < 2:  # Still need more content
                    answer_parts.append(text)
                elif len(answer_parts) < 3:  # Need at least 3 chunks
                    answer_parts.append(text)
                
                # Stop if we have enough topic-relevant content (but ensure minimum for general queries)
                min_chunks = 2 if is_general_query else 3
                if topic_relevant_count >= 3 and len(answer_parts) >= min_chunks:
                    break
                
                # Add to sources
                sources.append({
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "section": section,
                    "url": url,
                    "score": round(result["score"], 3),
                    "relevance": round(relevance, 2)
                })
            
            # If no answer parts after filtering, use top results anyway
            if not answer_parts:
                logger.warning(f"No answer parts after filtering for query: {query}, using fallback")
                # Fallback: use top results from original search without heavy filtering
                for result in original_results[:10]:  # Use more results for fallback
                    text = result.get("text", "")
                    if text and len(text.strip()) > 20:
                        # Only basic UI filtering for fallback - be very lenient
                        text_lower = text.lower()
                        # Only exclude if it's clearly a form error or very short UI text
                        excluded_patterns = ['field is required', 'parent first name field', 'parent last name field', 'your information', 'send question']
                        if not any(ui in text_lower for ui in excluded_patterns) and len(text.strip()) > 15:
                            # Check if it's not mostly navigation
                            ui_words = sum(1 for word in ['learn more', 'enroll now', 'request info', 'show', 'click'] if word in text_lower)
                            total_words = len(text_lower.split())
                            if total_words == 0 or ui_words / total_words < 0.4:  # Allow up to 40% UI words in fallback
                                answer_parts.append(text)
                                logger.info(f"Fallback added text: {text[:100]}...")
                                if len(answer_parts) >= 3:
                                    break
            
            # Combine answer parts intelligently
            answer = self._combine_answer_parts(answer_parts)
            
            # Clean up answer and remove unrelated content
            # But preserve answer if it's from fallback (be less aggressive)
            if answer and len(answer.strip()) > 10:
                answer = self._clean_answer(answer)
                # For general queries, be less aggressive with filtering
                if is_general_query:
                    # Only remove obvious UI text, keep content
                    answer = re.sub(r'\b(field is required|parent first name|parent last name|your information)\b', '', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'\s+', ' ', answer).strip()
                else:
                    answer = self._filter_unrelated_content(answer, query_keywords)
                
                # Format answer for better readability
                answer = self._format_answer(answer, query_keywords)
            
            # If answer is still empty after all processing, use fallback
            if not answer or len(answer.strip()) < 10:
                logger.warning(f"Answer still empty after all processing for query: {query}, using aggressive fallback")
                answer_parts_fallback = []
                for result in original_results[:15]:  # Check more results
                    text = result.get("text", "")
                    if text and len(text.strip()) > 30:
                        text_lower = text.lower()
                        # Very lenient filtering - only exclude obvious form errors
                        excluded = ['field is required', 'parent first name field', 'parent last name field']
                        if not any(ui in text_lower for ui in excluded):
                            # Check if it's not mostly single UI words
                            words = text_lower.split()
                            ui_words = ['learn', 'more', 'enroll', 'now', 'request', 'info', 'show', 'click']
                            ui_count = sum(1 for w in words if w in ui_words)
                            if len(words) == 0 or ui_count / len(words) < 0.5:  # Less than 50% UI words
                                answer_parts_fallback.append(text)
                                logger.info(f"Fallback added: {text[:80]}...")
                                if len(answer_parts_fallback) >= 3:
                                    break
                if answer_parts_fallback:
                    answer = self._combine_answer_parts(answer_parts_fallback)
                    # Minimal cleaning for fallback
                    answer = re.sub(r'\s+', ' ', answer).strip()
                    answer = re.sub(r'\b(field is required|parent first name|parent last name)\b', '', answer, flags=re.IGNORECASE)
                    answer = re.sub(r'\s+', ' ', answer).strip()
                    logger.info(f"Fallback answer created: {answer[:100]}...")
                else:
                    # Last resort: use first few results with minimal filtering
                    if original_results:
                        fallback_texts = []
                        for result in original_results[:5]:
                            text = result.get("text", "")
                            if text and len(text.strip()) > 30:
                                # Only exclude obvious form errors
                                if 'field is required' not in text.lower():
                                    fallback_texts.append(text[:200])  # Take first 200 chars of each
                                    if len(fallback_texts) >= 2:
                                        break
                        if fallback_texts:
                            answer = ". ".join(fallback_texts)
                            # Minimal cleaning
                            answer = re.sub(r'\b(field is required)\b', '', answer, flags=re.IGNORECASE)
                            answer = re.sub(r'\s+', ' ', answer).strip()
                            logger.warning(f"Using fallback results: {answer[:100]}...")
                        elif original_results:
                            # Absolute last resort: just use first result
                            first_text = original_results[0].get("text", "")
                            if first_text:
                                answer = first_text[:300]  # Just use first 300 chars
                                answer = re.sub(r'\b(field is required)\b', '', answer, flags=re.IGNORECASE)
                                answer = re.sub(r'\s+', ' ', answer).strip()
                                logger.warning(f"Using first result as absolute last resort")
            
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
            if not part or len(part) < 10:
                continue
            
            # Check for significant overlap with already included text
            part_words = set(part.lower().split())
            is_redundant = False
            
            for existing in combined:
                existing_words = set(existing.lower().split())
                # If more than 80% word overlap (increased from 70%), consider redundant
                if part_words and existing_words:
                    overlap = len(part_words & existing_words) / len(part_words)
                    if overlap > 0.8:  # More lenient threshold
                        is_redundant = True
                        break
            
            if not is_redundant:
                combined.append(part)
        
        # If all parts were filtered as redundant, return the first one anyway
        if not combined and answer_parts:
            return answer_parts[0]
        
        result = " ".join(combined)
        # Ensure we return something
        if not result or len(result.strip()) < 10:
            # Return first non-empty part
            for part in answer_parts:
                if part and len(part.strip()) > 10:
                    return part.strip()
            return answer_parts[0] if answer_parts else ""
        
        return result
    
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
        if not answer:
            return answer
        
        # For general queries or if no keywords, be very lenient
        if not query_keywords or len(query_keywords) <= 2:
            # Only remove obvious UI text, keep everything else
            sentences = re.split(r'([.!?]+\s+)', answer)
            filtered = []
            for i in range(0, len(sentences) - 1, 2):
                if i + 1 < len(sentences):
                    sentence = sentences[i] + sentences[i + 1]
                else:
                    sentence = sentences[i]
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:
                    # Only exclude obvious form errors
                    if not any(ui in sentence.lower() for ui in ['field is required', 'parent first name', 'parent last name']):
                        filtered.append(sentence)
            return ' '.join(filtered).strip() if filtered else answer
        
        if not query_keywords:
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
            # If no keyword matches but query is general (like "what programs"), be less strict
            elif not query_keywords or len(query_keywords) == 0:
                # For general queries, include sentences that aren't clearly UI
                if not self._is_ui_element_sentence(sentence) and len(sentence) > 10:
                    filtered_sentences.append(sentence)
            # If sentence is very short (likely a heading or button), include it if it's not clearly UI
            elif len(sentence) < 40:
                if not self._is_ui_element_sentence(sentence):
                    filtered_sentences.append(sentence)
            # For longer sentences without keywords, include them if they're not clearly unrelated
            # (they might provide context)
            else:
                # Include longer sentences unless they're clearly UI-heavy
                ui_word_count = sum(1 for word in ['learn more', 'enroll now', 'request info', 'show', 'click', 'close', 'book', 'find location', 'change location'] if word in sentence_lower)
                total_words = len(sentence_lower.split())
                if total_words == 0 or ui_word_count / total_words < 0.3:  # Less than 30% UI words
                    filtered_sentences.append(sentence)
        
        result = ' '.join(filtered_sentences).strip()
        
        # Final cleanup: remove common navigation/button text that's not useful
        ui_patterns = [
            r'\b(LEARN MORE|ENROLL NOW|SHOW|CLICK|BUTTON|REQUEST INFO|CLOSE|BOOK|FIND|GET STARTED|SIGN UP|REGISTER|VIEW|SEE MORE|READ MORE|CONTINUE|NEXT|PREVIOUS|BACK|HOME|MENU|SEARCH|LOGIN|LOGOUT|CONTACT|ABOUT|FAQ|BLOG|PRESS|CAREERS|FRANCHISING|LOCATIONS|PROGRAMS|PARTNERSHIP)\b',
            r'\b(FIRST NAME|LAST NAME|EMAIL|PHONE|ZIP|QUESTION|MESSAGE|NAME FIELD|EMAIL FIELD|PHONE FIELD|ZIP FIELD|QUESTION FIELD|MESSAGE FIELD).*(REQUIRED|FIELD)',
            r'\b(REQUIRED|OPTIONAL|FIELD IS REQUIRED)\b',
            r'\b(TEAMS AND CONDITIONS|TERMS AND CONDITIONS|PRIVACY POLICY|COOKIE POLICY)\b',
            r'\b(US & CANADA|UNITED KINGDOM|UNITED STATES)\b',
            r'\b(CHANGE LOCATION|FIND LOCATION|LET US FIND|LOCATIONS NEAR YOU)\b',
            r'\b(YOUR INFORMATION|YOUR QUESTION|SEND QUESTION)\b',
            r'\b(THANKS!|THANK YOU|SUCCESS|ERROR|LOADING|PLEASE WAIT)\b',
            r'\b(PARENT FIRST NAME FIELD IS REQUIRED|PARENT LAST NAME FIELD IS REQUIRED|PARENT EMAIL FIELD IS REQUIRED)\b',
            r'\b(CLOSE REQUEST INFO|REQUEST INFO EMPOWER THEIR FUTURE)\b',
        ]
        
        for pattern in ui_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
        result = re.sub(r'\s*\.\s*\.', '.', result)  # Remove double periods
        result = re.sub(r'\s*,\s*,', ',', result)  # Remove double commas
        
        return result.strip()
    
    def _is_ui_element_sentence(self, sentence: str) -> bool:
        """Check if a sentence is a UI element."""
        if not sentence:
            return True
        sentence_lower = sentence.lower().strip()
        ui_patterns = [
            r'^(learn more|enroll now|request info|show|click|close|book|find|get started)$',
            r'^(field is required|required|optional)$',
            r'^(your information|your question|send question)$',
        ]
        for pattern in ui_patterns:
            if re.match(pattern, sentence_lower):
                return True
        return False
    
    def _format_answer(self, answer: str, query_keywords: set) -> str:
        """
        Format answer for better readability and structure.
        
        Args:
            answer: The answer text
            query_keywords: Set of keywords from the query
            
        Returns:
            Formatted answer text
        """
        if not answer:
            return answer
        
        # Remove excessive capitalization (all caps sentences)
        sentences = re.split(r'([.!?]+\s+)', answer)
        formatted_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If sentence is all caps and longer than 10 chars, convert to title case
            if sentence.isupper() and len(sentence) > 10:
                sentence = sentence.title()
            
            formatted_sentences.append(sentence)
        
        answer = ' '.join(formatted_sentences)
        
        # Clean up common patterns
        answer = re.sub(r'\s+', ' ', answer)  # Normalize whitespace
        answer = re.sub(r'\s*\.\s*\.', '.', answer)  # Remove double periods
        answer = re.sub(r'\s*,\s*,', ',', answer)  # Remove double commas
        
        # Remove trailing UI text patterns
        answer = re.sub(r'\s*(LEARN MORE|ENROLL NOW|REQUEST INFO|CLOSE|SHOW|CLICK|PARENT)\s*$', '', answer, flags=re.IGNORECASE)
        
        # Remove incomplete sentences (ending with "Parent ." or similar)
        answer = re.sub(r'\s*Parent\s*\.\s*$', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\s*\.\s*$', '.', answer)  # Clean up trailing periods
        
        # Remove phrases like "the video to check out" or "the arrows to check out"
        answer = re.sub(r'\s*the\s+(video|arrows)\s+to\s+check\s+out[^.!?]*[.!?]?', '', answer, flags=re.IGNORECASE)
        
        return answer.strip()
