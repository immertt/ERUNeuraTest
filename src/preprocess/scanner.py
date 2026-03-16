"""
Benchmark projelerini tarayıp preprocess pipeline'ını çalıştıran modül.

benchmark/ altındaki her projeyi dolaşır, .py dosyalarını bulur,
ASTAnalyzer ile analiz eder, ComplexityCalculator ile skorlar,
MethodSelector ile 50 metot seçer ve JSONExporter ile dışa aktarır.
"""
from pathlib import Path
from typing import List

class ProjectScanner:
    
    def scan_project(self, path: str) -> List[Path]:
        """Verilen dizindeki tüm .py dosyalarını özyinelemeli listeler."""
        scan_path = Path(path)
        
        if not scan_path.exists():
            print(f"Hata: {scan_path} bulunamadı!")
            return []
        
        all_files = list(scan_path.rglob("*.py"))
        filtered = self.filter_python_files(all_files)
        
        print(f"Toplam .py dosyası: {len(all_files)}")
        print(f"Filtreleme sonrası: {len(filtered)}")
        
        return filtered
    
    def filter_python_files(self, files: List[Path]) -> List[Path]:
        """Test ve __init__ dosyalarını filtreler."""
        return [
            f for f in files
            if not f.name.startswith("test_")
            and not f.name.endswith("_test.py")
            and f.name != "__init__.py"
        ]