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


