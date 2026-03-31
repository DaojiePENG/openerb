"""Unified LLM client with provider factory pattern."""

import logging
from typing import Type, Dict, Optional, List

from openerb.llm.base import LLMProvider, Message, LLMResponse

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client that abstracts away provider differences.
    
    Supports multiple LLM providers through a factory pattern:
    - openai: OpenAI API
    - dashscope: Alibaba DashScope (Qwen models)
    - bytedance: ByteDance API
    - google: Google Gemini API
    - vllm: Local vLLM service
    - custom: Custom OpenAI-compatible APIs
    
    Example:
        >>> from openerb.llm import LLMClient, Message
        >>> client = LLMClient(
        ...     provider_type="openai",
        ...     api_key="sk-xxx",
        ...     model="gpt-4"
        ... )
        >>> response = await client.call([
        ...     Message(role="user", content="Hello!")
        ... ])
        >>> print(response.content)
    """

    # Registry of available providers
    _providers: Dict[str, Type[LLMProvider]] = {}

    def __init__(
        self,
        provider_type: str,
        api_key: str,
        model: str,
        api_base: Optional[str] = None,
        **provider_kwargs,
    ):
        """Initialize the LLM client.

        Args:
            provider_type: Type of provider ("openai", "dashscope", "custom", etc.)
            api_key: API key for authentication
            model: Model name/identifier
            api_base: Optional custom API base URL
            **provider_kwargs: Provider-specific configuration options

        Raises:
            ValueError: If provider_type is not supported
        """
        provider_class = self._get_provider_class(provider_type)
        self.provider = provider_class(
            api_key=api_key,
            model=model,
            api_base=api_base,
            **provider_kwargs,
        )
        logger.info(f"Initialized LLM client with provider: {provider_type}, model: {model}")

    @staticmethod
    def _get_provider_class(provider_type: str) -> Type[LLMProvider]:
        """Get provider class by type name.

        Args:
            provider_type: Name of the provider

        Returns:
            Provider class

        Raises:
            ValueError: If provider type is not supported
        """
        # Lazy import to avoid circular dependencies
        providers = {
            "dashscope": "openerb.llm.providers.dashscope.DashscopeProvider",
            "openai": "openerb.llm.providers.openai_compat.OpenAIProvider",
            "custom": "openerb.llm.providers.openai_compat.OpenAIProvider",  # Custom uses OpenAI-compatible format
        }

        if provider_type not in providers:
            raise ValueError(
                f"Unsupported provider: {provider_type}. "
                f"Supported providers: {', '.join(providers.keys())}"
            )

        module_path = providers[provider_type]
        module_name, class_name = module_path.rsplit(".", 1)

        try:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load provider {provider_type}: {e}")

    async def call(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Call the LLM API.

        Args:
            messages: List of messages (conversation history)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse: Response from the LLM

        Raises:
            RuntimeError: If API call fails
        """
        logger.debug(f"Calling LLM with {len(messages)} messages")
        return await self.provider.call(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f"LLMClient({self.provider})"
