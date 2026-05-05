from pathlib import Path
import re

from src.postprocess.fixers.syntax import SyntaxFixer


test_file = Path("src/postprocess/faulty_test_examples/test_calculator.py")
output_file = Path("src/postprocess/faulty_test_examples/test_calculator_syntax_fixed.py")

test_code = test_file.read_text(encoding="utf-8")
fixer = SyntaxFixer()


def fix_example_block(match: re.Match) -> str:
    name = match.group("name")
    quote = match.group("quote")
    code_block = match.group("code")

    fixed_block = fixer.fix(code_block)

    return f"{name} = {quote}{fixed_block}{quote}"


pattern = (
    r'(?P<name>[A-Z0-9_]*EXAMPLE[A-Z0-9_]*)'
    r'\s*=\s*'
    r'(?P<quote>"""|\'\'\')'
    r'(?P<code>[\s\S]*?)'
    r'(?P=quote)'
)

fixed_code = re.sub(pattern, fix_example_block, test_code)

output_file.write_text(fixed_code, encoding="utf-8")

print(f"Syntax fixed test file written to: {output_file}")