"""DashScope (Alibaba Qwen) LLM provider implementation using official SDK."""

import asyncio
import logging
from typing import List, Optional, Dict, Any

import dashscope
from dashscope import MultiModalConversation

from openerb.llm.base import LLMProvider, Message, LLMResponse

logger = logging.getLogger(__name__)


class DashscopeProvider(LLMProvider):
    """Provider for Alibaba DashScope API (Qwen models) using official SDK.
    
    Supports both text and multi-modal models (Qwen-VL-Plus, etc.).
    Uses the official dashscope Python SDK for API calls.
    
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

    # Models that support multi-modal input
    MULTIMODAL_MODELS = {"qwen-vl-plus", "qwen-vl-max", "qwen-vl", "qwen-vl-32b"}
    
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        api_key: str,
        model: str,
        api_base: Optional[str] = None,  # Not used with official SDK, kept for compatibility
        timeout: float = 60.0,
        **kwargs,
    ):
        """Initialize DashScope provider.

        Args:
            api_key: DashScope API key
            model: Model name (e.g., "qwen-vl-plus", "qwen-max")
            api_base: Not used (for compatibility with other providers)
            timeout: Request timeout in seconds (not directly used with SDK)
            **kwargs: Additional configuration options
        """
        super().__init__(api_key=api_key, model=model, api_base=api_base, **kwargs)
        self.timeout = timeout
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
        """Call DashScope API using official SDK with retry logic.

        Args:
            messages: List of messages
            temperature: Sampling temperature (0-2, controls randomness)
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

        # Convert messages to DashScope format
        dashscope_messages = self._convert_to_dashscope_format(messages)

        # Execute with retry logic
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"DashScope API call attempt {attempt + 1}/{self.MAX_RETRIES}")
                
                # Call DashScope API using official SDK
                response = MultiModalConversation.call(
                    api_key=self.api_key,
                    model=self.model,
                    messages=dashscope_messages,
                    temperature=temperature,
                    max_tokens=max_tokens or 1024,
                    top_p=kwargs.get("top_p", 0.7),
                )

                # Check response status
                if response.status_code != 200:
                    error_msg = response.get("message", str(response))
                    raise RuntimeError(
                        f"DashScope API error (HTTP {response.status_code}): {error_msg}"
                    )

                # Parse response
                return self._parse_response(response)

            except RuntimeError as e:
                last_error = e
                # Check if error is retryable
                error_str = str(e).lower()
                if any(code in error_str for code in ["429", "503", "500", "timeout", "temporarily unavailable"]):
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

    def _convert_to_dashscope_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to DashScope API format.

        DashScope uses a content array where each element is either:
        - {"text": "text content"}
        - {"image": "image_url or base64_data"}

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in DashScope format
        """
        dashscope_messages = []
        
        for msg in messages:
            content = []
            
            # Add text content first
            if msg.content:
                content.append({"text": msg.content})
            
            # Add image if present
            if msg.image_url:
                content.append({"image": msg.image_url})
            elif msg.image_base64:
                # For base64, embed as data URL
                content.append({
                    "image": f"data:image/jpeg;base64,{msg.image_base64}"
                })
            
            # Ensure content is not empty
            if not content:
                content = [{"text": ""}]
            
            dashscope_messages.append({
                "role": msg.role,
                "content": content
            })
        
        return dashscope_messages

    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """Parse DashScope API response into LLMResponse.

        Args:
            response: API response from official SDK

        Returns:
            LLMResponse object

        Raises:
            RuntimeError: If response format is invalid
        """
        try:
            # DashScope SDK can return response in different formats
            output = response.get("output", {})
            content = ""
            
            # Try format 1: output.text (newer format)
            if output.get("text"):
                content = output.get("text", "")
            
            # Try format 2: output.choices[0].message.content (array format)
            if not content and output.get("choices"):
                choices = output.get("choices", [])
                if choices and choices[0].get("message"):
                    message = choices[0].get("message", {})
                    message_content = message.get("content", [])
                    if isinstance(message_content, list) and message_content:
                        # Extract text from content array
                        for item in message_content:
                            if isinstance(item, dict) and item.get("text"):
                                content = item.get("text", "")
                                break
                    elif isinstance(message_content, str):
                        content = message_content
            
            if not content:
                logger.warning(f"Empty content in DashScope response. Full response: {response}")
                raise RuntimeError("Empty content in DashScope response")

            # Extract usage information
            usage_data = response.get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("input_tokens", 0),
                "completion_tokens": usage_data.get("output_tokens", 0),
                "total_tokens": usage_data.get("total_tokens", usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)),
            }

            # Determine finish reason
            finish_reason = output.get("finish_reason", "stop")
            if output.get("choices") and output["choices"]:
                finish_reason = output["choices"][0].get("finish_reason", finish_reason)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                raw_response=response,
            )

        except (KeyError, TypeError, AttributeError) as e:
            logger.error(f"Failed to parse DashScope response: {response}", exc_info=True)
            raise RuntimeError(f"Invalid DashScope response format: {e}") from e
