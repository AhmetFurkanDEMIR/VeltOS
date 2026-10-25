# Windows 11's media card above Quick Settings (2026-10-25, dev VM)

Item 27 of the product owner's 2026-10-23 list. QEMU dev VM (Turkish
session) with this change's `veltos-desktop`, `veltos-settings` and
`veltos-media`; the sample song and video (`/usr/share/veltos/samples`)
played in VeltOS Media Player.

| Picture | What it shows |
|---|---|
| `card-playing.png` | Quick Settings with the media card above it: Media Player's icon and name, "Bloom" / "VeltOS", the cover on the right, Previous / Pause / Next (Next greyed: nothing follows in the queue) |
| `card-paused-from-the-card.png` | The card's Pause clicked: Media Player paused (MPRIS `PlaybackStatus` read back as "Paused"), the button turned to Play ("Oynat") |
| `two-sessions-song.png`, `two-sessions-video.png` | Two players: arrows at the top right; ">" ("Sonraki medya oturumu") goes to the video, shown with its thumbnail |
| `two-players-desktop.png` | The whole screen with both players |
| `tray-before.png`, `tray-after.png` | The "^" overflow before and after: Plasma's own media item is gone (the session fix-up removes it from older trays; new users never get it) |

VeltOS Media Player had no MPRIS, so nothing it played reached any media
control. It now registers `org.mpris.MediaPlayer2.veltos_media.instance<pid>`
(Gio); `gdbus ... Properties.GetAll` in the VM returned PlaybackStatus,
Metadata (title, artist, album, track, length, cover file), Position,
CanGoNext/CanGoPrevious/CanSeek and Volume, and `Player.Play` started
playback. Plasma's own model (`org.kde.plasma.private.mpris`) was read
with a small QML probe and reported the same player, track and cover.

Not tested: other players (Firefox, Spotify) in the card, media keys,
real audio output (the VM has no sound card to listen to).
