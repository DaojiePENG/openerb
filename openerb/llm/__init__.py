"""OpenERB LLM Module - Unified interface for multiple LLM providers.

This module provides a unified abstraction layer for interacting with various LLM services,
including OpenAI, Alibaba DashScope, ByteDance, Google Gemini, and local vLLM instances.

Example:
    Using OpenAI:
        >>> from openerb.llm import LLMClient
        >>> client = LLMClient(
        ...     provider_type="openai",
        ...     api_key="sk-xxx",
        ...     model="gpt-4"
        ... )
        >>> response = await client.call([Message(role="user", content="Hello")])

    Using local vLLM:
        >>> client = LLMClient(
        ...     provider_type="custom",
        ...     api_key="not_needed",
        ...     model="llama-2-7b",
        ...     api_base="http://localhost:8000/v1"
        ... )
"""

from openerb.llm.base import Message, LLMResponse, LLMProvider

__all__ = [
    "Message",
    "LLMResponse",
    "LLMProvider",
]
