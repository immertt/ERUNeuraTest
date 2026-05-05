from src.postprocess.fixers.syntax import SyntaxFixer


def run_case(name: str, broken_code: str, expected_code: str):
    fixer = SyntaxFixer()
    fixed_code = fixer.fix(broken_code)

    print(f"\n=== {name} ===")

    if fixed_code.strip() == expected_code.strip():
        print("PASSED")
    else:
        print("FAILED")
        print("EXPECTED:")
        print(expected_code)
        print("GOT:")
        print(fixed_code)


run_case(
    "missing colon",
    """
def test_add(calculator)
    assert calculator.add(2, 3) == 5
""",
    """
def test_add(calculator):
    assert calculator.add(2, 3) == 5
"""
)

run_case(
    "unclosed parenthesis",
    """
def test_unclosed_parenthesis(calculator):
    assert calculator.add(2, 3 == 5
""",
    """
def test_unclosed_parenthesis(calculator):
    assert calculator.add(2, 3 == 5)
"""
)

run_case(
    "unterminated string literal",
    """
def test_unterminated_string():
    name = "Mert
    assert name == "Mert"
""",
    """
def test_unterminated_string():
    name = "Mert"
    assert name == "Mert"
"""
)

run_case(
    "assert single equals",
    """
def test_assert_single_equals(calculator):
    assert calculator.add(2, 3) = 5
""",
    """
def test_assert_single_equals(calculator):
    assert calculator.add(2, 3) == 5
"""
)

run_case(
    "extra closing parenthesis",
    """
def test_extra_parenthesis(calculator):
    assert calculator.add(2, 3)) == 5
""",
    """
def test_extra_parenthesis(calculator):
    assert calculator.add(2, 3) == 5
"""
)

run_case(
    "incomplete assert",
    """
def test_incomplete_assert(calculator):
    assert calculator.add(2, 3) ==
""",
    """
def test_incomplete_assert(calculator):
    assert calculator.add(2, 3) == None
"""
)

run_case(
    "missing comma between numbers",
    """
def test_missing_comma(calculator):
    result = calculator.add(2 3)
    assert result == 5
""",
    """
def test_missing_comma(calculator):
    result = calculator.add(2, 3)
    assert result == 5
"""
)

run_case(
    "extra closing square bracket",
    """
def test_extra_square_bracket():
    values = [1, 2, 3]]
    assert values == [1, 2, 3]
""",
    """
def test_extra_square_bracket():
    values = [1, 2, 3]
    assert values == [1, 2, 3]
"""
)

run_case(
    "extra closing curly bracket",
    """
def test_extra_curly_bracket():
    data = {"name": "Mert"}}
    assert data["name"] == "Mert"
""",
    """
def test_extra_curly_bracket():
    data = {"name": "Mert"}
    assert data["name"] == "Mert"
"""
)

run_case(
    "incomplete greater than assert",
    """
def test_incomplete_greater_than(calculator):
    assert calculator.add(2, 3) >
""",
    """
def test_incomplete_greater_than(calculator):
    assert calculator.add(2, 3) > None
"""
)

run_case(
    "incomplete not equal assert",
    """
def test_incomplete_not_equal(calculator):
    assert calculator.add(2, 3) !=
""",
    """
def test_incomplete_not_equal(calculator):
    assert calculator.add(2, 3) != None
"""
)