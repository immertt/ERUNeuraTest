from src.postprocess.fixers.syntax import SyntaxFixer


def assert_valid_python_code(code: str):
    compile(code, "<test_code>", "exec")


def test_fix_missing_colon_in_function_definition():
    fixer = SyntaxFixer()

    broken_code = """
def test_add()
    assert 2 + 3 == 5
""".strip()

    fixed_code = fixer.fix(broken_code)

    assert "def test_add():" in fixed_code
    assert_valid_python_code(fixed_code)


def test_fix_unclosed_parenthesis():
    fixer = SyntaxFixer()

    broken_code = """
def test_add():
    assert (2 + 3 == 5
""".strip()

    fixed_code = fixer.fix(broken_code)

    assert_valid_python_code(fixed_code)


def test_fix_unterminated_string_literal():
    fixer = SyntaxFixer()

    broken_code = '''
def test_name():
    name = "Mert
'''.strip()

    fixed_code = fixer.fix(broken_code)

    assert_valid_python_code(fixed_code)
    assert 'name = "Mert"' in fixed_code


def test_fix_assert_single_equals_to_double_equals():
    fixer = SyntaxFixer()

    broken_code = """
def test_add():
    assert 2 + 3 = 5
""".strip()

    fixed_code = fixer.fix(broken_code)

    assert "assert 2 + 3 == 5" in fixed_code
    assert_valid_python_code(fixed_code)


def test_fix_extra_closing_parenthesis():
    fixer = SyntaxFixer()

    broken_code = """
def test_add():
    assert (2 + 3)) == 5
""".strip()

    fixed_code = fixer.fix(broken_code)

    assert "assert (2 + 3) == 5" in fixed_code
    assert_valid_python_code(fixed_code)


def test_fix_incomplete_assert_adds_none():
    fixer = SyntaxFixer()

    broken_code = """
def test_add():
    assert 2 + 3 ==
""".strip()

    fixed_code = fixer.fix(broken_code)
    
    # TODO: improve incomplete assert handling (use 'is None' instead of '== None')
    assert "assert 2 + 3 == None" in fixed_code 
    assert_valid_python_code(fixed_code)


def test_does_not_modify_valid_code():
    fixer = SyntaxFixer()

    valid_code = """
def test_add():
    assert 2 + 3 == 5
""".strip()

    fixed_code = fixer.fix(valid_code)

    assert fixed_code == valid_code or fixed_code.strip() == valid_code.strip()


def test_multiple_syntax_errors():
    fixer = SyntaxFixer()

    broken_code = """
def test_add()
    assert (2 + 3 = 5
""".strip()

    fixed_code = fixer.fix(broken_code)

    assert_valid_python_code(fixed_code)