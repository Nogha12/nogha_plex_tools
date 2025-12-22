"""Greet command."""


def greet(name: str = "friend", count: int = 1):
    """Greet someone."""
    greeting = f"Hello, {name}!"
    for _ in range(count):
        print(greeting)
