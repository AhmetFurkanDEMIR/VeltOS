# veltos-calculator

VeltOS Calculator: the Standard and Scientific modes of Windows 11's
Calculator, in the same layout and behaviour.

## What the user sees

- **Standard**: the navigation button and "Standard" at the top with
  "Keep on top" beside it and History on the right; the calculation in
  small grey text above the number; the memory row (MC, MR, M+, M−, MS,
  M⌄); the keypad (%, CE, C, ⌫, 1/x, x², ²√x, ÷, digits, ×, −, +, +/−,
  decimal point, =). Operations run in the order they are entered
  (2 + 3 × 4 = 20) and the line above shows the running result ("5 ×"),
  as in Windows. "=" repeats the last operation; % depends on the pending
  operation.
- **Scientific**: DEG/RAD/GRAD and F-E, the Trigonometry flyout (2nd, hyp,
  sin, cos, tan, sec, csc, cot and their inverses and hyperbolic forms) and
  the Function flyout (|x|, ⌊x⌋, ⌈x⌉, rand, →dms, dms), and a 5-column
  keypad with 2nd (x³, ³√x, ʸ√x, 2ˣ, logᵧx, eˣ), π, e, exp, mod, n!,
  parentheses (the open count on the "(" key) and precedence
  (2 + 3 × 4 = 14). The clear key reads CE while a number is typed.
- **History and Memory**: beside the keypad when the window is wide, over
  the keypad otherwise (History button, M⌄); a history item brings its
  calculation back, a memory item is recalled and offers MC, M+ and M− on
  hover; the waste basket clears the list.
- **Keep on top**: a small window with the basic keypad that stays above
  other windows (a KWin script sets "keep above"; Wayland clients cannot
  ask for it themselves).
- **Navigation pane**: Calculator > Standard, Scientific; Settings (app
  theme Light, Dark or Use system setting; About).
- Keyboard as in Windows: digits, + − * /, Enter or =, Backspace, Esc (C),
  Delete (CE), F9 (+/−), %, r (1/x), @ (√), q (x²); Scientific also ( ) ^
  ! p s o t l n # x; Ctrl+C/V copy and paste the number, Ctrl+M/R/P/Q/L
  memory, Ctrl+H history, Alt+1/Alt+2 change the mode. The keyboard's
  calculator key opens the app (`X-KDE-Shortcuts=Calculator`, the key name
  KCalc 25.04 uses).
- English and Turkish (Turkish uses "," as the decimal point and "." to
  group digits).

## How it works

| File | Role |
|---|---|
| `veltos_calculator/engine.py` | The calculator without a user interface: key handling, operator stack (precedence in Scientific), functions, memory, history, number text. Python `decimal`: 40 digits kept, 16 (Standard) or 32 (Scientific) shown; trigonometry, logarithms and powers in decimal, n! of non-integers through `math.gamma` (15 digits) |
| `veltos_calculator/app.py` | `Backend` for QML (display texts, theme and accent from kdeglobals and the app setting, clipboard, keep on top) and `main()` |
| `veltos_calculator/strings.py` | English and Turkish texts |
| `veltos_calculator/qml/` | `Main.qml` (window), `CalcButton.qml` (keys), `FlatButton.qml`, `Records.qml` (History/Memory), `SettingsPage.qml`, `Glyph.qml` (line icons drawn by VeltOS), `Theme.qml` |
| `data/` | Start menu entry and icon (VeltOS artwork) |

Settings are kept in `~/.config/veltos/calculator.conf` (mode, angle unit,
theme). History and memory are not kept after closing, as in Windows.

## Not included (honest list)

Windows' Graphing, Programmer and Date calculation modes and the unit
converters are not there yet.

## Tests

`tests/test_engine.py` checks the arithmetic against Windows' behaviour
(order of entry, repeat, percent, errors, 16/32 digits, separators,
memory, history, precedence, trigonometry, roots, logarithms, factorial,
exponent entry). `tests/test_ui.py` loads the window offscreen in English
and Turkish (Turkish C locale), clicks through both modes, the lists,
flyouts, navigation, settings and keep on top, and fails on any QML
warning.
