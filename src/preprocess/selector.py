"""
Karmaşıklığa göre en kritik metotları seçen modül.

Metotları (cyclomatic + cognitive) toplam skoruna göre büyükten küçüğe sıralar
ve en karmaşık N metodu seçer. Varsayılan limit: 50.
"""

from typing import List
from .models import MethodModel


class MethodSelector:
    """Complexity skoruna göre en önemli N metodu seçer."""

    def __init__(self, limit: int = 50):
        if limit is None:
            self.limit = None
            return
        if not isinstance(limit, int):
            raise ValueError("limit tamsayi olmali")
        self.limit = max(0, limit)

    def select_best_methods(self, methods: List[MethodModel]) -> List[MethodModel]:
        """
        Metotları karmaşıklık puanına göre sıralar ve ilk N tanesini seçer.
        Aynı skorlarda satır sayısı fazla olan önceliklidir.
        """
        if self.limit is None:
            raise ValueError("limit bos olamaz")
        if methods is None:
            return []
        ranked = self._rank_by_complexity(methods)
        return ranked[:self.limit]

    def _rank_by_complexity(self, methods: List[MethodModel]) -> List[MethodModel]:
        """
        Metotları toplam complexity skoruna göre büyükten küçüğe sıralar.
        İkincil kriter: satır sayısı (line_count).
        """
        if not methods:
            return []
        valid = []
        for method in methods:
            try:
                if method.complexity is None:
                    continue
                _ = method.complexity.cyclomatic_complexity
                _ = method.complexity.cognitive_complexity
                _ = method.line_count
                valid.append(method)
            except Exception:
                continue
        return sorted(
            valid,
            key=lambda m: (
                m.complexity.cyclomatic_complexity + m.complexity.cognitive_complexity,
                m.line_count,
            ),
            reverse=True,
        )