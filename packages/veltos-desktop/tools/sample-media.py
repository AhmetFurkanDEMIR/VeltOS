#!/usr/bin/env python3
"""Makes VeltOS' sample media (samples/), as Windows ships sample pictures,
music and a video. Everything is VeltOS' own work (CC-BY-SA-4.0): the music
is synthesized here note by note, the video animates VeltOS' wallpapers
(tools/wallpapers.py) and logo. The results are committed, so the package
build does not need ffmpeg:

    python3 tools/sample-media.py OUT_DIR     (needs rsvg-convert and ffmpeg)

    OUT_DIR/VeltOS - Bloom.mp3     about 63 s, with tags and cover art
    OUT_DIR/VeltOS.mp4             about 31 s, 1920x1080, the music as sound
"""

import math
import random
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wallpapers  # noqa: E402

RATE = 44100
BEAT = 60 / 84                    # 84 beats per minute
BAR = 4 * BEAT
# D major, gently: Dmaj9 - Bm7 - Gmaj7 - A6/9, each one bar; MIDI notes.
CHORDS = [
    (50, [62, 66, 69, 73, 76]),   # D:  D F# A C# E
    (47, [62, 66, 69, 71, 74]),   # Bm: D F# A B D
    (43, [62, 67, 71, 74, 78]),   # G:  D G B D F#
    (45, [61, 64, 69, 71, 76]),   # A:  C# E A B E
]
BARS = 20                         # five times round
TAIL = 6.0                        # the last chord rings out


def freq(note):
    return 440.0 * 2 ** ((note - 69) / 12)


class Track:
    def __init__(self, seconds):
        self.n = int(seconds * RATE)
        self.left = [0.0] * self.n
        self.right = [0.0] * self.n

    def add(self, start, samples, pan=0.0, gain=1.0):
        """Mixes mono samples in at `start` seconds; pan -1 (left) .. 1."""
        lg = gain * math.cos((pan + 1) * math.pi / 4)
        rg = gain * math.sin((pan + 1) * math.pi / 4)
        offset = int(start * RATE)
        left, right = self.left, self.right
        for i, value in enumerate(samples):
            j = offset + i
            if j >= self.n:
                break
            left[j] += value * lg
            right[j] += value * rg


def pad(note, seconds, attack=1.6, release=2.2):
    """A warm pad: two slightly detuned voices with a few soft harmonics."""
    f = freq(note)
    count = int((seconds + release) * RATE)
    out = [0.0] * count
    two_pi = 2 * math.pi
    sin = math.sin
    for detune in (0.997, 1.003):
        step = two_pi * f * detune / RATE
        phase = random.random() * two_pi
        for i in range(count):
            p = phase + step * i
            out[i] += sin(p) * 0.6 + sin(2 * p) * 0.18 + sin(3 * p) * 0.06
    for i in range(count):
        t = i / RATE
        if t < attack:
            env = (t / attack) ** 2
        elif t < seconds:
            env = 1.0
        else:
            env = max(0.0, 1 - (t - seconds) / release) ** 2
        out[i] *= env * 0.5
    return out


def bell(note, seconds=2.4):
    """A soft bell (two-operator FM) for the arpeggio."""
    f = freq(note)
    count = int(seconds * RATE)
    out = [0.0] * count
    sin, exp = math.sin, math.exp
    w = 2 * math.pi * f / RATE
    for i in range(count):
        t = i / RATE
        mod = sin(w * 3.5 * i) * 0.9 * exp(-t * 5)
        out[i] = sin(w * i + mod) * exp(-t * 2.2) * min(1.0, t * 400)
    # A gentle low-pass (one pole, about 4 kHz): a soft bell, not a bright one.
    a = 1 - math.exp(-2 * math.pi * 4000 / RATE)
    y = 0.0
    for i in range(count):
        y += a * (out[i] - y)
        out[i] = y
    return out


def bass(note, seconds):
    f = freq(note)
    count = int((seconds + 0.6) * RATE)
    w = 2 * math.pi * f / RATE
    out = [0.0] * count
    for i in range(count):
        t = i / RATE
        env = min(1.0, t * 8) * (1.0 if t < seconds else max(0.0, 1 - (t - seconds) / 0.6))
        out[i] = (math.sin(w * i) + 0.25 * math.sin(2 * w * i)) * env
    return out


def delay(track, seconds=BEAT * 0.75, feedback=0.38, mix=0.32):
    """A ping-pong echo: space without a reverb."""
    d = int(seconds * RATE)
    left, right = track.left, track.right
    wet_l, wet_r = [0.0] * track.n, [0.0] * track.n
    for i in range(d, track.n):
        wet_l[i] = right[i - d] * mix + wet_r[i - d] * feedback
        wet_r[i] = left[i - d] * mix + wet_l[i - d] * feedback
    for i in range(track.n):
        left[i] += wet_l[i]
        right[i] += wet_r[i]


def compose():
    random.seed(20261025)
    seconds = BARS * BAR + TAIL
    music = Track(seconds)
    bells = Track(seconds)
    for bar in range(BARS):
        root, notes = CHORDS[bar % len(CHORDS)]
        start = bar * BAR
        last = bar == BARS - 1
        length = BAR + (TAIL - 2 if last else 0.2)
        for k, note in enumerate(notes[:4]):
            music.add(start, pad(note, length), pan=(-0.5, 0.5, -0.25, 0.25)[k], gain=0.10)
        if bar >= 2:                                   # the bass comes in on the third bar
            music.add(start, bass(root, BAR * 0.95 if not last else length), gain=0.16)
        if 4 <= bar < BARS - 1:                        # the arpeggio from bar five
            pattern = [0, 2, 4, 3, 1, 3, 2, 4] if bar % 2 else [0, 1, 2, 4, 3, 2, 1, 3]
            for step, index in enumerate(pattern):
                if bar >= BARS - 3 and step % 2:         # thinner before the end
                    continue
                note = notes[index] + 12
                bells.add(start + step * BEAT / 2, bell(note), pan=(-0.6 if step % 2 else 0.6),
                          gain=0.07 if step % 4 else 0.09)
    delay(bells)
    for i in range(music.n):
        music.left[i] += bells.left[i]
        music.right[i] += bells.right[i]
    # Fade in and out, then normalise to -1 dBFS.
    fade_in, fade_out = int(1.5 * RATE), int(TAIL * RATE)
    for i in range(fade_in):
        g = i / fade_in
        music.left[i] *= g
        music.right[i] *= g
    for k in range(fade_out):
        i = music.n - 1 - k
        g = (k / fade_out) ** 1.5
        music.left[i] *= g
        music.right[i] *= g
    peak = max(max(map(abs, music.left)), max(map(abs, music.right)))
    scale = 10 ** (-1 / 20) / peak
    return music, scale


def write_wav(path, music, scale):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        frames = bytearray()
        for left, right in zip(music.left, music.right):
            frames += struct.pack("<hh", int(left * scale * 32767), int(right * scale * 32767))
        out.writeframes(bytes(frames))


def render(svg_text, path, width, height):
    svg = path.with_suffix(".svg")
    svg.write_text(svg_text, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), str(svg), "-o", str(path)], check=True)


def end_card(logo_svg):
    """The video's last picture: VeltOS' navy (#050818-#0E1846) with a soft
    blue glow and the logo in the middle."""
    inner = logo_svg[logo_svg.index(">", logo_svg.index("<svg")) + 1:logo_svg.rindex("</svg>")]
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">\n'
            '  <defs>\n'
            '    <linearGradient id="navy" x1="0" y1="0" x2="1" y2="1">\n'
            '      <stop offset="0" stop-color="#050818"/><stop offset="1" stop-color="#0E1846"/>\n'
            '    </linearGradient>\n'
            '    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">\n'
            '      <stop offset="0" stop-color="#4F7CFF" stop-opacity="0.55"/>\n'
            '      <stop offset="0.6" stop-color="#5B3FE0" stop-opacity="0.18"/>\n'
            '      <stop offset="1" stop-color="#5B3FE0" stop-opacity="0"/>\n'
            '    </radialGradient>\n'
            '  </defs>\n'
            '  <rect width="3840" height="2160" fill="url(#navy)"/>\n'
            '  <ellipse cx="1920" cy="1080" rx="1300" ry="900" fill="url(#glow)"/>\n'
            f'  <svg x="1600" y="760" width="640" height="640" viewBox="0 0 64 64">{inner}</svg>\n'
            '</svg>\n')


def main(argv):
    out = Path(argv[1]) if len(argv) > 1 else HERE.parent / "samples"
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())
    print("composing ...")
    music, scale = compose()
    write_wav(work / "bloom.wav", music, scale)
    print("rendering pictures ...")
    shots = [("bloom", "light"), ("flow", "light"), ("glow", "dark"), ("lake", "light")]
    for index, (design, variant) in enumerate(shots):
        render(wallpapers.svg(design, variant), work / f"w{index}.png", 1920, 1080)
    logo = (HERE.parent / "artwork/veltos-logo.svg").read_text(encoding="utf-8")
    (work / "logo.svg").write_text(logo, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", "300", str(work / "logo.svg"), "-o", str(work / "logo.png")], check=True)
    # Cover art: the Bloom wallpaper, square, with the logo.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(work / "w0.png"), "-i", str(work / "logo.png"),
                    "-filter_complex", "[0]crop=1080:1080:420:0,scale=600:600[b];[1]scale=200:-1[l];"
                    "[b][l]overlay=(W-w)/2:(H-h)/2", "-frames:v", "1", str(work / "cover.jpg")], check=True)
    print("encoding the music ...")
    music_path = out / "VeltOS - Bloom.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(work / "bloom.wav"), "-i", str(work / "cover.jpg"),
                    "-map", "0:a", "-map", "1:v", "-c:a", "libmp3lame", "-b:a", "160k", "-c:v", "mjpeg",
                    "-disposition:v", "attached_pic", "-id3v2_version", "3",
                    "-metadata", "title=Bloom", "-metadata", "artist=VeltOS", "-metadata", "album=VeltOS Samples",
                    "-metadata", "date=2026", "-metadata", "genre=Ambient", "-metadata", "track=1",
                    "-metadata", "copyright=CC-BY-SA-4.0 VeltOS Project",
                    "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)", str(music_path)],
                   check=True)
    print("encoding the video ...")
    # Four wallpapers, each 7 s with a slow zoom, 1 s cross-fades, then an
    # end card (the logo glowing on VeltOS' navy); the music as sound.
    render(end_card(logo), work / f"w{len(shots)}.png", 1920, 1080)
    each, fade, fps = 7, 1, 30
    scenes = len(shots) + 1
    inputs, filters = [], []
    for index in range(scenes):
        # One still frame per picture: zoompan makes `d` frames from each
        # input frame (a looped input multiplied them).
        inputs += ["-i", str(work / f"w{index}.png")]
        zoom = "1+0.0006*on" if index % 2 == 0 else "1.13-0.0006*on"
        if index == scenes - 1:
            zoom = "1.06-0.0003*on"                    # the end card settles gently
        filters.append(f"[{index}]scale=3840:2160,zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                       f":d={each * fps}:s=1920x1080:fps={fps},setsar=1[v{index}]")
    chain, offset = "v0", each - fade
    for index in range(1, scenes):
        filters.append(f"[{chain}][v{index}]xfade=transition=fade:duration={fade}:offset={offset}[x{index}]")
        chain = f"x{index}"
        offset += each - fade
    total = each * scenes - fade * (scenes - 1)
    filters.append(f"[{chain}]fade=t=out:st={total - 1.2}:d=1.2,format=yuv420p[v]")
    audio_index = scenes
    inputs += ["-i", str(work / "bloom.wav")]
    filters.append(f"[{audio_index}]atrim=0:{total},afade=t=out:st={total - 3}:d=3[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "24",
                    "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    "-metadata", "title=VeltOS", "-metadata", "copyright=CC-BY-SA-4.0 VeltOS Project",
                    str(out / "VeltOS.mp4")], check=True)
    for path in sorted(out.iterdir()):
        print(f"{path.name}: {path.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    main(sys.argv)
