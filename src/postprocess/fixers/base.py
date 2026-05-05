from abc import ABC, abstractmethod


class BaseFixer(ABC):
    """
    Her fixer LLM tarafından üretilen test kodunu alır,
    belirli kurallara göre düzeltir ve yeni kodu geri döndürür.

    Alt sınıflar fix() metodunu implement etmelidir.
    """

    #test_code: LLM tarafından üretilen veya hatalı olabilecek test kodu.
    @abstractmethod
    def fix(self, test_code: str) -> str:
        pass