"""
Analiz sonuçlarını JSON formatında dışa aktaran modül.

Seçilen metotları src/preprocess/output/selected_methods/ dizinine proje bazlı kaydeder.
UTF-8 encoding ve okunabilir format (indent=2) kullanır.
"""

import json
from pathlib import Path
from typing import List
from .models import MethodModel

DEFAULT_OUTPUT = Path(__file__).parent / "output" / "selected_methods"


class JSONExporter:
    """Seçilen metotları proje bazlı JSON dosyasına kaydeder."""

    def __init__(self, output_base_dir=None):
        if output_base_dir == "":
            raise ValueError("output_base_dir bos olamaz")
        try:
            if output_base_dir is None:
                self.output_base_dir = DEFAULT_OUTPUT
            elif isinstance(output_base_dir, (str, Path)):
                self.output_base_dir = Path(output_base_dir)
            else:
                raise ValueError("output_base_dir gecersiz tip")
        except (TypeError, ValueError) as exc:
            raise ValueError("output_base_dir gecersiz") from exc
        try:
            self.output_base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise OSError(f"output dizini olusturulamadi: {self.output_base_dir}") from exc

    def export(self, methods: List[MethodModel], project_name: str) -> bool:
        """Metot listesini JSON dosyasına kaydeder. Başarılıysa True döner."""
        if not methods:
            print(f"Uyarı: {project_name} için dışa aktarılacak metot bulunamadı.")
            return False

        if not isinstance(project_name, str) or project_name.strip() == "":
            raise ValueError("project_name gecersiz")
        if "/" in project_name or "\\" in project_name:
            raise ValueError("project_name path separator iceremez")

        file_path = self.output_base_dir / f"{project_name}_methods.json"

        try:
            data = []
            for method in methods:
                try:
                    item = self.format_method(method)
                    json.dumps(item)
                    data.append(item)
                except Exception as exc:
                    print(f"Uyarı: metot atlandi - {exc}")

            if not data:
                print(f"Uyarı: {project_name} için gecerli metot bulunamadı.")
                return False

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Kaydedildi: {file_path} ({len(data)} metot)")
            return True

        except Exception as e:
            print(f"Kaydetme hatasi: {e}")
            return False

    def format_method(self, method: MethodModel) -> dict:
        """MethodModel nesnesini JSON-uyumlu dict'e dönüştürür."""
        if method is None:
            raise ValueError("method bos olamaz")
        return method.to_dict()