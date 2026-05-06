from src.postprocess.validator import CodeValidator

class TestCodeValidator:
    #hata var, hata dedi-> TruePositive
    def test_validate_syntax_returns_invalid_for_broken_code(self):
        validator = CodeValidator()
        code = "def test_example(\n    assert True" #Validator'un hata yakalamasını ölçmek için örnek bir kod yerleştiriyoruz.

        result = validator.validate_syntax(code)

        assert result.is_valid is False #syntax bozuksa isFalse olmalı
        assert len(result.errors)>0 #Yanlışsa en az 1 tane hata mesajı da üretmeli
        assert "SyntaxError at line" in result.errors[0] #satır numarasıyla hatayı raporla

    #hata yok hata yok dedi -> TrueNegative
    def test_validate_syntax_returns_valid_for_correct_code(self):
        validator = CodeValidator()
        code = """
def test_example():
    assert 1 == 1
"""
        result = validator.validate_syntax(code)

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    #kodda pytest kullanılıyor ama improt pytest yoksa hata üretiyor mu ? (eksik import tespiti)
    def test_validate_imports_warns_for_missing_pytest_import(self):
        validator = CodeValidator()
        code = """
def test_example():
    with pytest.raises(ValueError):
        int("x")
"""
        result = validator.validate_imports(code)

        assert result.is_valid is True
        assert any("pytest" in warning for warning in result.warnings) #listede pytest var mı ?

    #pytest import edilmiş, dolayısıyla warning üretmemeli.
    def test_validate_imports_does_not_warn_when_pytest_is_imported(self):
        validator = CodeValidator()
        code = """
import pytest

def test_example():
    with pytest.raises(ValueError):
        int("x")
"""

        result = validator.validate_imports(code)

        assert result.is_valid is True
        assert result.warnings == []

    #test_ ile başlayan fonksiyon yoksa bunu fark ediyor mu ?
    def test_validate_rule_based_warns_when_no_test_function_exists(self):
        validator = CodeValidator()
        code = """  
def example():      #fonksiyon var ama test_ ile başlamıyor
    assert 1 == 1
"""
        result = validator.validate_rule_based(code)

        assert result.is_valid is True #Hata yok warning var
        assert any("Test fonksiyonu bulunamadı." in warning for warning in result.warnings)

    #test_ ile başlayan fonk. var ama test mantıgı var mı ?
    def test_validate_rule_based_warns_when_no_assertion_exists(self):
        validator = CodeValidator()
        code = """
def test_example(): #test_ ile başlıyor ama içinde as.. yok, p...rai.. yok
    x = 1 + 1
"""
        result = validator.validate_rule_based(code)
        
        assert result.is_valid is True
        assert any("Assertion ifadesi bulunamadı." in warning for warning in result.warnings)

    #ana validate() fonk. akışı dogru mu ? syntax check, merge, erken return
    def test_validate_returns_combined_result_for_invalid_syntax(self):
        validator = CodeValidator()
        code = "def test_example(\n    assert True"

        result = validator.validate(code)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "SyntaxError at line" in result.errors[0]

    def test_run_test_returns_passed_for_valid_test_code(self, tmp_path):
        validator = CodeValidator()
        code = """
def test_example():
    assert 1 + 1 == 2
"""
        result = validator.run_test(code, str(tmp_path))

        assert result.passed is True
        assert result.failed is False
        assert result.errors == []
        assert "passed" in result.output

    def test_run_test_returns_failed_for_failing_test_code(self, tmp_path):
        validator = CodeValidator()
        code = """
def test_example():
    assert 1 + 1 == 3
"""
        result = validator.run_test(code, str(tmp_path))

        assert result.passed is False
        assert result.failed is True
        assert len(result.errors) > 0
        assert "failed" in result.output


    def test_run_test_returns_failed_when_timeout_expires(self, tmp_path):
        validator = CodeValidator()
        code = """
def test_timeout():
    while True:
        pass
"""
        result = validator.run_test(code, str(tmp_path), timeout=1)

        assert result.passed is False
        assert result.failed is True
        assert any("timeout" in error.lower() for error in result.errors)

    def test_run_test_removes_temporary_test_file(self, tmp_path):
        validator = CodeValidator()
        code = """
def test_example():
    assert True
"""
        validator.run_test(code, str(tmp_path))

        generated_files = list(tmp_path.glob("test_*_generated_test.py"))

        assert generated_files == []