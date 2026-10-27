"""The keyboard light helper: /usr/libexec/veltos/keyboard-light, run as root
through pkexec (polkit action org.veltos.lighting.set: the signed-in user
of the active session, no password, as Windows changes keyboard lights).

    keyboard-light LED [--brightness N] [--color #RRGGBB] [--effect static|breathing|cycle] [--speed 0-2]

It only writes the brightness and colour files of a keyboard light
(leds.writes); the LED must be a keyboard light of this PC and every value
is checked, so the helper cannot be used to write anything else.
"""

import argparse
import sys

from . import leds


def main(argv=None, root=leds.LEDS):
    parser = argparse.ArgumentParser(prog="keyboard-light", description=__doc__.splitlines()[0])
    parser.add_argument("led")
    parser.add_argument("--brightness", type=int)
    parser.add_argument("--color")
    parser.add_argument("--effect", choices=leds.EFFECTS, default="static")
    parser.add_argument("--speed", type=int, choices=(0, 1, 2), default=1)
    args = parser.parse_args(argv)
    folder = leds.valid_id(args.led, root)
    if folder is None:
        print(f"keyboard-light: {args.led!r} is not a keyboard light of this PC", file=sys.stderr)
        return 2
    if args.color is not None and leds.parse_color(args.color) is None:
        print(f"keyboard-light: {args.color!r} is not a colour (#RRGGBB)", file=sys.stderr)
        return 2
    kind = leds.color_kind(folder)
    status = 0
    for path, text in leds.writes(folder, kind, args.brightness, args.color, args.effect, args.speed):
        try:
            path.write_text(text + "\n", encoding="ascii")
        except OSError as error:
            print(f"keyboard-light: {path.name}: {error}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
