"""
AST tabanlı kod analiz modülü.

Python kaynak kodunu ast modülü ile parse eder, sınıf içi metotları
ve bağımsız fonksiyonları tespit ederek MethodModel nesnelerine dönüştürür.
Her metot için imza, gövde, parametreler, bağımlılıklar ve dekoratörler çıkarılır.
"""

import ast
import warnings
from dataclasses import dataclass
from .models import MethodModel

MAX_FILE_SIZE = 500_000


@dataclass
class ASTAnalyzer:
    """Python kaynak kodunu AST ile parse ederek metot bilgilerini çıkarır."""
    source_code: str
    module_name: str = "unknown"
    file_path: str = "unknown"     

    def _parse_code(self):
        if len(self.source_code) > MAX_FILE_SIZE:
           print(f"Atlandı (çok büyük): {self.file_path}")
           return None
        try:
           with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                return ast.parse(self.source_code)
        except (SyntaxError, ValueError, RecursionError) as e:
            print(f"Parse hatası: {self.file_path} - {e}")
            return None

    def get_methods_info(self):
        """Tüm fonksiyon ve sınıf metotlarını bulur, MethodModel listesi döner."""
        methods = []
        tree = self._parse_code()
        if not tree:
            return methods

        for node in tree.body:
            try:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(self._extract_method(node))
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(self._extract_method(item, node.name))
            except Exception as e:
                print(f"Uyarı: {self.file_path} içinde metot çıkarılamadı - {e}")
                continue
        return methods

    def _extract_method(self, node, class_name=None):
        """Tek bir AST düğümünden MethodModel oluşturur."""
        return MethodModel(
            name=node.name,
            signature=self._build_signature(node),
            body=ast.get_source_segment(self.source_code, node) or "",
            module_name=self.module_name,
            file_path=self.file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            class_name=class_name,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=class_name is not None,
            return_type=self._safe_unparse(node.returns),
            parameters=[arg.arg for arg in node.args.args],
            dependencies=self._find_dependencies(node),
            decorators=self._extract_decorators(node),
            docstring=ast.get_docstring(node),
        )

    def _build_signature(self, node):
        """Metot imzasını tip ipuçlarıyla birlikte oluşturur."""
        try:
            args_str = ast.unparse(node.args)
        except Exception:
            args_str = "..."
        
        returns = ""
        if node.returns:
            ret = self._safe_unparse(node.returns)
            if ret:
                returns = f" -> {ret}"
        
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        return f"{prefix} {node.name}({args_str}){returns}"

    def _extract_decorators(self, node):
        """Dekoratörleri güvenli şekilde string'e çevirir."""
        decorators = []
        for d in node.decorator_list:
            try:
                decorators.append(ast.unparse(d))
            except Exception:
                # Karmaşık dekoratörler çözülemezse adını al
                if isinstance(d, ast.Name):
                    decorators.append(d.id)
                elif isinstance(d, ast.Attribute):
                    decorators.append(d.attr)
                else:
                    decorators.append("unknown_decorator")
        return decorators

    def _safe_unparse(self, node):
        """AST node'u güvenli şekilde string'e çevirir."""
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except Exception:
            return None

    def _find_dependencies(self, node):
        """Metot içinde çağrılan fonksiyon adlarını bulur (mocking için)."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))


"""
TestExtractMethod / TestExtractDecorators / TestFindDependencies —
ASTAnalyzer'ın test edilmemiş üç metodu için kapsamlı test sınıfları.

Kapsam:
  - Defect / Infection / Failure analizi (1-4 arası görevler)
  - Sınır değer testleri
  - Davranış odaklı, given/when/then + should isimlendirmesi
"""

import ast
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocess.analyzer import ASTAnalyzer


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def make_analyzer(source: str, module_name: str = "test_module", file_path: str = "test.py") -> ASTAnalyzer:
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
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
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
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     Fonksiyonda node.args.vararg (ör. *args) veya node.args.kwarg
#     (ör. **kwargs) varken bunların `node.args.args` listesinde OLMAMASI.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_vararg_and_kwarg_when_extracted_should_include_in_parameters
#       [GÖREV 1c — orijinal kodla BAŞARISIZ olmalı]

class TestExtractMethod:

    def test_given_vararg_and_kwarg_when_extracted_should_include_in_parameters(self):
        """
        GIVEN: *args ve **kwargs içeren bir fonksiyon
        WHEN : _extract_method çağrılır
        THEN : parameters listesi 'args' ve 'kwargs' adlarını da içermeli

        [GÖREV 1c — orijinal kodla BAŞARISIZ olması beklenir]
        """
        source = "def foo(a, *args, **kwargs): pass"
        result = _extract(source)

        assert "args" in result.parameters, (
            "'*args' parametresi parameters listesinde bulunamadı — KUSUR aktif. "
            f"Dönen liste: {result.parameters}"
        )
        assert "kwargs" in result.parameters, (
            "'**kwargs' parametresi parameters listesinde bulunamadı — KUSUR aktif. "
            f"Dönen liste: {result.parameters}"
        )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Fonksiyonda *args ve **kwargs yoksa node.args.vararg ve
    #     node.args.kwarg None olur. Yalnızca node.args.args kullanılır →
    #     kusurlu path'e ulaşılmaz.
    #
    # (b) Test: yalnızca pozisyonel parametreler içeren fonksiyon

    def test_given_only_positional_params_when_extracted_should_not_trigger_param_defect(self):
        """
        GIVEN: Yalnızca pozisyonel parametreler içeren fonksiyon (a, b, c)
        WHEN : _extract_method çağrılır
        THEN : parameters doğru döner, kusur tetiklenmez

        [GÖREV 2b — kusur tetiklenmez]
        """
        source = "def foo(a, b, c): pass"
        result = _extract(source)

        assert result.parameters == ["a", "b", "c"]

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Fonksiyonda *args var ama parameters listesini hiç kontrol
    #     etmiyorsak durum bozulur (eksik parametre) ancak gözlemlenmez.
    #     Burada daha dar bir senaryo: sadece keyword-only parametreler.
    #     node.args.args boş, node.args.kwonlyargs dolu → liste yanlış
    #     (keyword-only da eksik), ama test yalnızca uzunluğu değil adı sormasa
    #     infection gizlenir.
    #
    # (b) Test: keyword-only parametre, yalnızca `name` alanı kontrol ediliyor

    def test_given_keyword_only_param_when_extracted_only_name_checked_infection_hidden(self):
        """
        GIVEN: Keyword-only parametresi olan fonksiyon (def foo(*, key))
        WHEN : _extract_method çağrılır ve yalnızca name alanı kontrol edilir
        THEN : Test geçer — keyword-only parametre kayıp ama bu kontrol görmez

        [GÖREV 3b — kusur çalışır (kwonlyargs atlandı), infection gizleniyor]
        """
        source = "def foo(*, key): pass"
        result = _extract(source)

        # Yüzeysel kontrol → infection görünmez
        assert result.name == "foo"

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. *args içeren fonksiyon çıkarıldığında parameters=['a'] (args
    #     eksik = infection). Ama test yalnızca 'a'nın var olduğunu sorgularsa
    #     assertion geçer → failure görünmez.
    #
    # (b) Test: sadece mevcut parametreyi kontrol et

    def test_given_vararg_func_when_only_positional_param_checked_should_pass_despite_infection(self):
        """
        GIVEN: *args içeren fonksiyon (infection: args eksik parameters'da)
        WHEN : Yalnızca 'a' pozisyonel parametresinin varlığı kontrol edilir
        THEN : Test geçer — ama 'args' kayıp (infection gizleniyor)

        [GÖREV 4b — infection var, failure yok]
        """
        source = "def foo(a, *args): pass"
        result = _extract(source)

        # Yüzeysel kontrol → infection görünmez
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
            source_code=source,
            module_name="my_module",
            file_path="/project/my_module.py"
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
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
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
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     Dekoratör `ast.Attribute` tipinde olmalı (ör. @module.deco) VE
#     ast.unparse exception fırlatmalıdır. Bu koşulda yalnızca "deco" döner,
#     "module.deco" dönmez.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_attribute_decorator_when_unparse_fails_should_return_full_qualified_name
#       [GÖREV 1c — orijinal kodla BAŞARISIZ olmalı]

class TestExtractDecorators:

    def test_given_attribute_decorator_when_unparse_fails_should_return_full_qualified_name(self):
        """
        GIVEN: @module.decorator şeklinde nitelikli dekoratör ve ast.unparse başarısız
        WHEN : _extract_decorators çağrılır
        THEN : Tam nitelikli ad ('module.decorator') dönmeli
               Orijinal kod yalnızca 'decorator' döndürür → BAŞARISIZ

        [GÖREV 1c — orijinal kodla BAŞARISIZ olması beklenir]
        """
        source = "@module.decorator\ndef foo(): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        with patch("ast.unparse", side_effect=Exception("Simulated failure")):
            result = analyzer._extract_decorators(node)

        assert len(result) == 1
        assert result[0] == "module.decorator", (
            "Nitelikli dekoratör için tam ad bekleniyor ama yalnızca son kısım döndü — KUSUR aktif. "
            f"Dönen: '{result[0]}'"
        )

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. ast.unparse başarılı olursa except bloğuna hiç girilmez →
    #     fallback kodu (d.attr kusuru) hiç çalışmaz.
    #
    # (b) Test: ast.unparse'ın başarıyla çalıştığı basit dekoratör

    def test_given_simple_decorator_when_unparse_succeeds_should_not_trigger_fallback_defect(self):
        """
        GIVEN: ast.unparse'ın başarıyla çalıştığı basit dekoratör (@staticmethod)
        WHEN : _extract_decorators çağrılır
        THEN : Doğru dekoratör adı döner, fallback kusuru tetiklenmez

        [GÖREV 2b — kusur tetiklenmez]
        """
        result = _decorators("@staticmethod\ndef foo(): pass\n")
        assert result == ["staticmethod"]

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Dekoratör ast.Attribute tipinde ama `d.attr` zaten tam adı
    #     temsil ediyorsa (örn. tek segmentli attribute) kayıp olmaz.
    #     Pratikte bu zor ama ast.Name fallback'i için mümkün: ast.Name tipinde
    #     dekoratör + unparse fail → `d.id` doğru adı verir → durum bozulmaz.
    #
    # (b) Test: ast.Name tipinde dekoratör, unparse başarısız → d.id doğru sonuç

    def test_given_name_decorator_when_unparse_fails_should_return_correct_name_without_infection(self):
        """
        GIVEN: @property gibi ast.Name tipinde dekoratör, ast.unparse exception fırlatıyor
        WHEN : _extract_decorators çağrılır
        THEN : d.id ile doğru ad ('property') döner, durum bozulmaz

        [GÖREV 3b — Attribute kusuru çalışmaz (Name dalı), infection yok]
        """
        source = "@property\ndef foo(self): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        with patch("ast.unparse", side_effect=Exception("Simulated")):
            result = analyzer._extract_decorators(node)

        assert result == ["property"]

    # -----------------------------------------------------------------------
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. @module.deco için fallback "decorator" döndürüyor (infection:
    #     "module" kayıp). Test yalnızca listenin boş olmadığını kontrol ederse
    #     eksikliği görmez → failure yok.
    #
    # (b) Test: yalnızca uzunluk kontrol et

    def test_given_attribute_decorator_when_only_list_length_checked_infection_hidden(self):
        """
        GIVEN: @module.decorator ve unparse başarısız (infection: tam ad kayıp)
        WHEN : Yalnızca listenin boş olmadığı kontrol edilir
        THEN : Test geçer — 'module' kısmı kayıp ama bu kontrol görmez

        [GÖREV 4b — infection var, failure yok]
        """
        source = "@module.decorator\ndef foo(): pass\n"
        analyzer = make_analyzer(source)
        node = _first_func_node(source)

        with patch("ast.unparse", side_effect=Exception("Simulated")):
            result = analyzer._extract_decorators(node)

        # Yüzeysel kontrol → infection gizleniyor
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
# ══════════════════════════════════════════════════════════════════════════
# KUSUR ANALİZİ
# ══════════════════════════════════════════════════════════════════════════
#
# (a) KUSUR NEDİR VE NEREDE?
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
# (b) BAŞARISIZLIĞA NEDEN OLAN KOŞUL
#     Dış fonksiyon içinde tanımlı bir iç fonksiyon (nested def) ve bu
#     iç fonksiyon içinde çağrılan bir fonksiyon (ör. inner_dep()) olması
#     gerekir. ast.walk tüm alt node'ları gezer ve inner_dep'i dış
#     fonksiyonun bağımlılığı olarak raporlar.
#
# (c) BAŞARISIZLIĞI GÖSTEREN TEST
#     → test_given_nested_function_calls_when_finding_deps_should_not_include_inner_calls
#       [GÖREV 1c — orijinal kodla BAŞARISIZ olmalı]

class TestFindDependencies:

    def test_given_nested_function_calls_when_finding_deps_should_not_include_inner_calls(self):
        """
        GIVEN: Dış fonksiyon içinde nested fonksiyon, nested gövdede inner_dep() çağrısı
        WHEN : _find_dependencies çağrılır
        THEN : inner_dep dış fonksiyonun bağımlılığı olarak raporlanmamalı
               Orijinal kod ast.walk ile tüm iç düzeyleri tarar → BAŞARISIZ

        [GÖREV 1c — orijinal kodla BAŞARISIZ olması beklenir]
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
            f"raporlandı — KUSUR aktif. Dönen liste: {result}"
        )
        assert "outer_dep" in result

    # -----------------------------------------------------------------------
    # GÖREV 2b — Kusur tetiklenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Fonksiyon içinde nested def yoksa ast.walk sadece
    #     doğrudan çağrıları bulur → kusur tetiklenmez, sonuç doğrudur.
    #
    # (b) Test: nested fonksiyon olmayan düz fonksiyon

    def test_given_flat_function_with_calls_when_finding_deps_should_not_trigger_nesting_defect(self):
        """
        GIVEN: İçinde nested fonksiyon olmayan, doğrudan çağrılar içeren fonksiyon
        WHEN : _find_dependencies çağrılır
        THEN : Yalnızca doğrudan çağrılar döner, kusur tetiklenmez

        [GÖREV 2b — kusur tetiklenmez]
        """
        source = "def foo():\n    bar()\n    baz()\n"
        result = _deps(source)

        assert "bar" in result
        assert "baz" in result

    # -----------------------------------------------------------------------
    # GÖREV 3b — Kusur çalışır ama infection olmaz
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. Nested fonksiyon var ama iç fonksiyon herhangi bir şey
    #     çağırmıyorsa ast.walk'ın iç düzeye inmesi sonucu değiştirmez →
    #     durum bozulmaz.
    #
    # (b) Test: nested fonksiyon var ama iç fonksiyon içinde çağrı yok

    def test_given_nested_function_with_no_calls_inside_when_finding_deps_should_not_infect(self):
        """
        GIVEN: Nested fonksiyon var ama iç gövdede hiç çağrı yok
        WHEN : _find_dependencies çağrılır
        THEN : Yalnızca dış çağrılar döner, durum bozulmaz

        [GÖREV 3b — kusur çalışır (walk iner), infection yok]
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
    # GÖREV 4b — Infection var ama failure gözlemlenmez
    # -----------------------------------------------------------------------
    #
    # (a) Mümkün mü?
    #     Evet. inner_dep dış bağımlılık olarak raporlandı (infection). Ama
    #     test yalnızca outer_dep'in varlığını kontrol ederse inner_dep'in
    #     fazladan gelmesi görülmez → failure yok.
    #
    # (b) Test: yalnızca outer_dep'i kontrol et

    def test_given_nested_function_when_only_outer_dep_checked_should_pass_despite_infection(self):
        """
        GIVEN: Nested fonksiyon ve inner_dep çağrısı (infection: inner_dep fazladan var)
        WHEN : Yalnızca outer_dep'in bağımlılıklarda olduğu kontrol edilir
        THEN : Test geçer — inner_dep fazladan var ama bu kontrol görmez

        [GÖREV 4b — infection var, failure yok]
        """
        source = """
def outer():
    outer_dep()

    def inner():
        inner_dep()
"""
        result = _deps(source)

        # Yüzeysel kontrol → infection gizleniyor
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