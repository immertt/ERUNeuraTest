from abc import ABC, abstractmethod
from typing import List, Optional


# Exceptions

class LLMProviderError(Exception):
    """Tüm LLM provider'lar için temel hata sınıfı."""

    def __init__(self, message: str, provider: Optional[str] = None):
        self.provider = provider
        super().__init__(f"[{provider or 'Unknown'}] {message}")


class RateLimitError(LLMProviderError):
    """API rate limit aşıldığında fırlatılır."""
    pass


# Abstract Base Class

class BaseLLMProvider(ABC):
    """Tüm LLM provider'ların implement edeceği abstract base class."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """LLM'e prompt gönderir ve string cevap döner."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Provider'ın desteklediği model listesini döner."""
        pass