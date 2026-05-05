"""
Metot ve karmaşıklık verilerini tutan dataclass modelleri.

ComplexityMetrics: Cyclomatic/cognitive complexity ve risk seviyesi.
MethodModel: Bir metodun tüm yapısal bilgileri (imza, gövde, bağımlılıklar vb.)
             to_dict() ile JSON-uyumlu formata dönüştürülür.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Literal
from pathlib import Path


@dataclass
class ComplexityMetrics:
    """Bir metodun cyclomatic/cognitive complexity ve risk seviyesini tutar."""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    risk_levels: Literal["LOW", "MODERATE", "HIGH", "VERY_HIGH"] = "LOW"

    @property
    def risk_level(self) -> str:
        return self.risk_levels

    @risk_level.setter
    def risk_level(self, value: str) -> None:
        self.risk_levels = value

    def to_dict(self) -> Dict:
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "risk_levels": {"overall_risk": self.risk_levels},
        }


@dataclass
class MethodModel:
    """Bir Python metodunun tüm yapısal bilgilerini tutan veri modeli."""

    # Temel bilgiler
    name: str
    signature: str
    body: str

    # Konum bilgileri
    module_name: str
    file_path: str
    start_line: int
    end_line: int
    class_name: Optional[str] = None

    # Metot özellikleri
    is_async: bool = False
    is_method: bool = False
    return_type: Optional[str] = None

    # Yapısal bilgiler
    parameters: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)

    docstring: Optional[str] = None
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)

    @property
    def file_name(self) -> str:
        """Dosya yolundan sadece dosya adını döner."""
        return Path(self.file_path).name

    @property
    def fqn(self) -> Optional[str]:
        """Fully Qualified Name: module.ClassName veya None."""
        if self.class_name:
            return f"{self.module_name}.{self.class_name}.{self.name}"
        return None

    @property
    def line_count(self) -> int:
        """Metodun satır sayısını hesaplar."""
        if self.end_line < self.start_line:
            return 0
        return self.end_line - self.start_line + 1

    def to_dict(self) -> Dict:
        """JSON formatına uygun sözlük döner."""
        return {
            "project": {
                "name": self.module_name,
            },
            "file": {
                "name": self.file_name,
                "path": self.file_path,
            },
            "class": {
                "name": self.class_name,
                "fqn": self.fqn,
            },
            "method": {
                "name": self.name,
                "signature": self.signature,
                "body": self.body,
                "start_line": self.start_line,
                "end_line": self.end_line,
                "line_count": self.line_count,
                "is_async": self.is_async,
                "is_method": self.is_method,
                "return_type": self.return_type,
                "parameters": self.parameters,
                "dependencies": self.dependencies,
                "decorators": self.decorators,
                "docstring": self.docstring,
            },
            "complexity": self.complexity.to_dict(),
        }