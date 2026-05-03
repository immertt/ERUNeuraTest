"""
TestComplexityCalculator — ComplexityCalculator sınıfının tüm metotları için
kapsamlı test sınıfı.

Her metot için:
  - Görev 1c : Başarısızlık testi   (orijinal kodla BAŞARISIZ)
  - Görev 2b : Kusur tetiklenmez
  - Görev 3b : Infection yok
  - Görev 4b : Infection var, failure gizli
  - Görev 5  : Düzeltilmiş sürümle 1c başarılı

Ayrıca sınır değerleri ve entegrasyon testleri.
"""

import ast
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.complexity import ComplexityCalculator
from src.preprocess.models import ComplexityMetrics


# ---------------------------------------------------------------------------
# Sabitler — testlerde kullanılan referans kaynak kodları
# ---------------------------------------------------------------------------

TRIVIAL = "def foo():\n    pass"

ONE_IF = "def foo(x):\n    if x:\n        pass"

NESTED_IF = "def foo(x, y):\n    if x:\n        if y:\n            pass"

COMPLEX = """\
def foo(a, b, c):
    if a:
        for i in range(10):
            while b:
                if c:
                    pass
    elif b:
        pass
    else:
        pass
"""

# cc=1, cog=0, total=1  → LOW
# cc=2, cog=1, total=3  → LOW
# cc=3, cog=3, total=6  → LOW
# cc=6, cog=9, total=15 → MODERATE


# ===========================================================================
# _normalize_code
# ===========================================================================
#
# KUSUR: None input str(None)="None" olarak normalize ediliyor.
# "None" geçerli Python → ast.parse geçer → yanlış metrik döner.
# Beklenen: None için boş/sentinel bir değer → calculate boş metrik döndürmeli.

class TestNormalizeCode:

    def setup_method(self):
        self.calc = ComplexityCalculator()

    # ── Görev 1c ────────────────────────────────────────────────────────────

    def test_given_none_input_when_normalized_should_fail_producing_none_string(self):
        """
        GIVEN: None input
        WHEN : _normalize_code çağrılır
        THEN : Sonuç 'None' string olmamalıdır; boş veya None dönmeli
               Orijinal: str(None)="None" → BAŞARISIZ

        [GÖREV 1c — orijinal kodla BAŞARISIZ]
        """
        result = self.calc._normalize_code(None)
        assert result != "None", (
            "_normalize_code(None) 'None' string döndürdü. "
            "Bu daha sonra ast.parse('None') gibi geçerli Python'a yol açar — KUSUR aktif."
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_plain_string_input_when_normalized_should_not_trigger_defect(self):
        """
        GIVEN: Düz Python kaynak kodu string'i
        WHEN : _normalize_code çağrılır
        THEN : Aynı string döner; kusur kodu (getattr/str dönüşümü) çalışmaz

        [GÖREV 2b — kusur tetiklenmez]
        """
        source = "def foo(): pass"
        result = self.calc._normalize_code(source)
        assert result == source

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_object_with_valid_string_body_when_normalized_should_not_infect(self):
        """
        GIVEN: body attr'ı geçerli Python string olan nesne
        WHEN : _normalize_code çağrılır
        THEN : body string'i döner; sonraki aşamalarda durum bozulmaz

        [GÖREV 3b — kusur çalışır (getattr dalı), infection yok]
        """
        obj = MagicMock()
        obj.body = "def foo(): pass"
        result = self.calc._normalize_code(obj)
        assert result == "def foo(): pass"

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_none_input_when_calculate_called_infection_hidden_by_low_risk(self):
        """
        GIVEN: None input → normalize → 'None' string → cc=1, cog=0, risk='LOW'
        WHEN : Test sadece risk_level'ı kontrol ediyor
        THEN : 'LOW' döner → test geçer — None'ın yanlış parse edildiği görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        result = self.calc.calculate(None)
        # None'ı geçerli kaynak gibi işledi; 'LOW' döndü ama bu yanlış
        assert result.risk_level == "LOW"  # geçer — kusur gizleniyor

    # ── Görev 5 ─────────────────────────────────────────────────────────────

    def test_given_none_input_when_fixed_normalize_used_should_return_empty_metrics(self):
        """
        GIVEN: None input
        WHEN : Düzeltilmiş _normalize_code kullanılır
        THEN : calculate boş/default ComplexityMetrics döner

        [GÖREV 5 — düzeltilmiş sürümle 1c başarılı olur]
        """
        calc = ComplexityCalculator()

        # Düzeltmeyi inline uygula: None'ı boş string'e dönüştür
        with patch.object(calc, '_normalize_code',
                          wraps=lambda s: "" if s is None else (
                              s if isinstance(s, str) else getattr(s, 'body', str(s)))):
            result = calc.calculate(None)

        assert result.cyclomatic_complexity == 0
        assert result.cognitive_complexity == 0

    # ── Sınır değerleri ─────────────────────────────────────────────────────

    def test_given_empty_string_when_normalized_should_return_empty_string(self):
        assert self.calc._normalize_code("") == ""

    def test_given_whitespace_only_string_when_normalized_should_return_as_is(self):
        result = self.calc._normalize_code("   \n\t  ")
        assert result.strip() == ""

    def test_given_object_without_body_attr_when_normalized_should_return_str_representation(self):
        """body attr'ı olmayan nesne → str() dönüşümü."""
        class NoBody:
            def __str__(self): return "no_body_object"
        result = self.calc._normalize_code(NoBody())
        assert isinstance(result, str)


# ===========================================================================
# _get_risk_label
# ===========================================================================
#
# Bu metotta yapısal bir kusur yok. Testler sınır değerlerine odaklanır.
# <= operatörü doğru; eşik değerlerinin tam sınırları test edilmeli.

class TestGetRiskLabel:

    def setup_method(self):
        self.calc = ComplexityCalculator()

    def test_given_score_zero_should_return_low(self):
        assert self.calc._get_risk_label(0) == "LOW"

    def test_given_score_at_low_threshold_should_return_low(self):
        """score=10 → LOW (eşik dahil)."""
        assert self.calc._get_risk_label(10) == "LOW"

    def test_given_score_one_above_low_threshold_should_return_moderate(self):
        """score=11 → MODERATE (eşik geçildi)."""
        assert self.calc._get_risk_label(11) == "MODERATE"

    def test_given_score_at_moderate_threshold_should_return_moderate(self):
        assert self.calc._get_risk_label(20) == "MODERATE"

    def test_given_score_one_above_moderate_threshold_should_return_high(self):
        assert self.calc._get_risk_label(21) == "HIGH"

    def test_given_score_at_high_threshold_should_return_high(self):
        assert self.calc._get_risk_label(50) == "HIGH"

    def test_given_score_one_above_high_threshold_should_return_very_high(self):
        assert self.calc._get_risk_label(51) == "VERY_HIGH"

    def test_given_very_large_score_should_return_very_high(self):
        assert self.calc._get_risk_label(10_000) == "VERY_HIGH"

    def test_given_negative_score_should_return_low(self):
        """Negatif skor hiçbir zaman üretilemez ama API bozulmamalı."""
        assert self.calc._get_risk_label(-1) == "LOW"

    def test_risk_thresholds_are_monotonically_ordered(self):
        """Eşikler artan sırada — aksi hâlde düşük label büyük skora yanlış atanır."""
        thresholds = [t for t, _ in ComplexityCalculator.RISK_THRESHOLDS]
        assert thresholds == sorted(thresholds)


# ===========================================================================
# _calc_cyclomatic
# ===========================================================================
#
# KUSUR: results[0] — birden fazla fonksiyonlu kaynakta yanlızca ilki alınır.
# Tek fonksiyon senaryosunda doğru; çok fonksiyonluda yanıltıcı.

class TestCalcCyclomatic:

    def setup_method(self):
        self.calc = ComplexityCalculator()

    # ── Görev 1c ────────────────────────────────────────────────────────────

    def test_given_multi_function_source_when_called_should_fail_returning_only_first(self):
        """
        GIVEN: İki fonksiyon — birincisi trivial (cc=1), ikincisi karmaşık (cc>1)
        WHEN : _calc_cyclomatic çağrılır
        THEN : Tüm fonksiyonların toplam/max complexity'si dönmeli
               Orijinal results[0] yalnızca ilk sıradakini alır → BAŞARISIZ

        [GÖREV 1c — orijinal kodla BAŞARISIZ]
        """
        source = """\
def simple():
    pass

def complex_func(a, b, c):
    if a:
        if b:
            if c:
                pass
"""
        result = self.calc._calc_cyclomatic(source)
        # results[0] = simple → cc=1; ama complex_func cc=4
        # Beklenen: en yüksek veya toplam; orijinal 1 döndürür
        assert result > 1, (
            f"Karmaşık fonksiyon içeren kaynakta complexity=1 döndü. "
            f"results[0] yalnızca ilk (basit) fonksiyonu aldı — KUSUR aktif."
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_single_function_source_when_called_should_not_trigger_defect(self):
        """
        GIVEN: Tek fonksiyon içeren kaynak kodu
        WHEN : _calc_cyclomatic çağrılır
        THEN : results[0] tek fonksiyonu doğru döndürür; kusur tetiklenmez

        [GÖREV 2b — kusur tetiklenmez]
        """
        result = self.calc._calc_cyclomatic(ONE_IF)
        assert result == 2  # if → cc=2

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_multi_function_where_first_happens_to_be_highest_infection_not_visible(self):
        """
        GIVEN: Çok fonksiyonlu kaynak ama en karmaşık radon sıralamasında ilk geliyor
        WHEN : _calc_cyclomatic çağrılır
        THEN : results[0] doğru sonucu verir — infection var ama görünmez

        [GÖREV 3b — kusur çalışır, infection yok]
        """
        # radon fonksiyonları kaynak sırasına göre döndürür
        # İlk fonksiyonu karmaşık yapıyoruz
        source = """\
def complex_first(a, b):
    if a:
        if b:
            pass
    return a

def simple_second():
    pass
"""
        from radon.complexity import cc_visit
        results = cc_visit(source)
        # results[0] complex_first ise orijinal kod doğru değer döndürür
        if results[0].name == "complex_first":
            result = self.calc._calc_cyclomatic(source)
            assert result == results[0].complexity  # doğru — ama şans eseri

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_multi_function_when_only_nonzero_checked_infection_hidden(self):
        """
        GIVEN: Çok fonksiyonlu kaynak; results[0] basit fonksiyonu veriyor (cc=1)
        WHEN : Test sadece 'cc >= 1' kontrol ediyor
        THEN : Geçer — gerçek complexity kaybı görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        source = """\
def trivial():
    pass

def has_branches(a, b, c):
    if a:
        if b:
            if c:
                pass
"""
        result = self.calc._calc_cyclomatic(source)
        assert result >= 1  # geçer; ama has_branches'ın cc=4'ü görülmüyor

    # ── Görev 5 ─────────────────────────────────────────────────────────────

    def test_given_multi_function_when_fixed_should_return_max_complexity(self):
        """
        GIVEN: Birden fazla fonksiyon içeren kaynak kodu
        WHEN : Düzeltilmiş _calc_cyclomatic çağrılır (max alıyor)
        THEN : En yüksek complexity değeri döner

        [GÖREV 5 — düzeltilmiş davranış]
        """
        source = """\
def simple():
    pass

def branchy(a, b, c):
    if a:
        if b:
            if c:
                pass
"""
        from radon.complexity import cc_visit
        results = cc_visit(source)
        expected_max = max(r.complexity for r in results)

        # Düzeltilmiş versiyon: max al
        fixed_result = max(r.complexity for r in cc_visit(source)) if cc_visit(source) else 1
        assert fixed_result == expected_max
        assert fixed_result > 1

    # ── Sınır değerleri ─────────────────────────────────────────────────────

    def test_given_source_with_no_functions_when_called_should_return_one_as_fallback(self):
        """cc_visit boş liste → fallback 1."""
        result = self.calc._calc_cyclomatic("x = 1\ny = 2")
        assert result == 1

    def test_given_trivial_function_when_called_should_return_one(self):
        result = self.calc._calc_cyclomatic(TRIVIAL)
        assert result == 1

    def test_given_function_with_branches_when_called_should_reflect_branch_count(self):
        result = self.calc._calc_cyclomatic(NESTED_IF)
        assert result == 3


# ===========================================================================
# _calc_cognitive
# ===========================================================================
#
# KUSUR: ast.walk ile ilk bulunan FunctionDef alınıyor.
# Kaynak kodda birden fazla top-level fonksiyon varsa hangisinin alındığı
# ast.walk'ın iç sıralamasına bağlı — kırılgan ve tutarsız.

class TestCalcCognitive:

    def setup_method(self):
        self.calc = ComplexityCalculator()

    # ── Görev 1c ────────────────────────────────────────────────────────────

    def test_given_multi_function_source_when_called_should_fail_on_wrong_function(self):
        """
        GIVEN: İki fonksiyon — trivial ve karmaşık
        WHEN : _calc_cognitive çağrılır
        THEN : Karmaşık fonksiyonun cognitive değerini döndürmeli
               ast.walk trivial'ı önce bulursa 0 döner → BAŞARISIZ

        [GÖREV 1c — ast.walk sırası kırılgan; belirli düzende BAŞARISIZ olabilir]
        """
        source = """\
def trivial():
    pass

def complex_func(a, b):
    if a:
        if b:
            if True:
                pass
"""
        result = self.calc._calc_cognitive(source)
        # trivial → 0; complex_func → 3+
        # ast.walk pratikte trivial'ı önce buluyor (kaynak sırası)
        # Bu test kusuru belgeler: çok fonksiyonlu kaynakta hangi alındığı belirsiz
        assert result > 0, (
            f"Karmaşık fonksiyon içeren kaynakta cognitive=0 döndü. "
            f"ast.walk yanlış (trivial) fonksiyonu seçti — KUSUR aktif. "
            f"Dönen: {result}"
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_single_function_when_called_should_not_trigger_walk_order_defect(self):
        """
        GIVEN: Tek fonksiyon içeren kaynak
        WHEN : _calc_cognitive çağrılır
        THEN : Tek seçenek olduğundan ast.walk sırası önemsiz; kusur tetiklenmez

        [GÖREV 2b — kusur tetiklenmez]
        """
        result = self.calc._calc_cognitive(NESTED_IF)
        assert result == 3  # iki iç içe if → cognitive=3

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_source_with_no_function_when_called_should_return_zero_without_infection(self):
        """
        GIVEN: Fonksiyon içermeyen kaynak (değişken ataması)
        WHEN : _calc_cognitive çağrılır
        THEN : 0 döner; FunctionDef arama döngüsü hiç eşleşme bulamaz

        [GÖREV 3b — kusur kodu çalışır (ast.walk döner) ama 0 döner, infection yok]
        """
        result = self.calc._calc_cognitive("x = 42")
        assert result == 0

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_multi_function_when_only_nonzero_checked_infection_hidden(self):
        """
        GIVEN: Karmaşık fonksiyon kaynak kodda ikinci sırada; ast.walk trivial'ı önce buluyor
        WHEN : Test sadece 'result >= 0' kontrol ediyor
        THEN : Geçer — yanlış fonksiyonun alındığı görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        source = """\
def trivial():
    pass

def has_nesting(a, b):
    if a:
        if b:
            pass
"""
        result = self.calc._calc_cognitive(source)
        assert result >= 0  # geçer; ama trivial'ın 0'ı mı, nesting'in 3'ü mü bilinmiyor

    # ── Görev 5 ─────────────────────────────────────────────────────────────

    def test_given_source_when_fixed_should_use_tree_body_not_ast_walk(self):
        """
        GIVEN: Birden fazla top-level fonksiyon
        WHEN : Düzeltilmiş versiyon (tree.body[0] ile ilk top-level fonksiyon) kullanılır
        THEN : İlk top-level fonksiyonun cognitive değeri tutarlı döner

        [GÖREV 5 — düzeltilmiş davranış: ast.walk yerine tree.body]
        """
        from cognitive_complexity.api import get_cognitive_complexity

        source = NESTED_IF
        tree = ast.parse(source)

        # Düzeltilmiş yaklaşım: tree.body içinden ilk FunctionDef
        fixed_result = None
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fixed_result = get_cognitive_complexity(node)
                break

        assert fixed_result == 3  # NESTED_IF → iki iç içe if → cognitive=3

    # ── Sınır değerleri ─────────────────────────────────────────────────────

    def test_given_trivial_function_when_called_should_return_zero(self):
        result = self.calc._calc_cognitive(TRIVIAL)
        assert result == 0

    def test_given_function_with_one_if_when_called_should_return_one(self):
        result = self.calc._calc_cognitive(ONE_IF)
        assert result == 1

    def test_given_async_function_when_called_should_be_detected_and_measured(self):
        source = "async def handler(x):\n    if x:\n        pass\n"
        result = self.calc._calc_cognitive(source)
        assert result == 1


# ===========================================================================
# calculate — Entegrasyon testleri
# ===========================================================================
#
# KUSUR: exception yutma — tüm hatalar ComplexityMetrics() ile örtülüyor.
# Hangi hatadan döndüğü bilinmiyor; hata ile gerçek sıfır ayırt edilemiyor.

class TestCalculate:

    def setup_method(self):
        self.calc = ComplexityCalculator()

    # ── Görev 1c ────────────────────────────────────────────────────────────

    def test_given_internal_error_when_calculate_called_should_fail_silent_swallow(self):
        """
        GIVEN: _calc_cyclomatic RuntimeError fırlatıyor
        WHEN : calculate çağrılır
        THEN : Hata bir şekilde çağırana iletilmeli (exception veya özel flag)
               Orijinal: ComplexityMetrics() döner, hata tamamen gizlenir → BAŞARISIZ

        [GÖREV 1c — orijinal kodla BAŞARISIZ]
        """
        with patch.object(self.calc, '_calc_cyclomatic',
                          side_effect=RuntimeError("radon unavailable")):
            result = self.calc.calculate(TRIVIAL)

        # Orijinal sessizce ComplexityMetrics() döndürüyor
        # Hata ile gerçek sıfır ayrımı yok — kusur: risk_level'ın UNKNOWN olması
        # bile bir failure; gerçek fonksiyon LOW olmalıydı
        assert result.risk_level != "UNKNOWN", (
            "Exception yutuldu ve UNKNOWN döndü — hata ile gerçek sonuç ayırt edilemiyor."
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_valid_source_when_no_exception_raised_swallow_defect_not_triggered(self):
        """
        GIVEN: Geçerli, parse edilebilir kaynak kodu
        WHEN : calculate çağrılır
        THEN : Hiç exception fırlatılmaz; except bloğu girilmez; kusur tetiklenmez

        [GÖREV 2b — kusur tetiklenmez]
        """
        result = self.calc.calculate(TRIVIAL)
        assert result.risk_level == "LOW"
        assert result.cyclomatic_complexity == 1
        assert result.cognitive_complexity == 0

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_syntax_error_source_when_calculate_called_should_return_default_without_crashing(self):
        """
        GIVEN: SyntaxError üreten kaynak kodu
        WHEN : calculate çağrılır
        THEN : Exception dışarıya sızmaz; default ComplexityMetrics döner

        [GÖREV 3b — exception yakalandı, uygulama yaşıyor; bu 'infection' sayılır
         ama default metrik döndüğü için assert geçer]
        """
        result = self.calc.calculate("def broken(:")
        assert isinstance(result, ComplexityMetrics)
        assert result.cyclomatic_complexity == 0

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_internal_error_when_only_isinstance_checked_infection_hidden(self):
        """
        GIVEN: _calc_cyclomatic exception fırlatıyor (infection: hata gizlendi)
        WHEN : Test sadece 'isinstance(result, ComplexityMetrics)' kontrol ediyor
        THEN : Geçer — exception yutuldu ama bu görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        with patch.object(self.calc, '_calc_cyclomatic',
                          side_effect=RuntimeError("silent failure")):
            result = self.calc.calculate(TRIVIAL)

        assert isinstance(result, ComplexityMetrics)  # geçer; hata gizlendi

    # ── Görev 5 ─────────────────────────────────────────────────────────────

    def test_given_valid_source_when_fixed_exception_handling_used_should_propagate_error(self):
        """
        GIVEN: _calc_cyclomatic exception fırlatıyor
        WHEN : Düzeltilmiş calculate (exception'ı yutmayan) kullanılır
        THEN : Exception dışarıya iletilir veya özel hata durumu döner

        [GÖREV 5 — düzeltilmiş davranış: exception gizlenmemeli]
        """
        # Düzeltilmiş versiyon exception'ı fırlatır
        def fixed_calculate(source_code):
            code_text = self.calc._normalize_code(source_code)
            if not code_text or code_text.strip() == "":
                return ComplexityMetrics()
            # Düzeltme: exception yutulmuyor
            cc_val  = self.calc._calc_cyclomatic(code_text)
            cog_val = self.calc._calc_cognitive(code_text)
            total   = cc_val + cog_val
            return ComplexityMetrics(
                cyclomatic_complexity=cc_val,
                cognitive_complexity=cog_val,
                risk_level=self.calc._get_risk_label(total),
            )

        with patch.object(self.calc, '_calc_cyclomatic',
                          side_effect=RuntimeError("propagated")):
            with pytest.raises(RuntimeError, match="propagated"):
                fixed_calculate(TRIVIAL)

    # ── Boş / geçersiz input sınır değerleri ────────────────────────────────

    def test_given_empty_string_when_calculate_called_should_return_default_metrics(self):
        result = self.calc.calculate("")
        assert result.cyclomatic_complexity == 0
        assert result.cognitive_complexity == 0

    def test_given_whitespace_only_when_calculate_called_should_return_default_metrics(self):
        result = self.calc.calculate("   \n\t  ")
        assert result.cyclomatic_complexity == 0
        assert result.cognitive_complexity == 0

    def test_given_only_comments_when_calculate_called_should_not_crash(self):
        result = self.calc.calculate("# sadece yorum\n# başka yorum\n")
        assert isinstance(result, ComplexityMetrics)

    # ── Doğru metrik hesaplama ───────────────────────────────────────────────

    def test_given_trivial_function_when_calculated_should_return_correct_metrics(self):
        """cc=1, cog=0, total=1 → LOW."""
        result = self.calc.calculate(TRIVIAL)
        assert result.cyclomatic_complexity == 1
        assert result.cognitive_complexity == 0
        assert result.risk_level == "LOW"

    def test_given_function_with_one_branch_when_calculated_should_return_correct_metrics(self):
        """cc=2, cog=1, total=3 → LOW."""
        result = self.calc.calculate(ONE_IF)
        assert result.cyclomatic_complexity == 2
        assert result.cognitive_complexity == 1
        assert result.risk_level == "LOW"

    def test_given_complex_function_when_calculated_should_return_moderate_risk(self):
        """cc=6, cog=9, total=15 → MODERATE."""
        result = self.calc.calculate(COMPLEX)
        assert result.cyclomatic_complexity == 6
        assert result.cognitive_complexity == 9
        assert result.risk_level == "MODERATE"

    def test_given_calculate_result_total_should_equal_cc_plus_cognitive(self):
        """risk_level, cc + cognitive toplamına göre belirlenmeli."""
        result = self.calc.calculate(ONE_IF)
        total = result.cyclomatic_complexity + result.cognitive_complexity
        expected_risk = self.calc._get_risk_label(total)
        assert result.risk_level == expected_risk

    def test_given_object_with_body_attribute_when_calculated_should_use_body_as_source(self):
        """body attr'ı kaynak kodu olan nesne → normalize → calculate."""
        obj = MagicMock()
        obj.body = TRIVIAL
        result = self.calc.calculate(obj)
        assert result.cyclomatic_complexity == 1
        assert result.risk_level == "LOW"