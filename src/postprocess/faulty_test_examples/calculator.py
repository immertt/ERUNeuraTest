class User:
    def __init__(self, name: str):
        self.name = name


class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b

    def multiply(self, a: int, b: int) -> int:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def is_even(self, number: int) -> bool:
        return number % 2 == 0

    def get_user_name(self, user: User) -> str:
        return user.name