"""OpenAI-compatible LLM provider implementation.

Supports OpenAI API, vLLM, and other OpenAI-compatible services.
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any

import httpx

from openerb.llm.base import LLMProvider, Message, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI and OpenAI-compatible APIs.
    
    Supports:
    - OpenAI API (https://api.openai.com/v1)
    - vLLM (local inference server)
    - Other OpenAI-compatible APIs
    
    API Reference: https://platform.openai.com/docs/api-reference/chat/create
    
    Example:
        >>> # Using OpenAI
        >>> provider = OpenAIProvider(
        ...     api_key="sk-xxx",
        ...     model="gpt-4"
        ... )
        
        >>> # Using local vLLM
        >>> provider = OpenAIProvider(
        ...     api_key="not_needed",
        ...     model="llama-2-7b",
        ...     api_base="http://localhost:8000/v1"
        ... )
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        api_key: str,
        model: str,
        api_base: Optional[str] = None,
        timeout: float = 60.0,
        **kwargs,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (can be dummy for local services)
            model: Model name
            api_base: Custom API base URL (defaults to OpenAI)
            timeout: Request timeout in seconds
            **kwargs: Additional configuration
        """
        super().__init__(api_key=api_key, model=model, api_base=api_base, **kwargs)
        self.timeout = timeout
        self.base_url = (api_base or self.DEFAULT_BASE_URL).rstrip("/")
        self.validate_config()

    def validate_config(self) -> bool:
        """Validate OpenAI configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.model:
            raise ValueError("Model name is required")
        if not self.base_url:
            raise ValueError("API base URL is required")
        logger.info(f"OpenAI config validated: model={self.model}, base_url={self.base_url}")
        return True

    async def call(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Call OpenAI API with retry logic.

        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters (top_p, frequency_penalty, etc.)

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If API call fails after retries
        """
        # Validate input
        for msg in messages:
            msg.validate()

        # Prepare request payload
        payload = self._prepare_payload(messages, temperature, max_tokens, **kwargs)

        # Execute with retry logic
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"OpenAI API call attempt {attempt + 1}/{self.MAX_RETRIES}")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=self._get_headers(),
                    )

                    # Handle HTTP errors
                    if response.status_code != 200:
                        error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                        error_message = error_data.get("error", {}).get("message", response.text)
                        raise RuntimeError(f"OpenAI API error (HTTP {response.status_code}): {error_message}")

                    # Parse response
                    return self._parse_response(response.json())

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"OpenAI timeout on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.INITIAL_RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)

            except RuntimeError as e:
                last_error = e
                # Check if error is retryable (rate limit, temporary error)
                if any(code in str(e) for code in ["429", "503", "500", "timeout"]):
                    logger.warning(f"Retryable error on attempt {attempt + 1}: {e}")
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.INITIAL_RETRY_DELAY * (2 ** attempt)
                        await asyncio.sleep(delay)
                else:
                    raise

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
                raise RuntimeError(f"OpenAI API call failed: {e}") from e

        # All retries exhausted
        raise RuntimeError(f"OpenAI API call failed after {self.MAX_RETRIES} attempts: {last_error}")

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers for OpenAI API.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "openerb/llm/openai",
        }

    def _prepare_payload(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs,
    ) -> Dict[str, Any]:
        """Prepare request payload for OpenAI API.

        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Payload dictionary for API request
        """
        formatted_messages = []

        for msg in messages:
            message_obj: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }

            # Add image if present (OpenAI vision format)
            if msg.image_url or msg.image_base64:
                # Convert to OpenAI vision format with content array
                image_content = {}
                if msg.image_url:
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": msg.image_url},
                    }
                elif msg.image_base64:
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{msg.image_base64}"},
                    }

                # For multi-modal messages, use content array
                message_obj["content"] = [
                    {"type": "text", "text": msg.content},
                    image_content,
                ]

            formatted_messages.append(message_obj)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }

        # Add optional parameters
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Support additional OpenAI parameters
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            payload["presence_penalty"] = kwargs["presence_penalty"]

        return payload

    def _parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """Parse OpenAI API response into LLMResponse.

        Args:
            response_data: Raw API response dictionary

        Returns:
            LLMResponse object

        Raises:
            RuntimeError: If response format is invalid
        """
        try:
            # Extract content from choices
            choices = response_data.get("choices", [])
            if not choices:
                raise RuntimeError("No choices in OpenAI response")

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("Empty content in OpenAI response")

            # Extract usage information
            usage_data = response_data.get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("prompt_tokens", 0),
                "completion_tokens": usage_data.get("completion_tokens", 0),
                "total_tokens": usage_data.get("total_tokens", 0),
            }

            # Get finish reason
            finish_reason = choices[0].get("finish_reason", "stop")

            return LLMResponse(
                content=content,
                model=response_data.get("model", self.model),
                usage=usage,
                finish_reason=finish_reason,
                raw_response=response_data,
            )

        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Failed to parse OpenAI response: {response_data}", exc_info=True)
            raise RuntimeError(f"Invalid OpenAI response format: {e}") from e
