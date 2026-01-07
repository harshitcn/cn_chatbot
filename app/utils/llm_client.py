"""
LLM client for event discovery using Grok or OpenAI-compatible APIs.
Supports retry logic and error handling.
Supports web search via function calling for OpenAI models.
"""
import logging
import httpx
from typing import Optional, List, Dict, Any
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
        
        # Initialize web search service if enabled
        self.web_search_enabled = (
            self.provider == "openai" and 
            getattr(self.settings, 'web_search_enabled', False)
        )
        if self.web_search_enabled:
            from app.utils.web_search import WebSearchService
            self.web_search = WebSearchService()
            if not self.web_search.enabled:
                logger.warning("Web search requested but not properly configured. Continuing without web search.")
                self.web_search_enabled = False
        else:
            self.web_search = None
        
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
            # "temperature": getattr(self.settings, 'llm_temperature', 0.8),
            # "max_tokens": getattr(self.settings, 'llm_max_tokens', 8000)
        }
    
    def _get_web_search_tool(self) -> Dict[str, Any]:
        """Get web search tool definition for OpenAI function calling."""
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the internet for current information, events, and real-time data. Use this when you need to find information that may not be in your training data, such as upcoming events, current dates, or location-specific information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find information on the internet. Be specific and include location, date range, and event type when relevant."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of search results to return (default: 10, max: 20)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def _build_openai_payload(self, prompt: str, messages: Optional[List[Dict[str, Any]]] = None) -> dict:
        """Build request payload for OpenAI API."""
        # Add current date context to emphasize upcoming events
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        enhanced_prompt = f"Today's date is {current_date}. {prompt}"
        
        # Use provided messages or create new conversation
        if messages is None:
            messages = [
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ]
        
        payload = {
            "model": getattr(self.settings, 'llm_model', 'gpt-4'),
            "messages": messages,
            # "temperature": getattr(self.settings, 'llm_temperature', 0.8),
            # "max_tokens": getattr(self.settings, 'llm_max_tokens', 8000)
        }
        
        # Add tools if web search is enabled
        if self.web_search_enabled and self.web_search and self.web_search.enabled:
            payload["tools"] = [self._get_web_search_tool()]
            payload["tool_choice"] = "auto"  # Let the model decide when to use the tool
        
        return payload
    
    def _build_payload(self, prompt: str, model_name: Optional[str] = None) -> dict:
        """Build appropriate payload based on provider."""
        if self.provider == "grok":
            return self._build_grok_payload(prompt, model_name)
        elif self.provider == "openai":
            return self._build_openai_payload(prompt)
        else:
            # Default to OpenAI format
            return self._build_openai_payload(prompt)
    
    def _extract_response(self, response_data: dict) -> tuple:
        """
        Extract text response and function calls from API response.
        
        Returns:
            tuple: (response_text, function_call_info)
        """
        if self.provider == "grok":
            # Grok API response format
            if "choices" in response_data and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message", {})
                return message.get("content", ""), None
        elif self.provider == "openai":
            # OpenAI API response format
            if "choices" in response_data and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls")
                
                # Check for function calls
                if tool_calls and len(tool_calls) > 0:
                    # Return the first tool call (we only support web_search)
                    tool_call = tool_calls[0]
                    if tool_call.get("function", {}).get("name") == "web_search":
                        return content, tool_call
                
                return content, None
        
        # Fallback: try common patterns
        if "content" in response_data:
            return response_data["content"], None
        if "text" in response_data:
            return response_data["text"], None
        if "response" in response_data:
            return response_data["response"], None
        
        logger.warning(f"Unexpected API response format: {response_data}")
        return "", None
    
    async def _handle_function_call(self, tool_call: Dict[str, Any], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle function call by executing web search and adding results to conversation.
        
        Args:
            tool_call: The tool call from OpenAI response
            messages: Current conversation messages
            
        Returns:
            Updated messages list with function call and result
        """
        function_name = tool_call.get("function", {}).get("name")
        function_args_str = tool_call.get("function", {}).get("arguments", "{}")
        
        if function_name != "web_search":
            logger.warning(f"Unknown function call: {function_name}")
            return messages
        
        try:
            import json
            function_args = json.loads(function_args_str)
            query = function_args.get("query", "")
            max_results = function_args.get("max_results", 10)
            
            logger.info(f"Executing web search: {query}")
            
            # Perform web search (async)
            search_results = await self.web_search.search(query, max_results=max_results)
            
            # Format search results
            formatted_results = self.web_search.format_search_results(search_results)
            
            # Add function call and result to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "name": "web_search",
                "content": formatted_results
            })
            
            logger.info(f"Web search completed, added {len(search_results)} results to conversation")
            
        except Exception as e:
            logger.error(f"Error handling function call: {str(e)}", exc_info=True)
            # Add error message to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "name": "web_search",
                "content": f"Error performing web search: {str(e)}"
            })
        
        return messages
    
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
            # Build initial payload
            if self.provider == "grok":
                payload = self._build_grok_payload(prompt, model_name)
            else:
                payload = self._build_openai_payload(prompt)
            
            # Log request details for debugging (without exposing API key)
            logger.debug(f"LLM Request - URL: {self.api_url}, Provider: {self.provider}, Model: {payload.get('model', 'N/A')}")
            if self.web_search_enabled:
                logger.info("Web search tool enabled - LLM can search the internet for real-time information")
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"Querying LLM (attempt {attempt}/{self.max_retries}) - URL: {self.api_url}, Model: {payload.get('model', 'N/A')}")
                    
                    # Create timeout configuration: 30s connect, rest for read/write
                    connect_timeout = min(30.0, self.timeout * 0.2)  # 20% for connection or max 30s
                    read_timeout = self.timeout - connect_timeout  # Rest for reading response
                    timeout_config = httpx.Timeout(connect=connect_timeout, read=read_timeout, write=30.0, pool=30.0)
                    
                    # Handle conversation with function calls for OpenAI
                    messages = payload.get("messages", [])
                    max_function_calls = 5  # Limit to prevent infinite loops
                    function_call_count = 0
                    
                    while function_call_count < max_function_calls:
                        async with httpx.AsyncClient(timeout=timeout_config) as client:
                            # Update payload with current messages
                            current_payload = payload.copy()
                            current_payload["messages"] = messages
                            
                            response = await client.post(
                                self.api_url,
                                headers=headers,
                                json=current_payload
                            )
                            response.raise_for_status()
                            response_data = response.json()
                            
                            result, tool_call = self._extract_response(response_data)
                            
                            # If there's a function call, execute it and continue conversation
                            if tool_call and self.web_search_enabled and self.web_search and self.web_search.enabled:
                                function_call_count += 1
                                logger.info(f"Function call detected (call #{function_call_count}), executing web search...")
                                messages = await self._handle_function_call(tool_call, messages)
                                # Continue the conversation loop
                                continue
                            
                            # If we have a result (no more function calls), return it
                            if result:
                                logger.info(f"Successfully received LLM response ({len(result)} characters)")
                                if function_call_count > 0:
                                    logger.info(f"Completed after {function_call_count} web search call(s)")
                                return result
                            else:
                                logger.warning("LLM response was empty")
                                if attempt < self.max_retries:
                                    break  # Break inner loop to retry
                                return None
                    
                    # If we exhausted function calls, return the last result
                    if function_call_count >= max_function_calls:
                        logger.warning(f"Reached maximum function calls ({max_function_calls}), returning last response")
                        if result:
                            return result
                            
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

