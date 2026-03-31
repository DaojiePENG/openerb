"""DashScope (Alibaba Qwen) LLM provider implementation."""

import asyncio
import base64
import json
import logging
from typing import List, Optional, Dict, Any

import httpx

from openerb.llm.base import LLMProvider, Message, LLMResponse

logger = logging.getLogger(__name__)


class DashscopeProvider(LLMProvider):
    """Provider for Alibaba DashScope API (Qwen models).
    
    Supports Qwen-VL-Plus for multi-modal understanding and other Qwen models.
    
    API Reference: https://help.aliyun.com/document_detail/2712693.html
    
    Example:
        >>> provider = DashscopeProvider(
        ...     api_key="sk-xxx",
        ...     model="qwen-vl-plus"
        ... )
        >>> response = await provider.call([
        ...     Message(role="user", content="What's in this image?", image_url="https://...")
        ... ])
    """

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
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
        """Initialize DashScope provider.

        Args:
            api_key: DashScope API key
            model: Model name (e.g., "qwen-vl-plus", "qwen-max")
            api_base: Optional custom API endpoint
            timeout: Request timeout in seconds
            **kwargs: Additional configuration options
        """
        super().__init__(api_key=api_key, model=model, api_base=api_base, **kwargs)
        self.timeout = timeout
        self.base_url = api_base or self.DEFAULT_BASE_URL
        self.validate_config()

    def validate_config(self) -> bool:
        """Validate DashScope configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key:
            raise ValueError("DashScope API key is required")
        if not self.model:
            raise ValueError("Model name is required")
        if len(self.api_key) < 10:
            raise ValueError("Invalid API key format")
        logger.info(f"DashScope config validated: model={self.model}")
        return True

    async def call(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Call DashScope API with retry logic.

        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters (top_p, etc.)

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
                logger.debug(f"DashScope API call attempt {attempt + 1}/{self.MAX_RETRIES}")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.base_url,
                        json=payload,
                        headers=self._get_headers(),
                    )

                    # Handle HTTP errors
                    if response.status_code != 200:
                        error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                        raise RuntimeError(
                            f"DashScope API error (HTTP {response.status_code}): "
                            f"{error_data.get('message', response.text)}"
                        )

                    # Parse response
                    return self._parse_response(response.json())

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"DashScope timeout on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.INITIAL_RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)

            except RuntimeError as e:
                last_error = e
                # Check if error is retryable (rate limit, temporary error)
                if "429" in str(e) or "503" in str(e) or "500" in str(e):
                    logger.warning(f"Retryable error on attempt {attempt + 1}: {e}")
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.INITIAL_RETRY_DELAY * (2 ** attempt)
                        await asyncio.sleep(delay)
                else:
                    raise

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
                raise RuntimeError(f"DashScope API call failed: {e}") from e

        # All retries exhausted
        raise RuntimeError(f"DashScope API call failed after {self.MAX_RETRIES} attempts: {last_error}")

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers for DashScope API.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "openerb/llm/dashscope",
        }

    def _prepare_payload(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs,
    ) -> Dict[str, Any]:
        """Prepare request payload for DashScope API.

        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Payload dictionary for API request
        """
        # Format messages for DashScope
        formatted_messages = []
        for msg in messages:
            message_obj: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }

            # Add image if present
            if msg.image_url or msg.image_base64:
                # For Qwen-VL models, images are included in content
                if msg.image_url:
                    message_obj["content"] = f"{msg.content}\n![image]({msg.image_url})"
                elif msg.image_base64:
                    # Embed base64 image
                    message_obj["content"] = (
                        f"{msg.content}\n![image](data:image/jpeg;base64,{msg.image_base64})"
                    )

            formatted_messages.append(message_obj)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }

        # Add optional parameters
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Support additional parameters like top_p
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]

        return payload

    def _parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """Parse DashScope API response into LLMResponse.

        Args:
            response_data: Raw API response dictionary

        Returns:
            LLMResponse object

        Raises:
            RuntimeError: If response format is invalid
        """
        try:
            # Extract content from nested structure
            output = response_data.get("output", {})
            choices = output.get("choices", [])

            if not choices:
                raise RuntimeError("No choices in DashScope response")

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("Empty content in DashScope response")

            # Extract usage information
            usage_data = response_data.get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("input_tokens", 0),
                "completion_tokens": usage_data.get("output_tokens", 0),
                "total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
            }

            # Determine finish reason
            finish_reason = choices[0].get("finish_reason", "stop")

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                raw_response=response_data,
            )

        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Failed to parse DashScope response: {response_data}", exc_info=True)
            raise RuntimeError(f"Invalid DashScope response format: {e}") from e
