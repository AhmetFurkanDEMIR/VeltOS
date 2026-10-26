# Taskbar audio badge (2026-10-26, dev VM)

Item 39 of the product owner's list. VeltOS Media Player played a 12-second
test tone in the QEMU dev VM before and after installing the rebuilt
`veltos-desktop` package.

| Picture | What it shows |
|---|---|
| `speaker-badge-before.png` | Before the package update: Media Player is playing and its taskbar icon has a speaker badge. |
| `speaker-badge-removed.png` | After the update and Plasma session restart: Media Player is playing, but its taskbar icon has no speaker badge. |

The Media Player's pause button and advancing playback position confirmed
that the app was playing in both captures. Audio output itself was not
evaluated.
