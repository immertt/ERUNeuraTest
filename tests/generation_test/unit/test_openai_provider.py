from unittest.mock import MagicMock, patch
import pytest

from src.generation.providers.base import LLMProviderError, RateLimitError
from src.generation.providers.openai_provider import OpenAIProvider


@pytest.fixture
def provider():
    with patch("src.generation.providers.openai_provider.OpenAI"):
        p = OpenAIProvider(api_key="test-key", model="gpt-4o")
    return p


def _mock_response(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def test_invoke_returns_string(provider):
    provider.client.chat.completions.create.return_value = _mock_response("Merhaba!")
    result = provider.invoke("test")
    assert isinstance(result, str)
    assert result == "Merhaba!"


def test_invoke_invalid_api_key_raises_llm_error(provider):
    from openai import AuthenticationError as OpenAIAuthError
    provider.client.chat.completions.create.side_effect = OpenAIAuthError(
        message="Invalid API key",
        response=MagicMock(status_code=401),
        body={},
    )
    with pytest.raises(LLMProviderError, match="Geçersiz API key"):
        provider.invoke("test")


def test_invoke_rate_limit_retries_then_raises(provider):
    from openai import RateLimitError as OpenAIRateLimitError
    provider.client.chat.completions.create.side_effect = OpenAIRateLimitError(
        message="rate limit",
        response=MagicMock(status_code=429),
        body={},
    )
    with patch("time.sleep"):
        with pytest.raises(RateLimitError):
            provider.invoke("test")
    assert provider.client.chat.completions.create.call_count == OpenAIProvider.MAX_RETRIES


def test_get_available_models_returns_list(provider):
    models = provider.get_available_models()
    assert isinstance(models, list)
    assert "gpt-4o" in models
    assert "gpt-4-turbo" in models