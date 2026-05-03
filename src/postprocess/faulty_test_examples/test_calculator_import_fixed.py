"""
Burada bir LLM tarafından oluşturulan hatalı pytest örnekleri.

Bu dosya kasıtlı olarak hatalı testler içermektedir.
Amaç, işlem sonrası onarım mekanizmaları için örnekler sağlamaktır.
"""

import random
import pytest
from calculator import Calculator, User

@pytest.fixture
def calculator():
    return Calculator()


# ============================================================
# T001 - SyntaxError
# ============================================================

SYNTAX_ERROR_EXAMPLE = """
def test_add_syntax_error()
    assert calculator.add(2, 3) == 5
"""


# ============================================================
# T002 - IndentationError
# ============================================================

INDENTATION_ERROR_EXAMPLE = """
def test_add_indentation_error():
assert calculator.add(2, 3) == 5
"""


# ============================================================
# T003 - NameError / Missing Import
# ============================================================

def test_missing_import_or_name_error(calculator):
    assert calculator.power(2, 3) == 8


# ============================================================
# T004 - ModuleNotFoundError
# ============================================================

MODULE_NOT_FOUND_EXAMPLE = """
from calculator import Calculator, User

def test_add_module_error():
    calculator = Calculator()
    assert calculator.add(2, 3) == 5
"""


# ============================================================
# T005 - TypeError: Eksik Parametre
# ============================================================

def test_missing_argument(calculator):
    assert calculator.multiply(4) == 4


# ============================================================
# T006 - TypeError: Yanlış Parametre Tipi
# ============================================================

def test_wrong_argument_type(calculator):
    assert calculator.divide("10", 2) == 5


# ============================================================
# T007 - AssertionError
# ============================================================

def test_wrong_expected_value(calculator):
    assert calculator.add(2, 3) == 6


# ============================================================
# T008 - Zayıf / Anlamsız Doğrulama
# ============================================================

def test_weak_assertion(calculator):
    result = calculator.add(2, 3)
    assert result is not None


# ============================================================
# T009 - Kararsız Test
# ============================================================

def test_flaky_random():
    assert random.randint(1, 10) == 5
