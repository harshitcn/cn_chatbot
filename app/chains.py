"""
LangChain chains and retrieval logic.
Handles the semantic search and answer retrieval from FAQ data.
"""
import logging
import re
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.faq_data import FAQ_DATA
from app.predefined_qa import get_predefined_answer, normalize_question
from app.utils.embeddings import load_or_build_faiss_index, get_embeddings
from app.utils.location_detector import LocationDetector
from app.utils.location_api import LocationAPIClient
from app.utils.data_api_client import DataAPIClient
from app.utils.api_query_engine import APIQueryEngine
from app.utils.llm_client import LLMClient


class FAQRetriever:
    """
    FAQ retrieval system using semantic search.
    Uses FAISS vector store with HuggingFace embeddings to find relevant answers.
    Supports both static FAQ data and location-based data.
    """
    
    def __init__(self, top_k: int = 1, similarity_threshold: float = 1.2):
        """
        Initialize the FAQ retriever.
        
        Args:
            top_k: Number of top results to return (default: 1 for best match)
            similarity_threshold: Maximum distance threshold for relevant answers (default: 1.2)
                                 Answers with distance > threshold will return default response
                                 For normalized embeddings with L2 distance:
                                 - 0.0-0.8: Very similar (excellent match)
                                 - 0.8-1.0: Similar (good match)
                                 - 1.0-1.2: Somewhat related (acceptable match)
                                 - >1.2: Poor match, reject and try API calls
        """
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.vector_store: Optional[FAISS] = None
        self.location_detector = LocationDetector()
        self.location_api_client = LocationAPIClient()
        self.data_api_client = DataAPIClient()
        self.api_query_engine = APIQueryEngine(self.data_api_client)
        self.llm_client = LLMClient()
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
    
    def _exact_text_match_in_faq(self, question: str) -> Optional[str]:
        """
        Perform exact text matching in FAQ data before semantic search.
        This helps catch queries that might not match well with semantic search.
        
        Args:
            question: User's question string
        
        Returns:
            Optional[str]: Answer if exact match found, None otherwise
        """
        logger = logging.getLogger(__name__)
        normalized_question = normalize_question(question)
        
        for faq in FAQ_DATA:
            faq_question = faq.get("question", "")
            faq_answer = faq.get("answer", "")
            
            if not faq_question or not faq_answer:
                continue
            
            # Normalize FAQ question for comparison
            faq_normalized = normalize_question(faq_question)
            
            # Check for exact match
            if normalized_question == faq_normalized:
                logger.info(f"Exact text match found in FAQ: {faq_question[:100]}")
                return self._format_urls_as_clickable(faq_answer)
            
            # Check if user question is contained in FAQ question or vice versa
            if normalized_question in faq_normalized or faq_normalized in normalized_question:
                # Additional check: ensure significant overlap (at least 70% of shorter string)
                shorter_len = min(len(normalized_question.split()), len(faq_normalized.split()))
                if shorter_len > 0:
                    common_words = set(normalized_question.split()) & set(faq_normalized.split())
                    overlap_ratio = len(common_words) / shorter_len
                    if overlap_ratio >= 0.7:
                        logger.info(f"High overlap text match found in FAQ: {faq_question[:100]} (overlap: {overlap_ratio:.2%})")
                        return self._format_urls_as_clickable(faq_answer)
        
        return None
    
    def _truncate_response(self, response: str, max_words: int = 50) -> str:
        """
        Truncate a response to ensure it stays within word limit.
        
        Args:
            response: The response string to truncate
            max_words: Maximum number of words allowed (default: 50)
            
        Returns:
            str: Truncated response
        """
        if not response:
            return response
        
        words = response.strip().split()
        if len(words) <= max_words:
            return response.strip()
        
        # Truncate to max_words and add ellipsis if needed
        truncated = ' '.join(words[:max_words])
        # Remove trailing incomplete sentence if it ends with a comma or lowercase letter
        if truncated[-1] in [',', '.'] or truncated[-1].islower():
            # Try to find the last complete sentence
            last_period = truncated.rfind('.')
            if last_period > max_words * 0.6:  # If period is in last 40% of text
                truncated = truncated[:last_period + 1]
            else:
                truncated = truncated.rstrip(',.') + '.'
        
        return truncated.strip()
    
    def _format_urls_as_clickable(self, text: str) -> str:
        """
        Detect URLs in text and format them as clickable markdown links.
        
        Args:
            text: The text string that may contain URLs
            
        Returns:
            str: Text with URLs formatted as markdown links [text](url)
        """
        if not text:
            return text
        
        # Skip if text already contains markdown links (avoid double-formatting)
        if '](' in text and 'http' in text:
            # Check if it's already formatted as markdown link
            if re.search(r'\[.*?\]\(https?://', text):
                return text
        
        # URL pattern: matches http://, https://, www., and domains with common TLDs
        # Pattern breakdown:
        # - https?://[^\s<>"{}|\\^`\[\]]+ : URLs with protocol
        # - www\.[^\s<>"{}|\\^`\[\]]+ : www. URLs
        # - [a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})[^\s<>"{}|\\^`\[\]]* : domain names
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})(/[^\s<>"{}|\\^`\[\]]*)?)'
        
        def replace_url(match):
            url = match.group(0).rstrip('.,;:!?)')  # Remove trailing punctuation
            original_url = url
            
            # Ensure URL has protocol
            if url.startswith('www.'):
                url = 'https://' + url
            elif not url.startswith(('http://', 'https://')):
                # Check if it looks like a domain (has TLD)
                if '.' in url and not url.startswith('.'):
                    url = 'https://' + url
                else:
                    return match.group(0)  # Return as-is if not a valid URL
            
            # Create markdown link - use the URL as both text and link
            # Add back trailing punctuation if it was removed
            trailing_punct = match.group(0)[len(original_url):]
            return f'[{url}]({url}){trailing_punct}'
        
        # Replace URLs with markdown links
        formatted_text = re.sub(url_pattern, replace_url, text)
        
        return formatted_text
    
    def _generate_codeninjas_prompt(self, question: str, location_slug: Optional[str] = None) -> str:
        """
        Generate a prompt for CodeNinjas website queries using Grok LLM.
        
        Args:
            question: User's question string
            location_slug: Optional location slug for context
            
        Returns:
            str: Formatted prompt for Grok LLM
        """
        base_prompt = f"""You are a concise AI assistant for CodeNinjas. Answer the user's question in the SHORTEST way possible.

CRITICAL RULES - STRICTLY FOLLOW:
- Maximum 2-3 sentences OR 50 words - whichever is shorter
- Answer ONLY the specific question asked - nothing else
- NO introductory phrases, NO explanations, NO additional context
- NO "Here's...", "Let me...", "I can...", "Sure!" - just answer directly
- If you don't know, say "I don't have that information" (one sentence only)
- Be direct and factual - cut straight to the answer

User Question: {question}"""

        if location_slug:
            # Add location context if available
            base_prompt += f"\n\nLocation: {location_slug}"
        
        base_prompt += """\n\nAnswer the question above in the shortest possible way. Maximum 50 words. No extra information."""
        
        return base_prompt
    
    async def get_answer(self, question: str, location_slug: Optional[str] = None) -> str:
        """
        Get answer to a user question using improved multi-tier approach:
        1. Check for "Go back to main menu" queries - return welcome message
        2. Check predefined Q&A (exact/precise matching) - only return if it's a string answer (not menu/list)
        3. Check FAQ list with exact text matching first
        4. Check FAQ list with semantic search
        5. Use API-based data extraction for location-specific queries
        
        Args:
            question: User's question string
            location_slug: Optional location slug for location-specific queries
        
        Returns:
            str: Best matching answer from predefined Q&A, FAQ data, or API data
        """
        logger = logging.getLogger(__name__)
        
        # Default response when no relevant answer is found
        DEFAULT_RESPONSE = "I'm sorry, I don't have information about that. Please try asking about our services, programs, or locations, or contact our support team for assistance."
        
        # Check for "Go back to main menu" queries - return welcome message
        normalized_question = normalize_question(question)
        # Specific menu-related phrases that indicate user wants to go back
        menu_phrases = [
            "go back to main menu",
            "go back to the main menu",
            "back to main menu",
            "return to main menu",
            "return to the main menu",
            "go back to menu",
            "back to menu",
            "main menu",
            "start over",
            "go home"
        ]
        
        # Check if the question matches any menu-related phrase
        # Also check for standalone "home" or "menu" if the question is very short
        question_length = len(normalized_question.split())
        if question_length <= 3:
            # For short questions, also check for single words
            if normalized_question in ["home", "menu", "back"]:
                logger.info("User requested to go back to main menu (short query), returning welcome message")
                return "Welcome to Code Ninjas! Are you interested in a Program or a Franchisee? Which role fits you the best?,['Parent/Guardian', 'Existing Franchise Owner','Franchise Staff', 'Potential Franchisee Owner', 'Something else/just browsing']"
        
        # Check for menu-related phrases in longer questions
        if any(phrase in normalized_question for phrase in menu_phrases):
            logger.info("User requested to go back to main menu, returning welcome message")
            # Return the welcome message
            return "Welcome to Code Ninjas! Are you interested in a Program or a Franchisee? Which role fits you the best?,['Parent/Guardian', 'Existing Franchise Owner','Franchise Staff', 'Potential Franchisee Owner', 'Something else/just browsing']"
        
        # TIER 1: Check predefined Q&A first (exact/precise matching)
        logger.info("Tier 1: Checking predefined Q&A...")
        
        # Special handling for "Something else/just browsing" - ask user what they're looking for
        # Use the same normalization as predefined_qa for consistent matching
        normalized_question = normalize_question(question)
        browsing_normalized = normalize_question("Something else/just browsing")
        
        # Check if the normalized question matches the browsing option
        # Also check if it contains key words in case of slight variations
        if (normalized_question == browsing_normalized or 
            ("something" in normalized_question and "else" in normalized_question and "browsing" in normalized_question)):
            logger.info("User selected 'Something else/just browsing', prompting for more details")
            return "Please tell us what you are looking for"
        
        predefined_answer = get_predefined_answer(question)
        if predefined_answer:
            logger.info("Found answer in predefined Q&A")
            # Convert list to JSON string format if needed (for menu options)
            if isinstance(predefined_answer, list):
                import json
                logger.info("Predefined Q&A returned menu options")
                return json.dumps(predefined_answer)
            # Return string answer directly with URL formatting
            return self._format_urls_as_clickable(predefined_answer)
        
        logger.info("No match found in predefined Q&A, proceeding to FAQ search...")
        
        # TIER 2a: Check FAQ list with exact text matching first
        logger.info("Tier 2a: Checking FAQ list with exact text matching...")
        exact_match_answer = self._exact_text_match_in_faq(question)
        if exact_match_answer:
            logger.info("Found answer via exact text matching in FAQ")
            return self._format_urls_as_clickable(exact_match_answer)
        
        # TIER 2b: Check FAQ list (semantic search)
        logger.info("Tier 2b: Checking FAQ list with semantic search...")
        if not self.vector_store:
            self._initialize_vector_store()
        
        # Use location_slug if provided, otherwise detect location in the question
        location_name = None
        use_slug_directly = False
        if location_slug:
            location_name = location_slug
            use_slug_directly = True
            logger.info(f"Using provided location_slug: '{location_slug}' -> location_name: '{location_name}'")
        else:
            location_name = self.location_detector.extract_location(question)
            if location_name:
                logger.info(f"Location detected from question: '{location_name}'")
        
        # Log location state before Tier 3
        logger.info(f"Before Tier 3: location_slug='{location_slug}', location_name='{location_name}', use_slug_directly={use_slug_directly}")
        
        vector_store = self.vector_store
        
        # If location is detected or provided, fetch location data and merge with static data
        if location_name:
            try:
                if use_slug_directly:
                    # Use slug directly to get location data
                    logger.info(f"Fetching location data using slug: '{location_slug}'")
                    location_data = await self.location_api_client.get_location_data(location_slug, question)
                else:
                    # Get slug from location name first, then get data
                    logger.info(f"Location detected: '{location_name}' in question: '{question[:100]}'")
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
                
                # Calculate keyword overlap for the best match to ensure authenticity
                best_result_question = best_result.page_content.lower()
                best_result_words = set(best_result_question.split())
                best_result_keywords = best_result_words - stop_words
                best_common_keywords = user_keywords.intersection(best_result_keywords)
                best_keyword_overlap = len(best_common_keywords) / len(user_keywords) if user_keywords else 0
                
                # Determine if the match is relevant - stricter criteria
                # Require BOTH good semantic score AND meaningful keyword overlap
                # For normalized embeddings with L2 distance:
                # - Scores <= 1.0: Very good semantic match
                # - Scores <= 1.2: Good semantic match (threshold)
                # - Scores > 1.2: Poor semantic match, reject
                
                # Stricter relevance check:
                # 1. Semantic score must be within threshold
                # 2. Must have at least 40% keyword overlap OR at least 3 common keywords
                # 3. If location_slug provided, be even stricter (require 50% overlap or 4 keywords)
                semantic_match = best_score <= self.similarity_threshold
                keyword_match = (best_keyword_overlap >= 0.4 and len(best_common_keywords) >= 2) or len(best_common_keywords) >= 3
                
                # If location_slug is provided, require higher quality matches
                if location_slug:
                    keyword_match = (best_keyword_overlap >= 0.5 and len(best_common_keywords) >= 3) or len(best_common_keywords) >= 4
                    logger.info(f"Location slug provided - using stricter matching criteria")
                
                is_relevant = semantic_match and keyword_match
                
                # Additional check: if we have multiple results and the top one is much better,
                # consider it relevant only if it's a very good match
                if not is_relevant and len(results_with_scores) > 1:
                    second_score = results_with_scores[1][1]
                    score_gap = second_score - best_score
                    # Only accept if it's a very good match (score < 1.0) and has good keyword overlap
                    if score_gap > 0.3 and best_score < 1.0 and best_keyword_overlap >= 0.5:
                        is_relevant = True
                        logger.info(f"Top result accepted due to significant gap and good keyword match: {score_gap:.4f}, overlap: {best_keyword_overlap:.2%}")
                
                logger.info(f"Selected match - Score: {best_score:.4f}, Threshold: {self.similarity_threshold}")
                logger.info(f"Keyword overlap: {best_keyword_overlap:.2%} ({len(best_common_keywords)} common keywords)")
                logger.info(f"Semantic match: {semantic_match}, Keyword match: {keyword_match}, Relevant: {is_relevant}")
                logger.info(f"Matched question: {best_result.page_content[:150]}")
                
                if is_relevant:
                    answer = best_result.metadata.get("answer", DEFAULT_RESPONSE)
                    # Additional check: if answer is empty or too short, return default
                    if answer and len(answer.strip()) > 10:
                        logger.info(f"Found answer in FAQ list with score {best_score:.4f} and {best_keyword_overlap:.2%} keyword overlap")
                        return self._format_urls_as_clickable(answer)
                    else:
                        logger.info(f"Answer found but too short or empty, proceeding to API calls. Score: {best_score}")
                else:
                    # Score is too high or keyword overlap too low, meaning poor match
                    logger.info(f"No relevant answer in FAQ. Best match score: {best_score:.4f}, keyword overlap: {best_keyword_overlap:.2%}")
                    if location_slug:
                        logger.info(f"Location slug provided - prioritizing API calls over poor FAQ match")
            else:
                # No results found
                logger.info("No results found in FAQ list")
                
        except Exception as e:
            # If similarity search fails, log and proceed to API calls
            logger.warning(f"Error during FAQ similarity search: {str(e)}. Proceeding to API calls.")
        
        # TIER 3: Use API-based data extraction
        # Prioritize location-based API calls if location_slug is provided or location detected
        # IMPORTANT: Use location_slug directly if provided, as it's the source of truth
        location_for_tier3 = location_slug if location_slug else location_name
        
        logger.info(f"Tier 3: Using API-based data extraction. location_slug='{location_slug}', location_name='{location_name}', location_for_tier3='{location_for_tier3}'")
        
        api_failed = False
        if location_for_tier3:
            # If location_slug was provided, prioritize API calls for that location
            if location_slug:
                logger.info(f"Tier 3a: Attempting API data extraction for location slug '{location_slug}' (priority)...")
            else:
                logger.info(f"Tier 3a: Attempting API data extraction for location '{location_name}'...")
            
            try:
                # Use the location slug/name for API calls - use location_slug if available, otherwise location_name
                location_to_use = location_slug if location_slug else location_name
                
                # Use API-based query engine
                response = await self.api_query_engine.answer_query(question, location_to_use)
                
                if response.get('status') == 'success' and response.get('answer'):
                    answer = response.get('answer', '')
                    # Truncate API response to ensure it's concise (max 50 words)
                    truncated_answer = self._truncate_response(answer, max_words=50)
                    # Format URLs as clickable links
                    formatted_answer = self._format_urls_as_clickable(truncated_answer)
                    logger.info(f"Successfully got answer from API for location '{location_to_use}' (found {response.get('count', 0)} items, {len(answer)} chars -> {len(formatted_answer)} chars after formatting)")
                    return formatted_answer
                else:
                    logger.warning(f"API did not return data for location '{location_to_use}'")
                    api_failed = True
            except Exception as e:
                logger.warning(f"Error fetching data from API for location '{location_to_use}': {str(e)}, trying fallback...")
                api_failed = True
        else:
            logger.info("Tier 3: No location provided, skipping location-based API calls")
            api_failed = True
        
        # TIER 4: Fallback to Grok LLM when API fails
        if api_failed:
            logger.info("Tier 4: API failed or no location provided, attempting Grok LLM fallback...")
            # Check if LLM client is configured
            if not self.llm_client.api_key or not self.llm_client.api_url:
                logger.warning(f"Tier 4: LLM client not configured - api_key: {'present' if self.llm_client.api_key else 'missing'}, api_url: {'present' if self.llm_client.api_url else 'missing'}")
            else:
                logger.info(f"Tier 4: LLM client configured - provider: {self.llm_client.provider}, api_url: {self.llm_client.api_url[:50]}...")
                try:
                    # Generate prompt for CodeNinjas website query
                    prompt = self._generate_codeninjas_prompt(question, location_slug)
                    logger.info(f"Querying Grok LLM with user question: {question[:100]}...")
                    
                    # Query Grok LLM
                    llm_response = await self.llm_client.query_llm(prompt)
                    
                    if llm_response and llm_response.strip():
                        # Truncate response to ensure it's concise (max 50 words)
                        truncated_response = self._truncate_response(llm_response.strip(), max_words=50)
                        # Format URLs as clickable links
                        formatted_response = self._format_urls_as_clickable(truncated_response)
                        logger.info(f"Successfully got answer from Grok LLM ({len(llm_response)} chars -> {len(formatted_response)} chars after formatting)")
                        return formatted_response
                    else:
                        logger.warning("Grok LLM returned empty response")
                except Exception as e:
                    logger.error(f"Error querying Grok LLM: {str(e)}", exc_info=True)
        
        # If all tiers fail, return default response
        logger.info("All tiers exhausted, returning default response")
        return self._format_urls_as_clickable(DEFAULT_RESPONSE)


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

