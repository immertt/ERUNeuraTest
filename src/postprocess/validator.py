import ast
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


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

@dataclass
class TestResult:
    """
    Pytest çalıştırma sonucunu temsil eder.

    Attributes:
        passed: Testlerin başarılı olup olmadığını belirtir.
        failed: Testlerin başarısız olup olmadığını belirtir.
        errors: Çalıştırma sırasında oluşan hata mesajları.
        output: Pytest çıktısı.
    """
    passed: bool
    failed: bool
    errors: list[str] = field(default_factory=list)
    output: str = ""


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
    
    def run_test(self, code: str, context_path: str, timeout: int = 10) -> TestResult:
        """
        Verilen test kodunu geçici bir dosyaya yazar ve pytest ile çalıştırır.

        Args:
            code: Çalıştırılacak test kodu.
            context_path: Testin çalışacağı dizin.
            timeout: Pytest çalıştırması için saniye cinsinden zaman sınırı.

        Returns:
            Pytest çalışma sonucunu içeren TestResult nesnesi.
        """
        context_dir = Path(context_path)

        if context_dir.is_file():
            context_dir = context_dir.parent

        temp_file_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix="_generated_test.py",
                prefix="test_",
                dir=context_dir,
                delete=False,
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = Path(temp_file.name)

            completed_process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(temp_file_path),
                    "-q",
                ],
                cwd=str(context_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = completed_process.stdout + completed_process.stderr

            if completed_process.returncode == 0:
                return TestResult(
                    passed=True,
                    failed=False,
                    output=output,
                )

            return TestResult(
                passed=False,
                failed=True,
                errors=[output],
                output=output,
            )

        except subprocess.TimeoutExpired as error:
            output = ""

            if error.stdout:
                output += error.stdout

            if error.stderr:
                output += error.stderr

            return TestResult(
                passed=False,
                failed=True,
                errors=[f"Pytest timeout after {timeout} seconds."],
                output=output,
            )

        finally:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()