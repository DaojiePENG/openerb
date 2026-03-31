"""
Base abstractions for LLM providers.

Defines the common interface that all LLM providers must implement,
enabling support for multiple LLM services (OpenAI, DashScope, local vLLM, etc.)
with a unified API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Message:
    """Unified message format for all LLM providers."""

    role: str  # "system", "user", "assistant"
    content: str
    image_url: Optional[str] = None  # Optional image URL for multi-modal
    image_base64: Optional[str] = None  # Optional base64-encoded image
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate message content and format."""
        if not self.role in ("system", "user", "assistant"):
            raise ValueError(f"Invalid role: {self.role}")
        if not self.content or not isinstance(self.content, str):
            raise ValueError("Message content must be a non-empty string")
        return True


@dataclass
class LLMResponse:
    """Unified response format from all LLM providers."""

    content: str  # Generated text
    model: str  # Model name used
    usage: Dict[str, int] = field(default_factory=dict)  # Token usage: {"prompt_tokens": X, "completion_tokens": Y}
    finish_reason: str = "stop"  # "stop", "length", "error", etc.
    raw_response: Optional[Dict[str, Any]] = None  # Raw API response for debugging
    timestamp: datetime = field(default_factory=datetime.now)


class LLMProvider(ABC):
    """Abstract base class for all LLM providers.
    
    All concrete implementations must inherit from this class and implement
    the abstract methods.
    """

    def __init__(self, api_key: str, model: str, api_base: Optional[str] = None, **kwargs):
        """Initialize the LLM provider.

        Args:
            api_key: API key for authentication (can be None for local services)
            model: Model name/identifier
            api_base: Custom API base URL (for self-hosted or local services)
            **kwargs: Provider-specific configuration options
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.config = kwargs

    @abstractmethod
    async def call(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Call the LLM API with the given messages.

        Args:
            messages: List of messages (conversation history)
            temperature: Sampling temperature (0-1, controls randomness)
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse: Unified response object

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If API call fails (after retries)
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that the provider is properly configured.

        Returns:
            True if valid, raises exception otherwise

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert Message objects to provider-specific format.

        This is a helper method that can be overridden by subclasses if needed.

        Args:
            messages: List of Message objects

        Returns:
            List of dicts in format {"role": str, "content": str}
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
