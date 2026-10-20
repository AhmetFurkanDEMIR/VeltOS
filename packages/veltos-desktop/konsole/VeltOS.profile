# VeltOS terminal profile: the look of Windows Terminal's default profile
# (Campbell colours, Cascadia Mono 12, bar cursor, 120 x 30, 9001 lines of
# history). Made the default by /etc/xdg/konsolerc.
# SPDX-License-Identifier: GPL-3.0-or-later

[Appearance]
ColorScheme=VeltOS-Campbell
Font=Cascadia Mono,12,-1,5,400,0,0,0,0,0,0,0,0,0,0,1

[Cursor Options]
CursorShape=1

[General]
Name=VeltOS
Parent=FALLBACK/
TerminalColumns=120
TerminalRows=30
TerminalMargin=8
LocalTabTitleFormat=%w
RemoteTabTitleFormat=%w
ShowTerminalSizeHint=false

[Interaction Options]
AutoCopySelectedText=false
TrimLeadingSpacesInSelectedText=true
TrimTrailingSpacesInSelectedText=true

[Scrolling]
HistoryMode=1
HistorySize=9001
ScrollBarPosition=1

[Terminal Features]
BlinkingCursorEnabled=true
