class User:
    def __init__(self, name: str):
        self.name = name

def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b

def multiply(a: int, b: int) -> int:
    return a * b

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def is_even(number: int) -> bool:
    return number % 2 == 0

def get_user_name(user: User) -> str:
    return user.name