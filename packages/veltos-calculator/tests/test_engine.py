"""Behaviour of the calculator engine, checked against what Windows 11's
Calculator does (standard library only)."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veltos_calculator import engine  # noqa: E402
from veltos_calculator.engine import Calculator  # noqa: E402


def run(keys, mode="standard", lang="en", angle="deg"):
    calc = Calculator(lang, mode)
    calc.angle = angle
    for key in keys.split():
        calc.press(key)
    return calc


def shown(keys, **kw):
    return run(keys, **kw).display()


class StandardTests(unittest.TestCase):
    def test_order_of_entry(self):
        calc = run("2 + 3 * 4 =")
        self.assertEqual(calc.display(), "20")
        self.assertEqual(calc.expression(), "5 × 4 =")

    def test_running_result_in_the_line_above(self):
        calc = run("2 + 3 *")
        self.assertEqual(calc.display(), "5")
        self.assertEqual(calc.expression(), "5 ×")

    def test_equals_repeats(self):
        self.assertEqual(shown("2 + 3 = ="), "8")
        self.assertEqual(shown("2 + 3 = 7 ="), "10")
        self.assertEqual(shown("2 + ="), "4")

    def test_second_operator_replaces_the_first(self):
        calc = run("2 + * 3 =")
        self.assertEqual(calc.display(), "6")
        self.assertEqual(calc.expression(), "2 × 3 =")

    def test_decimal_arithmetic(self):
        self.assertEqual(shown("0 . 1 + 0 . 2 ="), "0.3")
        self.assertEqual(shown("1 / 3 * 3 ="), "1")
        self.assertEqual(shown("1 / 3 ="), "0.3333333333333333")
        self.assertEqual(shown("2 / 3 ="), "0.6666666666666667")

    def test_percent(self):
        calc = run("2 0 0 + 5 %")
        self.assertEqual(calc.display(), "10")
        self.assertEqual(calc.expression(), "200 + 10")
        self.assertEqual(shown("2 0 0 + 5 % ="), "210")
        self.assertEqual(shown("5 0 * 1 0 % ="), "5")
        self.assertEqual(shown("5 0 %"), "0")

    def test_functions_are_written_above(self):
        calc = run("5 sqr")
        self.assertEqual((calc.display(), calc.expression()), ("25", "sqr(5)"))
        calc = run("9 sqrt + 2 +")
        self.assertEqual((calc.display(), calc.expression()), ("5", "5 +"))
        calc = run("4 inv")
        self.assertEqual((calc.display(), calc.expression()), ("0.25", "1/(4)"))
        calc = run("2 + 3 = negate")
        self.assertEqual((calc.display(), calc.expression()), ("-5", "negate(5)"))

    def test_errors(self):
        calc = run("1 / 0 =")
        self.assertEqual(calc.display(), "divide_by_zero")
        self.assertEqual(calc.expression(), "1 ÷ 0 =")
        self.assertEqual(shown("0 / 0 ="), "undefined")
        self.assertEqual(shown("0 inv"), "divide_by_zero")
        self.assertEqual(shown("4 negate sqrt"), "invalid_input")
        # A digit after an error starts again.
        self.assertEqual(shown("1 / 0 = 7"), "7")

    def test_entry_editing(self):
        self.assertEqual(shown("1 2 3 back"), "12")
        self.assertEqual(shown("1 2 back back back"), "0")
        self.assertEqual(shown("4 + 5 CE 6 ="), "10")
        self.assertEqual(shown("1 . 5 negate"), "-1.5")
        self.assertEqual(shown("0 . 0 5"), "0.05")
        self.assertEqual(shown("1 . ."), "1.")

    def test_sixteen_digits(self):
        self.assertEqual(shown(" ".join("1234567890123456789")), "1,234,567,890,123,456")
        self.assertEqual(shown("9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 9 + 1 ="), "1.e+16")
        self.assertEqual(shown("1 / 3 0 0 0 ="), "3.333333333333333e-4")
        self.assertEqual(shown("0 . 0 0 0 1 2 3 + 0 ="), "0.000123")

    def test_overflow(self):
        calc = run("1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        for _ in range(12):
            calc.press("sqr")
        self.assertEqual(calc.display(), "overflow")

    def test_turkish_separators(self):
        calc = run("1 2 3 4 . 5 + 1 =", lang="tr")
        self.assertEqual(calc.display(), "1.235,5")
        self.assertEqual(calc.expression(), "1.234,5 + 1 =")

    def test_memory(self):
        calc = run("5 MS 3 M+ MR")
        self.assertEqual(calc.display(), "8")
        calc.press("MS")
        self.assertEqual(calc.memory, [Decimal(8), Decimal(8)])
        calc.memory_add(-1, 1)          # M− on the second item
        self.assertEqual(calc.memory, [Decimal(8), Decimal(0)])
        calc.memory_clear(0)
        self.assertEqual(calc.memory, [Decimal(0)])
        calc.press("MC")
        self.assertEqual(calc.memory, [])
        # M+ with an empty memory creates an item.
        self.assertEqual(run("4 M+").memory, [Decimal(4)])

    def test_history(self):
        calc = run("2 + 3 = 4 * 5 =")
        self.assertEqual([h[0] for h in calc.history], ["4 × 5 =", "2 + 3 ="])
        calc.use_history(1)
        self.assertEqual((calc.display(), calc.expression()), ("5", "2 + 3 ="))
        calc.press("+")
        calc.press("1")
        calc.press("=")
        self.assertEqual(calc.display(), "6")
        # Without an operation nothing is added.
        self.assertEqual(run("5 =").history, [])

    def test_paste(self):
        calc = Calculator("en")
        self.assertTrue(calc.paste("1,234.5"))
        self.assertEqual(calc.display(), "1,234.5")
        calc = Calculator("tr")
        self.assertTrue(calc.paste("1.234,5"))
        self.assertEqual(calc.value(), Decimal("1234.5"))
        self.assertFalse(calc.paste("hello"))
        self.assertFalse(calc.paste("nan"))

    def test_mode_switch_keeps_the_number(self):
        calc = run("1 2")
        calc.set_mode("scientific")
        self.assertEqual(calc.display(), "12")
        calc.press("+")
        calc.press("1")
        calc.press("=")
        self.assertEqual(calc.display(), "13")


class ScientificTests(unittest.TestCase):
    def sci(self, keys, angle="deg"):
        return run(keys, mode="scientific", angle=angle)

    def test_precedence_and_parentheses(self):
        calc = self.sci("2 + 3 * 4 =")
        self.assertEqual((calc.display(), calc.expression()), ("14", "2 + 3 × 4 ="))
        self.assertEqual(self.sci("2 + 3 *").display(), "3")
        self.assertEqual(self.sci("2 * 3 +").display(), "6")
        calc = self.sci("2 + ( 3 + 4 ) * 5 =")
        self.assertEqual((calc.display(), calc.expression()), ("37", "2 + (3 + 4) × 5 ="))
        self.assertEqual(self.sci("2 pow 3 pow 2 =").display(), "64")       # left to right, as Windows
        self.assertEqual(self.sci("2 + 3 pow 2 =").display(), "11")
        self.assertEqual(self.sci("( ( 1 + 2 ) * 3").open_parens(), 1)
        self.assertEqual(self.sci("( 2 + 3 =").display(), "5")             # = closes parentheses

    def test_thirty_two_digits(self):
        self.assertEqual(self.sci("1 / 3 =").display(), "0.33333333333333333333333333333333")
        self.assertEqual(self.sci("pi").display(), "3.1415926535897932384626433832795")

    def test_trigonometry(self):
        self.assertEqual(self.sci("3 0 sin").display(), "0.5")
        self.assertEqual(self.sci("3 0 sin").expression(), "sin(30°)")
        self.assertEqual(self.sci("9 0 cos").display(), "0")
        self.assertEqual(self.sci("1 8 0 sin").display(), "0")
        self.assertEqual(self.sci("4 5 tan").display(), "1")
        self.assertEqual(self.sci("9 0 tan").display(), "invalid_input")
        self.assertEqual(self.sci("pi sin", angle="rad").display(), "0")
        self.assertEqual(self.sci("1 0 0 sin", angle="grad").display(), "1")
        self.assertEqual(self.sci("0 . 5 asin").display(), "30")
        self.assertEqual(self.sci("1 atan", angle="rad").display(), self.sci("pi / 4 =").display())
        self.assertEqual(self.sci("2 asin").display(), "invalid_input")
        self.assertEqual(self.sci("6 0 sec").display(), "2")
        self.assertEqual(self.sci("0 sinh").display(), "0")
        self.assertEqual(self.sci("0 cosh").display(), "1")
        self.assertEqual(self.sci("2 acosh").display()[:12], "1.3169578969")
        self.assertEqual(self.sci("0 . 5 asin").expression(), "sin⁻¹(0.5)")

    def test_powers_roots_logs(self):
        self.assertEqual(self.sci("2 pow 1 0 =").display(), "1,024")
        self.assertEqual(self.sci("8 root 3 =").display(), "2")
        self.assertEqual(self.sci("2 7 negate cuberoot").display(), "-3")
        self.assertEqual(self.sci("1 0 0 0 log").display(), "3")
        self.assertEqual(self.sci("e ln").display(), "1")
        self.assertEqual(self.sci("8 logbase 2 =").display(), "3")
        self.assertEqual(self.sci("3 pow10").display(), "1,000")
        self.assertEqual(self.sci("1 0 pow2").display(), "1,024")
        self.assertEqual(self.sci("0 log").display(), "invalid_input")
        self.assertEqual(self.sci("2 negate pow 0 . 5 =").display(), "invalid_input")
        self.assertEqual(self.sci("2 pow 0 . 5 =").display(), "1.4142135623730950488016887242097")

    def test_factorial_mod_abs(self):
        self.assertEqual(self.sci("5 fact").display(), "120")
        self.assertEqual(self.sci("0 fact").display(), "1")
        self.assertEqual(self.sci("0 . 5 fact").display(), "0.886226925452758")
        self.assertEqual(self.sci("3 negate fact").display(), "invalid_input")
        self.assertEqual(self.sci("4 0 0 0 fact").display(), "overflow")
        self.assertEqual(self.sci("7 negate mod 3 =").display(), "2")
        self.assertEqual(self.sci("7 mod 3 negate =").display(), "-2")
        self.assertEqual(self.sci("7 negate abs").display(), "7")
        self.assertEqual(self.sci("2 . 5 floor").display(), "2")
        self.assertEqual(self.sci("2 . 5 negate ceil").display(), "-2")

    def test_degrees_minutes_seconds(self):
        self.assertEqual(self.sci("1 . 5 todms").display(), "1.3")
        self.assertEqual(self.sci("1 . 3 fromdms").display(), "1.5")
        self.assertEqual(self.sci("1 . 2 5 7 5 todms").display(), "1.1527")

    def test_exponent_entry(self):
        calc = self.sci("2 exp")
        self.assertEqual(calc.display(), "2.e+0")
        calc.press("3")
        self.assertEqual(calc.display(), "2.e+3")
        calc.press("negate")
        self.assertEqual(calc.display(), "2.e-3")
        calc.press("=")
        self.assertEqual(calc.display(), "0.002")

    def test_fixed_exponent(self):
        calc = self.sci("1 2 3 4 =")
        calc.toggle_fixed_exponent()
        self.assertEqual(calc.display(), "1.234e+3")

    def test_constants_and_random(self):
        self.assertTrue(self.sci("e").display().startswith("2.718281828459045"))
        value = self.sci("rand").value()
        self.assertTrue(0 <= value < 1)


class TextTests(unittest.TestCase):
    def test_to_text(self):
        self.assertEqual(engine.to_text(Decimal("100")), "100")
        self.assertEqual(engine.to_text(Decimal("-0.5")), "-0.5")
        self.assertEqual(engine.to_text(Decimal("1e20")), "1.e+20")
        self.assertEqual(engine.to_text(Decimal("1.5e-20")), "1.5e-20")
        self.assertEqual(engine.to_text(Decimal("0.00000001")), "0.00000001")
        self.assertEqual(engine.to_text(Decimal("9.99999999999999999")), "10")

    def test_localize(self):
        self.assertEqual(engine.localize("-1234567.25", "en"), "-1,234,567.25")
        self.assertEqual(engine.localize("-1234567.25", "tr"), "-1.234.567,25")
        self.assertEqual(engine.localize("1.5e+20", "tr"), "1,5e+20")
        self.assertEqual(engine.localize("12.", "tr"), "12,")


if __name__ == "__main__":
    unittest.main()
