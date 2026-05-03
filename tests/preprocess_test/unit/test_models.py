"""
TestModels — ComplexityMetrics ve MethodModel için test sınıfları.

══════════════════════════════════════════════════════════════════════════════
TEST STRATEJİSİ
══════════════════════════════════════════════════════════════════════════════

Dataclass modelleri test ederken iki farklı alan vardır:

  TEST EDİLMELİ — Logic içeren davranışlar:
    • to_dict()      : Dönüşüm mantığı, key yapısı, nested dict formatı
    • file_name      : Path parsing (cross-platform)
    • fqn            : Koşullu string birleştirme (class_name kontrolü)
    • line_count     : Aritmetik hesaplama (edge case: start > end)

  TEST EDİLMEMELİ — Python/framework garantileri:
    • Basit field get/set: m.name == "foo" → framework testi
    • field(default_factory=list) izolasyonu → Python garantisi
    • Tip anotasyonları → runtime'da enforced değil
    • Default boolean değerleri (is_async=False) → dataclass garantisi

══════════════════════════════════════════════════════════════════════════════
TESPİT EDİLEN KUSURLAR
══════════════════════════════════════════════════════════════════════════════

  KUSUR 1 — fqn method adını içermiyor
    "Fully Qualified Name" metodun adını içermeli: module.Class.method
    Gerçek: f"{module_name}.{class_name}" — method.name eksik

  KUSUR 2 — line_count start > end → negatif değer
    Validasyon yok; start=10, end=5 → line_count=-4

  KUSUR 3 — fqn: class_name="" ile class_name=None aynı sonuç
    "" falsy → None döner. Boş string ve None semantik olarak farklı.

  KUSUR 4 — ComplexityMetrics default cyclomatic=1, "henüz hesaplanmadı" için 0 beklenir
    ComplexityCalculator hata durumunda cc=0 döndürür → uyumsuz default.
"""

import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.models import ComplexityMetrics, MethodModel


# ---------------------------------------------------------------------------
# Fixture: minimal geçerli MethodModel
# ---------------------------------------------------------------------------

def make_method(**overrides) -> MethodModel:
    """Test için minimum geçerli MethodModel üretir."""
    defaults = dict(
        name="foo",
        signature="def foo()",
        body="pass",
        module_name="my_module",
        file_path="/project/my_module.py",
        start_line=1,
        end_line=5,
    )
    defaults.update(overrides)
    return MethodModel(**defaults)


# ===========================================================================
# ComplexityMetrics
# ===========================================================================

class TestComplexityMetricsToDict:
    """
    to_dict() dönüşüm mantığını test eder.
    Alan değerleri → dict yapısı → JSON formatı.
    """

    # ── KUSUR 4 — Görev 1c ──────────────────────────────────────────────────

    def test_given_default_metrics_when_to_dict_called_should_fail_on_cyclomatic_default(self):
        """
        GIVEN: Default ComplexityMetrics (hesaplanmamış durum)
        WHEN : to_dict çağrılır
        THEN : cyclomatic_complexity 0 olmalı ("henüz hesaplanmadı")
               Orijinal default=1 → BAŞARISIZ

        [KUSUR 4 — GÖREV 1c]
        """
        metrics = ComplexityMetrics()
        result = metrics.to_dict()

        assert result["cyclomatic_complexity"] == 0, (
            f"Default ComplexityMetrics cyclomatic=1 döndürdü. "
            f"'Henüz hesaplanmadı' durumu için 0 bekleniyor — KUSUR aktif."
        )

    # ── Görev 2b — Kusur tetiklenmez ────────────────────────────────────────

    def test_given_explicit_cyclomatic_value_when_to_dict_called_default_defect_not_triggered(self):
        """
        GIVEN: Açıkça belirtilmiş cyclomatic_complexity değeri
        WHEN : to_dict çağrılır
        THEN : Verilen değer doğru yansıtılır; default kusuru tetiklenmez

        [GÖREV 2b]
        """
        metrics = ComplexityMetrics(cyclomatic_complexity=3)
        result = metrics.to_dict()
        assert result["cyclomatic_complexity"] == 3

    # ── Görev 3b — Infection yok ────────────────────────────────────────────

    def test_given_cyclomatic_one_explicitly_when_to_dict_called_state_not_corrupted(self):
        """
        GIVEN: cyclomatic_complexity=1 açıkça verilmiş (default değil, bilinçli)
        WHEN : to_dict çağrılır
        THEN : 1 döner; default'tan gelip gelmediği bilinemez ama state bozulmaz

        [GÖREV 3b — infection yok: doğru değer üretildi]
        """
        metrics = ComplexityMetrics(cyclomatic_complexity=1, cognitive_complexity=0)
        result = metrics.to_dict()
        assert result["cyclomatic_complexity"] == 1
        assert result["cognitive_complexity"] == 0

    # ── Görev 4b — Infection gizli ──────────────────────────────────────────

    def test_given_default_metrics_when_only_risk_checked_default_defect_hidden(self):
        """
        GIVEN: Default ComplexityMetrics (cc=1 — yanlış default)
        WHEN : Test yalnızca risk_level kontrol ediyor
        THEN : 'LOW' döner, test geçer — cc=1'in yanlış olduğu görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        metrics = ComplexityMetrics()
        result = metrics.to_dict()
        assert result["risk_levels"]["overall_risk"] == "LOW"  # geçer; cc=1 gizlendi

    # ── to_dict yapısal testler ──────────────────────────────────────────────

    def test_given_metrics_when_to_dict_called_should_contain_all_required_keys(self):
        """to_dict çıktısı beklenen tüm top-level key'leri içermeli."""
        result = ComplexityMetrics(cyclomatic_complexity=2, cognitive_complexity=3).to_dict()
        assert "cyclomatic_complexity" in result
        assert "cognitive_complexity" in result
        assert "risk_levels" in result

    def test_given_metrics_when_to_dict_called_risk_levels_should_be_nested_dict(self):
        """risk_levels bir dict olmalı ve 'overall_risk' key'ini içermeli."""
        result = ComplexityMetrics(risk_levels="HIGH").to_dict()
        assert isinstance(result["risk_levels"], dict)
        assert "overall_risk" in result["risk_levels"]
        assert result["risk_levels"]["overall_risk"] == "HIGH"

    def test_given_metrics_values_when_to_dict_called_should_propagate_exactly(self):
        """Tüm değerler to_dict'e eksiksiz taşınmalı."""
        metrics = ComplexityMetrics(
            cyclomatic_complexity=5,
            cognitive_complexity=8,
            risk_levels="VERY_HIGH",
        )
        result = metrics.to_dict()
        assert result["cyclomatic_complexity"] == 5
        assert result["cognitive_complexity"] == 8
        assert result["risk_levels"]["overall_risk"] == "VERY_HIGH"

    def test_given_any_valid_metrics_to_dict_output_should_be_json_serializable(self):
        """to_dict çıktısı doğrudan json.dumps'a verilebilmeli."""
        metrics = ComplexityMetrics(cyclomatic_complexity=3, cognitive_complexity=2, risk_levels="MODERATE")
        try:
            json.dumps(metrics.to_dict())
        except (TypeError, ValueError) as e:
            pytest.fail(f"to_dict çıktısı JSON serialize edilemedi: {e}")

    def test_given_all_risk_levels_when_to_dict_called_should_preserve_each(self):
        """Dört risk seviyesinin her biri to_dict'te doğru yansıtılmalı."""
        for level in ("LOW", "MODERATE", "HIGH", "VERY_HIGH"):
            result = ComplexityMetrics(risk_levels=level).to_dict()
            assert result["risk_levels"]["overall_risk"] == level


# ===========================================================================
# MethodModel — file_name property
# ===========================================================================

class TestMethodModelFileName:
    """
    file_name: Path(file_path).name davranışını test eder.
    Logic: path ayırma — tek satır ama cross-platform edge case'leri var.
    """

    def test_given_unix_nested_path_when_file_name_accessed_should_return_only_filename(self):
        m = make_method(file_path="/project/src/my_module.py")
        assert m.file_name == "my_module.py"

    def test_given_filename_only_path_when_file_name_accessed_should_return_same(self):
        m = make_method(file_path="standalone.py")
        assert m.file_name == "standalone.py"

    def test_given_deeply_nested_path_when_file_name_accessed_should_return_leaf(self):
        m = make_method(file_path="/a/b/c/d/e/module.py")
        assert m.file_name == "module.py"

    def test_given_file_without_extension_when_file_name_accessed_should_return_bare_name(self):
        m = make_method(file_path="/project/Makefile")
        assert m.file_name == "Makefile"

    def test_given_file_with_multiple_dots_when_file_name_accessed_should_return_full_name(self):
        m = make_method(file_path="/project/my.module.test.py")
        assert m.file_name == "my.module.test.py"


# ===========================================================================
# MethodModel — fqn property
# ===========================================================================

class TestMethodModelFqn:
    """
    fqn: "module.ClassName" veya None.
    Kusurlar: method adı eksik, boş string edge case.
    """

    # ── KUSUR 1 — Görev 1c ──────────────────────────────────────────────────

    def test_given_class_method_when_fqn_accessed_should_fail_missing_method_name(self):
        """
        GIVEN: class_name ve method name olan bir metot
        WHEN : fqn property'e erişilir
        THEN : 'module.ClassName.method_name' formatında tam FQN dönmeli
               Orijinal: 'module.ClassName' — method adı eksik → BAŞARISIZ

        [KUSUR 1 — GÖREV 1c]
        """
        m = make_method(
            name="calculate",
            module_name="analytics",
            class_name="Calculator",
        )
        assert m.fqn == "analytics.Calculator.calculate", (
            f"fqn method adını içermiyor. "
            f"Beklenen: 'analytics.Calculator.calculate', Gerçek: {m.fqn!r} — KUSUR aktif."
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_no_class_name_when_fqn_accessed_should_not_trigger_fqn_defect(self):
        """
        GIVEN: class_name=None (top-level fonksiyon)
        WHEN : fqn property'e erişilir
        THEN : None döner; string birleştirme kodu hiç çalışmaz

        [GÖREV 2b — kusur tetiklenmez]
        """
        m = make_method(class_name=None)
        assert m.fqn is None

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_class_method_when_fqn_checked_only_for_module_prefix_infection_not_visible(self):
        """
        GIVEN: class_name olan metot (fqn üretilecek)
        WHEN : fqn yalnızca module adını içerip içermediği kontrol ediliyor
        THEN : Kontrol geçer — method adı eksik ama bu görünmez

        [GÖREV 3b — kusur çalışır, state bozulmaz, infection yok bu assertion için]
        """
        m = make_method(module_name="mymod", class_name="MyClass", name="my_method")
        assert m.fqn is not None
        assert "mymod" in m.fqn
        assert "MyClass" in m.fqn
        # "my_method" kontrolü yok → infection bu testte görünmez

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_class_method_when_only_not_none_checked_infection_hidden(self):
        """
        GIVEN: class_name olan metot — fqn method adı eksik (infection)
        WHEN : Test yalnızca 'fqn is not None' kontrol ediyor
        THEN : Geçer — method adı eksikliği görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        m = make_method(class_name="SomeClass", name="some_method")
        assert m.fqn is not None  # geçer; "some_method" eksik ama sorulmadı

    # ── KUSUR 3 — class_name="" edge case ───────────────────────────────────

    def test_given_empty_string_class_name_when_fqn_accessed_should_return_none(self):
        """
        GIVEN: class_name="" (boş string — None değil)
        WHEN : fqn property'e erişilir
        THEN : "" falsy olduğundan None döner — bu class_name=None ile aynı

        [KUSUR 3 — boş string ve None aynı davranışı üretiyor; belgeleme testi]
        """
        m = make_method(class_name="")
        # Mevcut davranış: "" falsy → None döner
        assert m.fqn is None
        # Ama bu beklenen mi? "" geçersiz class adı, None ile aynı olması mantıklı.
        # Tutarsızlık: class_name'in normalize edilmemiş olması.

    # ── Normal davranış ─────────────────────────────────────────────────────

    def test_given_class_name_when_fqn_accessed_should_contain_module_and_class(self):
        m = make_method(module_name="pkg.module", class_name="MyService")
        assert "pkg.module" in m.fqn
        assert "MyService" in m.fqn


# ===========================================================================
# MethodModel — line_count property
# ===========================================================================

class TestMethodModelLineCount:
    """
    line_count: end_line - start_line + 1.
    Kusur: start > end → negatif değer.
    """

    # ── KUSUR 2 — Görev 1c ──────────────────────────────────────────────────

    def test_given_start_greater_than_end_when_line_count_accessed_should_fail_on_negative(self):
        """
        GIVEN: start_line=10 > end_line=5 (hatalı/tutarsız veri)
        WHEN : line_count property'e erişilir
        THEN : Negatif değer yerine hata fırlatılmalı veya 0/1 dönmeli
               Orijinal: -4 döner — BAŞARISIZ

        [KUSUR 2 — GÖREV 1c]
        """
        m = make_method(start_line=10, end_line=5)
        assert m.line_count >= 0, (
            f"start=10 > end=5 için line_count={m.line_count} döndü. "
            f"Negatif satır sayısı anlamlı değil — KUSUR aktif."
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_valid_line_range_when_line_count_accessed_should_not_trigger_defect(self):
        """
        GIVEN: start_line < end_line (geçerli aralık)
        WHEN : line_count property'e erişilir
        THEN : Pozitif değer döner; kusur tetiklenmez

        [GÖREV 2b]
        """
        m = make_method(start_line=1, end_line=10)
        assert m.line_count == 10

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_start_equals_end_when_line_count_accessed_should_return_one(self):
        """
        GIVEN: start_line == end_line (tek satırlık metot)
        WHEN : line_count property'e erişilir
        THEN : 1 döner; hesaplama doğru, kusur tetiklenmez

        [GÖREV 3b — kusur kodu çalışıyor (aritmetik yapılıyor) ama doğru sonuç]
        """
        m = make_method(start_line=7, end_line=7)
        assert m.line_count == 1

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_invalid_range_when_only_type_checked_infection_hidden(self):
        """
        GIVEN: start=10 > end=5 → line_count=-4 (infection)
        WHEN : Test yalnızca isinstance(line_count, int) kontrol ediyor
        THEN : Geçer — negatif değer görünmez

        [GÖREV 4b — infection var, failure yok]
        """
        m = make_method(start_line=10, end_line=5)
        assert isinstance(m.line_count, int)  # geçer; -4 de int

    # ── Sınır değerleri ─────────────────────────────────────────────────────

    def test_given_adjacent_lines_when_line_count_accessed_should_return_two(self):
        m = make_method(start_line=3, end_line=4)
        assert m.line_count == 2

    def test_given_large_method_when_line_count_accessed_should_reflect_actual_size(self):
        m = make_method(start_line=1, end_line=100)
        assert m.line_count == 100


# ===========================================================================
# MethodModel — to_dict
# ===========================================================================

class TestMethodModelToDict:
    """
    to_dict(): Tüm alanların JSON-uyumlu dict formatına dönüşümünü test eder.
    Yapısal bütünlük, nested key'ler, property değerleri.
    """

    def test_given_method_model_when_to_dict_called_should_contain_all_top_level_sections(self):
        """to_dict çıktısı 4 ana bölümü içermeli: project, file, class, method, complexity."""
        result = make_method().to_dict()
        for section in ("project", "file", "class", "method", "complexity"):
            assert section in result, f"'{section}' bölümü eksik"

    def test_given_method_in_class_when_to_dict_called_class_section_should_have_name_and_fqn(self):
        """class_name varsa class bölümü hem name hem fqn içermeli."""
        m = make_method(class_name="MyClass", module_name="mymod")
        result = m.to_dict()
        assert result["class"]["name"] == "MyClass"
        assert result["class"]["fqn"] is not None
        assert "mymod" in result["class"]["fqn"]

    def test_given_top_level_function_when_to_dict_called_class_section_should_be_none(self):
        """class_name=None → class bölümündeki değerler None olmalı."""
        m = make_method(class_name=None)
        result = m.to_dict()
        assert result["class"]["name"] is None
        assert result["class"]["fqn"] is None

    def test_given_method_when_to_dict_called_file_section_should_use_file_name_property(self):
        """file.name, file_name property'inden gelmeli (path'in sadece dosya adı)."""
        m = make_method(file_path="/deep/nested/path/module.py")
        result = m.to_dict()
        assert result["file"]["name"] == "module.py"
        assert result["file"]["path"] == "/deep/nested/path/module.py"

    def test_given_method_when_to_dict_called_line_count_should_be_computed_correctly(self):
        """method.line_count, line_count property'inden hesaplanmalı."""
        m = make_method(start_line=5, end_line=15)
        result = m.to_dict()
        assert result["method"]["line_count"] == 11
        assert result["method"]["start_line"] == 5
        assert result["method"]["end_line"] == 15

    def test_given_method_with_parameters_when_to_dict_called_should_preserve_list(self):
        """parameters listesi to_dict'e eksiksiz taşınmalı."""
        m = make_method(parameters=["self", "x", "y"])
        result = m.to_dict()
        assert result["method"]["parameters"] == ["self", "x", "y"]

    def test_given_method_with_complexity_when_to_dict_called_complexity_should_be_nested(self):
        """complexity bölümü, ComplexityMetrics.to_dict() çıktısını içermeli."""
        m = make_method()
        m.complexity = ComplexityMetrics(cyclomatic_complexity=4, cognitive_complexity=3, risk_levels="MODERATE")
        result = m.to_dict()
        assert result["complexity"]["cyclomatic_complexity"] == 4
        assert result["complexity"]["cognitive_complexity"] == 3
        assert result["complexity"]["risk_levels"]["overall_risk"] == "MODERATE"

    def test_given_async_method_when_to_dict_called_is_async_should_be_true(self):
        m = make_method(is_async=True)
        assert m.to_dict()["method"]["is_async"] is True

    def test_given_any_valid_method_when_to_dict_called_output_should_be_json_serializable(self):
        """to_dict çıktısı doğrudan json.dumps'a verilebilmeli."""
        m = make_method(
            class_name="MyClass",
            parameters=["self", "x"],
            dependencies=["helper"],
            decorators=["property"],
            docstring="Bir docstring.",
            is_async=True,
            return_type="int",
        )
        try:
            serialized = json.dumps(m.to_dict())
            assert len(serialized) > 0
        except (TypeError, ValueError) as e:
            pytest.fail(f"to_dict çıktısı JSON serialize edilemedi: {e}")

    def test_given_method_with_none_optionals_when_to_dict_called_should_not_raise(self):
        """None olan optional alanlar to_dict'te hata üretmemeli."""
        m = make_method(
            class_name=None,
            return_type=None,
            docstring=None,
        )
        result = m.to_dict()
        assert result["method"]["return_type"] is None
        assert result["method"]["docstring"] is None

    def test_given_method_model_when_to_dict_called_method_section_should_have_all_keys(self):
        """method bölümü tüm beklenen key'leri içermeli."""
        result = make_method().to_dict()
        expected_keys = {
            "name", "signature", "body", "start_line", "end_line",
            "line_count", "is_async", "is_method", "return_type",
            "parameters", "dependencies", "decorators", "docstring",
        }
        missing = expected_keys - result["method"].keys()
        assert not missing, f"method bölümünde eksik key'ler: {missing}"