import json
from pathlib import Path

from src.postprocess.fixers.imports import ImportFixer


def create_metadata_file(tmp_path: Path, metadata: dict) -> Path:
    metadata_path = tmp_path / "test_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata),
        encoding="utf-8"
    )
    return metadata_path


def test_fix_missing_import_adds_expected_import(tmp_path):
    metadata = {
        "module_name": "calculator",
        "expected_import": "from calculator import Calculator, User",
        "available_imports": {
            "classes": ["Calculator", "User"]
        }
    }

    metadata_path = create_metadata_file(tmp_path, metadata)
    fixer = ImportFixer(str(metadata_path))

    test_code = """
def test_add():
    calculator = Calculator()
    assert calculator.add(2, 3) == 5
""".strip()

    fixed_code = fixer.fix_missing_import(test_code)

    assert "from calculator import Calculator, User" in fixed_code


def test_fix_missing_import_does_not_duplicate_existing_import(tmp_path):
    metadata = {
        "module_name": "calculator",
        "expected_import": "from calculator import Calculator, User",
        "available_imports": {
            "classes": ["Calculator", "User"]
        }
    }

    metadata_path = create_metadata_file(tmp_path, metadata)
    fixer = ImportFixer(str(metadata_path))

    test_code = """
from calculator import Calculator, User

def test_add():
    calculator = Calculator()
    assert calculator.add(2, 3) == 5
""".strip()

    fixed_code = fixer.fix_missing_import(test_code)

    assert fixed_code.count("from calculator import Calculator, User") == 1


def test_fix_wrong_import_replaces_metadata_wrong_import(tmp_path):
    metadata = {
        "module_name": "calculator",
        "expected_import": "from calculator import Calculator, User",
        "available_imports": {
            "classes": ["Calculator", "User"]
        },
        "repair_targets": [
            {
                "wrong_import": "from wrong_calculator import Calculator",
                "correct_import": "from calculator import Calculator, User"
            }
        ]
    }

    metadata_path = create_metadata_file(tmp_path, metadata)
    fixer = ImportFixer(str(metadata_path))

    test_code = """
from wrong_calculator import Calculator

def test_add():
    calculator = Calculator()
    assert calculator.add(2, 3) == 5
""".strip()

    fixed_code = fixer.fix_wrong_import(test_code)

    assert "from calculator import Calculator, User" in fixed_code
    assert "from wrong_calculator import Calculator" not in fixed_code


def test_fix_wrong_import_removes_invalid_import_name_from_target_module(tmp_path):
    metadata = {
        "module_name": "calculator",
        "expected_import": "from calculator import Calculator, User",
        "available_imports": {
            "classes": ["Calculator", "User"]
        }
    }

    metadata_path = create_metadata_file(tmp_path, metadata)
    fixer = ImportFixer(str(metadata_path))

    test_code = """
from calculator import Calcular

def test_add():
    calculator = Calculator()
    assert calculator.add(2, 3) == 5
""".strip()

    fixed_code = fixer.fix_wrong_import(test_code)

    assert "from calculator import Calcular" not in fixed_code


def test_fix_normalizes_wrong_import_to_expected_import(tmp_path):
    metadata = {
        "module_name": "calculator",
        "expected_import": "from calculator import Calculator, User",
        "available_imports": {
            "classes": ["Calculator", "User"]
        }
    }

    metadata_path = create_metadata_file(tmp_path, metadata)
    fixer = ImportFixer(str(metadata_path))

    test_code = """
from calculator import Calcular

def test_add():
    calculator = Calculator()
    assert calculator.add(2, 3) == 5
""".strip()

    fixed_code = fixer.fix(test_code)

    assert "from calculator import Calculator, User" in fixed_code
    assert "from calculator import Calcular" not in fixed_code
    assert fixed_code.count("from calculator import Calculator, User") == 1