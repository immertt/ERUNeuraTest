from src.postprocess.fixers.indentation import IndentationFixer


def assert_code_compiles(code: str):
    compile(code, "<string>", "exec")


class TestIndentationFixer:
    def test_normalize_tabs_to_spaces(self):
        code = "def test_example():\n\tassert True\n"

        fixed_code = IndentationFixer().fix(code)

        assert "\t" not in fixed_code
        assert_code_compiles(fixed_code)

    def test_fix_expected_indented_block_after_function(self):
        code = "def test_add():\nassert 2 + 3 == 5\n"

        fixed_code = IndentationFixer().fix(code)

        expected = "def test_add():\n    assert 2 + 3 == 5\n"

        assert fixed_code == expected
        assert_code_compiles(fixed_code)

    def test_fix_unexpected_indent_at_top_level(self):
        # Tüm blok fazladan 4 space ile girintili
        code = "    def test_add():\n        assert 2 + 3 == 5\n"

        fixed_code = IndentationFixer().fix(code)

        # def 0'a, body 4'e çekilmeli
        expected = "def test_add():\n    assert 2 + 3 == 5\n"

        assert fixed_code == expected
        assert_code_compiles(fixed_code)

    def test_fix_unmatched_unindent(self):
        code = "def test_add():\n    result = 2 + 3\n  assert result == 5\n"

        fixed_code = IndentationFixer().fix(code)

        expected = "def test_add():\n    result = 2 + 3\n    assert result == 5\n"

        assert fixed_code == expected
        assert_code_compiles(fixed_code)

    def test_returns_valid_code_when_already_valid(self):
        code = "def test_add():\n    assert 2 + 3 == 5\n"

        fixed_code = IndentationFixer().fix(code)

        assert fixed_code == code
        assert_code_compiles(fixed_code)

    def test_normalize_mixed_tabs_and_spaces(self):
        code = "def test_example():\n\t    assert True\n"

        fixed_code = IndentationFixer().fix(code)

        assert "\t" not in fixed_code
        assert_code_compiles(fixed_code)

    def test_trailing_whitespace_is_removed(self):
        code = "def test_example():   \n    assert True    \n"

        fixed_code = IndentationFixer().fix(code)

        expected = "def test_example():\n    assert True\n"

        assert fixed_code == expected
        assert_code_compiles(fixed_code)

    def test_empty_string_returns_newline(self):
        code = ""

        fixed_code = IndentationFixer().fix(code)

        assert fixed_code == "\n"
        assert_code_compiles(fixed_code)

    def test_invalid_non_indentation_syntax_is_returned_after_normalization(self):
        code = "def test_example(:\n    assert True\n"

        fixed_code = IndentationFixer().fix(code)

        expected = "def test_example(:\n    assert True\n"

        assert fixed_code == expected

    def test_fix_nested_function_indentation(self):
        code = (
            "def test_outer():\n"
            "    def inner():\n"
            "    return True\n"
            "    assert inner() is True\n"
        )

        fixed_code = IndentationFixer().fix(code)

        expected = (
            "def test_outer():\n"
            "    def inner():\n"
            "        return True\n"
            "    assert inner() is True\n"
        )

        assert fixed_code == expected
        assert_code_compiles(fixed_code)

    def test_stops_after_max_iterations_when_not_fixable(self):
        code = (
            "def test_example():\n"
            "assert True\n"
            "if True:\n"
            "assert False\n"
        )

        fixer = IndentationFixer(max_iterations=1)
        fixed_code = fixer.fix(code)

        # En önemli şey: çökmemeli ve string dönmeli
        assert isinstance(fixed_code, str)
        assert len(fixed_code) > 0