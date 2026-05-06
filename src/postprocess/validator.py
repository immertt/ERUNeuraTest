from dataclasses import dataclass, field
import ast


@dataclass
class ValidationResult:
    """
    Kod validasyon sonucunu temsil eder.

    Attributes:
        is_valid: Kodun geçerli olup olmadığını belirtir.
        errors: Tespit edilen hata mesajları.
        warnings: Kritik olmayan uyarılar.
    """
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

class CodeValidator:
    """
    LLM tarafından üretilen test kodunun geçerliliğini kontrol eder.

    Validator kodu düzeltmez; yalnızca syntax, import ve temel
    kural tabanlı problemleri raporlar.
    """

    def validate_syntax(self, code: str) -> ValidationResult:
        try:
            ast.parse(code)
            return ValidationResult(is_valid=True)

        except SyntaxError as error:
            message = f"SyntaxError at line {error.lineno}: {error.msg}"
            return ValidationResult(
                is_valid=False,
                errors=[message]
            )

    def validate_imports(self, code: str) -> ValidationResult:
        warnings = []

        if "pytest." in code and "import pytest" not in code:
            warnings.append("pytest kullanılıyor ancak import pytest bulunamadı.")

        return ValidationResult(
            is_valid=True,
            warnings=warnings
        )

    def validate_indentation(self, code: str) -> ValidationResult:
        try:
            compile(code, "<test_code>", "exec")
            return ValidationResult(is_valid=True)

        except IndentationError as error:
            message = f"IndentationError at line {error.lineno}: {error.msg}"
            return ValidationResult(
                is_valid=False,
                errors=[message]
            )

        except SyntaxError:
            return ValidationResult(is_valid=True)

    def validate_rule_based(self, code: str) -> ValidationResult:
        warnings = []

        if "def test_" not in code:
            warnings.append("Test fonksiyonu bulunamadı.")

        if "assert " not in code:
            warnings.append("Assertion ifadesi bulunamadı.")

        return ValidationResult(
            is_valid=True,
            warnings=warnings
        )

    def validate(self, code: str) -> ValidationResult:
        """
        Tüm validasyon kontrollerini çalıştırır ve birleşik sonucu döndürür.
        """

        results = []

        indentation_result = self.validate_indentation(code)
        results.append(indentation_result)

        if indentation_result.is_valid:
            results.append(self.validate_syntax(code))

        results.append(self.validate_imports(code))
        results.append(self.validate_rule_based(code))

        errors = []
        warnings = []

        for result in results:
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )