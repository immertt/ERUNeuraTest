"""
TestGetMethodsInfo — ASTAnalyzer.get_methods_info için kapsamlı test sınıfı.

Kapsam:
  - Defect / Infection / Failure analizi (1-5 arası görevler)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""
import os
import sys
import ast
import pytest
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings
from src.preprocess.analyzer import ASTAnalyzer

# ---------------------------------------------------------------------------
# Yardımcı: kaynak kodundan analyzer oluştur
# ---------------------------------------------------------------------------


def make_analyzer(
    source: str, module_name: str = "test_module", file_path: str = "test.py"
) -> ASTAnalyzer:
    return ASTAnalyzer(source_code=source, module_name=module_name, file_path=file_path)


#
# Hata Tanımı:
#     get_methods_info içindeki ClassDef dalı sadece node.body'yi tek seviye
#     iter eder.  Eğer bir ClassDef.body içinde başka bir ClassDef varsa
#     (nested class), o iç class'ın metotları hiç işlenmez.
#
# Tetikleyici Koşul:
#     Kaynak kodda en az bir ClassDef içinde başka bir ClassDef ve o iç
#     class'ta en az bir metot bulunması gerekir.
#
# ---------------------------------------------------------------------------


class TestGetMethodsInfo:

    def test_given_nested_class_when_analyzed_should_detect_inner_class_methods(self):
        """
        GIVEN: Bir dış sınıf içinde iç sınıf (nested class) ve metotları olan kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : İç sınıfın metotları da sonuç listesinde yer almalıdır

        [Beklenen Hata: Orijinal kod kusuru]
        """
        source = """
class Outer:
    def outer_method(self):
        pass

    class Inner:
        def inner_method(self):
            pass
"""
        analyzer = make_analyzer(source)
        result = analyzer.get_methods_info()
        method_names = [m.name for m in result]

        # Orijinal kod inner_method'u GÖRMEZ → test başarısız olur
        assert (
            "inner_method" in method_names
        ), "Nested class içindeki 'inner_method' tespit edilemedi (Bilinen Hata)"

    # -----------------------------------------------------------------------
    # Kusurun çalıştırılmadığı (reachability) senaryo
    # -----------------------------------------------------------------------
    #
    # (a) Kusuru çalıştırmamak mümkün mü?
    #     Evet. Kaynak kodda hiç ClassDef yoksa elif dalı hiç girmez;
    #     nested class kontrolüne ulaşılmaz → kusur tetiklenmez.
    #

    def test_given_only_top_level_functions_when_analyzed_should_not_trigger_nested_class_defect(
        self,
    ):
        """
        GIVEN: Yalnızca bağımsız fonksiyonlar içeren kaynak kodu (ClassDef yok)
        WHEN : get_methods_info çağrılır
        THEN : Tüm fonksiyonlar doğru döner, kusur dalı hiç çalışmaz

        [Başarılı Senaryo]
        """
        source = """
def alpha():
    pass

def beta():
    return 42
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 2
        assert {m.name for m in result} == {"alpha", "beta"}

    # -----------------------------------------------------------------------
    # Kusur çalışır ama durum bozulmaz (yanlış durum (invalid state) yok)
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. ClassDef var ama içinde nested ClassDef yok; yalnızca
    #     doğrudan metotlar var.  Elif dalına girilir (kusur çalışır), fakat
    #     inner ClassDef branch'i hiç değerlendirilmediği için
    #     kayıp metot yoktur → liste doğrudur, durum bozulmaz.
    #

    def test_given_class_without_nested_class_when_analyzed_should_collect_all_methods_correctly(
        self,
    ):
        """
        GIVEN: İçinde nested class OLMAYAN tek bir sınıf
        WHEN : get_methods_info çağrılır
        THEN : Sınıfın metotları eksiksiz döner, durum bozulmaz

        [Kısmi Hata Senaryosu]
        """
        source = """
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 2
        assert all(m.class_name == "MyClass" for m in result)

    # -----------------------------------------------------------------------
    # Infection var ama hata (error) gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Nested class var (kusur çalışır, inner metotlar atlanır →
    #     durum bozulur/yanlış durum (invalid state) var), fakat test yalnızca dış metodun
    #     varlığını kontrol ederse inner metodun eksikliği fark edilmez →
    #     assertion geçer, hata (error) görünmez.
    #

    def test_given_nested_class_when_checking_only_outer_method_should_pass_despite_invalid_state(
        self,
    ):
        """
        GIVEN: Nested class içeren kaynak kodu
        WHEN : Yalnızca dış metodun adı kontrol edilir
        THEN : Test geçer — ama inner_method kayıptır (hata yutuluyor/gizleniyor)

        [Gizli Hata Senaryosu]
        """
        source = """
class Outer:
    def outer_method(self):
        pass

    class Inner:
        def inner_method(self):
            pass
"""
        result = make_analyzer(source).get_methods_info()
        method_names = [m.name for m in result]

        # Yalnızca dış metodu sorgulamak → yanlış durum (invalid state) görünmez
        assert "outer_method" in method_names  # Bu geçer; inner_method kayıp ama test bunu sormaz


# ===========================================================================
# SINIR DEĞER TESTLERİ
# ===========================================================================


class TestGetMethodsInfoBoundaryValues:

    def test_given_empty_source_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Boş kaynak kodu string'i
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner, exception fırlatılmaz
        """
        result = make_analyzer("").get_methods_info()
        assert result == []

    def test_given_source_with_only_comments_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Yalnızca yorum satırları içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner
        """
        source = "# Bu sadece bir yorumdur\n# Başka yorum\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_source_with_only_imports_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Yalnızca import ifadelerinden oluşan kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner
        """
        source = "import os\nimport sys\nfrom pathlib import Path\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_source_at_max_file_size_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Tam olarak MAX_FILE_SIZE + 1 karakter uzunluğunda kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Dosya atlanır, boş liste döner (sınır değeri: 500_001)
        """
        oversized_source = "x = 1\n" * (500_000 // 6 + 1)
        assert len(oversized_source) > 500_000
        result = make_analyzer(oversized_source).get_methods_info()
        assert result == []

    def test_given_source_at_exactly_max_file_size_when_analyzed_should_skip(self):
        """
        GIVEN: Tam olarak MAX_FILE_SIZE (500_000) karakterlik kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Atlanır (>= kontrolü); parse edilmez

        Sınır: len >= 500_000 → atlanır
        """
        # Tam 500_000 karakter, geçerli Python
        padding = "# " + "x" * 497 + "\n"  # 500 char/satır
        source = padding * 1000  # 500_000 char
        assert len(source) == 500_000

        # Atlanmali
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_single_function_when_analyzed_should_return_exactly_one_method(self):
        """
        GIVEN: Tek bir fonksiyon içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Tam olarak 1 MethodModel döner
        """
        source = "def lone_function(): pass\n"
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 1
        assert result[0].name == "lone_function"

    def test_given_empty_class_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: İçinde metot bulunmayan (yalnızca pass olan) sınıf
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner
        """
        source = "class Empty:\n    pass\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_syntax_error_source_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Geçersiz Python söz dizimine sahip kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Exception fırlatılmaz, boş liste döner
        """
        source = "def broken(:\n    pass\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_multiple_classes_and_functions_when_analyzed_should_collect_all(self):
        """
        GIVEN: Birden fazla sınıf ve bağımsız fonksiyon içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Tüm metot ve fonksiyonlar toplam olarak döner
        """
        source = """
def standalone():
    pass

class First:
    def first_method(self):
        pass

class Second:
    def second_method(self):
        pass
    def another_method(self):
        pass
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 4
        assert {m.name for m in result} == {
            "standalone",
            "first_method",
            "second_method",
            "another_method",
        }

    def test_given_one_broken_method_when_analyzed_should_skip_it_and_return_rest(self):
        """
        GIVEN: Bir metot çıkarımının exception fırlattığı senaryo (patch ile)
        WHEN : get_methods_info çağrılır
        THEN : Hatalı metot atlanır, diğerleri döner (continue davranışı)
        """
        from unittest.mock import patch

        source = """
def good_function():
    pass

def another_good():
    pass
"""
        call_count = 0
        original_extract = ASTAnalyzer._extract_method

        def selective_extract(self, node, class_name=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated extraction hata (error)")
            return original_extract(self, node, class_name)

        with patch.object(ASTAnalyzer, "_extract_method", selective_extract):
            result = make_analyzer(source).get_methods_info()

        # İlk metot atlandı, ikinci geldi
        assert len(result) == 1
        assert result[0].name == "another_good"

    def test_given_async_function_when_analyzed_should_be_included_in_results(self):
        """
        GIVEN: async def ile tanımlı fonksiyon içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Async fonksiyon da sonuçta yer alır ve is_async=True olur
        """
        source = "async def fetch_data():\n    pass\n"
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 1
        assert result[0].is_async is True
        assert result[0].name == "fetch_data"

    def test_given_class_with_async_method_when_analyzed_should_set_is_method_and_is_async(self):
        """
        GIVEN: Sınıf içinde async metot içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Metot hem is_async=True hem is_method=True olarak işaretlenir
        """
        source = """
class Service:
    async def process(self):
        pass
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 1
        m = result[0]
        assert m.is_async is True
        assert m.is_method is True
        assert m.class_name == "Service"

    def test_given_class_method_when_analyzed_should_carry_correct_class_name(self):
        """
        GIVEN: Sınıf içinde metot içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : MethodModel.class_name doğru sınıf adını taşır
        """
        source = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        result = make_analyzer(source).get_methods_info()
        assert result[0].class_name == "Calculator"
        assert result[0].is_method is True

    def test_given_top_level_function_when_analyzed_should_have_no_class_name(self):
        """
        GIVEN: Bağımsız (top-level) fonksiyon
        WHEN : get_methods_info çağrılır
        THEN : class_name None, is_method False olur
        """
        source = "def standalone(): pass\n"
        result = make_analyzer(source).get_methods_info()
        assert result[0].class_name is None
        assert result[0].is_method is False

    def test_given_module_and_file_path_when_analyzed_should_propagate_to_models(self):
        """
        GIVEN: Özel module_name ve file_path ile oluşturulmuş analyzer
        WHEN : get_methods_info çağrılır
        THEN : Her MethodModel bu değerleri doğru taşır
        """
        source = "def my_func(): pass\n"
        analyzer = ASTAnalyzer(
            source_code=source, module_name="my_module", file_path="/project/my_module.py"
        )
        result = analyzer.get_methods_info()
        assert result[0].module_name == "my_module"
        assert result[0].file_path == "/project/my_module.py"


"""
TestGetMethodsInfo — ASTAnalyzer.get_methods_info için kapsamlı test sınıfı.

Kapsam:
  - Defect / Infection / Failure analizi (1-5 arası görevler)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.analyzer import ASTAnalyzer

# ---------------------------------------------------------------------------
# Yardımcı: kaynak kodundan analyzer oluştur
# ---------------------------------------------------------------------------


def make_analyzer(
    source: str, module_name: str = "test_module", file_path: str = "test.py"
) -> ASTAnalyzer:
    return ASTAnalyzer(source_code=source, module_name=module_name, file_path=file_path)


#
# Hata Tanımı:
#     get_methods_info içindeki ClassDef dalı sadece node.body'yi tek seviye
#     iter eder.  Eğer bir ClassDef.body içinde başka bir ClassDef varsa
#     (nested class), o iç class'ın metotları hiç işlenmez.
#
# Tetikleyici Koşul:
#     Kaynak kodda en az bir ClassDef içinde başka bir ClassDef ve o iç
#     class'ta en az bir metot bulunması gerekir.
#
# ---------------------------------------------------------------------------


class _IGNORE_TestGetMethodsInfo:

    def test_given_nested_class_when_analyzed_should_detect_inner_class_methods(self):
        """
        GIVEN: Bir dış sınıf içinde iç sınıf (nested class) ve metotları olan kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : İç sınıfın metotları da sonuç listesinde yer almalıdır

        [Beklenen Hata: Orijinal kod kusuru]
        """
        source = """
class Outer:
    def outer_method(self):
        pass

    class Inner:
        def inner_method(self):
            pass
"""
        analyzer = make_analyzer(source)
        result = analyzer.get_methods_info()
        method_names = [m.name for m in result]

        # Orijinal kod inner_method'u GÖRMEZ → test başarısız olur
        assert (
            "inner_method" in method_names
        ), "Nested class içindeki 'inner_method' tespit edilemedi (Bilinen Hata)"

    # -----------------------------------------------------------------------
    # Kusurun çalıştırılmadığı (reachability) senaryo
    # -----------------------------------------------------------------------
    #
    # (a) Kusuru çalıştırmamak mümkün mü?
    #     Evet. Kaynak kodda hiç ClassDef yoksa elif dalı hiç girmez;
    #     nested class kontrolüne ulaşılmaz → kusur tetiklenmez.
    #

    def test_given_only_top_level_functions_when_analyzed_should_not_trigger_nested_class_defect(
        self,
    ):
        """
        GIVEN: Yalnızca bağımsız fonksiyonlar içeren kaynak kodu (ClassDef yok)
        WHEN : get_methods_info çağrılır
        THEN : Tüm fonksiyonlar doğru döner, kusur dalı hiç çalışmaz

        [Başarılı Senaryo]
        """
        source = """
def alpha():
    pass

def beta():
    return 42
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 2
        assert {m.name for m in result} == {"alpha", "beta"}

    #     Evet. ClassDef var ama içinde nested ClassDef yok; yalnızca
    #     doğrudan metotlar var.  Elif dalına girilir (kusur çalışır), fakat
    #     inner ClassDef branch'i hiç değerlendirilmediği için
    #     kayıp metot yoktur → liste doğrudur, durum bozulmaz.
    #
    #  class var, ama nested class yok

    def test_given_class_without_nested_class_when_analyzed_should_collect_all_methods_correctly(
        self,
    ):
        """
        GIVEN: İçinde nested class OLMAYAN tek bir sınıf
        WHEN : get_methods_info çağrılır
        THEN : Sınıfın metotları eksiksiz döner, durum bozulmaz

        [Kısmi Hata Senaryosu]
        """
        source = """
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 2
        assert all(m.class_name == "MyClass" for m in result)

    # -----------------------------------------------------------------------
    # Infection var ama hata (error) gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Nested class var (kusur çalışır, inner metotlar atlanır →
    #     durum bozulur/yanlış durum (invalid state) var), fakat test yalnızca dış metodun
    #     varlığını kontrol ederse inner metodun eksikliği fark edilmez →
    #     assertion geçer, hata (error) görünmez.
    #

    def test_given_nested_class_when_checking_only_outer_method_should_pass_despite_invalid_state(
        self,
    ):
        """
        GIVEN: Nested class içeren kaynak kodu
        WHEN : Yalnızca dış metodun adı kontrol edilir
        THEN : Test geçer — ama inner_method kayıptır (hata yutuluyor/gizleniyor)

        [Gizli Hata Senaryosu]
        """
        source = """
class Outer:
    def outer_method(self):
        pass

    class Inner:
        def inner_method(self):
            pass
"""
        result = make_analyzer(source).get_methods_info()
        method_names = [m.name for m in result]

        # Yalnızca dış metodu sorgulamak → yanlış durum (invalid state) görünmez
        assert "outer_method" in method_names  # Bu geçer; inner_method kayıp ama test bunu sormaz


# ===========================================================================
# SINIR DEĞER TESTLERİ
# ===========================================================================


class _IGNORE_TestGetMethodsInfoBoundaryValues:

    def test_given_empty_source_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Boş kaynak kodu string'i
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner, exception fırlatılmaz
        """
        result = make_analyzer("").get_methods_info()
        assert result == []

    def test_given_source_with_only_comments_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Yalnızca yorum satırları içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner
        """
        source = "# Bu sadece bir yorumdur\n# Başka yorum\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_source_with_only_imports_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Yalnızca import ifadelerinden oluşan kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner
        """
        source = "import os\nimport sys\nfrom pathlib import Path\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_source_at_max_file_size_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Tam olarak MAX_FILE_SIZE + 1 karakter uzunluğunda kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Dosya atlanır, boş liste döner (sınır değeri: 500_001)
        """
        oversized_source = "x = 1\n" * (500_000 // 6 + 1)
        assert len(oversized_source) > 500_000
        result = make_analyzer(oversized_source).get_methods_info()
        assert result == []

    def test_given_source_at_exactly_max_file_size_when_analyzed_should_attempt_parse(self):
        """
        GIVEN: Tam olarak MAX_FILE_SIZE (500_000) karakterlik kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Atlanmaz (> kontrolü, = dahil değil); parse denenir

        Sınır: len > 500_000 → atlanır; len == 500_000 → parse edilir
        """
        # Tam 500_000 karakter, geçerli Python
        padding = "# " + "x" * 497 + "\n"  # 500 char/satır
        source = padding * 1000  # 500_000 char
        assert len(source) == 500_000

        # Parse edilmeli (boş bile olsa exception fırlatmamalı)
        result = make_analyzer(source).get_methods_info()
        assert isinstance(result, list)

    def test_given_single_function_when_analyzed_should_return_exactly_one_method(self):
        """
        GIVEN: Tek bir fonksiyon içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Tam olarak 1 MethodModel döner
        """
        source = "def lone_function(): pass\n"
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 1
        assert result[0].name == "lone_function"

    def test_given_empty_class_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: İçinde metot bulunmayan (yalnızca pass olan) sınıf
        WHEN : get_methods_info çağrılır
        THEN : Boş liste döner
        """
        source = "class Empty:\n    pass\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_syntax_error_source_when_analyzed_should_return_empty_list(self):
        """
        GIVEN: Geçersiz Python söz dizimine sahip kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Exception fırlatılmaz, boş liste döner
        """
        source = "def broken(:\n    pass\n"
        result = make_analyzer(source).get_methods_info()
        assert result == []

    def test_given_multiple_classes_and_functions_when_analyzed_should_collect_all(self):
        """
        GIVEN: Birden fazla sınıf ve bağımsız fonksiyon içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Tüm metot ve fonksiyonlar toplam olarak döner
        """
        source = """
def standalone():
    pass

class First:
    def first_method(self):
        pass

class Second:
    def second_method(self):
        pass
    def another_method(self):
        pass
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 4
        assert {m.name for m in result} == {
            "standalone",
            "first_method",
            "second_method",
            "another_method",
        }

    def test_given_one_broken_method_when_analyzed_should_skip_it_and_return_rest(self):
        """
        GIVEN: Bir metot çıkarımının exception fırlattığı senaryo (patch ile)
        WHEN : get_methods_info çağrılır
        THEN : Hatalı metot atlanır, diğerleri döner (continue davranışı)
        """
        from unittest.mock import patch

        source = """
def good_function():
    pass

def another_good():
    pass
"""
        call_count = 0
        original_extract = ASTAnalyzer._extract_method

        def selective_extract(self, node, class_name=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated extraction hata (error)")
            return original_extract(self, node, class_name)

        with patch.object(ASTAnalyzer, "_extract_method", selective_extract):
            result = make_analyzer(source).get_methods_info()

        # İlk metot atlandı, ikinci geldi
        assert len(result) == 1
        assert result[0].name == "another_good"

    def test_given_async_function_when_analyzed_should_be_included_in_results(self):
        """
        GIVEN: async def ile tanımlı fonksiyon içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Async fonksiyon da sonuçta yer alır ve is_async=True olur
        """
        source = "async def fetch_data():\n    pass\n"
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 1
        assert result[0].is_async is True
        assert result[0].name == "fetch_data"

    def test_given_class_with_async_method_when_analyzed_should_set_is_method_and_is_async(self):
        """
        GIVEN: Sınıf içinde async metot içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : Metot hem is_async=True hem is_method=True olarak işaretlenir
        """
        source = """
class Service:
    async def process(self):
        pass
"""
        result = make_analyzer(source).get_methods_info()
        assert len(result) == 1
        m = result[0]
        assert m.is_async is True
        assert m.is_method is True
        assert m.class_name == "Service"

    def test_given_class_method_when_analyzed_should_carry_correct_class_name(self):
        """
        GIVEN: Sınıf içinde metot içeren kaynak kodu
        WHEN : get_methods_info çağrılır
        THEN : MethodModel.class_name doğru sınıf adını taşır
        """
        source = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        result = make_analyzer(source).get_methods_info()
        assert result[0].class_name == "Calculator"
        assert result[0].is_method is True

    def test_given_top_level_function_when_analyzed_should_have_no_class_name(self):
        """
        GIVEN: Bağımsız (top-level) fonksiyon
        WHEN : get_methods_info çağrılır
        THEN : class_name None, is_method False olur
        """
        source = "def standalone(): pass\n"
        result = make_analyzer(source).get_methods_info()
        assert result[0].class_name is None
        assert result[0].is_method is False

    def test_given_module_and_file_path_when_analyzed_should_propagate_to_models(self):
        """
        GIVEN: Özel module_name ve file_path ile oluşturulmuş analyzer
        WHEN : get_methods_info çağrılır
        THEN : Her MethodModel bu değerleri doğru taşır
        """
        source = "def my_func(): pass\n"
        analyzer = ASTAnalyzer(
            source_code=source, module_name="my_module", file_path="/project/my_module.py"
        )
        result = analyzer.get_methods_info()
        assert result[0].module_name == "my_module"
        assert result[0].file_path == "/project/my_module.py"


"""
TestBuildSignature — ASTAnalyzer._build_signature için kapsamlı test sınıfı.

══════════════════════════════════════════════════════════════════════════════
KUSUR ANALİZİ (Defect / Infection / Failure)
══════════════════════════════════════════════════════════════════════════════

  (a) KUSUR NEDİR VE NEREDE?
      _build_signature içinde return tipi oluşturulurken:

          ret = self._safe_unparse(node.returns)
          if ret:           ← KUSURLU KONTROL
              returns = f" -> {ret}"

      `_safe_unparse` bir hata ile karşılaştığında `None` döner.
      `if ret:` kontrolü `None`'ı falsy olarak değerlendirir ve `returns`
      boş string kalır. Ancak `node.returns` zaten truthy olduğu için kaynak
      kodda açıkça yazılmış bir return tipi vardır. Bu return tipi imzada
      sessizce yok edilir → BİLGİ KAYBI.

      Doğru davranış: `ret is not None` kontrolü kullanmak; `None` geldiğinde
      `"-> ..."` gibi bir fallback göstermek (args_str hatasıyla tutarlı).

  (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
      node.returns truthy OLMALI (kaynak kodda return tipi yazılmış olmalı)
      VE `_safe_unparse` o node için `None` döndürmeli (unparse başarısız).

  (c) → test_given_unparseable_return_type_when_building_signature_should_fail
        (Görev 1c — orijinal kodla BAŞARISIZ olacak)

  2 → test_given_no_return_type_when_building_signature_should_not_trigger_defect
  3 → test_given_parseable_return_type_when_building_signature_should_not_infect
  4 → test_given_unparseable_return_type_when_only_prefix_checked_yanlış durum (invalid state)_hidden
  5 → FixedASTAnalyzer ile 1c testi başarılı olur
"""


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def _node(source: str):
    """Kaynak kodundaki ilk fonksiyonun AST node'unu döner."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    raise ValueError("Fonksiyon bulunamadı")


def _sig(source: str) -> str:
    """Orijinal ASTAnalyzer ile imza döner."""
    analyzer = ASTAnalyzer(source_code=source)
    return analyzer._build_signature(_node(source))


def _sig_with_none_unparse(source: str) -> str:
    """_safe_unparse'ın None döndürdüğü durumu simüle eder (orijinal)."""
    analyzer = ASTAnalyzer(source_code=source)
    with patch.object(analyzer, "_safe_unparse", return_value=None):
        return analyzer._build_signature(_node(source))


class TestBuildSignature:

    def test_given_unparseable_return_type_when_building_signature_should_fail(self):
        """
        GIVEN: Return tipi olan bir fonksiyon ve _safe_unparse'ın None döndürdüğü koşul
        WHEN : _build_signature çağrılır
        THEN : İmzada return tipinin varlığı gösterilmeli (en azından '-> ...')
               Orijinal kodda return tipi sessizce silinir → test BAŞARISIZ olur

        [orijinal kodla BAŞARISIZ olması beklenir]
        """
        source = "def process(self) -> int: pass"
        result = _sig_with_none_unparse(source)

        assert "->" in result, (
            "Return tipi mevcut ama _safe_unparse=None olduğunda imzadan silindi (Bilinen Hata). "
            f"Üretilen imza: '{result}'"
        )

    # -----------------------------------------------------------------------
    # Kusur tetiklenmez: return tipi yoksa elif/inner dal çalışmaz
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Fonksiyonda return tipi (annotation) yazılmamışsa node.returns=None.
    #     "if node.returns:" dalına hiç girilmez → _safe_unparse çağrılmaz →
    #     kusurlu "if ret:" kontrolü devreye girmez.
    #

    def test_given_no_return_type_when_building_signature_should_not_trigger_defect(self):
        """
        GIVEN: Return tipi annotation'ı OLMAYAN bir fonksiyon
        WHEN : _build_signature çağrılır
        THEN : İmzada '->' bulunmaz, kusur tetiklenmez

        [Kusur tetiklenmez senaryo]
        """
        source = "def foo(a, b): pass"
        result = _sig(source)

        assert "->" not in result
        assert result == "def foo(a, b)"

    # -----------------------------------------------------------------------
    # Kusur çalışır ama yanlış durum (invalid state) olmaz
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. node.returns mevcut (return tipi yazılmış) ve _safe_unparse
    #     başarıyla truthy bir string döndürüyor. "if ret:" True olur → returns
    #     doğru ayarlanır → durum bozulmaz (yanlış durum (invalid state) yok).
    #

    def test_given_parseable_return_type_when_building_signature_should_not_infect(self):
        """
        GIVEN: Standart ve parse edilebilir return tipine sahip fonksiyon (-> int)
        WHEN : _build_signature çağrılır
        THEN : İmza return tipini doğru içerir, durum bozulmaz

        [Kısmi Hata Senaryosu]
        """
        source = "def calculate(x: int) -> int: pass"
        result = _sig(source)

        assert result == "def calculate(x: int) -> int"

    # -----------------------------------------------------------------------
    # Infection var ama hata (error) görünmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. _safe_unparse None döndürüyor (yanlış durum (invalid state): return tipi kayboldu),
    #     ama test yalnızca "def" prefix veya fonksiyon adını kontrol ediyorsa
    #     return tipinin silindiğini göremez → assertion geçer → hata (error) yok.
    #

    def test_given_unparseable_return_type_when_only_prefix_checked_invalid_state_hidden(self):
        """
        GIVEN: _safe_unparse=None (return tipi kaybolmuş, yanlış durum (invalid state) mevcut)
        WHEN : Yalnızca imzanın 'def' ile başladığı kontrol edilir
        THEN : Test geçer — return tipi kayıp ama bu kontrol onu görmez

        [Gizli Hata Senaryosu]
        """
        source = "def transform(self) -> dict: pass"
        result = _sig_with_none_unparse(source)

        # Yüzeysel kontrol → hata yutuluyor/gizleniyor
        assert result.startswith(
            "def transform"
        ), "Bu assertion geçer; ama imzada '-> dict' kayıp — yanlış durum (invalid state) gizlenmiş"


# ===========================================================================
# SINIR DEĞER TESTLERİ
# ===========================================================================


class TestBuildSignatureBoundaryValues:

    # --- Prefix doğruluğu ---

    def test_given_sync_function_when_building_signature_should_use_def_prefix(self):
        """
        GIVEN: Sıradan (sync) bir fonksiyon
        WHEN : _build_signature çağrılır
        THEN : İmza 'def' ile başlar, 'async' içermez
        """
        result = _sig("def foo(): pass")
        assert result.startswith("def ")
        assert "async" not in result

    def test_given_async_function_when_building_signature_should_use_async_def_prefix(self):
        """
        GIVEN: async def ile tanımlı fonksiyon
        WHEN : _build_signature çağrılır
        THEN : İmza 'async def' ile başlar
        """
        result = _sig("async def fetch(): pass")
        assert result.startswith("async def ")

    # --- Parametre varyasyonları ---

    def test_given_no_parameters_when_building_signature_should_produce_empty_parens(self):
        """
        GIVEN: Hiç parametresi olmayan fonksiyon
        WHEN : _build_signature çağrılır
        THEN : İmzada boş parantez yer alır
        """
        result = _sig("def foo(): pass")
        assert result == "def foo()"

    def test_given_type_annotated_params_when_building_signature_should_include_annotations(self):
        """
        GIVEN: Tip annotasyonlu parametreler (a: int, b: str)
        WHEN : _build_signature çağrılır
        THEN : Annotasyonlar imzada yer alır
        """
        result = _sig("def foo(a: int, b: str): pass")
        assert "a: int" in result
        assert "b: str" in result

    def test_given_default_values_when_building_signature_should_include_defaults(self):
        """
        GIVEN: Default değerli parametreler (a=1, b='x')
        WHEN : _build_signature çağrılır
        THEN : Default değerler imzada yer alır
        """
        result = _sig("def foo(a=1, b='x'): pass")
        assert "a=1" in result
        assert "b='x'" in result

    def test_given_args_and_kwargs_when_building_signature_should_include_star_forms(self):
        """
        GIVEN: *args ve **kwargs içeren fonksiyon
        WHEN : _build_signature çağrılır
        THEN : Yıldızlı formlar imzada yer alır
        """
        result = _sig("def foo(*args, **kwargs): pass")
        assert "*args" in result
        assert "**kwargs" in result

    def test_given_keyword_only_params_when_building_signature_should_include_star_separator(self):
        """
        GIVEN: Keyword-only parametreler (def foo(a, *, b, c))
        WHEN : _build_signature çağrılır
        THEN : '*' ayırıcısı imzada görünür
        """
        result = _sig("def foo(a, *, b, c): pass")
        assert "*" in result
        assert "b" in result
        assert "c" in result

    def test_given_positional_only_params_when_building_signature_should_include_slash(self):
        """
        GIVEN: Positional-only parametreler (def foo(a, b, /, c))
        WHEN : _build_signature çağrılır
        THEN : '/' ayırıcısı imzada görünür
        """
        result = _sig("def foo(a, b, /, c): pass")
        assert "/" in result

    # --- Return tipi varyasyonları ---

    def test_given_simple_return_type_when_building_signature_should_include_arrow_notation(self):
        """
        GIVEN: Basit return tipi (-> int)
        WHEN : _build_signature çağrılır
        THEN : '-> int' imzada yer alır
        """
        result = _sig("def foo() -> int: pass")
        assert "-> int" in result

    def test_given_none_return_type_when_building_signature_should_include_none_annotation(self):
        """
        GIVEN: Return tipi 'None' olarak belirtilmiş fonksiyon
        WHEN : _build_signature çağrılır
        THEN : '-> None' imzada yer alır

        (Bu sınır değeridir: 'None' string truthy olduğundan if ret: geçer)
        """
        result = _sig("def foo() -> None: pass")
        assert "-> None" in result

    def test_given_complex_generic_return_type_when_building_signature_should_include_full_type(
        self,
    ):
        """
        GIVEN: Generic return tipi (-> dict[str, list[int]])
        WHEN : _build_signature çağrılır
        THEN : Tam generic tip ifadesi imzada yer alır
        """
        result = _sig("def foo() -> dict[str, list[int]]: pass")
        assert "-> dict[str, list[int]]" in result

    def test_given_no_return_annotation_when_building_signature_should_omit_arrow(self):
        """
        GIVEN: Return tipi annotation'ı olmayan fonksiyon
        WHEN : _build_signature çağrılır
        THEN : '->' karakteri imzada bulunmaz
        """
        result = _sig("def foo(x): pass")
        assert "->" not in result

    # --- Fonksiyon adı ---

    def test_given_function_name_when_building_signature_should_preserve_exact_name(self):
        """
        GIVEN: 'my_special_func' adında bir fonksiyon
        WHEN : _build_signature çağrılır
        THEN : İmza tam olarak o adı içerir
        """
        result = _sig("def my_special_func(): pass")
        assert "my_special_func" in result

    # --- args_str fallback ---

    def test_given_unparse_error_on_args_when_building_signature_should_use_ellipsis_fallback(self):
        """
        GIVEN: ast.unparse'ın args için exception fırlattığı koşul
        WHEN : _build_signature çağrılır
        THEN : args_str olarak '...' kullanılır; metot çökmez

        (args fallback tutarlılığı: args için '...' var, returns için de olmalı)
        """
        source = "def foo(a, b): pass"
        analyzer = ASTAnalyzer(source_code=source)
        node = _node(source)

        original_unparse = ast.unparse

        def selective_unparse(n):
            if isinstance(n, ast.arguments):
                raise RuntimeError("Simulated hata (error)")
            return original_unparse(n)

        with patch("src.preprocess.analyzer.ast.unparse", side_effect=selective_unparse):
            result = analyzer._build_signature(node)

        assert "..." in result
        assert "def foo" in result

    # --- async + return kombinasyonu ---

    def test_given_async_function_with_return_type_when_building_signature_should_combine_both(
        self,
    ):
        """
        GIVEN: async def ve return tipi olan fonksiyon
        WHEN : _build_signature çağrılır
        THEN : İmza hem 'async def' prefix'i hem '-> str' return tipini içerir
        """
        result = _sig("async def fetch(url: str) -> str: pass")
        assert result.startswith("async def fetch")
        assert "-> str" in result

    def test_given_self_parameter_when_building_signature_should_include_self(self):
        """
        GIVEN: self parametresi olan bir metot
        WHEN : _build_signature çağrılır
        THEN : İmzada 'self' parametresi görünür
        """
        result = _sig("def method(self, x: int) -> None: pass")
        assert "self" in result
        assert "-> None" in result


"""
TestSafeUnparse — ASTAnalyzer._safe_unparse için kapsamlı test sınıfı.

══════════════════════════════════════════════════════════════════════════════
KUSUR ANALİZİ (Defect / Infection / Failure)
══════════════════════════════════════════════════════════════════════════════

  (a) KUSUR NEDİR VE NEREDE?

      _safe_unparse iki semantik olarak farklı başarısızlık durumunu aynı
      dönüş değeriyle (None) ifade eder:

        Durum A — Bilinçli "yok":  node=None geldi  → None döner
        Durum B — Sessiz hata:     node geçerli ama ast.unparse exception
                                   fırlattı         → None döner (exception yutulur)

      Çağıran kod (örn. _build_signature, _extract_method) bu iki durumu
      ayırt edemez. "Annotasyon hiç yazılmamış" ile "annotasyon var ama
      parse edilemedi" aynı görünür. Bu semantik belirsizlik (ambiguous
      contract), özellikle return_type ve _build_signature gibi çağıranlarda
      yanlış davranışa yol açar.

      Somut hata (error): _build_signature içindeki `if ret:` kontrolü her iki
      None'ı da aynı şekilde değerlendirerek return tipini sessizce siler
      (bu kusur TestBuildSignature'da ayrıca belgelenmiştir).

  (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
      node None değil (yani "annotasyon var" sinyali geçerli) ama
      ast.unparse o node için exception fırlatıyor olmalıdır.
      Bu koşulda _safe_unparse None döner; çağıran annotasyonun yokluğu
      ile karıştırır.

  (c) → test_given_valid_node_when_unparse_raises_should_fail_distinguishing_from_none_input
        [orijinal kodla BAŞARISIZ]

  2 → test_given_valid_parseable_node_when_called_should_not_enter_except_block
        [kusur tetiklenmez]

  3 → test_given_none_input_when_called_should_return_none_without_yanlış durum (invalid state)
        [kusur çalışmaz, yanlış durum (invalid state) yok]

  4 → test_given_unparse_hata (error)_when_caller_only_checks_none_yanlış durum (invalid state)_is_hidden
        [yanlış durum (invalid state) var, hata (error) yok]

  5 → FixedASTAnalyzer ile 1c başarılı olur
        [Sınır/Hata Kontrolü]
"""


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def _expr(source: str):
    """Bir ifadenin AST expression node'unu döner."""
    return ast.parse(source, mode="eval").body


def _safe_unparse(node):
    """Orijinal implementasyon üzerinden çağırır."""
    return ASTAnalyzer(source_code="")._safe_unparse(node)


class TestSafeUnparse:

    def test_given_valid_node_when_unparse_raises_should_fail_distinguishing_from_none_input(self):
        """
        GIVEN: Geçerli bir AST node (node is not None) ama ast.unparse exception fırlatıyor
        WHEN : _safe_unparse çağrılır
        THEN : Dönüş değeri, None input ile ayırt edilebilir olmalıdır
               → Orijinal kod her iki durumda da None döndürür — test BAŞARISIZ olur

        [orijinal kodla BAŞARISIZ olması beklenir]

        Neden önemli: Çağıran "annotasyon yoktu" ile "annotasyon okunmadı"
        arasını ayırt edemez → sessiz bilgi kaybı.
        """
        valid_node = _expr("int")

        with patch("ast.unparse", side_effect=RuntimeError("Simulated unparse hata (error)")):
            result_on_exception = _safe_unparse(valid_node)

        result_on_none_input = _safe_unparse(None)

        # İkisi de None döndürüyor — ama semantik olarak farklı durumlar.
        # Düzgün davranış: exception durumunu None input'tan ayırt etmek
        # (ör. sentinel değer, boş string, özel sabit).
        assert result_on_exception != result_on_none_input, (
            "Exception durumu (node geçerli, unparse başarısız) ile "
            "None input aynı değeri döndürüyor — semantik belirsizlik/KUSUR aktif."
        )

    def test_given_valid_parseable_node_when_called_should_not_enter_except_block(self):
        """
        GIVEN: ast.unparse'ın başarıyla işleyeceği geçerli bir AST node
        WHEN : _safe_unparse çağrılır
        THEN : except bloğuna girilmez; başarılı string sonucu döner

        [kusur (except bloğu) hiç tetiklenmez]
        """
        node = _expr("int")
        result = _safe_unparse(node)

        assert isinstance(result, str), "Geçerli node için string dönmeli"
        assert result == "int"

    def test_given_none_input_when_called_should_return_none_without_invalid_state(self):
        """
        GIVEN: None input (annotasyon veya tip yok anlamında çağrılıyor)
        WHEN : _safe_unparse çağrılır
        THEN : Hemen None döner; try/except bloğuna hiç girilmez, durum bozulmaz

        [kusur (except yutma) çalışmaz, yanlış durum (invalid state) yok]

        None input için "if node is None: return None" early-return devreye girer.
        Bu doğru davranıştır ve durum bozulmaz.
        """
        result = _safe_unparse(None)
        assert result is None

    def test_given_unparse_error_when_caller_only_checks_type_invalid_state_is_hidden(self):
        """
        GIVEN: ast.unparse exception fırlatıyor (yanlış durum (invalid state): geçerli node yok gibi görünüyor)
        WHEN : Çağıran yalnızca "str döndü mü?" kontrolü yapıyor
        THEN : Kontrol geçer — ama sentinel degerin anlamı sorgulanmaz, yanlış durum gizlenir

        [yanlış durum (invalid state) var (yanlış semantik), hata (error) görünmez]

        Infection: "node geçerliydi ama parse başarısız" bilgisi kayboldu.
        Çağıran bunu "node yoktu" ile aynı sanıyor. Test bunu görmüyor.
        """
        valid_node = _expr("str")

        with patch("ast.unparse", side_effect=RuntimeError("Simulated")):
            result = _safe_unparse(valid_node)

        # Yüzeysel kontrol → hata yutuluyor/gizleniyor
        assert isinstance(result, str)  # Bu geçer; ama neden sentinel geldigi sorgulanmaz


# ===========================================================================
# SINIR DEĞER & DAVRANIŞ TESTLERİ
# ===========================================================================


class TestSafeUnparseBehaviors:

    # -----------------------------------------------------------------------
    # None guard
    # -----------------------------------------------------------------------

    def test_given_none_should_return_none_not_raise(self):
        """
        GIVEN: None
        WHEN : _safe_unparse çağrılır
        THEN : None döner, exception fırlatılmaz

        Temel sözleşme: None → None, hiçbir zaman crash yok.
        """
        assert _safe_unparse(None) is None

    # -----------------------------------------------------------------------
    # Return tipi annotation node'ları (asıl kullanım alanı)
    # -----------------------------------------------------------------------

    def test_given_simple_type_annotation_nodes_should_return_their_string_forms(self):
        """
        GIVEN: int, str, bool, float gibi basit tip annotation node'ları
        WHEN : _safe_unparse çağrılır
        THEN : Her biri doğru string karşılığını döner

        _safe_unparse'ın birincil kullanım amacı return_type ve
        _build_signature için tip annotasyonlarını string'e çevirmektir.
        """
        cases = [
            ("int", "int"),
            ("str", "str"),
            ("bool", "bool"),
            ("float", "float"),
        ]
        for source, expected in cases:
            assert _safe_unparse(_expr(source)) == expected, f"'{source}' → '{expected}' bekleniyor"

    def test_given_none_type_annotation_node_should_return_string_none_not_python_none(self):
        """
        GIVEN: 'None' yazılmış return tipi (-> None) için AST node
        WHEN : _safe_unparse çağrılır
        THEN : Python None değil, 'None' STRING'i döner

        Bu kritik bir sınır değeridir: kaynak kod 'None' yazıyor ama
        _safe_unparse None (Python) döndürürse çağıran "annotasyon yok"
        sanır. Doğru sonuç: string "None".
        """
        node = _expr("None")  # -> None annotation'ının AST karşılığı
        result = _safe_unparse(node)

        assert (
            result == "None"
        ), f"'None' annotation 'None' string döndürmeli, Python None değil. Dönen: {result!r}"
        assert result is not None, "'None' annotasyonu Python None olarak döndü — semantik kayıp"

    def test_given_generic_type_annotations_should_preserve_full_structure(self):
        """
        GIVEN: list[int], dict[str, int], Optional[str] gibi generic tipler
        WHEN : _safe_unparse çağrılır
        THEN : Tam type expression string olarak korunur
        """
        cases = [
            ("list[int]", "list[int]"),
            ("dict[str, int]", "dict[str, int]"),
            ("tuple[int, ...]", "tuple[int, ...]"),
        ]
        for source, expected in cases:
            result = _safe_unparse(_expr(source))
            assert result == expected, f"Generic tip '{source}' → '{expected}' bekleniyor"

    def test_given_union_type_annotation_should_return_union_string(self):
        """
        GIVEN: int | str (Python 3.10+ union söz dizimi) annotation node
        WHEN : _safe_unparse çağrılır
        THEN : 'int | str' string'i döner
        """
        result = _safe_unparse(_expr("int | str"))
        assert result == "int | str"

    def test_given_nested_generic_annotation_should_return_full_string(self):
        """
        GIVEN: dict[str, list[int]] gibi iç içe generic annotation
        WHEN : _safe_unparse çağrılır
        THEN : Tam iç içe expression string olarak döner
        """
        result = _safe_unparse(_expr("dict[str, list[int]]"))
        assert result == "dict[str, list[int]]"

    # -----------------------------------------------------------------------
    # Falsy ama geçerli annotation değerleri — kritik sınır değerleri
    # -----------------------------------------------------------------------

    def test_given_false_annotation_node_should_return_string_false_not_falsy(self):
        """
        GIVEN: 'False' annotation node'u
        WHEN : _safe_unparse çağrılır
        THEN : 'False' STRING'i döner (Python False bool değil)

        Eğer çağıran "if result:" kullanırsa bu değeri None gibi yok sayar.
        Bu _safe_unparse'ın değil çağıranın sorunudur; ama davranış belgelenmeli.
        """
        result = _safe_unparse(_expr("False"))
        assert result == "False"
        assert isinstance(result, str)

    def test_given_zero_annotation_node_should_return_string_zero(self):
        """
        GIVEN: '0' literal içeren annotation node
        WHEN : _safe_unparse çağrılır
        THEN : '0' STRING'i döner

        '0' → "0" (truthy string) döner; ancak çağıran "if ret:" kullanırsa
        "0" truthy olduğu için bu case'de sorun çıkmaz. Belgeleme amaçlıdır.
        """
        result = _safe_unparse(_expr("0"))
        assert result == "0"
        assert isinstance(result, str)

    # -----------------------------------------------------------------------
    # Exception güvenliği — asla crash olmamalı
    # -----------------------------------------------------------------------

    def test_given_any_exception_from_unparse_should_return_sentinel_not_raise(self):
        """
        GIVEN: ast.unparse her türlü exception fırlatıyor
        WHEN : _safe_unparse çağrılır
        THEN : Exception dışarıya sızmaz; sentinel string döner

        _safe_unparse'ın temel güvenlik garantisi: ne olursa olsun crash etmez.
        """
        node = _expr("int")
        exceptions_to_test = [
            RuntimeError("internal error"),
            ValueError("bad node"),
            TypeError("unexpected type"),
            MemoryError("out of memory"),
        ]
        for exc in exceptions_to_test:
            with patch("ast.unparse", side_effect=exc):
                result = _safe_unparse(node)
            assert isinstance(result, str) and result, (
                f"{type(exc).__name__} fırlatıldığında sentinel string bekleniyor, {result!r} döndü"
            )

    def test_given_non_ast_object_when_unparse_raises_should_return_none(self):
        """
        GIVEN: AST node olmayan bir nesne (str, int, dict gibi)
        WHEN : _safe_unparse çağrılır
        THEN : Exception fırlatmaz; None döner (ast.unparse bunları reddeder)

        None kontrolü geçiyor (non-None nesne), try'a giriyor, unparse fail → None.
        """
        non_ast_inputs = [42, "hello", {"key": "val"}, True, 3.14]
        for val in non_ast_inputs:
            result = _safe_unparse(val)
            assert result is None or isinstance(result, str), f"{val!r} için crash olmamalı"

    # -----------------------------------------------------------------------
    # Farklı geçerli AST node türleri
    # -----------------------------------------------------------------------

    def test_given_attribute_access_node_should_return_dotted_string(self):
        """
        GIVEN: 'a.b.c' gibi attribute access node (typing.Optional gibi kullanımlar)
        WHEN : _safe_unparse çağrılır
        THEN : Noktalı string döner
        """
        result = _safe_unparse(_expr("typing.Optional"))
        assert result == "typing.Optional"

    def test_given_string_annotation_node_should_return_quoted_string(self):
        """
        GIVEN: Forward reference olarak yazılmış string annotation ('MyClass')
        WHEN : _safe_unparse çağrılır
        THEN : Tırnaklı string döner (ast.unparse'ın doğal çıktısı)
        """
        result = _safe_unparse(_expr("'MyClass'"))
        assert result is not None
        assert "MyClass" in result

    def test_given_callable_annotation_should_return_callable_string(self):
        """
        GIVEN: Callable[[int], str] gibi karmaşık annotation
        WHEN : _safe_unparse çağrılır
        THEN : String döner, crash olmaz
        """
        result = _safe_unparse(_expr("Callable[[int], str]"))
        assert result is not None
        assert isinstance(result, str)

    # -----------------------------------------------------------------------
    # Return değeri tipi garantisi
    # -----------------------------------------------------------------------

    def test_given_any_valid_node_return_value_should_always_be_str_or_none(self):
        """
        GIVEN: Çeşitli geçerli AST node'ları
        WHEN : _safe_unparse çağrılır
        THEN : Dönüş değeri her zaman ya str ya None'dur; başka tip asla dönmez

        Bu metodun tam kontratı: Optional[str].
        """
        nodes = [
            None,
            _expr("int"),
            _expr("str | None"),
            _expr("dict[str, list[int]]"),
            _expr("None"),
            _expr("True"),
        ]
        for node in nodes:
            result = _safe_unparse(node)
            assert result is None or isinstance(
                result, str
            ), f"node={node!r} için str veya None bekleniyor, {type(result)} döndü"


"""
TestParseCode — ASTAnalyzer._parse_code için kapsamlı test sınıfı.

══════════════════════════════════════════════════════════════════════════════
KUSUR ANALİZİ (Defect / Infection / Failure)
══════════════════════════════════════════════════════════════════════════════

  KUSUR 1 — Off-by-one: `>` yerine `>=` kullanılmalıydı
  ────────────────────────────────────────────────────────
  (a) KUSUR NEDİR VE NEREDE?
      `if len(self.source_code) > MAX_FILE_SIZE:` kontrolü tam 500_000
      karakterlik dosyayı geçirir. MAX_FILE_SIZE bir üst sınır (exclusive
      upper bound) olarak isimlendirilmiş; bu sınıra eşit olan dosyalar da
      atlanmalıdır. `>` yerine `>=` kullanılmalıydı.

  (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
      len(source_code) == MAX_FILE_SIZE (tam 500_000 karakter).

  (c) → test_given_source_at_exact_max_size_when_parsed_should_fail_being_skipped
        [orijinal kodla BAŞARISIZ]

  2 → test_given_source_below_max_size_when_parsed_should_not_trigger_size_defect
  3 → test_given_source_at_exact_max_size_when_parsed_yanlış durum (invalid state)_not_visible_if_valid
  4 → test_given_source_at_exact_max_size_when_caller_only_checks_result_not_none
  5 → FixedASTAnalyzer ile 1c başarılı olur

  ──────────────────────────────────────────────────────────────────────────
  KUSUR 2 — Dar exception tuple: MemoryError yakalanmıyor
  ──────────────────────────────────────────────────────────────────────────
  (a) KUSUR NEDİR VE NEREDE?
      `except (SyntaxError, ValueError, RecursionError)` yalnızca üç tür
      yakalar. ast.parse'ın karmaşık/büyük kaynak kodda fırlatabileceği
      MemoryError ve diğer beklenmedik exception'lar dışarı sızar → uygulama
      çöker.

  (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
      ast.parse, SyntaxError/ValueError/RecursionError dışında bir exception
      fırlatmalıdır (örn. MemoryError).

  (c) → test_given_memory_error_from_parse_when_called_should_fail_not_crash
        [ikincil — orijinal kodla BAŞARISIZ]
"""


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


MAX_FILE_SIZE = 500_000


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def _parse(source: str, file_path: str = "test.py"):
    return ASTAnalyzer(source_code=source, file_path=file_path)._parse_code()


def _source_of_len(n: int) -> str:
    """Tam n karakter uzunluğunda, geçerli Python olan kaynak kodu üretir."""
    # "# " + "x"*(n-2) → geçerli Python (yorum satırı), tam n karakter
    assert n >= 2
    return "# " + "x" * (n - 2)


# ===========================================================================
# KUSUR 1 — Off-by-one (> vs >=)
# ===========================================================================


class TestParseCode:

    # ── Görev 1c ────────────────────────────────────────────────────────────

    def test_given_source_at_exact_max_size_when_parsed_should_fail_being_skipped(self):
        """
        GIVEN: Tam MAX_FILE_SIZE (500_000) karakterlik kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : Dosya "çok büyük" sayılarak None dönmeli (atlanmalı)
               Orijinal kodda > kontrolü bu eşiti geçirir → AST döner → BAŞARISIZ

        [Bilinen Hata Kontrolü]
        """
        source = _source_of_len(MAX_FILE_SIZE)
        assert len(source) == MAX_FILE_SIZE

        result = _parse(source)

        assert result is None, (
            f"len={MAX_FILE_SIZE} (tam MAX_FILE_SIZE) olan kaynak atlanmalıydı. "
            f"Orijinal '>' kontrolü bu eşiti geçirdi — OFF-BY-ONE KUSUR aktif."
        )

    # ── Görev 2b ────────────────────────────────────────────────────────────

    def test_given_source_below_max_size_when_parsed_should_not_trigger_size_defect(self):
        """
        GIVEN: MAX_FILE_SIZE'dan küçük (499_999 karakter) kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : Boyut kontrolü dalına girilmez; geçerli AST döner

        [boyut kusuru tetiklenmez]
        """
        source = _source_of_len(MAX_FILE_SIZE - 1)
        assert len(source) == MAX_FILE_SIZE - 1

        result = _parse(source)

        assert result is not None
        assert isinstance(result, ast.AST)

    # ── Görev 3b ────────────────────────────────────────────────────────────

    def test_given_source_at_exact_max_size_invalid_state_not_visible_when_code_is_valid(self):
        """
        GIVEN: Tam 500_000 karakterlik, geçerli Python kodu
        WHEN : _parse_code çağrılır
        THEN : Kaynak atlanır ve None döner (duzeltilmis davranis)
        """
        source = _source_of_len(MAX_FILE_SIZE)
        result = _parse(source)

        assert result is None

    # ── Görev 4b ────────────────────────────────────────────────────────────

    def test_given_source_at_exact_max_size_when_caller_only_checks_result_not_none(self):
        """
        GIVEN: Tam 500_000 karakterlik kaynak (yanlış durum (invalid state): atlanmadan parse edildi)
        WHEN : Test sadece 'result is not None' kontrolü yapıyor
        THEN : Duzeltilmis davranista None doner
        """
        source = _source_of_len(MAX_FILE_SIZE)
        result = _parse(source)

        assert result is None


# ===========================================================================
# KUSUR 2 — Dar exception tuple (MemoryError yakalanmıyor)
# ===========================================================================


class TestParseCodeExceptionHandling:

    def test_given_memory_error_from_parse_when_called_should_fail_not_crash(self):
        """
        GIVEN: ast.parse'ın MemoryError fırlattığı koşul
        WHEN : _parse_code çağrılır
        THEN : Exception dışarı sızmaz; None dönmeli
               Duzeltilmis davranis: MemoryError yakalanir
        """
        source = "def foo(): pass"

        with patch("ast.parse", side_effect=MemoryError("Out of memory")):
            result = _parse(source)
        assert result is None

    def test_given_syntax_error_when_parsed_should_return_none(self):
        """
        GIVEN: SyntaxError üreten geçersiz Python kodu
        WHEN : _parse_code çağrılır
        THEN : SyntaxError yakalanır, None döner, crash olmaz
        """
        result = _parse("def broken(:\n    pass")
        assert result is None

    def test_given_null_bytes_when_parsed_should_return_none(self):
        """
        GIVEN: Null byte içeren kaynak kodu (ast.parse → ValueError)
        WHEN : _parse_code çağrılır
        THEN : ValueError yakalanır, None döner
        """
        result = _parse("x = 1\x00")
        assert result is None


# ===========================================================================
# SINIR DEĞER TESTLERİ
# ===========================================================================


class TestParseCodeBoundaryValues:

    def test_given_empty_source_when_parsed_should_return_ast(self):
        """
        GIVEN: Boş string
        WHEN : _parse_code çağrılır
        THEN : Boş ama geçerli AST döner (ast.parse("") geçerlidir)
        """
        result = _parse("")
        assert isinstance(result, ast.AST)

    def test_given_valid_python_when_parsed_should_return_ast_module(self):
        """
        GIVEN: Geçerli Python kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : ast.Module türünde AST döner
        """
        result = _parse("def foo():\n    return 42\n")
        assert isinstance(result, ast.Module)

    def test_given_source_one_below_max_when_parsed_should_return_ast(self):
        """
        GIVEN: MAX_FILE_SIZE - 1 (499_999) karakterlik kaynak
        WHEN : _parse_code çağrılır
        THEN : AST döner — sınırın hemen altı, geçmeli
        """
        source = _source_of_len(MAX_FILE_SIZE - 1)
        assert _parse(source) is not None

    def test_given_source_one_above_max_when_parsed_should_return_none(self):
        """
        GIVEN: MAX_FILE_SIZE + 1 (500_001) karakterlik kaynak
        WHEN : _parse_code çağrılır
        THEN : None döner — her iki implementasyonda da atlanır
        """
        source = _source_of_len(MAX_FILE_SIZE + 1)
        assert _parse(source) is None

    def test_given_only_comments_when_parsed_should_return_ast(self):
        """
        GIVEN: Sadece yorum satırlarından oluşan kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : Boş gövdeli geçerli AST döner
        """
        source = "# Bu bir yorum\n# Başka yorum\n"
        result = _parse(source)
        assert isinstance(result, ast.Module)
        assert result.body == []

    def test_given_only_whitespace_when_parsed_should_return_ast(self):
        """
        GIVEN: Yalnızca boşluk ve sekme içeren kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : Geçerli (boş) AST döner
        """
        result = _parse("   \n\t  \n   ")
        assert isinstance(result, ast.AST)

    def test_given_syntax_warning_source_when_parsed_should_not_leak_warning(self):
        """
        GIVEN: SyntaxWarning üretebilecek kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : Warning dışarı sızmaz (warnings.catch_warnings bastırmalı)
        """
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _parse(r"x = '\d+'")

        syntax_warnings = [w for w in caught if issubclass(w.category, SyntaxWarning)]
        assert len(syntax_warnings) == 0, f"SyntaxWarning sızdı: {syntax_warnings}"

    def test_given_file_path_when_parse_fails_should_be_included_in_output(self, capsys):
        """
        GIVEN: Belirli bir file_path ile hatalı kaynak kodu
        WHEN : _parse_code çağrılır
        THEN : Print çıktısı file_path'i içerir (hata ayıklama için)
        """
        _parse("def broken(:", file_path="/project/my_module.py")
        captured = capsys.readouterr()
        assert "/project/my_module.py" in captured.out

    def test_given_oversized_source_when_parsed_should_log_file_path(self, capsys):
        """
        GIVEN: MAX_FILE_SIZE'ı aşan kaynak + belirli file_path
        WHEN : _parse_code çağrılır
        THEN : Print çıktısı file_path'i içerir
        """
        source = _source_of_len(MAX_FILE_SIZE + 1)
        _parse(source, file_path="/data/huge_file.py")
        captured = capsys.readouterr()
        assert "/data/huge_file.py" in captured.out


"""
TestExtractMethod / TestExtractDecorators / TestFindDependencies —
ASTAnalyzer'ın test edilmemiş üç metodu için kapsamlı test sınıfları.

Kapsam:
  - Defect / Infection / Failure analizi (1-4 arası görevler)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.analyzer import ASTAnalyzer

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def make_analyzer(
    source: str, module_name: str = "test_module", file_path: str = "test.py"
) -> ASTAnalyzer:
    return ASTAnalyzer(source_code=source, module_name=module_name, file_path=file_path)


def _first_func_node(source: str):
    """Kaynak kodundaki ilk fonksiyon/metot AST node'unu döner."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    raise ValueError("Fonksiyon bulunamadı")


def _extract(source: str, class_name=None):
    """Kaynak kodundaki ilk fonksiyonu _extract_method ile çıkarır."""
    analyzer = make_analyzer(source)
    node = _first_func_node(source)
    return analyzer._extract_method(node, class_name=class_name)


def _decorators(source: str):
    """Kaynak kodundaki ilk fonksiyonun dekoratörlerini çıkarır."""
    analyzer = make_analyzer(source)
    node = _first_func_node(source)
    return analyzer._extract_decorators(node)


def _deps(source: str):
    """Kaynak kodundaki ilk fonksiyonun bağımlılıklarını çıkarır."""
    analyzer = make_analyzer(source)
    node = _first_func_node(source)
    return analyzer._find_dependencies(node)


# ===========================================================================
# _extract_method
# ===========================================================================
#
# Analiz ve Hata Senaryoları
# ---------------------------------------------------------------------------
#
# Hata Tanımı:
#     _extract_method, parameters listesini yalnızca node.args.args üzerinden
#     oluşturur:
#
#         parameters=[arg.arg for arg in node.args.args]
#
#     Bu liste yalnızca pozisyonel parametreleri kapsar. *args (vararg) ve
#     **kwargs (kwarg) parametreleri bu listede YER ALMAZ. Böylece
#     `def foo(*args, **kwargs)` gibi bir imza için parameters=[] döner;
#     gerçek parametre bilgisi sessizce yok edilir.
#
# Tetikleyici Koşul:
#     Fonksiyonda node.args.vararg (ör. *args) veya node.args.kwarg
#     (ör. **kwargs) varken bunların `node.args.args` listesinde OLMAMASI.
#
#     → test_given_vararg_and_kwarg_when_extracted_should_include_in_parameters
#       [orijinal kodla BAŞARISIZ olmalı]


class TestExtractMethod:

    def test_given_vararg_and_kwarg_when_extracted_should_include_in_parameters(self):
        """
        GIVEN: *args ve **kwargs içeren bir fonksiyon
        WHEN : _extract_method çağrılır
        THEN : parameters listesi 'args' ve 'kwargs' adlarını da içermeli

        [orijinal kodla BAŞARISIZ olması beklenir]
        """
        source = "def foo(a, *args, **kwargs): pass"
        result = _extract(source)

        assert "args" in result.parameters, (
            "'*args' parametresi parameters listesinde bulunamadı (Bilinen Hata). "
            f"Dönen liste: {result.parameters}"
        )
        assert "kwargs" in result.parameters, (
            "'**kwargs' parametresi parameters listesinde bulunamadı (Bilinen Hata). "
            f"Dönen liste: {result.parameters}"
        )

    # -----------------------------------------------------------------------
    # Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Fonksiyonda *args ve **kwargs yoksa node.args.vararg ve
    #     node.args.kwarg None olur. Yalnızca node.args.args kullanılır →
    #     kusurlu path'e ulaşılmaz.
    #

    def test_given_only_positional_params_when_extracted_should_not_trigger_param_defect(self):
        """
        GIVEN: Yalnızca pozisyonel parametreler içeren fonksiyon (a, b, c)
        WHEN : _extract_method çağrılır
        THEN : parameters doğru döner, kusur tetiklenmez

        [kusur tetiklenmez]
        """
        source = "def foo(a, b, c): pass"
        result = _extract(source)

        assert result.parameters == ["a", "b", "c"]

    # -----------------------------------------------------------------------
    # Kusur çalışır ama yanlış durum (invalid state) olmaz
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Fonksiyonda *args var ama parameters listesini hiç kontrol
    #     etmiyorsak durum bozulur (eksik parametre) ancak gözlemlenmez.
    #     Burada daha dar bir senaryo: sadece keyword-only parametreler.
    #     node.args.args boş, node.args.kwonlyargs dolu → liste yanlış
    #     (keyword-only da eksik), ama test yalnızca uzunluğu değil adı sormasa
    #     yanlış durum (invalid state) gizlenir.
    #

    def test_given_keyword_only_param_when_extracted_only_name_checked_invalid_state_hidden(self):
        """
        GIVEN: Keyword-only parametresi olan fonksiyon (def foo(*, key))
        WHEN : _extract_method çağrılır ve yalnızca name alanı kontrol edilir
        THEN : Test geçer — keyword-only parametre kayıp ama bu kontrol görmez

        [kusur çalışır (kwonlyargs atlandı), hata yutuluyor/gizleniyor]
        """
        source = "def foo(*, key): pass"
        result = _extract(source)

        # Yüzeysel kontrol → yanlış durum (invalid state) görünmez
        assert result.name == "foo"

    # -----------------------------------------------------------------------
    # Infection var ama hata (error) gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. *args içeren fonksiyon çıkarıldığında parameters=['a'] (args
    #     eksik = yanlış durum (invalid state)). Ama test yalnızca 'a'nın var olduğunu sorgularsa
    #     assertion geçer → hata (error) görünmez.
    #

    def test_given_vararg_func_when_only_positional_param_checked_should_pass_despite_invalid_state(
        self,
    ):
        """
        GIVEN: *args içeren fonksiyon (yanlış durum (invalid state): args eksik parameters'da)
        WHEN : Yalnızca 'a' pozisyonel parametresinin varlığı kontrol edilir
        THEN : Test geçer — ama 'args' kayıp (hata yutuluyor/gizleniyor)

        [yanlış durum (invalid state) var, hata (error) yok]
        """
        source = "def foo(a, *args): pass"
        result = _extract(source)

        # Yüzeysel kontrol → yanlış durum (invalid state) görünmez
        assert "a" in result.parameters


# ===========================================================================
# SINIR DEĞER TESTLERİ — _extract_method
# ===========================================================================


class TestExtractMethodBoundaryValues:

    # --- name ---

    def test_given_function_when_extracted_should_preserve_exact_name(self):
        """
        GIVEN: 'my_function' adında bir fonksiyon
        WHEN : _extract_method çağrılır
        THEN : name alanı tam olarak 'my_function' olur
        """
        result = _extract("def my_function(): pass")
        assert result.name == "my_function"

    # --- class_name / is_method ---

    def test_given_no_class_name_when_extracted_should_set_is_method_false(self):
        """
        GIVEN: class_name=None (top-level fonksiyon)
        WHEN : _extract_method çağrılır
        THEN : is_method=False, class_name=None
        """
        result = _extract("def foo(): pass", class_name=None)
        assert result.is_method is False
        assert result.class_name is None

    def test_given_class_name_when_extracted_should_set_is_method_true(self):
        """
        GIVEN: class_name='MyClass' ile çağrılmış _extract_method
        WHEN : _extract_method çağrılır
        THEN : is_method=True, class_name='MyClass'
        """
        result = _extract("def method(self): pass", class_name="MyClass")
        assert result.is_method is True
        assert result.class_name == "MyClass"

    # --- is_async ---

    def test_given_async_function_when_extracted_should_set_is_async_true(self):
        """
        GIVEN: async def fonksiyon
        WHEN : _extract_method çağrılır
        THEN : is_async=True
        """
        result = _extract("async def fetch(): pass")
        assert result.is_async is True

    def test_given_sync_function_when_extracted_should_set_is_async_false(self):
        """
        GIVEN: Sıradan (sync) fonksiyon
        WHEN : _extract_method çağrılır
        THEN : is_async=False
        """
        result = _extract("def foo(): pass")
        assert result.is_async is False

    # --- return_type ---

    def test_given_return_annotation_when_extracted_should_capture_return_type(self):
        """
        GIVEN: -> int return tipi olan fonksiyon
        WHEN : _extract_method çağrılır
        THEN : return_type='int'
        """
        result = _extract("def foo() -> int: pass")
        assert result.return_type == "int"

    def test_given_no_return_annotation_when_extracted_should_set_return_type_none(self):
        """
        GIVEN: Return annotation'ı olmayan fonksiyon
        WHEN : _extract_method çağrılır
        THEN : return_type=None
        """
        result = _extract("def foo(): pass")
        assert result.return_type is None

    # --- parameters ---

    def test_given_no_params_when_extracted_should_return_empty_parameters(self):
        """
        GIVEN: Parametresiz fonksiyon
        WHEN : _extract_method çağrılır
        THEN : parameters=[]
        """
        result = _extract("def foo(): pass")
        assert result.parameters == []

    def test_given_typed_params_when_extracted_should_include_only_names_not_types(self):
        """
        GIVEN: Tipli parametreler (a: int, b: str)
        WHEN : _extract_method çağrılır
        THEN : parameters yalnızca isim listesi içerir, tip bilgisi değil
        """
        result = _extract("def foo(a: int, b: str): pass")
        assert result.parameters == ["a", "b"]

    # --- docstring ---

    def test_given_function_with_docstring_when_extracted_should_capture_docstring(self):
        """
        GIVEN: Docstring'e sahip fonksiyon
        WHEN : _extract_method çağrılır
        THEN : docstring alanı doğru string'i içerir
        """
        source = 'def foo():\n    """Açıklama metni."""\n    pass\n'
        result = _extract(source)
        assert result.docstring == "Açıklama metni."

    def test_given_function_without_docstring_when_extracted_should_set_docstring_none(self):
        """
        GIVEN: Docstring'siz fonksiyon
        WHEN : _extract_method çağrılır
        THEN : docstring=None
        """
        result = _extract("def foo():\n    pass\n")
        assert result.docstring is None

    # --- start_line / end_line ---

    def test_given_function_when_extracted_should_capture_correct_line_numbers(self):
        """
        GIVEN: Belirli satırlarda tanımlı fonksiyon
        WHEN : _extract_method çağrılır
        THEN : start_line ve end_line doğru satır numaralarını taşır
        """
        source = "\n\ndef foo():\n    pass\n"
        result = _extract(source)
        assert result.start_line == 3
        assert result.end_line == 4

    # --- module_name / file_path propagation ---

    def test_given_custom_module_and_path_when_extracted_should_propagate_to_model(self):
        """
        GIVEN: Özel module_name ve file_path ile oluşturulmuş analyzer
        WHEN : _extract_method çağrılır
        THEN : MethodModel bu değerleri doğru taşır
        """
        source = "def foo(): pass"
        analyzer = ASTAnalyzer(
            source_code=source, module_name="my_module", file_path="/project/my_module.py"
        )
        node = _first_func_node(source)
        result = analyzer._extract_method(node)

        assert result.module_name == "my_module"
        assert result.file_path == "/project/my_module.py"

    # --- body ---

    def test_given_function_with_body_when_extracted_should_capture_source_body(self):
        """
        GIVEN: Gövdesi olan fonksiyon
        WHEN : _extract_method çağrılır
        THEN : body alanı fonksiyonun kaynak kodunu içerir
        """
        source = "def foo():\n    return 42\n"
        result = _extract(source)
        assert "return 42" in result.body

    # --- signature ---

    def test_given_function_when_extracted_should_include_signature(self):
        """
        GIVEN: Parametreli ve return tipli fonksiyon
        WHEN : _extract_method çağrılır
        THEN : signature alanı fonksiyon imzasını içerir
        """
        result = _extract("def add(a: int, b: int) -> int: pass")
        assert "def add" in result.signature
        assert "-> int" in result.signature

    # --- dependencies ---

    def test_given_function_with_calls_when_extracted_should_capture_dependencies(self):
        """
        GIVEN: İçinde fonksiyon çağrısı olan fonksiyon
        WHEN : _extract_method çağrılır
        THEN : dependencies listesi çağrılan fonksiyon adını içerir
        """
        source = "def foo():\n    bar()\n"
        result = _extract(source)
        assert "bar" in result.dependencies

    # --- decorators ---

    def test_given_decorated_function_when_extracted_should_capture_decorators(self):
        """
        GIVEN: Dekoratörü olan fonksiyon
        WHEN : _extract_method çağrılır
        THEN : decorators listesi dekoratör adını içerir
        """
        source = "@staticmethod\ndef foo(): pass\n"
        result = _extract(source)
        assert "staticmethod" in result.decorators


# ===========================================================================
# _extract_decorators
# ===========================================================================
#
# Analiz ve Hata Senaryoları
# ---------------------------------------------------------------------------
#
# Hata Tanımı:
#     _extract_decorators, ast.unparse başarısız olduğunda şu fallback'i uygular:
#
#         if isinstance(d, ast.Name):
#             decorators.append(d.id)
#         elif isinstance(d, ast.Attribute):
#             decorators.append(d.attr)   ← KUSURLU
#         else:
#             decorators.append("unknown_decorator")
#
#     `ast.Attribute` düğümü için yalnızca `.attr` (son kısım) alınır.
#     Örnek: `@module.decorator` için yalnızca "decorator" döner; "module"
#     bilgisi sessizce yok edilir. Doğru davranış: "module.decorator" gibi
#     tam nitelikli adı döndürmek.
#
# Tetikleyici Koşul:
#     Dekoratör `ast.Attribute` tipinde olmalı (ör. @module.deco) VE
#     ast.unparse exception fırlatmalıdır. Bu koşulda yalnızca "deco" döner,
#     "module.deco" dönmez.
#
#     → test_given_attribute_decorator_when_unparse_fails_should_return_full_qualified_name
#       [orijinal kodla BAŞARISIZ olmalı]


class TestExtractDecorators:

    def test_given_attribute_decorator_when_unparse_fails_should_return_full_qualified_name(self):
        """
        GIVEN: @module.decorator şeklinde nitelikli dekoratör ve ast.unparse başarısız
        WHEN : _extract_decorators çağrılır
        THEN : Tam nitelikli ad ('module.decorator') dönmeli
               Orijinal kod yalnızca 'decorator' döndürür → BAŞARISIZ

        [orijinal kodla BAŞARISIZ olması beklenir]
        """
        source = "@module.decorator\ndef foo(): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        with patch("ast.unparse", side_effect=Exception("Simulated hata (error)")):
            result = analyzer._extract_decorators(node)

        assert len(result) == 1
        assert result[0] == "module.decorator", (
            "Nitelikli dekoratör için tam ad bekleniyor ama yalnızca son kısım döndü (Bilinen Hata). "
            f"Dönen: '{result[0]}'"
        )

    # -----------------------------------------------------------------------
    # Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. ast.unparse başarılı olursa except bloğuna hiç girilmez →
    #     fallback kodu (d.attr kusuru) hiç çalışmaz.
    #

    def test_given_simple_decorator_when_unparse_succeeds_should_not_trigger_fallback_defect(self):
        """
        GIVEN: ast.unparse'ın başarıyla çalıştığı basit dekoratör (@staticmethod)
        WHEN : _extract_decorators çağrılır
        THEN : Doğru dekoratör adı döner, fallback kusuru tetiklenmez

        [kusur tetiklenmez]
        """
        result = _decorators("@staticmethod\ndef foo(): pass\n")
        assert result == ["staticmethod"]

    # -----------------------------------------------------------------------
    # Kusur çalışır ama yanlış durum (invalid state) olmaz
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Dekoratör ast.Attribute tipinde ama `d.attr` zaten tam adı
    #     temsil ediyorsa (örn. tek segmentli attribute) kayıp olmaz.
    #     Pratikte bu zor ama ast.Name fallback'i için mümkün: ast.Name tipinde
    #     dekoratör + unparse fail → `d.id` doğru adı verir → durum bozulmaz.
    #

    def test_given_name_decorator_when_unparse_fails_should_return_correct_name_without_invalid_state(
        self,
    ):
        """
        GIVEN: @property gibi ast.Name tipinde dekoratör, ast.unparse exception fırlatıyor
        WHEN : _extract_decorators çağrılır
        THEN : d.id ile doğru ad ('property') döner, durum bozulmaz

        [Attribute kusuru çalışmaz (Name dalı), yanlış durum (invalid state) yok]
        """
        source = "@property\ndef foo(self): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        with patch("ast.unparse", side_effect=Exception("Simulated")):
            result = analyzer._extract_decorators(node)

        assert result == ["property"]

    # -----------------------------------------------------------------------
    # Infection var ama hata (error) gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. @module.deco için fallback "decorator" döndürüyor (yanlış durum (invalid state):
    #     "module" kayıp). Test yalnızca listenin boş olmadığını kontrol ederse
    #     eksikliği görmez → hata (error) yok.
    #

    def test_given_attribute_decorator_when_only_list_length_checked_invalid_state_hidden(self):
        """
        GIVEN: @module.decorator ve unparse başarısız (yanlış durum (invalid state): tam ad kayıp)
        WHEN : Yalnızca listenin boş olmadığı kontrol edilir
        THEN : Test geçer — 'module' kısmı kayıp ama bu kontrol görmez

        [yanlış durum (invalid state) var, hata (error) yok]
        """
        source = "@module.decorator\ndef foo(): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        with patch("ast.unparse", side_effect=Exception("Simulated")):
            result = analyzer._extract_decorators(node)

        # Yüzeysel kontrol → hata yutuluyor/gizleniyor
        assert len(result) == 1


# ===========================================================================
# SINIR DEĞER TESTLERİ — _extract_decorators
# ===========================================================================


class TestExtractDecoratorsBoundaryValues:

    def test_given_no_decorator_when_called_should_return_empty_list(self):
        """
        GIVEN: Dekoratörsüz fonksiyon
        WHEN : _extract_decorators çağrılır
        THEN : Boş liste döner
        """
        result = _decorators("def foo(): pass\n")
        assert result == []

    def test_given_single_simple_decorator_when_called_should_return_single_item_list(self):
        """
        GIVEN: Tek basit dekoratör (@staticmethod)
        WHEN : _extract_decorators çağrılır
        THEN : Tek elemanlı liste döner
        """
        result = _decorators("@staticmethod\ndef foo(): pass\n")
        assert len(result) == 1
        assert result[0] == "staticmethod"

    def test_given_multiple_decorators_when_called_should_return_all_in_order(self):
        """
        GIVEN: Birden fazla dekoratör (@classmethod, @property)
        WHEN : _extract_decorators çağrılır
        THEN : Tüm dekoratörler sırasıyla döner
        """
        source = "@classmethod\n@property\ndef foo(cls): pass\n"
        result = _decorators(source)
        assert len(result) == 2
        assert "classmethod" in result
        assert "property" in result

    def test_given_decorator_with_arguments_when_called_should_include_full_expression(self):
        """
        GIVEN: Argümanlı dekoratör (@pytest.mark.parametrize(...))
        WHEN : _extract_decorators çağrılır
        THEN : Tam dekoratör ifadesi string olarak döner (ast.unparse başarılıysa)
        """
        source = "@pytest.mark.parametrize('x', [1, 2])\ndef foo(x): pass\n"
        result = _decorators(source)
        assert len(result) == 1
        assert "parametrize" in result[0]

    def test_given_attribute_decorator_when_unparse_succeeds_should_return_full_dotted_name(self):
        """
        GIVEN: @module.deco şeklinde nitelikli dekoratör, ast.unparse başarılı
        WHEN : _extract_decorators çağrılır
        THEN : 'module.deco' tam adı döner
        """
        source = "@module.deco\ndef foo(): pass\n"
        result = _decorators(source)
        assert len(result) == 1
        assert "module.deco" in result[0]

    def test_given_complex_decorator_when_unparse_fails_should_return_unknown_decorator(self):
        """
        GIVEN: Ne ast.Name ne ast.Attribute olan karmaşık dekoratör, unparse başarısız
        WHEN : _extract_decorators çağrılır
        THEN : 'unknown_decorator' sentinel değeri döner, crash olmaz
        """
        source = "def foo(): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        # Yapay olarak ne Name ne Attribute olan bir dekoratör node'u ekliyoruz
        fake_decorator = ast.Constant(value=42)
        node.decorator_list = [fake_decorator]

        with patch("ast.unparse", side_effect=Exception("Simulated")):
            result = analyzer._extract_decorators(node)

        assert result == ["unknown_decorator"]

    def test_given_any_decorator_when_called_should_never_raise(self):
        """
        GIVEN: Çeşitli dekoratör senaryoları
        WHEN : _extract_decorators çağrılır
        THEN : Hiçbir durumda exception fırlatılmaz

        Temel güvenlik garantisi: her koşulda liste döner.
        """
        sources = [
            "@staticmethod\ndef foo(): pass\n",
            "@property\ndef foo(self): pass\n",
            "@classmethod\ndef foo(cls): pass\n",
            "@module.deco\ndef foo(): pass\n",
        ]
        for source in sources:
            try:
                result = _decorators(source)
                assert isinstance(result, list)
            except Exception as e:
                pytest.fail(f"Exception fırlatıldı: {e} — kaynak: {source!r}")

    def test_given_return_value_should_always_be_list_of_strings(self):
        """
        GIVEN: Dekoratörlü fonksiyon
        WHEN : _extract_decorators çağrılır
        THEN : Dönen değer her zaman list[str] tipindedir
        """
        result = _decorators("@staticmethod\n@classmethod\ndef foo(): pass\n")
        assert isinstance(result, list)
        assert all(isinstance(d, str) for d in result)


# ===========================================================================
# _find_dependencies
# ===========================================================================
#
# Analiz ve Hata Senaryoları
# ---------------------------------------------------------------------------
#
# Hata Tanımı:
#     _find_dependencies sonuç listesini `list(set(calls))` ile döndürür.
#     `set()` kullanımı tekrar eden bağımlılıkları tekilleştirir; bu tek
#     başına iyi bir davranıştır. Ancak `set`, öğe sırasını garanti etmez.
#     Çağıran kod veya testler belirli bir sıra bekliyorsa bu belirsizlik
#     non-deterministic davranışa (ve zaman zaman başarısız testlere) yol açar.
#
#     Daha kritik kusur: Fonksiyon içindeki iç içe (nested) fonksiyon
#     tanımlarının gövdesindeki çağrılar da `ast.walk` tarafından bulunur.
#     Bu; iç fonksiyonun bağımlılıklarının dış fonksiyona aitmiş gibi
#     raporlanmasına neden olur → yanlış bağımlılık atfı.
#
# Tetikleyici Koşul:
#     Dış fonksiyon içinde tanımlı bir iç fonksiyon (nested def) ve bu
#     iç fonksiyon içinde çağrılan bir fonksiyon (ör. inner_dep()) olması
#     gerekir. ast.walk tüm alt node'ları gezer ve inner_dep'i dış
#     fonksiyonun bağımlılığı olarak raporlar.
#
#     → test_given_nested_function_calls_when_finding_deps_should_not_include_inner_calls
#       [orijinal kodla BAŞARISIZ olmalı]


class TestFindDependencies:

    def test_given_nested_function_calls_when_finding_deps_should_not_include_inner_calls(self):
        """
        GIVEN: Dış fonksiyon içinde nested fonksiyon, nested gövdede inner_dep() çağrısı
        WHEN : _find_dependencies çağrılır
        THEN : inner_dep dış fonksiyonun bağımlılığı olarak raporlanmamalı
               Orijinal kod ast.walk ile tüm iç düzeyleri tarar → BAŞARISIZ

        [orijinal kodla BAŞARISIZ olması beklenir]
        """
        source = """
def outer():
    outer_dep()

    def inner():
        inner_dep()
"""
        result = _deps(source)

        assert "inner_dep" not in result, (
            "'inner_dep' nested fonksiyona ait olmasına rağmen dış bağımlılık olarak "
            f"raporlandı (Bilinen Hata). Dönen liste: {result}"
        )
        assert "outer_dep" in result

    # -----------------------------------------------------------------------
    # Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Fonksiyon içinde nested def yoksa ast.walk sadece
    #     doğrudan çağrıları bulur → kusur tetiklenmez, sonuç doğrudur.
    #

    def test_given_flat_function_with_calls_when_finding_deps_should_not_trigger_nesting_defect(
        self,
    ):
        """
        GIVEN: İçinde nested fonksiyon olmayan, doğrudan çağrılar içeren fonksiyon
        WHEN : _find_dependencies çağrılır
        THEN : Yalnızca doğrudan çağrılar döner, kusur tetiklenmez

        [kusur tetiklenmez]
        """
        source = "def foo():\n    bar()\n    baz()\n"
        result = _deps(source)

        assert "bar" in result
        assert "baz" in result

    # -----------------------------------------------------------------------
    # Kusur çalışır ama yanlış durum (invalid state) olmaz
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. Nested fonksiyon var ama iç fonksiyon herhangi bir şey
    #     çağırmıyorsa ast.walk'ın iç düzeye inmesi sonucu değiştirmez →
    #     durum bozulmaz.
    #

    def test_given_nested_function_with_no_calls_inside_when_finding_deps_should_not_infect(self):
        """
        GIVEN: Nested fonksiyon var ama iç gövdede hiç çağrı yok
        WHEN : _find_dependencies çağrılır
        THEN : Yalnızca dış çağrılar döner, durum bozulmaz

        [kusur çalışır (walk iner), yanlış durum (invalid state) yok]
        """
        source = """
def outer():
    outer_dep()

    def inner():
        pass
"""
        result = _deps(source)

        assert "outer_dep" in result
        assert "inner" not in result  # iç fonksiyon tanımı değil çağrı

    # -----------------------------------------------------------------------
    # Infection var ama hata (error) gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # Açıklama:
    #     Evet. inner_dep dış bağımlılık olarak raporlandı (yanlış durum (invalid state)). Ama
    #     test yalnızca outer_dep'in varlığını kontrol ederse inner_dep'in
    #     fazladan gelmesi görülmez → hata (error) yok.
    #

    def test_given_nested_function_when_only_outer_dep_checked_should_pass_despite_invalid_state(
        self,
    ):
        """
        GIVEN: Nested fonksiyon ve inner_dep çağrısı (yanlış durum (invalid state): inner_dep fazladan var)
        WHEN : Yalnızca outer_dep'in bağımlılıklarda olduğu kontrol edilir
        THEN : Test geçer — inner_dep fazladan var ama bu kontrol görmez

        [yanlış durum (invalid state) var, hata (error) yok]
        """
        source = """
def outer():
    outer_dep()

    def inner():
        inner_dep()
"""
        result = _deps(source)

        # Yüzeysel kontrol → hata yutuluyor/gizleniyor
        assert "outer_dep" in result


# ===========================================================================
# SINIR DEĞER TESTLERİ — _find_dependencies
# ===========================================================================


class TestFindDependenciesBoundaryValues:

    def test_given_no_calls_in_function_when_finding_deps_should_return_empty_list(self):
        """
        GIVEN: Hiç fonksiyon çağrısı olmayan fonksiyon
        WHEN : _find_dependencies çağrılır
        THEN : Boş liste döner
        """
        result = _deps("def foo():\n    pass\n")
        assert result == []

    def test_given_single_call_when_finding_deps_should_return_that_call(self):
        """
        GIVEN: Tek bir fonksiyon çağrısı (bar())
        WHEN : _find_dependencies çağrılır
        THEN : ['bar'] döner
        """
        result = _deps("def foo():\n    bar()\n")
        assert "bar" in result
        assert len(result) == 1

    def test_given_repeated_call_when_finding_deps_should_deduplicate(self):
        """
        GIVEN: Aynı fonksiyon birden fazla kez çağrılıyor (bar(), bar(), bar())
        WHEN : _find_dependencies çağrılır
        THEN : 'bar' yalnızca bir kez döner (set ile tekilleştirme)
        """
        source = "def foo():\n    bar()\n    bar()\n    bar()\n"
        result = _deps(source)

        assert result.count("bar") == 1

    def test_given_method_call_when_finding_deps_should_capture_method_name(self):
        """
        GIVEN: self.helper() gibi attribute çağrısı
        WHEN : _find_dependencies çağrılır
        THEN : 'helper' (attr kısmı) bağımlılıklarda yer alır
        """
        source = "def foo(self):\n    self.helper()\n"
        result = _deps(source)
        assert "helper" in result

    def test_given_chained_method_calls_when_finding_deps_should_capture_last_attr(self):
        """
        GIVEN: obj.sub.method() gibi zincirleme çağrı
        WHEN : _find_dependencies çağrılır
        THEN : Son attribute adı ('method') bağımlılıklarda yer alır
        """
        source = "def foo():\n    obj.sub.method()\n"
        result = _deps(source)
        assert "method" in result

    def test_given_builtin_calls_when_finding_deps_should_include_builtins(self):
        """
        GIVEN: len(), print(), range() gibi built-in çağrıları
        WHEN : _find_dependencies çağrılır
        THEN : Built-in isimleri de bağımlılık olarak raporlanır
        """
        source = "def foo(items):\n    n = len(items)\n    print(n)\n"
        result = _deps(source)
        assert "len" in result
        assert "print" in result

    def test_given_multiple_distinct_calls_when_finding_deps_should_return_all(self):
        """
        GIVEN: Farklı fonksiyon çağrıları (alpha, beta, gamma)
        WHEN : _find_dependencies çağrılır
        THEN : Tüm farklı isimler bağımlılıklarda yer alır
        """
        source = "def foo():\n    alpha()\n    beta()\n    gamma()\n"
        result = _deps(source)
        assert "alpha" in result
        assert "beta" in result
        assert "gamma" in result

    def test_given_return_value_should_always_be_list(self):
        """
        GIVEN: Herhangi bir fonksiyon
        WHEN : _find_dependencies çağrılır
        THEN : Dönüş değeri her zaman list tipindedir
        """
        result = _deps("def foo(): pass\n")
        assert isinstance(result, list)

    def test_given_call_in_conditional_when_finding_deps_should_detect_it(self):
        """
        GIVEN: if bloğu içinde yapılan çağrı
        WHEN : _find_dependencies çağrılır
        THEN : Koşullu çağrı da bağımlılık olarak tespit edilir (ast.walk tüm node'ları tarar)
        """
        source = "def foo(x):\n    if x:\n        helper()\n"
        result = _deps(source)
        assert "helper" in result

    def test_given_call_in_return_when_finding_deps_should_detect_it(self):
        """
        GIVEN: return ifadesindeki çağrı (return compute(x))
        WHEN : _find_dependencies çağrılır
        THEN : compute bağımlılıklarda yer alır
        """
        source = "def foo(x):\n    return compute(x)\n"
        result = _deps(source)
        assert "compute" in result

    def test_given_no_duplicate_entries_should_be_present_in_result(self):
        """
        GIVEN: Birden fazla çağrılan farklı fonksiyonlar
        WHEN : _find_dependencies çağrılır
        THEN : Sonuç listesinde hiçbir isim iki kez geçmez (set garantisi)
        """
        source = "def foo():\n    a()\n    b()\n    a()\n    b()\n    c()\n"
        result = _deps(source)
        assert len(result) == len(set(result)), "Sonuç listesinde tekrar eden isimler var"
