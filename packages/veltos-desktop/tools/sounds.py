"""VeltOS sound theme: original system sounds, synthesised at build time.

Windows' own sounds are Microsoft's works and are not shipped. These are
new sounds in a similar spirit: soft bell-like chimes for signing in and
out, a short two-note chime for notifications, lower tones for errors,
rising/falling notes for devices. They are generated from sine partials
with exponential decay (standard library only, fixed parameters, so the
build is reproducible) and written as 16-bit mono WAV files under the
freedesktop sound naming spec:

    usr/share/sounds/veltos/index.theme
    usr/share/sounds/veltos/stereo/<event name>.wav

Events VeltOS has no own sound for fall back to KDE's Ocean theme.
"""

import math
import struct
import wave
from pathlib import Path

RATE = 32000
THEME = "veltos"

# Note frequencies (equal temperament, A4 = 440 Hz).
def note(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
             "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[pitch] + 12 * (octave - 4)) / 12)


# (start seconds, note, decay seconds, gain) per tone; partials give a soft
# bell timbre.
PARTIALS = ((1.0, 1.0), (2.0, 0.28), (3.0, 0.08), (4.01, 0.04))
SOUNDS = {
    "desktop-login": [(0.00, "E5", 1.6, 0.7), (0.12, "G#5", 1.6, 0.6), (0.24, "B5", 1.8, 0.6),
                      (0.36, "E6", 2.2, 0.55), (0.36, "E4", 2.2, 0.35)],
    "desktop-logout": [(0.00, "E6", 1.2, 0.5), (0.12, "B5", 1.3, 0.55), (0.24, "G#5", 1.4, 0.6),
                       (0.36, "E5", 1.8, 0.65)],
    "message-new-instant": [(0.00, "B5", 0.55, 0.6), (0.09, "E6", 0.8, 0.55)],
    "dialog-information": [(0.00, "A5", 0.6, 0.6), (0.09, "C#6", 0.8, 0.5)],
    "dialog-warning": [(0.00, "F#5", 0.7, 0.65), (0.11, "F#5", 0.8, 0.5)],
    "dialog-error": [(0.00, "C5", 0.7, 0.7), (0.12, "A4", 0.9, 0.65)],
    "dialog-error-serious": [(0.00, "C5", 0.8, 0.7), (0.12, "A4", 0.9, 0.65), (0.24, "F4", 1.1, 0.6)],
    "device-added": [(0.00, "C6", 0.45, 0.55), (0.08, "G6", 0.7, 0.5)],
    "device-removed": [(0.00, "G6", 0.45, 0.5), (0.08, "C6", 0.7, 0.55)],
    "power-plug": [(0.00, "D6", 0.4, 0.5), (0.07, "A6", 0.6, 0.45)],
    "power-unplug": [(0.00, "A6", 0.4, 0.45), (0.07, "D6", 0.6, 0.5)],
    "complete": [(0.00, "G5", 0.5, 0.55), (0.08, "D6", 0.6, 0.5), (0.16, "G6", 0.9, 0.45)],
}
# Aliases: freedesktop names that use the same sound.
ALIASES = {"bell": "dialog-information", "completion-success": "complete",
           "message": "message-new-instant", "battery-caution": "dialog-warning",
           "battery-low": "dialog-error"}


def render(tones):
    length = max(start + decay * 2 for start, _n, decay, _g in tones)
    samples = [0.0] * int(length * RATE)
    for start, name, decay, gain in tones:
        freq = note(name)
        first = int(start * RATE)
        for i in range(len(samples) - first):
            t = i / RATE
            env = math.exp(-t / decay) * min(1.0, t / 0.004)   # 4 ms attack, no click
            value = sum(amp * math.sin(2 * math.pi * freq * mult * t) * math.exp(-t * (mult - 1) / decay)
                        for mult, amp in PARTIALS)
            samples[first + i] += gain * env * value
    peak = max(abs(s) for s in samples) or 1.0
    scale = 0.7 / peak * 32767                                   # -3 dBFS
    fade = int(0.05 * RATE)
    for i in range(1, fade + 1):
        samples[-i] *= i / fade
    return b"".join(struct.pack("<h", int(max(-32767, min(32767, s * scale)))) for s in samples)


def write_wav(path, frames):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(frames)


def build(root):
    base = root / "usr/share/sounds" / THEME
    stereo = base / "stereo"
    stereo.mkdir(parents=True, exist_ok=True)
    for name, tones in SOUNDS.items():
        write_wav(stereo / f"{name}.wav", render(tones))
    for alias, target in ALIASES.items():
        link = stereo / f"{alias}.wav"
        if not link.exists():
            link.symlink_to(f"{target}.wav")
    (base / "index.theme").write_text(
        "[Sound Theme]\n"
        "Name=VeltOS\n"
        "Comment=VeltOS system sounds (original, synthesised)\n"
        "Inherits=ocean,freedesktop\n"
        "Directories=stereo\n\n"
        "[stereo]\nOutputProfile=stereo\n",
        encoding="utf-8", newline="\n")
    return base


if __name__ == "__main__":
    import sys
    print(build(Path(sys.argv[1])))
