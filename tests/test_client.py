def add_numbers(a: int, b: int) -> int:
    return a + b


def test_add_numbers() -> None:
    assert add_numbers(2, 3) == 5
    assert add_numbers(0, 0) == 0
    assert add_numbers(-1, 1) == 0


def test_add_negative_numbers() -> None:
    assert add_numbers(-5, -3) == -8
