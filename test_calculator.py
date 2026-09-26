import math
import unittest

from calculator import CalculationError, CalculatorEngine, display_number


class CalculatorEngineTests(unittest.TestCase):
    def test_arithmetic_constants_and_answer(self):
        engine = CalculatorEngine()
        self.assertEqual(engine.evaluate("2 + 3 * 4"), 14)
        self.assertAlmostEqual(engine.evaluate("pi"), math.pi)
        self.assertAlmostEqual(engine.evaluate("ans + 1"), math.pi + 1)

    def test_scientific_and_degree_functions(self):
        engine = CalculatorEngine(degrees=True)
        self.assertAlmostEqual(engine.evaluate("sin(30)"), 0.5)
        self.assertEqual(engine.evaluate("fact(5) + sqrt(9)"), 123)

    def test_graph_variable_and_unsafe_input_are_handled(self):
        engine = CalculatorEngine()
        self.assertEqual(engine.evaluate("2x + 1", x=4), 9)
        with self.assertRaises(CalculationError):
            engine.evaluate("__import__('os').system('bad')")

    def test_display_number(self):
        self.assertEqual(display_number(4.0), "4")
        self.assertEqual(display_number(1 / 3), "0.333333333333")


if __name__ == "__main__":
    unittest.main()
