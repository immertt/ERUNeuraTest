from pathlib import Path

from src.postprocess.fixers.imports import ImportFixer


test_file = Path("src/postprocess/faulty_test_examples/test_calculator.py")
metadata_file = Path("src/postprocess/faulty_test_examples/test_metadata.json")
output_file = Path("src/postprocess/faulty_test_examples/test_calculator_import_fixed.py")

test_code = test_file.read_text(encoding="utf-8")

fixer = ImportFixer(str(metadata_file))
fixed_code = fixer.fix(test_code)

output_file.write_text(fixed_code, encoding="utf-8")

print(f"Fixed test file written to: {output_file}")