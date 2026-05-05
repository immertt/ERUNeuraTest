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
        # > → >= : tam 500_000 karakterlik dosya da atlanır
        if len(self.source_code) >= MAX_FILE_SIZE:
            print(f"Atlandı (çok büyük): {self.file_path}")
            return None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                return ast.parse(self.source_code)
        # Dar tuple → Exception: MemoryError gibi beklenmedik hatalar da yakalanır
        except Exception as e:
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
                    # Nested class desteği: recursive toplama
                    self._collect_class_methods(node, methods)
            except Exception as e:
                print(f"Uyarı: {self.file_path} içinde metot çıkarılamadı - {e}")
                continue
        return methods

    def _collect_class_methods(self, class_node, methods):
        """ClassDef içindeki metotları ve nested class'ları recursive toplar."""
        for item in class_node.body:
            try:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(self._extract_method(item, class_node.name))
                elif isinstance(item, ast.ClassDef):
                    self._collect_class_methods(item, methods)
            except Exception as e:
                print(f"Uyarı: {self.file_path} içinde metot çıkarılamadı - {e}")
                continue

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
            # Tüm parametre türleri: positional-only, normal, *args, keyword-only, **kwargs
            parameters=self._extract_parameters(node.args),
            dependencies=self._find_dependencies(node),
            decorators=self._extract_decorators(node),
            docstring=ast.get_docstring(node),
        )

    def _extract_parameters(self, args) -> list:
        """
        Tüm parametre türlerini sırasıyla toplar:
          posonlyargs → args → vararg (*args) → kwonlyargs → kwarg (**kwargs)
        """
        params = []
        params.extend(arg.arg for arg in args.posonlyargs)
        params.extend(arg.arg for arg in args.args)
        if args.vararg:
            params.append(args.vararg.arg)
        params.extend(arg.arg for arg in args.kwonlyargs)
        if args.kwarg:
            params.append(args.kwarg.arg)
        return params

    def _build_signature(self, node):
        """Metot imzasını tip ipuçlarıyla birlikte oluşturur."""
        try:
            args_str = ast.unparse(node.args)
        except Exception:
            args_str = "..."

        returns = ""
        if node.returns:
            ret = self._safe_unparse(node.returns)
            # ret=None/"" → _safe_unparse başarısız, return tipi var ama okunamadı → "-> ..."
            # ret="None"  → geçerli Python return tipi → "-> None"
            # ret="int"   → başarılı → "-> int"
            if ret:
                returns = f" -> {ret}"
            else:
                returns = " -> ..."

        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        return f"{prefix} {node.name}({args_str}){returns}"

    def _extract_decorators(self, node):
        """Dekoratörleri güvenli şekilde string'e çevirir."""
        decorators = []
        for d in node.decorator_list:
            try:
                decorators.append(ast.unparse(d))
            except Exception:
                if isinstance(d, ast.Name):
                    decorators.append(d.id)
                elif isinstance(d, ast.Attribute):
                    # d.attr → tam nitelikli ad: "module.decorator"
                    decorators.append(self._unparse_attribute(d))
                else:
                    decorators.append("unknown_decorator")
        return decorators

    def _unparse_attribute(self, node) -> str:
        """ast.Attribute node'unu 'a.b.c' formatına dönüştürür."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _safe_unparse(self, node):
        """
        AST node'u güvenli şekilde string'e çevirir.

        Dönüş değerleri:
          None → node=None (annotasyon yazılmamış)
          ""   → node geçerli ama unparse başarısız (sentinel — None'dan farklı)
          str  → başarılı sonuç
        """
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except Exception:
            return ""

    def _find_dependencies(self, node):
        """
        Metodun doğrudan gövdesindeki fonksiyon çağrılarını bulur.
        Nested fonksiyon, lambda ve class tanımlarının içine inmez;
        yalnızca mevcut scope'un bağımlılıklarını raporlar.
        """
        calls = []

        def collect(current):
            for child in ast.iter_child_nodes(current):
                # Nested scope → bu scope'un bağımlılıkları değil, atla
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda, ast.ClassDef)):
                    continue

                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)

                collect(child)

        collect(node)
        return list(set(calls))