"""
LangChain chains and retrieval logic.
Handles the semantic search and answer retrieval from FAQ data.
"""
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from app.faq_data import FAQ_DATA
from app.utils.embeddings import load_or_build_faiss_index, get_embeddings
from app.utils.location_detector import LocationDetector
from app.utils.location_api import LocationAPIClient


class FAQRetriever:
    """
    FAQ retrieval system using semantic search.
    Uses FAISS vector store with HuggingFace embeddings to find relevant answers.
    Supports both static FAQ data and location-based data.
    """
    
    def __init__(self, top_k: int = 1):
        """
        Initialize the FAQ retriever.
        
        Args:
            top_k: Number of top results to return (default: 1 for best match)
        """
        self.top_k = top_k
        self.vector_store: Optional[FAISS] = None
        self.location_detector = LocationDetector()
        self.location_api_client = LocationAPIClient()
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the FAISS vector store with FAQ data."""
        self.vector_store = load_or_build_faiss_index(FAQ_DATA)
    
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
        
        Args:
            location_faq_data: Location-based FAQ data
            
        Returns:
            FAISS: Combined vector store
        """
        # Combine static and location data
        combined_data = FAQ_DATA + location_faq_data
        
        # Create documents
        embeddings = get_embeddings()
        documents = []
        for idx, faq in enumerate(combined_data):
            doc = Document(
                page_content=faq["question"],
                metadata={"answer": faq["answer"], "question": faq["question"], "index": idx}
            )
            documents.append(doc)
        
        # Create vector store from combined data
        # We'll create a temporary in-memory store for this query
        vector_store = FAISS.from_documents(documents, embeddings)
        return vector_store
    
    async def get_answer(self, question: str) -> str:
        """
        Get answer to a user question using semantic search.
        Detects location in question and fetches location-specific data if available.
        
        Args:
            question: User's question string
        
        Returns:
            str: Best matching answer from FAQ data (static + location-based if applicable)
        """
        if not self.vector_store:
            self._initialize_vector_store()
        
        # Detect location in the question
        location_name = self.location_detector.extract_location(question)
        vector_store = self.vector_store
        
        # If location is detected, fetch location data and merge with static data
        if location_name:
            try:
                location_data = await self.location_api_client.get_location_info(location_name)
                if location_data:
                    # Convert location data to FAQ format
                    location_faq_data = self._convert_location_data_to_faq(location_data, location_name)
                    
                    # Merge with static FAQ data
                    vector_store = self._merge_location_data_with_faq(location_faq_data)
            except Exception as e:
                # Log error but continue with static data only
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error fetching location data for '{location_name}': {str(e)}. Using static data only.")
        
        # Perform similarity search
        results: List[Document] = vector_store.similarity_search(
            question,
            k=self.top_k
        )
        
        # Return the answer from the top result
        if results and len(results) > 0:
            return results[0].metadata.get("answer", "I'm sorry, I couldn't find an answer to that question.")
        else:
            return "I'm sorry, I couldn't find an answer to that question. Please try rephrasing your question."


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

