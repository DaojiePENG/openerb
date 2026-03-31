"""LLM configuration management."""

import os
import logging
from typing import Optional

from openerb.llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMConfig:
    """Configuration management for LLM clients.
    
    Loads LLM configuration from environment variables.
    Supports multiple providers with a single configuration set.
    
    Environment variables:
        LLM_PROVIDER: Type of provider (default: "dashscope")
            - "openai": OpenAI API
            - "dashscope": Alibaba DashScope
            - "custom": Custom OpenAI-compatible API
        LLM_API_KEY: API key for authentication
        LLM_MODEL: Model name/identifier
        LLM_API_BASE: Optional custom API base URL (for local/custom APIs)
    
    Example:
        >>> from openerb.llm.config import LLMConfig
        >>> client = LLMConfig.create_client()
        >>> response = await client.call(messages)
    """

    @staticmethod
    def load_from_env() -> dict:
        """Load LLM configuration from environment variables.

        Returns:
            Dictionary with keys: provider_type, api_key, model, api_base
        """
        config = {
            "provider_type": os.getenv("LLM_PROVIDER", "dashscope"),
            "api_key": os.getenv("LLM_API_KEY"),
            "model": os.getenv("LLM_MODEL"),
            "api_base": os.getenv("LLM_API_BASE"),
        }

        # Validation
        if not config["api_key"]:
            raise ValueError("LLM_API_KEY environment variable is not set")
        if not config["model"]:
            raise ValueError("LLM_MODEL environment variable is not set")

        logger.info(f"Loaded LLM config: provider={config['provider_type']}, model={config['model']}")
        return config

    @staticmethod
    def create_client(
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> LLMClient:
        """Create an LLM client with configuration.

        Priority order:
        1. Explicit parameters passed to this method
        2. Environment variables
        3. Defaults

        Args:
            provider_type: LLM provider type
            api_key: API key for authentication
            model: Model name/identifier
            api_base: Custom API base URL

        Returns:
            Configured LLMClient instance

        Raises:
            ValueError: If required configuration is missing
        """
        # Load from environment
        env_config = LLMConfig.load_from_env()

        # Use explicit parameters if provided, otherwise use environment
        final_config = {
            "provider_type": provider_type or env_config["provider_type"],
            "api_key": api_key or env_config["api_key"],
            "model": model or env_config["model"],
            "api_base": api_base or env_config["api_base"],
        }

        # Filter out None values
        final_config = {k: v for k, v in final_config.items() if v is not None}

        logger.info(f"Creating LLM client: {final_config['provider_type']}")
        return LLMClient(**final_config)
