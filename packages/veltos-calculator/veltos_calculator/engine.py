"""The Standard and Scientific modes of Windows 11's Calculator, without
a user interface.

Behaviour follows Windows:

- Standard mode runs operations in the order they are entered
  (2 + 3 × 4 = 20) and shows the running result in the line above the
  number ("5 ×"); Scientific mode respects precedence (2 + 3 × 4 = 14),
  has parentheses and shows the whole expression.
- "=" repeats the last operation (2 + 3 = = gives 8), also with a new
  number (7 = gives 10).
- % (Standard) depends on the pending operation: with + and − it is a
  percentage of the first number, with × and ÷ a fraction, alone 0.
- Functions (1/x, x², √x, sin, n!, …) act on the shown number at once
  and are written into the line above it ("sqr(5)", "sin(30°)").
- Memory keeps a list (MS, MR, M+, M−, MC, and per item M+, M−, MC);
  every calculation goes into the history.

Numbers are decimal (Python's `decimal`), so 0.1 + 0.2 is 0.3. Like
Windows, more digits are kept than shown (40 kept; 16 shown in Standard,
32 in Scientific), so 1 ÷ 3 × 3 is 1. Trigonometry, logarithms and powers
are computed in decimal too; only n! of a non-integer (the gamma
function) uses floating point and is shown with 15 digits.
"""

import decimal
import math
import random
from decimal import (ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Context, Decimal, InvalidOperation,
                     localcontext)

WORK = Context(prec=60, Emax=999999, Emin=-999999)
KEEP = Context(prec=40, Emax=999999, Emin=-999999)
LIMIT = Decimal("1e10000")          # Windows: "Overflow" from 1e10000 on
TINY = Decimal("1e-10000")
PI = Decimal("3.1415926535897932384626433832795028841971693993751058209749445923")
E = Decimal("2.7182818284590452353602874713526624977572470936999595749669676277")

MODES = ("standard", "scientific")
DIGITS = {"standard": 16, "scientific": 32}
ANGLES = ("deg", "rad", "grad")
ANGLE_MARK = {"deg": "°", "rad": "", "grad": "ᵍ"}
MAX_EXPONENT_DIGITS = 4

# Binary operators: (written, precedence in Scientific mode)
BINARY = {
    "+": ("+", 1), "-": ("−", 1),
    "*": ("×", 2), "/": ("÷", 2), "mod": ("mod", 2),
    "pow": ("^", 3), "root": ("yroot", 3), "logbase": ("log base", 3),
}

# Functions of the shown number: how Windows writes them
WRITTEN = {
    "inv": "1/({})", "sqr": "sqr({})", "cube": "cube({})", "sqrt": "√({})",
    "cuberoot": "cuberoot({})", "pow10": "10^({})", "pow2": "2^({})", "powe": "e^({})",
    "log": "log({})", "ln": "ln({})", "fact": "fact({})", "abs": "abs({})",
    "floor": "floor({})", "ceil": "ceil({})", "todms": "dms({})", "fromdms": "degrees({})",
    "negate": "negate({})",
}
TRIG = ("sin", "cos", "tan", "sec", "csc", "cot")
FUNCTIONS = set(WRITTEN) | set(TRIG) | {f"a{t}" for t in TRIG} | {f"{t}h" for t in TRIG} \
    | {f"a{t}h" for t in TRIG}


class CalcError(Exception):
    """An error shown instead of a number; the text key of strings.py
    ("divide_by_zero", "undefined", "overflow", "invalid_input")."""


def keep(value):
    """A result as kept between operations (40 digits), or the error."""
    if not value.is_finite():
        raise CalcError("overflow" if value.is_infinite() else "invalid_input")
    if abs(value) >= LIMIT:
        raise CalcError("overflow")
    if value != 0 and abs(value) < TINY:
        return Decimal(0)
    return KEEP.plus(value)


def guarded(compute):
    """Run `compute` in the working precision and turn decimal's
    exceptions into the errors Windows shows."""
    try:
        with localcontext(WORK):
            return keep(compute())
    except CalcError:
        raise
    except decimal.Overflow:
        raise CalcError("overflow") from None
    except (decimal.DivisionByZero, ZeroDivisionError):
        raise CalcError("divide_by_zero") from None
    except OverflowError:
        raise CalcError("overflow") from None
    except (InvalidOperation, ValueError, ArithmeticError):
        raise CalcError("invalid_input") from None


# --- arithmetic ------------------------------------------------------------------------------

def is_integer(x):
    return x == x.to_integral_value()


def power(x, y):
    if is_integer(y) and abs(y) <= 1000000:
        if x == 0 and y < 0:
            raise CalcError("divide_by_zero")
        return x ** int(y)
    if x < 0:
        raise CalcError("invalid_input")
    if x == 0:
        if y > 0:
            return Decimal(0)
        raise CalcError("divide_by_zero")
    return x ** y


def root(x, y):
    """The y-th root of x; odd roots of negative numbers are negative."""
    if y == 0:
        raise CalcError("invalid_input")
    if x < 0:
        if is_integer(y) and int(y) % 2 == 1:
            return -root(-x, y)
        raise CalcError("invalid_input")
    if x == 0:
        if y > 0:
            return Decimal(0)
        raise CalcError("divide_by_zero")
    result = (x.ln() / y).exp()
    # Exact roots (cuberoot(27) = 3) come out 2.99…9: round to whole
    # numbers that are exact.
    nearest = result.to_integral_value()
    if nearest != 0 and is_integer(y) and nearest ** int(abs(y)) == (x if y > 0 else 1 / x):
        return nearest
    return result


def apply(left, op, right):
    def compute():
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise CalcError("undefined" if left == 0 else "divide_by_zero")
            return left / right
        if op == "mod":
            if right == 0:
                raise CalcError("divide_by_zero")
            # The sign of the divisor, as Windows: -7 mod 3 = 2
            return left - right * (left / right).to_integral_value(rounding=ROUND_FLOOR)
        if op == "pow":
            return power(left, right)
        if op == "root":
            return root(left, right)
        if op == "logbase":
            if left <= 0 or right <= 0 or right == 1:
                raise CalcError("invalid_input")
            return left.ln() / right.ln()
        raise ValueError(op)
    return guarded(compute)


# --- trigonometry in decimal -----------------------------------------------------------------

def _sin_series(r):
    total, term, n, r2 = r, r, 1, r * r
    while True:
        term = -term * r2 / ((n + 1) * (n + 2))
        n += 2
        new = total + term
        if new == total:
            return total
        total = new


def _cos_series(r):
    total, term, n, r2 = Decimal(1), Decimal(1), 0, r * r
    while True:
        term = -term * r2 / ((n + 1) * (n + 2))
        n += 2
        new = total + term
        if new == total:
            return total
        total = new


def _atan(x):
    if x == 0:
        return Decimal(0)
    doublings = 0
    while abs(x) > Decimal("0.1"):          # atan(x) = 2 atan(x / (1 + √(1 + x²)))
        x = x / (1 + (1 + x * x).sqrt())
        doublings += 1
    total, term, n, x2 = x, x, 1, x * x
    while True:
        term = -term * x2
        n += 2
        new = total + term / n
        if new == total:
            return total * (2 ** doublings)
        total = new


def _asin(x):
    if abs(x) > 1:
        raise CalcError("invalid_input")
    if abs(x) == 1:
        return PI / 2 * x
    return _atan(x / (1 - x * x).sqrt())


def quarter_turns(x, angle):
    """0–3 when x is an exact multiple of a quarter turn (where sine and
    cosine are exactly 0 or ±1), else None. In radians a multiple of π/2
    entered with the π key counts (π is kept with 40 digits)."""
    if angle == "deg":
        q = x / 90
    elif angle == "grad":
        q = x / 100
    else:
        q = x / (PI / 2)
        nearest = q.to_integral_value()
        return int(nearest) % 4 if abs(q - nearest) < Decimal("1e-36") else None
    return int(q) % 4 if is_integer(q) else None


def sin_cos(x, angle):
    quarter = quarter_turns(x, angle)
    if quarter is not None:
        return [(0, 1), (1, 0), (0, -1), (-1, 0)][quarter]
    if angle == "deg":
        r = (x % 360) * PI / 180
    elif angle == "grad":
        r = (x % 400) * PI / 200
    else:
        r = x % (2 * PI)
    if r > PI:
        r -= 2 * PI
    elif r < -PI:
        r += 2 * PI
    return _sin_series(r), _cos_series(r)


def from_radians(r, angle):
    if angle == "deg":
        return r * 180 / PI
    if angle == "grad":
        return r * 200 / PI
    return r


def trig(kind, x, angle):
    hyperbolic = kind.endswith("h")
    inverse = kind.startswith("a")
    base = kind[1:] if inverse else kind
    base = base[:-1] if hyperbolic else base
    if hyperbolic and not inverse:
        ex, emx = x.exp(), (-x).exp()
        sinh, cosh = (ex - emx) / 2, (ex + emx) / 2
        values = {"sin": (sinh, 1), "cos": (cosh, 1), "tan": (sinh, cosh),
                  "sec": (1, cosh), "csc": (1, sinh), "cot": (cosh, sinh)}
        top, bottom = values[base]
        if bottom == 0:
            raise CalcError("invalid_input")
        return Decimal(top) / bottom
    if hyperbolic:                      # inverse hyperbolic
        if base in ("sec", "csc", "cot"):
            if x == 0:
                raise CalcError("invalid_input")
            x = 1 / x
            base = {"sec": "cos", "csc": "sin", "cot": "tan"}[base]
        if base == "sin":
            return (abs(x) + (x * x + 1).sqrt()).ln().copy_sign(x) if x else Decimal(0)
        if base == "cos":
            if x < 1:
                raise CalcError("invalid_input")
            return (x + (x * x - 1).sqrt()).ln()
        if abs(x) >= 1:
            raise CalcError("invalid_input")
        return ((1 + x) / (1 - x)).ln() / 2
    if inverse:
        if base in ("sec", "csc"):
            if abs(x) < 1:
                raise CalcError("invalid_input")
            x = 1 / x
            base = {"sec": "cos", "csc": "sin"}[base]
        if base == "sin":
            r = _asin(x)
        elif base == "cos":
            r = PI / 2 - _asin(x)
        elif base == "tan":
            r = _atan(x)
        else:                           # acot: 0 … π, like the textbooks
            r = PI / 2 - _atan(x)
        return from_radians(r, angle)
    s, c = sin_cos(x, angle)
    top, bottom = {"sin": (s, 1), "cos": (c, 1), "tan": (s, c),
                   "sec": (1, c), "csc": (1, s), "cot": (c, s)}[base]
    if bottom == 0:
        raise CalcError("invalid_input")
    return Decimal(top) / Decimal(bottom)


def trig_written(kind, shown, angle):
    hyperbolic = kind.endswith("h")
    inverse = kind.startswith("a")
    base = kind[1:] if inverse else kind
    base = base[:-1] if hyperbolic else base
    name = base + ("h" if hyperbolic else "") + ("⁻¹" if inverse else "")
    mark = ANGLE_MARK[angle] if not (inverse or hyperbolic) else ""
    return f"{name}({shown}{mark})"


# --- other functions -------------------------------------------------------------------------

def factorial(x):
    if is_integer(x):
        if x < 0:
            raise CalcError("invalid_input")
        if x > 3300:                    # far above 1e10000 (Overflow)
            raise CalcError("overflow")
        result = Decimal(1)
        for n in range(2, int(x) + 1):
            result *= n
        return result
    # Non-integers: the gamma function, like Windows (0.5! = 0.886…);
    # floating point, so 15 digits.
    value = math.gamma(float(x) + 1)
    return Context(prec=15).plus(Decimal(repr(value)))


def to_dms(x):
    """Decimal degrees as degrees.minutesseconds (1.5 → 1.3, 1°30′)."""
    sign, x = (-1 if x < 0 else 1), abs(x)
    degrees = x.to_integral_value(rounding=ROUND_FLOOR)
    minutes_all = (x - degrees) * 60
    minutes = minutes_all.to_integral_value(rounding=ROUND_FLOOR)
    seconds = (minutes_all - minutes) * 60
    return sign * (degrees + minutes / 100 + seconds / 10000)


def from_dms(x):
    """degrees.minutesseconds as decimal degrees (1.3 → 1.5)."""
    sign, x = (-1 if x < 0 else 1), abs(x)
    degrees = x.to_integral_value(rounding=ROUND_FLOOR)
    minutes_all = (x - degrees) * 100
    minutes = minutes_all.to_integral_value(rounding=ROUND_FLOOR)
    seconds = (minutes_all - minutes) * 100
    return sign * (degrees + minutes / 60 + seconds / 3600)


def function(kind, x, angle="deg"):
    def compute():
        if kind == "inv":
            if x == 0:
                raise CalcError("divide_by_zero")
            return 1 / x
        if kind == "sqr":
            return x * x
        if kind == "cube":
            return x * x * x
        if kind == "sqrt":
            if x < 0:
                raise CalcError("invalid_input")
            return x.sqrt()
        if kind == "cuberoot":
            return root(x, Decimal(3))
        if kind == "pow10":
            return power(Decimal(10), x)
        if kind == "pow2":
            return power(Decimal(2), x)
        if kind == "powe":
            return x.exp()
        if kind in ("log", "ln"):
            if x <= 0:
                raise CalcError("invalid_input")
            return x.log10() if kind == "log" else x.ln()
        if kind == "fact":
            return factorial(x)
        if kind == "abs":
            return abs(x)
        if kind == "floor":
            return x.to_integral_value(rounding=ROUND_FLOOR)
        if kind == "ceil":
            return x.to_integral_value(rounding=ROUND_CEILING)
        if kind == "todms":
            return to_dms(x)
        if kind == "fromdms":
            return from_dms(x)
        if kind == "negate":
            return -x
        if kind in FUNCTIONS:
            return trig(kind, x, angle)
        raise ValueError(kind)
    return guarded(compute)


# --- text ------------------------------------------------------------------------------------

def to_text(value, digits=16, scientific=False):
    """Plain text ('.' and 'e') of `value` with at most `digits`
    significant digits: fixed when it fits in `digits` digits, else
    scientific like Windows ("1.e+16", "3.333333333333333e-4")."""
    if value == 0:
        return "0"
    rounded = Context(prec=digits, rounding=ROUND_HALF_UP, Emax=999999, Emin=-999999).plus(value)
    rounded = rounded.normalize(Context(prec=digits, Emax=999999, Emin=-999999))
    sign, numerals, _exponent = rounded.as_tuple()
    adjusted = rounded.adjusted()
    if adjusted >= 0:
        width = max(adjusted + 1, len(numerals))
    else:
        width = -adjusted - 1 + len(numerals)
    if not scientific and width <= digits:
        return format(rounded, "f")
    first, rest = str(numerals[0]), "".join(str(n) for n in numerals[1:])
    return f"{'-' if sign else ''}{first}.{rest}e{'+' if adjusted >= 0 else '-'}{abs(adjusted)}"


def localize(text, lang):
    """Group thousands and use the language's separators (Turkish: 1.234,5)."""
    if "e" in text:
        mantissa, exponent = text.split("e", 1)
        return localize(mantissa, lang) + "e" + exponent
    group, point = (".", ",") if lang == "tr" else (",", ".")
    sign = "-" if text.startswith("-") else ""
    whole, dot, fraction = text.lstrip("-").partition(".")
    grouped = ""
    while len(whole) > 3:
        grouped = group + whole[-3:] + grouped
        whole = whole[:-3]
    return sign + whole + grouped + (point + fraction if dot else "")


def read_number(text, lang="en"):
    """A number pasted from the clipboard ("1.234,5" in Turkish,
    "1,234.5", "1.5e+3"), or None."""
    text = text.strip().replace(" ", "").replace(" ", "").replace("−", "-")
    if lang == "tr":
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


# --- the calculator --------------------------------------------------------------------------

class Calculator:
    """Keys go in through `press(key)`:

        "0"–"9", ".", "+", "-", "*", "/", "=", "%", "C", "CE", "back",
        "negate", "(", ")", "mod", "pow", "root", "logbase", "exp",
        "pi", "e", "rand", "MS", "MR", "M+", "M-", "MC",
        and the functions of `FUNCTIONS` ("sqr", "sin", "asinh", …).
    """

    def __init__(self, lang="en", mode="standard"):
        self.lang = lang
        self.mode = mode if mode in MODES else "standard"
        self.angle = "deg"
        self.fixed_exponent = False     # F-E: always scientific notation
        self.memory = []                # newest first
        self.history = []               # [(expression, result Decimal)], newest first
        self.random = random.SystemRandom()
        self.clear_all()

    # --- state -------------------------------------------------------------------------------

    def clear_all(self):
        self.typing = None              # the number being typed ("12.5", "2e+3") or None
        self.number = Decimal(0)        # the shown number when nothing is typed
        self.written = ""               # how a computed shown number is written ("sqr(5)")
        self.ready = False              # the shown number is an operand (not just an echo)
        self.values = []                # operands waiting for their operator
        self.ops = []                   # binary operators and "("
        self.parens = []                # positions of "(" in `expr`
        self.expr = []                  # the line above the number, part by part
        self.after_equals = False
        self.last = None                # (op, right) that "=" repeats
        self.error = ""

    @property
    def digits(self):
        return DIGITS[self.mode]

    def set_mode(self, mode):
        """Switch Standard/Scientific; the shown number stays (Windows)."""
        if mode not in MODES or mode == self.mode:
            return
        number = Decimal(0) if self.error else self.value()
        self.mode = mode
        self.clear_all()
        self.number = keep(number)
        self.ready = number != 0

    def value(self):
        if self.typing is None:
            return self.number
        text = self.typing
        if text.endswith(("e+", "e-")):
            text += "0"
        return keep(Decimal(text))

    def fmt(self, value):
        return localize(to_text(value, self.digits, self.fixed_exponent), self.lang)

    def display(self):
        """The shown number, as text (the error key when there is one)."""
        if self.error:
            return self.error
        if self.typing is None:
            return self.fmt(self.number)
        mantissa, e, exponent = self.typing.partition("e")
        if not e:
            return localize(mantissa, self.lang)
        if "." not in mantissa:
            mantissa += "."
        return localize(mantissa, self.lang) + "e" + (exponent if exponent[1:] else exponent + "0")

    def expression(self):
        parts = self.expr + ([self.written] if self.written and not self.after_equals else [])
        return " ".join(parts).replace("( ", "(").replace(" )", ")")

    def open_parens(self):
        return self.ops.count("(")

    def _fail(self, key, attempted=""):
        if attempted:
            self.expr = self.expr + [attempted]
        self.error = key
        self.values, self.ops, self.parens = [], [], []
        self.typing = None
        self.written = ""
        self.after_equals = False

    def _start_over(self):
        """A new calculation after "=" or an error (the repeat stays)."""
        last = self.last
        if self.error:
            self.clear_all()
        self.expr = []
        self.after_equals = False
        self.last = last

    def _shown(self):
        return self.written or self.fmt(self.value())

    def _set_number(self, value, written=""):
        self.number = value
        self.typing = None
        self.written = written
        self.ready = True

    # --- keys --------------------------------------------------------------------------------

    def press(self, key):
        handler = {
            ".": self.point, "=": self.equals, "%": self.percent, "C": self.clear_all,
            "CE": self.clear_entry, "back": self.backspace, "negate": self.negate,
            "(": self.open_paren, ")": self.close_paren, "exp": self.exponent,
            "pi": lambda: self.constant(PI), "e": lambda: self.constant(E),
            "rand": self.random_number, "MS": self.memory_store, "MR": self.memory_recall,
            "M+": lambda: self.memory_add(1), "M-": lambda: self.memory_add(-1),
            "MC": self.memory_clear,
        }.get(key)
        if handler is not None:
            handler()
        elif key.isdigit() and len(key) == 1:
            self.digit(key)
        elif key in BINARY:
            self.operator(key)
        elif key in FUNCTIONS:
            self.function(key)
        else:
            raise ValueError(key)

    def digit(self, d):
        if self.error or self.after_equals:
            self._start_over()
        if self.typing is None:
            self.typing = "0"
            self.written = ""
        self.ready = True
        mantissa, e, exponent = self.typing.partition("e")
        if e:
            if len(exponent) - 1 < MAX_EXPONENT_DIGITS and not (exponent[1:] == "" and d == "0"):
                self.typing += d
            return
        if len(mantissa.lstrip("-").replace(".", "").lstrip("0") or "") >= self.digits:
            return
        if mantissa.lstrip("-") == "0":
            self.typing = mantissa[:-1] + d
        else:
            self.typing += d

    def point(self):
        if self.error or self.after_equals:
            self._start_over()
        if self.typing is None:
            self.typing = "0."
            self.written = ""
        elif "." not in self.typing and "e" not in self.typing:
            self.typing += "."
        self.ready = True

    def exponent(self):
        """The exp key: type an exponent (2 exp 3 = 2000)."""
        if self.error or self.mode != "scientific":
            return
        if self.typing is None:
            if self.after_equals:
                self._start_over()
            text = to_text(self.number, self.digits)
            if "e" in text:             # already in scientific notation
                return
            self.typing = text
            self.written = ""
        if "e" not in self.typing:
            self.typing = self.typing.rstrip(".") + "e+"
        self.ready = True

    def backspace(self):
        if self.error:
            self.clear_all()
            return
        if self.after_equals:
            self.expr = []              # Windows clears the line above
            return
        if self.typing is None:
            return
        if self.typing.endswith(("e+", "e-")):
            self.typing = self.typing[:-2]
        else:
            self.typing = self.typing[:-1]
        if self.typing in ("", "-", "-0"):
            self.typing = "0"

    def clear_entry(self):
        if self.error or self.after_equals:
            self.clear_all()
            return
        self.typing = "0"
        self.written = ""
        self.ready = True

    def negate(self):
        if self.error:
            return
        if self.typing is not None:
            mantissa, e, exponent = self.typing.partition("e")
            if e:
                self.typing = mantissa + "e" + ("-" if exponent[0] == "+" else "+") + exponent[1:]
            elif mantissa.startswith("-"):
                self.typing = mantissa[1:]
            elif mantissa not in ("0", "0."):
                self.typing = "-" + mantissa
            return
        self.function("negate")

    def constant(self, value):
        if self.error or self.after_equals:
            self._start_over()
        self._set_number(keep(value))

    def random_number(self):
        self.constant(Decimal(self.random.randrange(10 ** 32)) / Decimal(10) ** 32)

    def function(self, kind):
        if self.error:
            return
        shown = self._shown()
        if kind in TRIG or kind[1:] in TRIG or kind[:-1] in TRIG or kind[1:-1] in TRIG:
            written = trig_written(kind, shown, self.angle)
        else:
            written = WRITTEN[kind].format(shown)
        if self.after_equals:
            self.expr = []
            self.after_equals = False
        try:
            result = function(kind, self.value(), self.angle)
        except CalcError as error:
            self._fail(str(error), written)
            return
        self._set_number(result, written)

    def operator(self, op):
        if self.error:
            return
        if self.after_equals:
            self.expr = []
            self.after_equals = False
        try:
            if not self.ready and self.ops and self.ops[-1] != "(":
                self.ops.pop()          # a second operator replaces the first (2 + × → 2 ×)
                self.expr.pop()
            else:
                self._commit()
            reduced = self._push(op)
        except CalcError as error:
            self._fail(str(error))
            return
        self._set_number(self.values[-1])
        self.ready = False
        if self.mode == "standard" and reduced:
            # Standard mode shows the running result: "2 + 3 ×" becomes "5 ×".
            self.expr = [self.fmt(self.values[-1])]
        self.expr.append(BINARY[op][0])

    def _commit(self):
        self.values.append(self.value())
        self.expr.append(self._shown())
        self.typing = None
        self.written = ""

    def _precedence(self, op):
        return BINARY[op][1] if self.mode == "scientific" else 1

    def _reduce(self):
        right = self.values.pop()
        left = self.values.pop()
        op = self.ops.pop()
        self.values.append(apply(left, op, right))
        self.last = (op, right)

    def _push(self, op):
        reduced = False
        while self.ops and self.ops[-1] != "(" and self._precedence(self.ops[-1]) >= self._precedence(op):
            self._reduce()
            reduced = True
        self.ops.append(op)
        return reduced

    def open_paren(self):
        if self.error or self.mode != "scientific":
            return
        if self.after_equals:
            self._start_over()
        # The shown number has no operator before "(": it is not an operand
        # (Windows drops a number typed right before "(").
        self._set_number(self.value())
        self.ready = False
        self.ops.append("(")
        self.parens.append(len(self.expr))
        self.expr.append("(")

    def close_paren(self):
        if self.error or "(" not in self.ops:
            return
        try:
            self._commit()
            while self.ops[-1] != "(":
                self._reduce()
        except CalcError as error:
            self._fail(str(error))
            return
        self.ops.pop()
        start = self.parens.pop()
        group = "(" + " ".join(self.expr[start + 1:]) + ")"
        self.expr = self.expr[:start]
        self._set_number(self.values.pop(), group)

    def equals(self):
        if self.error:
            self.clear_all()
            return
        try:
            if self.ops:
                self._commit()
                while self.ops:
                    if self.ops[-1] == "(":
                        self.ops.pop()
                        self.expr.append(")")
                        continue
                    self._reduce()
                result = self.values.pop()
                self.parens = []
                expression = self.expr + ["="]
            elif self.last is not None:
                op, right = self.last
                shown = self._shown()
                result = apply(self.value(), op, right)
                expression = [shown, BINARY[op][0], self.fmt(right), "="]
            else:
                expression = [self._shown(), "="]
                self.expr = expression
                self._set_number(self.value())
                self.after_equals = True
                return
        except CalcError as error:
            self._fail(str(error), "=")
            return
        self.expr = expression
        self._set_number(result)
        self.after_equals = True
        self.history.insert(0, (self.expression(), result))

    def percent(self):
        if self.error:
            return
        if self.after_equals:
            self._start_over()
        current = self.value()
        if self.ops and self.ops[-1] in ("+", "-") and self.values:
            result = keep(self.values[-1] * current / 100)
        elif self.ops and self.ops[-1] in ("*", "/"):
            result = keep(current / 100)
        else:
            result = Decimal(0)         # Windows: % without an operation gives 0
        self._set_number(result, self.fmt(result))
        if not self.ops:
            self.expr = []

    # --- memory and history ------------------------------------------------------------------

    def memory_store(self):
        if self.error:
            return
        self.memory.insert(0, self.value())
        self._set_number(self.value(), self.written)

    def memory_recall(self, index=0):
        if self.error or not 0 <= index < len(self.memory):
            return
        if self.after_equals:
            self._start_over()
        self._set_number(self.memory[index])

    def memory_add(self, sign, index=0):
        if self.error:
            return
        value = self.value()
        if not self.memory:
            self.memory.insert(0, Decimal(0))
            index = 0
        if 0 <= index < len(self.memory):
            try:
                self.memory[index] = guarded(lambda: self.memory[index] + sign * value)
            except CalcError:
                return
        self._set_number(value, self.written)

    def memory_clear(self, index=None):
        if index is None:
            self.memory = []
        elif 0 <= index < len(self.memory):
            del self.memory[index]

    def use_history(self, index):
        if 0 <= index < len(self.history):
            expression, result = self.history[index]
            self.clear_all()
            self.expr = [expression]
            self._set_number(result)
            self.after_equals = True

    def clear_history(self):
        self.history = []

    def paste(self, text):
        value = read_number(text, self.lang)
        if value is None:
            return False
        try:
            value = keep(value)
        except CalcError:
            return False
        if self.error or self.after_equals:
            self._start_over()
        self._set_number(value)
        return True

    def next_angle(self):
        self.angle = ANGLES[(ANGLES.index(self.angle) + 1) % len(ANGLES)]

    def toggle_fixed_exponent(self):
        self.fixed_exponent = not self.fixed_exponent
