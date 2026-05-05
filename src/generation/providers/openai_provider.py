from openai import OpenAI, RateLimitError as OpenAIRateLimitError, AuthenticationError
import time
from typing import List

from src.generation.providers.base import BaseLLMProvider, LLMProviderError, RateLimitError


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API'yi kullanan LLM provider implementasyonu."""

    DEFAULT_MODELS = ["gpt-4o", "gpt-4-turbo"]
    MAX_RETRIES = 3
    BASE_DELAY = 1  # saniye

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def invoke(self, prompt: str) -> str:
        """
        Prompt'u OpenAI chat completions endpoint'ine gönderir.
        Rate limit durumunda exponential backoff uygular.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content

            except OpenAIRateLimitError as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise RateLimitError(
                        f"Rate limit aşıldı, {self.MAX_RETRIES} denemede çözülemedi.",
                        provider="OpenAI",
                    ) from e
                delay = self.BASE_DELAY * (2 ** attempt)
                time.sleep(delay)

            except AuthenticationError as e:
                raise LLMProviderError(
                    "Geçersiz API key. Lütfen anahtarınızı kontrol edin.",
                    provider="OpenAI",
                ) from e

            except Exception as e:
                raise LLMProviderError(str(e), provider="OpenAI") from e

    def get_available_models(self) -> List[str]:
        return self.DEFAULT_MODELS