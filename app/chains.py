"""
LangChain chains and retrieval logic.
Handles the semantic search and answer retrieval from FAQ data.
"""
import logging
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.faq_data import FAQ_DATA
from app.predefined_qa import get_predefined_answer
from app.utils.embeddings import load_or_build_faiss_index, get_embeddings
from app.utils.location_detector import LocationDetector
from app.utils.location_api import LocationAPIClient
from app.utils.web_scraper import WebScraper


class FAQRetriever:
    """
    FAQ retrieval system using semantic search.
    Uses FAISS vector store with HuggingFace embeddings to find relevant answers.
    Supports both static FAQ data and location-based data.
    """
    
    def __init__(self, top_k: int = 1, similarity_threshold: float = 1.5):
        """
        Initialize the FAQ retriever.
        
        Args:
            top_k: Number of top results to return (default: 1 for best match)
            similarity_threshold: Maximum distance threshold for relevant answers (default: 1.5)
                                 Answers with distance > threshold will return default response
                                 For normalized embeddings with L2 distance:
                                 - 0.0-0.8: Very similar
                                 - 0.8-1.2: Similar
                                 - 1.2-1.5: Somewhat related
                                 - >1.5: Poor match, return default
        """
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.vector_store: Optional[FAISS] = None
        self.location_detector = LocationDetector()
        self.location_api_client = LocationAPIClient()
        self.web_scraper = WebScraper()
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the FAISS vector store with FAQ data.
        Optimized for memory usage on free tier platforms.
        """
        import gc
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Initializing vector store (this may take a moment)...")
            self.vector_store = load_or_build_faiss_index(FAQ_DATA)
            # Force garbage collection after initialization
            gc.collect()
            logger.info("Vector store initialized successfully")
        except MemoryError as e:
            logger.error(f"Out of memory during vector store initialization: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def _convert_location_data_to_faq(self, location_data: Dict[str, Any], location_name: str) -> List[Dict[str, str]]:
        """
        Convert location API response to FAQ format.
        
        This function handles various API response formats:
        - Direct content strings
        - Key-value pairs
        - Nested dictionaries
        - Lists of items
        - Common API response structures (data, content, results, etc.)
        
        Args:
            location_data: Location data from API
            location_name: Name of the location
            
        Returns:
            List[Dict[str, str]]: List of FAQ entries in the format {"question": ..., "answer": ...}
        """
        faq_entries = []
        
        # Handle string responses directly
        if isinstance(location_data, str):
            question = f"Tell me about {location_name}"
            answer = location_data
            faq_entries.append({"question": question, "answer": answer})
            return faq_entries
        
        # Handle list responses
        if isinstance(location_data, list):
            for idx, item in enumerate(location_data):
                if isinstance(item, dict):
                    # Recursively process each item in the list
                    item_faqs = self._convert_location_data_to_faq(item, location_name)
                    faq_entries.extend(item_faqs)
                elif isinstance(item, (str, int, float)):
                    question = f"What is item {idx + 1} for {location_name}?"
                    answer = str(item)
                    faq_entries.append({"question": question, "answer": answer})
            if faq_entries:
                return faq_entries
        
        # Convert location data to FAQ format
        # This is a generic conversion - adjust based on your API response structure
        if isinstance(location_data, dict):
            # Check for common API response structures first
            if "content" in location_data:
                content = location_data["content"]
                if isinstance(content, str):
                    question = f"Tell me about {location_name}"
                    answer = content
                    faq_entries.append({"question": question, "answer": answer})
                elif isinstance(content, (dict, list)):
                    # Recursively process nested content
                    nested_faqs = self._convert_location_data_to_faq(content, location_name)
                    faq_entries.extend(nested_faqs)
            
            if "data" in location_data:
                data = location_data["data"]
                nested_faqs = self._convert_location_data_to_faq(data, location_name)
                faq_entries.extend(nested_faqs)
            
            if "results" in location_data:
                results = location_data["results"]
                if isinstance(results, list):
                    for item in results:
                        nested_faqs = self._convert_location_data_to_faq(item, location_name)
                        faq_entries.extend(nested_faqs)
            
            # If the API returns structured data, convert it to Q&A pairs
            for key, value in location_data.items():
                # Skip already processed keys
                if key in ["content", "data", "results"]:
                    continue
                    
                if isinstance(value, (str, int, float)):
                    question = f"What is the {key} for {location_name}?"
                    answer = f"For {location_name}, {key} is {value}."
                    faq_entries.append({"question": question, "answer": answer})
                elif isinstance(value, dict):
                    # Nested dictionaries
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (str, int, float)):
                            question = f"What is the {sub_key} for {location_name}?"
                            answer = f"For {location_name}, {sub_key} is {sub_value}."
                            faq_entries.append({"question": question, "answer": answer})
                elif isinstance(value, list):
                    # List values
                    for idx, item in enumerate(value):
                        if isinstance(item, (str, int, float)):
                            question = f"What is {key} item {idx + 1} for {location_name}?"
                            answer = f"For {location_name}, {key} item {idx + 1} is {item}."
                            faq_entries.append({"question": question, "answer": answer})
        
        # If no structured data found, create a general entry
        if not faq_entries:
            question = f"Tell me about {location_name}"
            # Try to format the answer nicely
            if isinstance(location_data, dict):
                answer = f"Here is information about {location_name}: {str(location_data)}"
            else:
                answer = f"Here is information about {location_name}: {str(location_data)}"
            faq_entries.append({"question": question, "answer": answer})
        
        return faq_entries
    
    def _merge_location_data_with_faq(self, location_faq_data: List[Dict[str, str]]) -> FAISS:
        """
        Merge location-based FAQ data with static FAQ data and create a vector store.
        Optimized for memory usage.
        
        Args:
            location_faq_data: Location-based FAQ data
            
        Returns:
            FAISS: Combined vector store
        """
        import gc
        
        # Combine static and location data
        combined_data = FAQ_DATA + location_faq_data
        
        # Create documents (minimize memory)
        embeddings = get_embeddings()
        documents = []
        for idx, faq in enumerate(combined_data):
            doc = Document(
                page_content=faq["question"],
                metadata={"answer": faq["answer"], "index": idx}  # Removed duplicate question
            )
            documents.append(doc)
        
        # Create vector store from combined data
        # We'll create a temporary in-memory store for this query
        vector_store = FAISS.from_documents(documents, embeddings)
        
        # Clean up
        del documents
        gc.collect()
        
        return vector_store
    
    async def get_answer(self, question: str) -> str:
        """
        Get answer to a user question using three-tier approach:
        1. Check predefined Q&A (exact/precise matching)
        2. Check FAQ list (semantic search)
        3. Scrape website for location (if location detected and FAQ doesn't have answer)
        
        Args:
            question: User's question string
        
        Returns:
            str: Best matching answer from predefined Q&A, FAQ data, or scraped content
        """
        logger = logging.getLogger(__name__)
        
        # Default response when no relevant answer is found
        DEFAULT_RESPONSE = "I'm sorry, I don't have information about that. Please try asking about our services, programs, or locations, or contact our support team for assistance."
        
        # TIER 1: Check predefined Q&A first (exact/precise matching)
        logger.info("Tier 1: Checking predefined Q&A...")
        predefined_answer = get_predefined_answer(question)
        if predefined_answer:
            logger.info("Found answer in predefined Q&A")
            return predefined_answer
        logger.info("No match found in predefined Q&A, proceeding to FAQ search...")
        
        # TIER 2: Check FAQ list (semantic search)
        if not self.vector_store:
            self._initialize_vector_store()
        
        # Detect location in the question
        location_name = self.location_detector.extract_location(question)
        vector_store = self.vector_store
        
        # If location is detected, fetch location data and merge with static data
        if location_name:
            try:
                logger.info(f"Location detected: '{location_name}' in question: '{question[:100]}'")
                # Pass the full question to the API for better context
                location_data = await self.location_api_client.get_location_info(location_name, question)
                if location_data:
                    logger.info(f"Successfully fetched location data for '{location_name}'")
                    # Convert location data to FAQ format
                    location_faq_data = self._convert_location_data_to_faq(location_data, location_name)
                    
                    # Merge with static FAQ data
                    vector_store = self._merge_location_data_with_faq(location_faq_data)
                else:
                    logger.warning(f"No location data returned for '{location_name}'")
            except Exception as e:
                # Log error but continue with static data only
                logger.warning(f"Error fetching location data for '{location_name}': {str(e)}. Using static data only.")
        
        logger.info("Tier 2: Searching FAQ list...")
        
        # Perform similarity search with scores to check relevance
        # Get multiple results to enable relative comparison
        try:
            results_with_scores = vector_store.similarity_search_with_score(
                question,
                k=min(3, self.top_k + 2)  # Get a few more results for comparison
            )
            
            # Check if we have results
            if results_with_scores and len(results_with_scores) > 0:
                # Log all top results for debugging
                logger.info(f"Top {len(results_with_scores)} similarity search results:")
                for idx, (result, score) in enumerate(results_with_scores):
                    matched_question = result.page_content[:100] if result.page_content else "N/A"
                    logger.info(f"  {idx+1}. Score: {score:.4f} - Question: {matched_question}")
                
                top_result, top_score = results_with_scores[0]
                matched_question = top_result.page_content
                
                # For normalized embeddings with L2 distance:
                # - Lower score (distance) = more similar
                # - Distance ranges from 0 (identical) to 2 (opposite)
                # - Typical good matches have distance < 1.0-1.2
                # - Very poor matches have distance > 1.5
                
                # Try to find a better match by checking if any result has a question that starts similarly
                # This helps when the semantic search finds a related but not exact match
                best_result = top_result
                best_score = top_score
                
                # Normalize the user question for comparison
                user_question_lower = question.lower().strip()
                user_question_words = set(user_question_lower.split())
                
                # Remove common stop words for better matching
                stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'does', 'do', 'how', 'can', 'will', 'would', 'should', 'could'}
                user_keywords = user_question_words - stop_words
                
                # Check if any result has a question that's a better text match
                for result, score in results_with_scores:
                    if score > self.similarity_threshold:
                        continue  # Skip results that are too dissimilar
                    
                    result_question = result.page_content.lower()
                    result_words = set(result_question.split())
                    result_keywords = result_words - stop_words
                    
                    # Calculate keyword overlap
                    common_keywords = user_keywords.intersection(result_keywords)
                    keyword_overlap_ratio = len(common_keywords) / len(user_keywords) if user_keywords else 0
                    
                    # Prefer results where:
                    # 1. The FAQ question starts with the user's question (or vice versa)
                    # 2. High keyword overlap (>= 50%)
                    # 3. The user's question is contained in the FAQ question
                    is_better_match = False
                    
                    if user_question_lower in result_question or result_question.startswith(user_question_lower[:30]):
                        # User question is a subset of FAQ question - this is likely the best match
                        is_better_match = True
                        logger.info(f"Found subset match: user question is in FAQ question")
                    elif keyword_overlap_ratio >= 0.5 and len(common_keywords) >= 2:
                        # High keyword overlap - prefer this if score is similar
                        if score <= best_score + 0.15:  # Allow slightly worse score if keyword match is better
                            is_better_match = True
                            logger.info(f"Found high keyword overlap match: {keyword_overlap_ratio:.2%} overlap")
                    
                    if is_better_match:
                        # Update best match if this is better
                        if score < best_score or (score <= best_score + 0.15 and keyword_overlap_ratio > 0.6):
                            best_result = result
                            best_score = score
                            logger.info(f"Updated best match: {result.page_content[:100]} (score: {score:.4f}, overlap: {keyword_overlap_ratio:.2%})")
                
                # Determine if the match is relevant
                # For normalized embeddings with L2 distance, scores > 1.5 indicate poor matches
                # We'll be permissive and only reject very poor matches
                is_relevant = best_score <= self.similarity_threshold
                
                # Additional check: if we have multiple results and the top one is much better,
                # it's likely relevant even if slightly above threshold
                if not is_relevant and len(results_with_scores) > 1:
                    second_score = results_with_scores[1][1]
                    score_gap = second_score - best_score
                    # If top result is significantly better (gap > 0.2), consider it relevant
                    if score_gap > 0.2 and best_score < 1.8:
                        is_relevant = True
                        logger.info(f"Top result accepted due to significant gap: {score_gap:.4f}")
                
                logger.info(f"Selected match - Score: {best_score:.4f}, Threshold: {self.similarity_threshold}, Relevant: {is_relevant}")
                logger.info(f"Matched question: {best_result.page_content[:150]}")
                
                if is_relevant:
                    answer = best_result.metadata.get("answer", DEFAULT_RESPONSE)
                    # Additional check: if answer is empty or too short, return default
                    if answer and len(answer.strip()) > 10:
                        logger.info(f"Found answer in FAQ list with score {best_score:.4f}")
                        return answer
                    else:
                        logger.info(f"Answer found but too short or empty, proceeding to web scraping. Score: {best_score}")
                else:
                    # Score is too high, meaning low similarity
                    logger.info(f"No relevant answer in FAQ. Best match score: {best_score:.4f} exceeds threshold: {self.similarity_threshold}")
            else:
                # No results found
                logger.info("No results found in FAQ list")
                
        except Exception as e:
            # If similarity search fails, log and proceed to web scraping
            logger.warning(f"Error during FAQ similarity search: {str(e)}. Proceeding to web scraping if location detected.")
        
        # TIER 3: Scrape website for location (if location detected and FAQ doesn't have answer)
        if location_name:
            logger.info(f"Tier 3: Attempting to scrape website for location '{location_name}'...")
            try:
                scraped_answer = await self.web_scraper.scrape_and_extract_answer(location_name, question)
                if scraped_answer:
                    logger.info(f"Successfully scraped content for location '{location_name}'")
                    return scraped_answer
                else:
                    logger.warning(f"Could not scrape content for location '{location_name}'")
            except Exception as e:
                logger.warning(f"Error scraping website for location '{location_name}': {str(e)}")
        
        # If all tiers fail, return default response
        logger.info("All tiers exhausted, returning default response")
        return DEFAULT_RESPONSE


# Global retriever instance (initialized lazily)
_retriever: Optional[FAQRetriever] = None


def get_retriever() -> FAQRetriever:
    """
    Get or create the global FAQ retriever instance.
    
    Returns:
        FAQRetriever: Singleton retriever instance
    """
    global _retriever
    if _retriever is None:
        _retriever = FAQRetriever()
    return _retriever

