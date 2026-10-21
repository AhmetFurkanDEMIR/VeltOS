# veltos-camera

VeltOS Camera: Windows 11's Camera app on VeltOS.

## What the user sees

- The camera picture fills the window (black around it).
- Right: "Change camera" at the top when there is more than one camera,
  the Photo/Video switch, the shutter (white disc for photos, red for
  videos, a red square while recording) and, at the bottom, the last
  photo or video (opens it).
- Left: Settings and, for photos, the photo timer (Off, 2, 5, 10 s; the
  count-down shows in the middle; pressing the shutter again cancels it).
- While recording: the time at the top with a red dot.
- Settings (from the left): framing grid (None, Rule of thirds, Square,
  Crosshairs), "Record audio with videos", save location with "Open
  folder".
- Without a camera: "We can't find your camera" and what to check, as
  Windows says it (Windows' Microsoft error code is not copied).
- Space or Enter takes a photo / starts and stops a video; Esc closes
  Settings.
- Photos and videos go to Pictures > Camera Roll ("Film Rulosu" in
  Turkish, as Windows names it), named `IMG_YYYYMMDD_HHMMSS.jpg` and
  `VID_YYYYMMDD_HHMMSS.mp4`. English and Turkish.

## How it works

| File | Role |
|---|---|
| `veltos_camera/qml/Main.qml` | The window; Qt Multimedia's `CaptureSession` with `Camera`, `ImageCapture`, `MediaRecorder` and (videos, if allowed) `AudioInput` |
| `veltos_camera/app.py` | `Backend`: file names, save folder, last capture, settings (`~/.config/veltos/camera.conf`) |
| `veltos_camera/files.py` | XDG Pictures folder, Camera Roll, names, newest capture |
| `veltos_camera/strings.py` | Texts |
| `veltos_camera/qml/Glyph.qml` | Line icons (VeltOS drawings) |

Qt Multimedia 6.8 in Debian 13 (`libqt6multimedia6`) uses its FFmpeg
backend, which reads V4L2 cameras and encodes videos with FFmpeg.

## Tested / not tested

- Unit tests: file names, folders, newest capture, texts; the window
  offscreen in English and Turkish without a camera (no-camera state,
  modes, timer, settings, last capture).
- **Not tested with a real camera**: the test VMs (QEMU) have no camera.
  Taking photos and videos is untested until it runs on hardware (or in
  VirtualBox with a host webcam attached).

## Not included

Windows' Document, Barcode and Panorama modes, HDR, zoom and the quality
settings.
