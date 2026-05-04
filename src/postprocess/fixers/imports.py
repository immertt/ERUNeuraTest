from pathlib import Path #dosya yolunu platformdan bagımsız almak için
import json #test_metadata.json dosyasını okumak için
import ast
from difflib import get_close_matches
from src.postprocess.fixers.base import BaseFixer

class ImportFixer(BaseFixer):
    """
    Eksik veya yanlış import ifadelerini düzeltmek için kullanılan
    kural tabanlı fixer sınıfı.
    """

    def __init__(self, metadata_path: str):
        self.metadata_path = Path(metadata_path) #json dosyasının path'ini alıyoruz ve Path nesnesine dönüştürüyoruz.
        self.metadata = self._load_metadata() #json dosyasını okuduk, şimdi bellege alıyoruz.

    #json dosyasını okuyuyoruz ve içindeki tüm bilgileri python dict formatına çeviriyoruz.
    def _load_metadata(self) -> dict:
        with open(self.metadata_path, "r", encoding="utf-8") as file:
            return json.load(file)


    def fix_missing_import(self, test_code: str) -> str:
        expected_import = self.metadata.get("expected_import")
        module_name = self.metadata.get("module_name")

        if not expected_import:
            return test_code

        lines = test_code.splitlines()
        lines_to_remove = set()

        try:
            tree = ast.parse(test_code)

            # expected_import zaten tam olarak var mı?
            expected_found = False

            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and node.module == module_name:
                    imported_names = [alias.name for alias in node.names]
                    imported_aliases = [alias.asname for alias in node.names]

                    # Hedef modülden gelen bütün importları kaldıracağız.
                    # Çünkü en sonunda tek normalize edilmiş import ekleyeceğiz.
                    lines_to_remove.add(node.lineno - 1)

                    if (
                        set(imported_names) == {"Calculator", "User"}
                        and all(alias is None for alias in imported_aliases)
                    ):
                        expected_found = True

            # Eğer zaten doğru import tek başına varsa, değişiklik yapma
            if expected_found and len(lines_to_remove) == 1:
                return test_code

        except SyntaxError:
            return test_code

        # Eski calculator importlarını kaldır
        fixed_lines = [
            line
            for index, line in enumerate(lines)
            if index not in lines_to_remove
        ]

        # Yeni import nereye eklenecek?
        insert_index = 0

        try:
            fixed_code = "\n".join(fixed_lines) + "\n"
            tree = ast.parse(fixed_code)

            last_import_index = None

            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_index = node.end_lineno - 1

            if last_import_index is not None:
                insert_index = last_import_index + 1

        except SyntaxError:
            for index, line in enumerate(fixed_lines):
                stripped = line.strip()

                if stripped.startswith("import ") or stripped.startswith("from "):
                    insert_index = index + 1

        fixed_lines.insert(insert_index, expected_import)

        return "\n".join(fixed_lines) + "\n"

    def fix_wrong_import(self, test_code: str) -> str:
        module_name = self.metadata.get("module_name")
        expected_import = self.metadata.get("expected_import")
        available_classes = self.metadata.get("available_imports", {}).get("classes", [])
        repair_targets = self.metadata.get("repair_targets", [])

        if not expected_import:
            return test_code

        lines = test_code.splitlines()
        lines_to_remove = set()
        replacements = {}

        # 1. Metadata'da açıkça belirtilmiş yanlış importları düzelt
        for target in repair_targets:
            wrong_import = target.get("wrong_import")
            correct_import = target.get("correct_import")

            if not wrong_import or not correct_import:
                continue

            for index, line in enumerate(lines):
                if line.strip() == wrong_import:
                    replacements[index] = correct_import

        # 2. AST ile gerçek importları incele
        try:
            tree = ast.parse(test_code)

            for node in tree.body:
                # from calculator import Calcular gibi hatalı importlar
                if isinstance(node, ast.ImportFrom):
                    if node.module == module_name:
                        imported_names = [alias.name for alias in node.names]

                        has_wrong_name = any(
                            name not in available_classes
                            for name in imported_names
                        )

                        if has_wrong_name:
                            lines_to_remove.add(node.lineno - 1)

                # import usr gibi hatalı importlar
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_name = alias.name

                        for class_name in available_classes:
                            if imported_name.lower() != class_name.lower():
                                continue

                            # örn: import user gibi bir şey varsa, sınıf importu olmalı
                            lines_to_remove.add(node.lineno - 1)

                        # usr -> User gibi typo ihtimali
                        if imported_name.lower() in ["usr", "user"]:
                            lines_to_remove.add(node.lineno - 1)

        except SyntaxError:
            # Parse edilemezse basit satır bazlı fallback
            for index, line in enumerate(lines):
                stripped = line.strip()

                if stripped.startswith(f"from {module_name} import "):
                    imported_part = stripped.replace(f"from {module_name} import ", "")
                    imported_names = [name.strip() for name in imported_part.split(",")]

                    has_wrong_name = any(
                        name not in available_classes
                        for name in imported_names
                    )

                    if has_wrong_name:
                        lines_to_remove.add(index)

                if stripped in ["import usr", "import user"]:
                    lines_to_remove.add(index)

        fixed_lines = []

        for index, line in enumerate(lines):
            if index in replacements:
                fixed_lines.append(replacements[index])
            elif index in lines_to_remove:
                continue
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines) + "\n"

    def _normalize_target_import(self, test_code: str) -> str:
        module_name = self.metadata.get("module_name")
        available_classes = self.metadata.get("available_imports", {}).get("classes", [])

        if not module_name or not available_classes:
            return test_code

        lines = test_code.splitlines()

        try:
            tree = ast.parse(test_code)
        except SyntaxError:
            return test_code

        imported_names = set()
        import_line_indexes = []

        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == module_name:
                import_line_indexes.append(node.lineno - 1)

                for alias in node.names:
                    name = alias.name

                    if name in available_classes:
                        imported_names.add(name)
                    else:
                        match = get_close_matches(
                            name,
                            available_classes,
                            n=1,
                            cutoff=0.70
                        )

                        if match:
                            imported_names.add(match[0])

        required_names = set(available_classes)
        final_names = sorted(imported_names | required_names)

        normalized_import = f"from {module_name} import {', '.join(final_names)}"

        fixed_lines = []

        for index, line in enumerate(lines):
            if index in import_line_indexes:
                continue
            fixed_lines.append(line)

        insert_index = self._find_import_insert_index("\n".join(fixed_lines))

        fixed_lines.insert(insert_index, normalized_import)

        return "\n".join(fixed_lines) + "\n"

    def _find_import_insert_index(self, code: str) -> int:
        try:
            tree = ast.parse(code)

            last_import = None
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import = node.end_lineno - 1

            return last_import + 1 if last_import is not None else 0

        except SyntaxError:
            lines = code.splitlines()
            last_import_index = -1

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    last_import_index = i

            return last_import_index + 1

    def fix(self, test_code: str) -> str:
        test_code = self.fix_wrong_import(test_code)
        test_code = self.fix_missing_import(test_code)
        test_code = self._normalize_target_import(test_code)
        return test_code