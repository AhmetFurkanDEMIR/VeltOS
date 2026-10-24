# Sample pictures, music and video (2026-10-25, dev VM)

Item 14 of the product owner's 2026-10-23 list. veltos-desktop installs
`/usr/share/veltos/samples/`: `Wallpapers/` (every VeltOS wallpaper,
light and dark, as links to the 3840x2160 pictures), `Music/VeltOS -
Bloom.mp3` (63 s, synthesized by `tools/sample-media.py`, with tags and
cover art) and `Videos/VeltOS.mp4` (31 s, 1920x1080 H.264 + AAC, the
wallpapers with slow zooms and cross-fades, an end card with the logo,
the song as sound). Photos and Media Player include these folders in
their default libraries.

| Picture | What it shows |
|---|---|
| `photos-wallpapers-and-sample-video.png` | Photos: 17 items (16 wallpapers and the video), folders "Duvar kağıtları" and "Örnek videolar" |
| `media-album-with-cover.png` | Media Player > Music > Albums: "VeltOS Samples" with its cover |
| `media-playing-bloom.png` | The song playing (0:02 of 1:03) |
| `media-video-library.png` | Media Player > Videos: "VeltOS", 0:31 |
| `video-end-card-and-music-spectrum.png` | Frames at 22/26/28/30 s and the song's spectrum (left: the softened bells used; right: the first, brighter version) |

The song was checked by its levels (mean -13.3 dB, peak -1.4 dB) and
spectrum, not by listening.
