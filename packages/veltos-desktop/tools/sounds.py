"""VeltOS sound theme: original system sounds, synthesised at build time.

Windows' own sounds are Microsoft's works and are not shipped. These are
new sounds in the spirit of Windows 11's: soft, glassy chimes with a
gentle attack and a short room reverb, never sharp. Signing in and out
get short rising and falling motifs, notifications a two-note chime,
errors lower tones, devices rising/falling pairs. Everything is generated
from sine partials (recursive oscillators) with exponential decay, a
slightly detuned second voice for width, a one-pole low-pass that takes
the edge off, and a small Schroeder reverb (standard library only, fixed
parameters, so the build is reproducible). Written as 16-bit mono WAV
files under the freedesktop sound naming spec:

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
ATTACK = 0.018              # seconds; a raised-cosine fade-in, no click
DETUNE = 0.0028             # second voice slightly sharp: a softer, wider tone
LOWPASS_HZ = 5200           # takes the glassy edge off the high partials
REVERB_SECONDS = 0.55       # how long the room rings after the last tone
REVERB_MIX = 0.24
PEAK = 0.5                  # -6 dBFS: quieter than the Ocean theme


# Note frequencies (equal temperament, A4 = 440 Hz).
def note(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
             "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[pitch] + 12 * (octave - 4)) / 12)


# (multiple of the note, amplitude): a glassy bell with faint upper partials.
PARTIALS = ((1.0, 1.0), (2.0, 0.17), (3.0, 0.05), (4.0, 0.014))
# (start seconds, note, decay seconds, gain) per tone.
SOUNDS = {
    "desktop-login": [(0.00, "C5", 1.5, 0.62), (0.14, "E5", 1.6, 0.56), (0.28, "G5", 1.8, 0.52),
                      (0.42, "C6", 2.1, 0.42), (0.42, "C4", 2.1, 0.30)],
    "desktop-logout": [(0.00, "C6", 1.1, 0.42), (0.14, "G5", 1.3, 0.5), (0.28, "E5", 1.5, 0.56),
                       (0.42, "C5", 1.9, 0.6)],
    "message-new-instant": [(0.00, "G5", 0.45, 0.55), (0.10, "C6", 0.6, 0.48)],
    "dialog-information": [(0.00, "F5", 0.5, 0.55), (0.10, "A5", 0.65, 0.48)],
    "dialog-warning": [(0.00, "E5", 0.6, 0.6), (0.13, "E5", 0.7, 0.45)],
    "dialog-error": [(0.00, "A4", 0.7, 0.62), (0.14, "F4", 0.9, 0.58)],
    "dialog-error-serious": [(0.00, "A4", 0.8, 0.62), (0.14, "F4", 0.9, 0.58), (0.28, "D4", 1.1, 0.55)],
    "device-added": [(0.00, "A5", 0.4, 0.5), (0.09, "E6", 0.6, 0.42)],
    "device-removed": [(0.00, "E6", 0.4, 0.42), (0.09, "A5", 0.6, 0.5)],
    "power-plug": [(0.00, "B5", 0.4, 0.46), (0.08, "F#6", 0.55, 0.38)],
    "power-unplug": [(0.00, "F#6", 0.4, 0.38), (0.08, "B5", 0.55, 0.46)],
    "complete": [(0.00, "E5", 0.45, 0.52), (0.09, "B5", 0.55, 0.46), (0.18, "E6", 0.8, 0.4)],
    # Alarms and timers (VeltOS Clock): a clear four-note motif, played
    # again by the agent until the alarm is answered.
    "alarm-clock-elapsed": [(0.00, "E5", 0.5, 0.6), (0.22, "G5", 0.5, 0.6), (0.44, "B5", 0.5, 0.6),
                            (0.66, "E6", 0.9, 0.55), (1.30, "E5", 0.5, 0.6), (1.52, "G5", 0.5, 0.6),
                            (1.74, "B5", 0.5, 0.6), (1.96, "E6", 1.1, 0.55)],
}
# Aliases: freedesktop names that use the same sound.
ALIASES = {"bell": "dialog-information", "completion-success": "complete",
           "message": "message-new-instant", "battery-caution": "dialog-warning",
           "battery-low": "dialog-error"}


def add_tone(samples, start, freq, decay, gain):
    """Add one tone (its partials, two slightly detuned voices) in place.
    Each partial is a recursive sine oscillator: s[n] = 2cos(w)s[n-1] - s[n-2]."""
    first = int(start * RATE)
    count = len(samples) - first
    if count <= 0:
        return
    attack = max(1, int(ATTACK * RATE))
    for voice, voice_gain in ((1.0, 0.62), (1.0 + DETUNE, 0.38)):
        for mult, amp in PARTIALS:
            f = freq * mult * voice
            if f >= RATE / 2 * 0.9:
                continue
            w = 2 * math.pi * f / RATE
            coefficient = 2 * math.cos(w)
            s2, s1 = -math.sin(2 * w), -math.sin(w)      # s[-2], s[-1]: a sine that starts at 0
            # Higher partials die faster, as on a real bell.
            step = math.exp(-1.0 / (RATE * decay / mult ** 1.3))
            env = gain * voice_gain * amp
            for i in range(count):
                s0 = coefficient * s1 - s2
                s2, s1 = s1, s0
                level = env
                if i < attack:
                    level *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
                samples[first + i] += level * s0
                env *= step


def lowpass(samples, cutoff=LOWPASS_HZ):
    k = 1 - math.exp(-2 * math.pi * cutoff / RATE)
    out, y = [0.0] * len(samples), 0.0
    for i, x in enumerate(samples):
        y += k * (x - y)
        out[i] = y
    return out


def reverb(samples, mix=REVERB_MIX):
    """A small room: four parallel comb filters and two all-pass filters
    (Schroeder), mixed under the dry signal."""
    combs = [(int(RATE * d), fb) for d, fb in ((0.0297, 0.74), (0.0371, 0.72), (0.0411, 0.70), (0.0437, 0.68))]
    allpasses = [int(RATE * 0.005), int(RATE * 0.0017)]
    n = len(samples)
    wet = [0.0] * n
    for delay, feedback in combs:
        buf = [0.0] * delay
        for i in range(n):
            j = i % delay
            y = buf[j]
            buf[j] = samples[i] + y * feedback
            wet[i] += y
    for delay in allpasses:
        buf = [0.0] * delay
        for i in range(n):
            j = i % delay
            delayed = buf[j]
            x = wet[i]
            buf[j] = x + delayed * 0.7
            wet[i] = delayed - 0.7 * buf[j]
    return [d + mix * w / len(combs) for d, w in zip(samples, wet)]


def render(tones):
    length = max(start + decay * 2 for start, _n, decay, _g in tones) + REVERB_SECONDS
    samples = [0.0] * int(length * RATE)
    for start, name, decay, gain in tones:
        add_tone(samples, start, note(name), decay, gain)
    samples = reverb(lowpass(samples))
    peak = max(abs(s) for s in samples) or 1.0
    scale = PEAK / peak * 32767
    fade = int(0.08 * RATE)
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
