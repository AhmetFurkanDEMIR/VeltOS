# veltos-media

VeltOS Media Player: music and videos in the layout of Windows 11's Media
Player (PySide6 + QML, Qt Multimedia with its FFmpeg backend). It opens
audio and video files by default (veltos-desktop's `update-app-names`
writes the default apps).

- **Window**: navigation pane (search, Home, Music library, Video library,
  Play queue, Playlists with the playlists, Settings), the pages, the
  player bar at the bottom, "now playing" over the pages. Own frame and
  shadow (`frame.py`). The search box is in the Tab order and shows the
  text (I-beam) pointer, like a Windows text box.
- **Home**: Open file(s), recent media (the last played songs and videos).
- **Music library** (`library.py`): the songs of the Music folder (XDG
  user folder) and added folders with their tags read by mutagen (title,
  artist, album, album artist, track, disc, year, genre, length) and the
  cover picture (embedded in MP3/FLAC/MP4/Ogg, else cover.jpg/folder.jpg
  next to the files; embedded ones are kept once in
  `~/.cache/veltos/media-covers`). Songs, Albums and Artists tabs, an
  album or artist opens its songs, "Shuffle and play", "Play all". The
  index is cached in `~/.cache/veltos/media-index.json`.
- **Video library**: the videos of the Videos folder with their frames
  (shared thumbnail cache, ffmpegthumbnailer), newest first.
- **Play queue** (`playqueue.py`): shuffle (the playing item stays
  first), repeat off/all/one, previous goes back to the start first (3 s,
  like Windows), remove, clear; Play, Play next, Add to the play queue or
  a playlist from the item menus.
- **Playlists**: create, add songs, remove, delete, play all (kept in
  `~/.config/veltos/media.conf`).
- **Player bar**: picture, title and artist (opens "now playing"),
  shuffle, previous, play/pause, next, repeat, the seek bar with times,
  mute, volume (logarithmic) and full screen. Its two sides are equally
  wide, so the buttons and the seek bar stay in the middle of the window
  at every size, also in full screen (product owner, 2026-10-22). The
  logarithmic volume is computed in the QML: Qt 6.8 does not offer
  `QtAudio.convertVolume` to QML, and the old call left the volume at
  100 %. **Now playing**: the video (click pauses, double click full
  screen, controls hide in full screen), or a song's album picture on a
  blurred copy of it.
- Keys: Space/Ctrl+P play/pause, Ctrl+F next, Ctrl+B previous, Ctrl+H
  shuffle, Ctrl+T repeat, Ctrl+O open, F11 full screen, arrows seek 10 s,
  F8/F9/F10 mute/volume.
- **Settings**: library locations (add, remove, refresh), app theme,
  about. English and Turkish.

Not yet: MPRIS (the desktop's media controls), mini player, video
subtitles and audio track choice.

Tests: `tests/test_library.py` (queue logic; tags of real WAV files written
with mutagen) and `tests/test_ui.py` (the window offscreen in English and
Turkish: pages, playing the queue, playlists, volume).
