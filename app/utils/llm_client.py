"""
LLM client for event discovery using Grok or OpenAI-compatible APIs.
Supports retry logic and error handling.
"""
import logging
import httpx
from typing import Optional
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with LLM APIs (Grok, OpenAI, etc.)
    Supports retry logic and configurable endpoints.
    """
    
    def __init__(self):
        """Initialize LLM client with settings."""
        self.settings = get_settings()
        self.api_key = self.settings.llm_api_key
        self.api_url = self.settings.llm_api_url
        self.provider = self.settings.llm_provider.lower()  # 'grok', 'openai', etc.
        self.max_retries = 3
        # Get timeout from settings, default to 180 seconds (3 minutes)
        self.timeout = getattr(self.settings, 'llm_timeout', 180.0)
        
        if not self.api_key:
            logger.warning("LLM API key not configured. Event discovery will fail.")
        if not self.api_url:
            logger.warning("LLM API URL not configured. Event discovery will fail.")
    
    def _get_grok_headers(self) -> dict:
        """Get headers for Grok API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_openai_headers(self) -> dict:
        """Get headers for OpenAI API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_headers(self) -> dict:
        """Get appropriate headers based on provider."""
        if self.provider == "grok":
            return self._get_grok_headers()
        elif self.provider == "openai":
            return self._get_openai_headers()
        else:
            # Default to OpenAI format
            return self._get_openai_headers()
    
    def _build_grok_payload(self, prompt: str) -> dict:
        """Build request payload for Grok API."""
        # Add current date context to emphasize upcoming events
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        enhanced_prompt = f"Today's date is {current_date}. {prompt}"
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ],
            "model": getattr(self.settings, 'llm_model', 'grok-beta'),
            "temperature": getattr(self.settings, 'llm_temperature', 0.8),
            "max_tokens": getattr(self.settings, 'llm_max_tokens', 8000)
        }
    
    def _build_openai_payload(self, prompt: str) -> dict:
        """Build request payload for OpenAI API."""
        # Add current date context to emphasize upcoming events
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        enhanced_prompt = f"Today's date is {current_date}. {prompt}"
        
        return {
            "model": getattr(self.settings, 'llm_model', 'gpt-4'),
            "messages": [
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ],
            "temperature": getattr(self.settings, 'llm_temperature', 0.8),
            "max_tokens": getattr(self.settings, 'llm_max_tokens', 8000)
        }
    
    def _build_payload(self, prompt: str) -> dict:
        """Build appropriate payload based on provider."""
        if self.provider == "grok":
            return self._build_grok_payload(prompt)
        elif self.provider == "openai":
            return self._build_openai_payload(prompt)
        else:
            # Default to OpenAI format
            return self._build_openai_payload(prompt)
    
    def _extract_response(self, response_data: dict) -> str:
        """Extract text response from API response."""
        if self.provider == "grok":
            # Grok API response format
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0].get("message", {}).get("content", "")
        elif self.provider == "openai":
            # OpenAI API response format
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0].get("message", {}).get("content", "")
        
        # Fallback: try common patterns
        if "content" in response_data:
            return response_data["content"]
        if "text" in response_data:
            return response_data["text"]
        if "response" in response_data:
            return response_data["response"]
        
        logger.warning(f"Unexpected API response format: {response_data}")
        return ""
    
    async def query_llm(self, prompt: str) -> Optional[str]:
        """
        Query the LLM API with retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Optional[str]: The LLM response text, or None if failed
        """
        if not self.api_key or not self.api_url:
            logger.error("LLM API key or URL not configured")
            return None
        
        headers = self._get_headers()
        payload = self._build_payload(prompt)
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Querying LLM (attempt {attempt}/{self.max_retries}) with timeout {self.timeout}s...")
                
                # Create timeout configuration: 30s connect, rest for read/write
                connect_timeout = min(30.0, self.timeout * 0.2)  # 20% for connection or max 30s
                read_timeout = self.timeout - connect_timeout  # Rest for reading response
                timeout_config = httpx.Timeout(connect=connect_timeout, read=read_timeout, write=30.0, pool=30.0)
                
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    
                    result = self._extract_response(response_data)
                    if result:
                        logger.info(f"Successfully received LLM response ({len(result)} characters)")
                        return result
                    else:
                        logger.warning("LLM response was empty")
                        if attempt < self.max_retries:
                            continue
                        return None
                        
            except httpx.TimeoutException as e:
                last_error = f"Timeout: {str(e)}"
                logger.warning(f"LLM API timeout on attempt {attempt}: {last_error}")
                if attempt < self.max_retries:
                    continue
                    
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {str(e)}"
                logger.warning(f"LLM API HTTP error on attempt {attempt}: {last_error}")
                
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    break
                if attempt < self.max_retries:
                    continue
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"LLM API error on attempt {attempt}: {last_error}", exc_info=True)
                if attempt < self.max_retries:
                    continue
        
        logger.error(f"Failed to query LLM after {self.max_retries} attempts. Last error: {last_error}")
        return None
    
    def generate_events_prompt(
        self,
        location: str,
        radius: int,
        country: str = "USA"
    ) -> str:
        """
        Generate the events discovery prompt by loading template and substituting values.
        
        Args:
            location: ZIP code, postal code, or town name
            radius: Search radius in miles
            country: Country name
            
        Returns:
            str: The formatted prompt
        """
        # Load prompt template
        prompt_template_path = Path(__file__).parent.parent / "prompts" / "events_discovery_prompt.txt"
        
        try:
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template not found at {prompt_template_path}")
            # Fallback to inline template
            template = """I want you to act as a research assistant for Code Ninjas Home Office. Your task is to search the internet and compile a list of upcoming family-friendly community events near a specific Code Ninjas center.

Center location: {{ZIP code, postal code, or town}}
Search radius: {{radius}} miles
Country: {{country}}

Please search for any family-friendly or community-oriented events and return results in a structured table with columns: Event Name, Event Date, Event Website / URL, Location, Organizer Contact Information, Fees (if any), Notes."""
        
        # Replace placeholders
        prompt = template.replace("{{ZIP code, postal code, or town}}", location)
        prompt = prompt.replace("{{radius}}", str(radius))
        prompt = prompt.replace("{{country}}", country)
        
        return prompt

