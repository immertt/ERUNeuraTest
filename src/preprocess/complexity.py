"""
Cyclomatic ve Cognitive complexity hesaplama modülü.

radon ile cyclomatic, cognitive_complexity kütüphanesi ile cognitive
complexity hesaplar. Toplam skora göre risk seviyesi belirler
(LOW / MODERATE / HIGH / VERY_HIGH).
"""

import ast
from radon.complexity import cc_visit
from cognitive_complexity.api import get_cognitive_complexity
from .models import ComplexityMetrics


class ComplexityCalculator:
    """Metotların karmaşıklık değerlerini hesaplayan sınıf."""

    # Risk eşikleri (toplam skor)
    RISK_THRESHOLDS = [
        (10, "LOW"),# toplam <= 10
        (20, "MODERATE"),# toplam <= 20
        (50, "HIGH"),# toplam <= 50
    ]
    DEFAULT_RISK = "VERY_HIGH"# toplam > 50

    def calculate(self, source_code) -> ComplexityMetrics:
        """Kaynak kod için ComplexityMetrics döner."""
        code_text = self._normalize_code(source_code)

        if not code_text or code_text.strip() == "":
            return ComplexityMetrics()

        try:
            cc_val = self._calc_cyclomatic(code_text)
            cog_val = self._calc_cognitive(code_text)
            total = cc_val + cog_val

            return ComplexityMetrics(
                cyclomatic_complexity=cc_val,
                cognitive_complexity=cog_val,
                risk_levels=self._get_risk_label(total),
            )
        except Exception:
            return ComplexityMetrics()

    def _calc_cyclomatic(self, code_text: str) -> int:
        """radon ile cyclomatic complexity hesaplar."""
        results = cc_visit(code_text)
        if not results:
            return 1
        return max(r.complexity for r in results)

    def _calc_cognitive(self, code_text: str) -> int:
        """cognitive_complexity kütüphanesi ile cognitive complexity hesaplar."""
        tree = ast.parse(code_text)
        values = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                values.append(get_cognitive_complexity(node))
        return max(values) if values else 0

    def _normalize_code(self, source_code) -> str:
        """String veya nesne girdisini string'e normalize eder."""
        if source_code is None:
            return ""
        if isinstance(source_code, str):
            return source_code
        if hasattr(source_code, "body"):
            body = getattr(source_code, "body")
            return "" if body is None else body
        return str(source_code)

    def _get_risk_label(self, score: int) -> str:
        """Toplam skora göre risk seviyesi döner."""
        for threshold, label in self.RISK_THRESHOLDS:
            if score <= threshold:
                return label
        return self.DEFAULT_RISK