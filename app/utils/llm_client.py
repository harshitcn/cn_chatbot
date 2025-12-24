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
    
    def _build_grok_payload(self, prompt: str, model_name: Optional[str] = None) -> dict:
        """Build request payload for Grok API."""
        # Add current date context to emphasize upcoming events
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        enhanced_prompt = f"Today's date is {current_date}. {prompt}"
        
        # Use provided model_name or get from settings, with fallback
        if model_name is None:
            model_name = getattr(self.settings, 'llm_model', 'grok-beta')
        # Common Grok model names: grok-beta, grok-2, grok-2-1212, grok-vision-beta
        # If grok-beta returns 404 or 400, try grok-2
        logger.debug(f"Using Grok model: {model_name}")
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ],
            "model": model_name,
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
    
    def _build_payload(self, prompt: str, model_name: Optional[str] = None) -> dict:
        """Build appropriate payload based on provider."""
        if self.provider == "grok":
            return self._build_grok_payload(prompt, model_name)
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
        For Grok, automatically tries alternative models if the primary model fails.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Optional[str]: The LLM response text, or None if failed
        """
        if not self.api_key or not self.api_url:
            logger.error("LLM API key or URL not configured")
            return None
        
        headers = self._get_headers()
        
        # For Grok, try alternative models if primary fails
        grok_models_to_try = []
        if self.provider == "grok":
            primary_model = getattr(self.settings, 'llm_model', 'grok-beta')
            grok_models_to_try = [primary_model]
            # Add fallback models if primary is grok-beta
            if primary_model == 'grok-beta':
                grok_models_to_try.extend(['grok-2', 'grok-2-1212'])
            elif primary_model == 'grok-2':
                grok_models_to_try.extend(['grok-2-1212', 'grok-beta'])
        else:
            grok_models_to_try = [None]  # Use default for non-Grok providers
        
        last_error = None
        for model_index, model_name in enumerate(grok_models_to_try):
            payload = self._build_payload(prompt, model_name)
            
            # Log request details for debugging (without exposing API key)
            logger.debug(f"LLM Request - URL: {self.api_url}, Provider: {self.provider}, Model: {payload.get('model', 'N/A')}")
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"Querying LLM (attempt {attempt}/{self.max_retries}) - URL: {self.api_url}, Model: {payload.get('model', 'N/A')}")
                    
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
                    # Try next model if available
                    break
                        
                except httpx.HTTPStatusError as e:
                    last_error = f"HTTP {e.response.status_code}: {str(e)}"
                    # Log detailed error information for debugging
                    try:
                        error_body = e.response.json() if e.response.content else {}
                        logger.error(f"LLM API HTTP error on attempt {attempt}: {last_error}")
                        logger.error(f"   Request URL: {self.api_url}")
                        logger.error(f"   Request method: POST")
                        logger.error(f"   Model used: {payload.get('model', 'N/A')}")
                        logger.error(f"   Error response: {error_body}")
                        logger.error(f"   Response headers: {dict(e.response.headers)}")
                        # Extract error message if available
                        if isinstance(error_body, dict):
                            error_msg = error_body.get('error', {}).get('message', '') if isinstance(error_body.get('error'), dict) else error_body.get('message', '')
                            if error_msg:
                                logger.error(f"   Error message: {error_msg}")
                    except:
                        error_text = e.response.text if hasattr(e.response, 'text') else str(e.response.content)
                        logger.error(f"LLM API HTTP error on attempt {attempt}: {last_error}")
                        logger.error(f"   Request URL: {self.api_url}")
                        logger.error(f"   Model used: {payload.get('model', 'N/A')}")
                        logger.error(f"   Error response text: {error_text[:500]}")
                    
                    # For 4xx errors with Grok, try next model if available
                    if 400 <= e.response.status_code < 500:
                        if self.provider == "grok" and len(grok_models_to_try) > model_index + 1:
                            logger.info(f"Model {payload.get('model')} failed with 4xx error, trying next model...")
                            break  # Break inner loop to try next model
                        else:
                            # No more models to try, give up
                            logger.error(f"Failed with 4xx error and no more models to try")
                            return None
                    if attempt < self.max_retries:
                        continue
                    # Try next model if available
                    break
                        
                except Exception as e:
                    last_error = f"Unexpected error: {str(e)}"
                    logger.error(f"LLM API error on attempt {attempt}: {last_error}", exc_info=True)
                    if attempt < self.max_retries:
                        continue
                    # Try next model if available
                    break
        
        logger.error(f"Failed to query LLM after trying {len(grok_models_to_try)} model(s). Last error: {last_error}")
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

