# Taskbar follows light/dark and the accent (2026-10-24)

Dev VM (live, Turkish session), VeltOS Settings > Personalization > Colours.

Scripted, as Settings does it (`out/vm/theme-loop.sh`, `accent-loop.sh`):
six light/dark switches and seven accent/mode changes, the taskbar's
background and the active app's line sampled after each (all followed):

```
1 dark bar (38, 41, 51)      2 light bar (234, 237, 243)   ... (6 of 6)
accent #E81123 line (232, 17, 35)   accent #107C10 line (16, 124, 16)
mode light line (16, 124, 16)       accent #8764B8 line (135, 100, 184)
mode dark  line (135, 100, 184)     mode light line (135, 100, 184)
accent #0078D4 line (0, 120, 212)
```

Through the window with the fix: "Koyu" then the red accent 0.5 s later:
line (231, 72, 86), bar (41, 39, 46); light, green, dark within ~2 s:
line (16, 137, 62), bar (36, 41, 45), kdeglobals AccentColor=16,137,62,
LookAndFeelPackage=org.veltos.dark, plasmarc name=VeltOS-Dark.
