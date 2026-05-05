"""
Benchmark projelerini tarayıp preprocess pipeline'ını çalıştıran modül.

benchmark/ altındaki her projeyi dolaşır, .py dosyalarını bulur,
ASTAnalyzer ile analiz eder, ComplexityCalculator ile skorlar,
MethodSelector ile 50 metot seçer ve JSONExporter ile dışa aktarır.
"""

from pathlib import Path
from typing import List
from .analyzer import ASTAnalyzer
from .complexity import ComplexityCalculator
from .selector import MethodSelector
from .exporter import JSONExporter
from .models import MethodModel

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_BENCHMARK = PROJECT_ROOT / "benchmark"


class ProjectScanner:
    """Benchmark dizinini tarar ve preprocess pipeline'ını çalıştırır."""

    def __init__(self, benchmark_dir=None):
        if benchmark_dir is None:
            self.benchmark_dir = DEFAULT_BENCHMARK
        elif isinstance(benchmark_dir, (str, Path)):
            self.benchmark_dir = Path(benchmark_dir)
        else:
            raise ValueError("benchmark_dir gecersiz tip")
        self.complexity_calc = ComplexityCalculator()
        self.selector = MethodSelector(limit=50)
        self.exporter = JSONExporter()

    def run(self):
        """Tüm projeleri tarar ve her biri için pipeline'ı çalıştırır."""
        print(f"Tarama dizini: {self.benchmark_dir.absolute()}")

        if not self.benchmark_dir.exists():
            print(f"Hata: {self.benchmark_dir} klasörü bulunamadı!")
            return

        try:
            projects = [d for d in self.benchmark_dir.iterdir() if d.is_dir()]
        except PermissionError as exc:
            print(f"Hata: {self.benchmark_dir} okunamadi - {exc}")
            return
        print(f"Bulunan projeler: {[p.name for p in projects]}")

        for project_path in projects:
            try:
                self._process_project(project_path)
            except Exception as exc:
                print(f"Hata: {project_path} islenemedi - {exc}")
                continue

    def _process_project(self, project_path: Path):
        """Tek bir projeyi analiz eder, seçer ve dışa aktarır."""
        project_name = project_path.name
        print(f"İşleniyor: {project_name}")

        methods = self._scan_files(project_path)

        if not methods:
            print(f"Uyarı: {project_name} içinde metot bulunamadı.")
            return

        processed_methods = []
        for method in methods:
            try:
                method.complexity = self.complexity_calc.calculate(method.body)
                processed_methods.append(method)
            except Exception as exc:
                print(f"Uyarı: {project_name} icin complexity hesaplanamadi - {exc}")
                continue

        if not processed_methods:
            print(f"Uyarı: {project_name} icin gecerli metot bulunamadi.")
            return

        try:
            selected = self.selector.select_best_methods(processed_methods)
        except Exception as exc:
            print(f"Hata: {project_name} secim hatasi - {exc}")
            return

        if not selected:
            print(f"Uyarı: {project_name} icin secilecek metot bulunamadi.")
            return

        try:
            self.exporter.export(selected, project_name)
        except Exception as exc:
            print(f"Hata: {project_name} export hatasi - {exc}")

    def _scan_files(self, project_path: Path) -> List[MethodModel]:
        """Projedeki tüm .py dosyalarını tarar ve metotları çıkarır."""
        methods = []

        for file_path in project_path.rglob("*.py"):
            try:
                if "__pycache__" in file_path.parts:
                    continue
                code = file_path.read_text(encoding="utf-8")
                analyzer = ASTAnalyzer(
                    source_code=code,
                    module_name=file_path.stem,
                    file_path=str(file_path),
                )
                methods.extend(analyzer.get_methods_info())
            except UnicodeDecodeError as e:
                print(f"Hata: {file_path} encoding okunamadi - {e}")
                continue
            except Exception as e:
                print(f"Hata: {file_path} okunamadı - {e}")
                continue

        return methods
