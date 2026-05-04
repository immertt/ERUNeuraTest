import re
from src.postprocess.fixers.base import BaseFixer

class SyntaxFixer(BaseFixer):
    """
    SyntaxError durumlarını düzeltmek için kullanılan
    kural tabanlı fixer sınıfı.
    """

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.rules = [
            self._rule_missing_colon,
            self._rule_unclosed_bracket,
            self._rule_unterminated_string,
            self._rule_extra_closing_bracket,
            self._rule_assert_single_equals,
            self._rule_invalid_syntax,
        ]

    def fix(self, test_code: str) -> str:
        for _ in range(self.max_iterations):
            try:
                compile(test_code, "<test_code>", "exec")
                return test_code

            except SyntaxError as error:
                fixed_code = self._apply_syntax_rule(test_code, error)

                if fixed_code == test_code:
                    return test_code

                test_code = fixed_code

        return test_code

    def _apply_syntax_rule(self, test_code: str, error: SyntaxError) -> str:
        for rule in self.rules:
            fixed_code = rule(test_code, error)

            if fixed_code != test_code:
                return fixed_code

        return test_code

    def _rule_missing_colon(self, test_code: str, error: SyntaxError) -> str:
        if error.lineno is None:
            return test_code

        if "expected ':'" in error.msg:
            return self._fix_missing_colon(test_code, error.lineno)

        return test_code


    def _rule_unclosed_bracket(self, test_code: str, error: SyntaxError) -> str:
        if "was never closed" in error.msg:
            return self._fix_unclosed_bracket(test_code, error)

        return test_code


    def _rule_unterminated_string(self, test_code: str, error: SyntaxError) -> str:
        if error.lineno is None:
            return test_code

        if "unterminated string literal" in error.msg:
            return self._fix_unterminated_string(test_code, error.lineno)

        return test_code


    def _rule_extra_closing_bracket(self, test_code: str, error: SyntaxError) -> str:
        if error.lineno is None:
            return test_code

        if "unmatched ')'" in error.msg:
            return self._fix_extra_closing_bracket(test_code, error.lineno, ")")

        if "unmatched ']'" in error.msg:
            return self._fix_extra_closing_bracket(test_code, error.lineno, "]")

        if "unmatched '}'" in error.msg:
            return self._fix_extra_closing_bracket(test_code, error.lineno, "}")

        return test_code


    def _rule_assert_single_equals(self, test_code: str, error: SyntaxError) -> str:
        if error.lineno is None:
            return test_code

        if "cannot assign to" in error.msg:
            return self._fix_assert_single_equals(test_code, error.lineno)

        return test_code


    def _rule_invalid_syntax(self, test_code: str, error: SyntaxError) -> str:
        if error.lineno is None:
            return test_code

        if "invalid syntax" not in error.msg:
            return test_code

        fixed_code = self._fix_incomplete_assert(test_code, error.lineno)

        if fixed_code != test_code:
            return fixed_code

        fixed_code = self._fix_missing_comma_between_numbers(test_code, error.lineno)

        if fixed_code != test_code:
            return fixed_code

        return self._fix_assert_single_equals(test_code, error.lineno)

    def _fix_unclosed_bracket(self, test_code: str, error: SyntaxError) -> str:
        lines = test_code.splitlines()
        line_number = error.lineno

        if line_number is None:
            return test_code

        index = line_number - 1

        if index < 0 or index >= len(lines):
            return test_code

        line = lines[index]

        brackets = [
            ("(", ")"),
            ("[", "]"),
            ("{", "}"),
        ]

        for opening, closing in brackets:
            if line.count(opening) > line.count(closing):
                lines[index] = line.rstrip() + closing
                return "\n".join(lines) + "\n"

        return test_code

    def _fix_missing_colon(self, test_code: str, line_number: int) -> str:
        lines = test_code.splitlines()
        index = line_number - 1

        if index < 0 or index >= len(lines):
            return test_code

        line = lines[index]

        if not line.rstrip().endswith(":"):
            lines[index] = line.rstrip() + ":"

        return "\n".join(lines) + "\n"
    
    def _fix_unterminated_string(self, test_code: str, line_number: int) -> str:
        lines = test_code.splitlines()
        index = line_number - 1

        if index < 0 or index >= len(lines):
            return test_code

        line = lines[index]
        stripped = line.rstrip()

        double_quote_count = stripped.count('"')
        single_quote_count = stripped.count("'")

        if double_quote_count % 2 == 1:
            lines[index] = stripped + '"'
        elif single_quote_count % 2 == 1:
            lines[index] = stripped + "'"
        else:
            return test_code

        return "\n".join(lines) + "\n"
    
    def _fix_assert_single_equals(self, test_code: str, line_number: int) -> str:
        lines = test_code.splitlines()
        index = line_number - 1

        if index < 0 or index >= len(lines):
            return test_code

        line = lines[index]
        stripped = line.strip()

        if not stripped.startswith("assert "):
            return test_code

        if " == " in line:
            return test_code

        if " = " in line:
            lines[index] = line.replace(" = ", " == ", 1)
            return "\n".join(lines) + "\n"

        return test_code
    
    def _fix_extra_closing_bracket(
        self,
        test_code: str,
        line_number: int,
        closing_bracket: str
    ) -> str:
        lines = test_code.splitlines()
        index = line_number - 1

        if index < 0 or index >= len(lines):
            return test_code

        line = lines[index]

        bracket_pairs = {
            ")": "(",
            "]": "[",
            "}": "{",
        }

        opening_bracket = bracket_pairs.get(closing_bracket)

        if opening_bracket is None:
            return test_code

        if line.count(closing_bracket) <= line.count(opening_bracket):
            return test_code

        close_index = line.rfind(closing_bracket)

        if close_index == -1:
            return test_code

        lines[index] = line[:close_index] + line[close_index + 1:]

        return "\n".join(lines) + "\n"
    
    def _fix_incomplete_assert(self, test_code: str, line_number: int) -> str:
        lines = test_code.splitlines()

        start_index = line_number - 1

        if start_index >= len(lines):
            start_index = len(lines) - 1

        if start_index < 0:
            return test_code

        comparison_operators = ("==", "!=", ">=", "<=", ">", "<", "is", "is not", "in", "not in")

        for index in range(start_index, -1, -1):
            line = lines[index]
            stripped = line.strip()

            if not stripped.startswith("assert "):
                continue

            if stripped.endswith(comparison_operators):
                lines[index] = line.rstrip() + " None"
                return "\n".join(lines) + "\n"

            return test_code

        return test_code
    
    def _fix_missing_comma_between_numbers(self, test_code: str, line_number: int) -> str:
        lines = test_code.splitlines()
        index = line_number - 1

        if index < 0 or index >= len(lines):
            return test_code

        line = lines[index]

        fixed_line = re.sub(r"(\d)\s+(\d)", r"\1, \2", line)

        if fixed_line != line:
            lines[index] = fixed_line
            return "\n".join(lines) + "\n"

        return test_code
    
    