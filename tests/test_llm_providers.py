"""Unit tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from openerb.llm.base import Message, LLMResponse
from openerb.llm.providers.dashscope import DashscopeProvider
from openerb.llm.providers.openai_compat import OpenAIProvider


class TestDashscopeProvider:
    """Test DashScope provider."""

    def test_init_valid(self):
        """Test provider initialization with valid config."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        assert provider.api_key == "sk-test-key"
        assert provider.model == "qwen-vl-plus"

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            DashscopeProvider(api_key="", model="qwen-vl-plus")

    def test_init_missing_model(self):
        """Test initialization fails without model."""
        with pytest.raises(ValueError, match="Model name is required"):
            DashscopeProvider(api_key="sk-test-key", model="")

    def test_validate_config(self):
        """Test config validation."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        assert provider.validate_config() is True

    def test_get_headers(self):
        """Test header generation."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        headers = provider._get_headers()
        assert headers["Authorization"] == "Bearer sk-test-key"
        assert headers["Content-Type"] == "application/json"

    def test_prepare_payload_text_only(self):
        """Test payload preparation with text-only message."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        messages = [Message(role="user", content="Hello")]
        payload = provider._prepare_payload(messages, temperature=0.7, max_tokens=100)

        assert payload["model"] == "qwen-vl-plus"
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 100
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["content"] == "Hello"

    def test_prepare_payload_with_image_url(self):
        """Test payload preparation with image URL."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        messages = [
            Message(
                role="user",
                content="What's in this image?",
                image_url="https://example.com/image.jpg",
            )
        ]
        payload = provider._prepare_payload(messages, temperature=0.7, max_tokens=None)

        assert len(payload["messages"]) == 1
        assert "https://example.com/image.jpg" in payload["messages"][0]["content"]

    def test_parse_response_valid(self):
        """Test response parsing with valid response."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        response_data = {
            "output": {
                "choices": [
                    {
                        "message": {"content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ]
            },
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
            },
        }
        result = provider._parse_response(response_data)

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"
        assert result.model == "qwen-vl-plus"
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 5

    def test_parse_response_empty_content(self):
        """Test response parsing fails with empty content."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        response_data = {
            "output": {"choices": [{"message": {"content": ""}}]},
            "usage": {},
        }
        with pytest.raises(RuntimeError, match="Empty content"):
            provider._parse_response(response_data)

    @pytest.mark.asyncio
    async def test_call_success(self):
        """Test successful API call."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        messages = [Message(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "choices": [
                    {
                        "message": {"content": "Hi there!"},
                        "finish_reason": "stop",
                    }
                ]
            },
            "usage": {"input_tokens": 5, "output_tokens": 3},
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.call(messages)

        assert result.content == "Hi there!"
        assert result.model == "qwen-vl-plus"

    @pytest.mark.asyncio
    async def test_call_api_error(self):
        """Test API error handling."""
        provider = DashscopeProvider(
            api_key="sk-test-key",
            model="qwen-vl-plus",
        )
        messages = [Message(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "message": "Unauthorized"
        }
        mock_response.headers = {"content-type": "application/json"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(RuntimeError, match="API error"):
                await provider.call(messages)


class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_init_valid(self):
        """Test provider initialization with valid config."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        assert provider.api_key == "sk-test-key"
        assert provider.model == "gpt-4"
        assert provider.base_url == "https://api.openai.com/v1"

    def test_init_custom_base_url(self):
        """Test initialization with custom base URL."""
        provider = OpenAIProvider(
            api_key="dummy",
            model="local-model",
            api_base="http://localhost:8000/v1",
        )
        assert provider.base_url == "http://localhost:8000/v1"

    def test_init_missing_model(self):
        """Test initialization fails without model."""
        with pytest.raises(ValueError, match="Model name is required"):
            OpenAIProvider(api_key="sk-test-key", model="")

    def test_get_headers(self):
        """Test header generation."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        headers = provider._get_headers()
        assert headers["Authorization"] == "Bearer sk-test-key"
        assert headers["Content-Type"] == "application/json"

    def test_prepare_payload_text_only(self):
        """Test payload preparation with text-only message."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        messages = [Message(role="user", content="Hello")]
        payload = provider._prepare_payload(messages, temperature=0.7, max_tokens=100)

        assert payload["model"] == "gpt-4"
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 100
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["content"] == "Hello"

    def test_prepare_payload_with_image_url(self):
        """Test payload preparation with image URL (vision format)."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4-vision",
        )
        messages = [
            Message(
                role="user",
                content="What's in this image?",
                image_url="https://example.com/image.jpg",
            )
        ]
        payload = provider._prepare_payload(messages, temperature=0.7, max_tokens=None)

        assert len(payload["messages"]) == 1
        # Check for OpenAI vision format
        content = payload["messages"][0]["content"]
        assert isinstance(content, list)
        assert any(item["type"] == "image_url" for item in content)

    def test_parse_response_valid(self):
        """Test response parsing with valid response."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        response_data = {
            "choices": [
                {
                    "message": {"content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }
        result = provider._parse_response(response_data)

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"
        assert result.model == "gpt-4"
        assert result.usage["prompt_tokens"] == 10

    def test_parse_response_empty_content(self):
        """Test response parsing fails with empty content."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        response_data = {
            "choices": [{"message": {"content": ""}}],
            "usage": {},
        }
        with pytest.raises(RuntimeError, match="Empty content"):
            provider._parse_response(response_data)

    @pytest.mark.asyncio
    async def test_call_success(self):
        """Test successful API call."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        messages = [Message(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Hi there!"},
                    "finish_reason": "stop",
                }
            ],
            "model": "gpt-4",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await provider.call(messages)

        assert result.content == "Hi there!"
        assert result.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_call_api_error(self):
        """Test API error handling."""
        provider = OpenAIProvider(
            api_key="sk-test-key",
            model="gpt-4",
        )
        messages = [Message(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {"message": "Unauthorized"}
        }
        mock_response.headers = {"content-type": "application/json"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(RuntimeError, match="API error"):
                await provider.call(messages)
