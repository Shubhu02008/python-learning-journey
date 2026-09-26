"""Regression tests for the calculator operations."""

import unittest

from calculator import add, calculate, divide, multiply, subtract


class CalculatorTests(unittest.TestCase):
    def test_basic_operations(self) -> None:
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(subtract(2, 3), -1)
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(divide(9, 3), 3)

    def test_calculate_accepts_symbols_and_words(self) -> None:
        self.assertEqual(calculate(10, " + ", 5), 15)
        self.assertEqual(calculate(10, "subtract", 5), 5)
        self.assertEqual(calculate(10, "MULTIPLY", 5), 50)
        self.assertEqual(calculate(10, "/", 5), 2)

    def test_division_by_zero_is_not_silently_accepted(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            divide(1, 0)

    def test_invalid_input_has_a_clear_error(self) -> None:
        with self.assertRaises(TypeError):
            add("2", 3)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            calculate(2, "%", 1)


if __name__ == "__main__":
    unittest.main()
