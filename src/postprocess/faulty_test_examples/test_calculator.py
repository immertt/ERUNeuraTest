"""
Burada bir LLM tarafından oluşturulan hatalı pytest örnekleri.

Bu dosya kasıtlı olarak hatalı testler içermektedir.
Amaç, işlem sonrası onarım mekanizmaları için örnekler sağlamaktır.

SyntaxError ve IndentationError gibi bazı hatalar, pytest derlemesini engelledikleri için 
çalıştırılabilir bir Python test dosyası içinde aktif kalamazlar.

Bu nedenle, dize parçacıkları olarak saklanırlar.
"""

import random
import pytest
from calculator import add, divide, multiply, is_even, get_user_name

# ============================================================
# T001 - SyntaxError
# Repair Type: Rule-based (Kural Tabanlı)
# ============================================================

SYNTAX_ERROR_EXAMPLE = """
def test_add_syntax_error()
    assert add(2, 3) == 5
"""

# ============================================================
# T002 - IndentationError (Girinti Hatası)
# Repair Type: Rule-based (kural Tabanlı)
# ============================================================

INDENTATION_ERROR_EXAMPLE = """
def test_add_indentation_error():
assert add(2, 3) == 5
"""

# ============================================================
# T003 - NameError / Missing Import (Eksik import)
# Repair Type: Rule-based or LLM-based
# ============================================================

def test_missing_import_or_name_error():
    assert power(2, 3) == 8

# ============================================================
# T004 - ModuleNotFoundError
# Onarım Türü: Kural tabanlı
# ============================================================

MODULE_NOT_FOUND_EXAMPLE = """
from wrong_calculator import add

def test_add_module_error():
    assert add(2, 3) == 5
"""

# ============================================================
# T005 - TypeError: Eksik Parametre
# Onarım Türü: Kural tabanlı / LLM tabanlı
# ============================================================

def test_missing_argument():
    assert multiply(4) == 4


# ============================================================
# T006 - TypeError: Yanlış Parametre Tipi
# Onarım Türü: LLM tabanlı
# ============================================================

def test_wrong_argument_type():
    assert divide("10", 2) == 5


# ============================================================
# T007 - AssertionError (Yanlış Beklenen Değer)
# Onarım Türü: LLM tabanlı / Güvenli durumlarda kural tabanlı
# ============================================================

def test_wrong_expected_value():
    assert add(2, 3) == 6


# ============================================================
# T008 - Zayıf / Anlamsız Doğrulama (Weak Assertion)
# Onarım Türü: LLM tabanlı
# ============================================================

def test_weak_assertion():
    result = add(2, 3)
    assert result is not None


# ============================================================
# T009 - Kararsız Test (Flaky Test)
# Onarım Türü: LLM tabanlı
# ============================================================

def test_flaky_random():
    assert random.randint(1, 10) == 5

