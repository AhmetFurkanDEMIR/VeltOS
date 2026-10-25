"""MPRIS for VeltOS Media Player: the desktop's media controls (Quick
Settings' media card, Plasma's media keys, the lock screen) see what plays
and can play, pause, skip and seek, as Windows' media controls do with its
Media Player.

The D-Bus side uses Gio (PyGObject): Qt's event loop on Linux is GLib's,
so Gio's callbacks run in the program's main thread. The player is the
QML MediaPlayer (objectName "player"); the window's own functions
`togglePlay()` and `previous()` keep Windows' behaviour (Previous goes back
to the start of the song first).

Plain functions (`status`, `metadata`, `track_id`, `variant`) are tested without D-Bus.
"""

import hashlib
import os
from pathlib import Path, PurePosixPath

BUS_NAME = "org.mpris.MediaPlayer2.veltos_media"
PATH = "/org/mpris/MediaPlayer2"
ROOT_IFACE = "org.mpris.MediaPlayer2"
PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
DESKTOP_ENTRY = "veltos-media"

# Qt Multimedia's MediaPlayer.playbackState values.
STOPPED, PLAYING, PAUSED = 0, 1, 2

INTROSPECTION = """<node>
  <interface name="org.mpris.MediaPlayer2">
    <method name="Raise"/>
    <method name="Quit"/>
    <property name="CanQuit" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
  </interface>
  <interface name="org.mpris.MediaPlayer2.Player">
    <method name="Next"/>
    <method name="Previous"/>
    <method name="Pause"/>
    <method name="PlayPause"/>
    <method name="Stop"/>
    <method name="Play"/>
    <method name="Seek"><arg direction="in" type="x" name="Offset"/></method>
    <method name="SetPosition">
      <arg direction="in" type="o" name="TrackId"/>
      <arg direction="in" type="x" name="Position"/>
    </method>
    <method name="OpenUri"><arg direction="in" type="s" name="Uri"/></method>
    <signal name="Seeked"><arg type="x" name="Position"/></signal>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="Rate" type="d" access="readwrite"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="MinimumRate" type="d" access="read"/>
    <property name="MaximumRate" type="d" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
  </interface>
</node>"""

MIME_TYPES = ["audio/mpeg", "audio/flac", "audio/ogg", "audio/mp4", "audio/x-wav", "audio/aac",
              "video/mp4", "video/x-matroska", "video/webm", "video/quicktime", "video/x-msvideo"]


def status(state):
    """MPRIS PlaybackStatus of a MediaPlayer playbackState."""
    return {PLAYING: "Playing", PAUSED: "Paused"}.get(state, "Stopped")


def track_id(path):
    """A D-Bus object path naming the track (MPRIS wants one per track)."""
    if not path:
        return "/org/mpris/MediaPlayer2/TrackList/NoTrack"
    return "/org/veltos/media/track/" + hashlib.sha1(path.encode("utf-8")).hexdigest()


def metadata(entry, length_ms=0, picture=""):
    """MPRIS Metadata of a library entry, as {key: (D-Bus type, value)};
    `picture` (a video's thumbnail) stands in for a missing cover."""
    if not entry or not entry.get("path"):
        return {"mpris:trackid": ("o", track_id(""))}
    path = entry["path"]
    title = entry.get("title") or PurePosixPath(path).stem
    data = {
        "mpris:trackid": ("o", track_id(path)),
        "xesam:title": ("s", title),
        "xesam:url": ("s", PurePosixPath(path).as_uri()),
    }
    length = int(length_ms or (entry.get("duration") or 0) * 1000)
    if length > 0:
        data["mpris:length"] = ("x", length * 1000)          # microseconds
    if entry.get("artist"):
        data["xesam:artist"] = ("as", [entry["artist"]])
    if entry.get("album"):
        data["xesam:album"] = ("s", entry["album"])
    if entry.get("albumArtist"):
        data["xesam:albumArtist"] = ("as", [entry["albumArtist"]])
    if entry.get("track"):
        data["xesam:trackNumber"] = ("i", int(entry["track"]))
    cover = entry.get("cover") or picture
    if cover and os.path.isfile(cover):
        data["mpris:artUrl"] = ("s", Path(cover).as_uri())
    return data


def variant(typed):
    """A GLib.Variant of a (D-Bus type, value) pair, dictionaries of such
    pairs (Metadata) included."""
    from gi.repository import GLib
    kind, value = typed
    if kind == "a{sv}":
        value = {key: variant(item) for key, item in value.items()}
    return GLib.Variant(kind, value)


class Service:
    """org.mpris.MediaPlayer2 on the session bus for one Media Player window."""

    def __init__(self, window, player, backend, identity):
        from gi.repository import Gio, GLib
        from PySide6.QtCore import QMetaObject
        self.Gio, self.GLib, self.invoke = Gio, GLib, QMetaObject.invokeMethod
        self.window, self.player, self.backend, self.identity = window, player, backend, identity
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        node = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION)
        self.ids = [self.connection.register_object(PATH, iface, self._call, self._get, self._set)
                    for iface in node.interfaces]
        # One name per running Media Player (MPRIS' ".instance" form).
        self.owner = Gio.bus_own_name_on_connection(self.connection, f"{BUS_NAME}.instance{os.getpid()}",
                                                    Gio.BusNameOwnerFlags.NONE, None, None)
        self._last = {}
        player.stateNumberChanged.connect(self._changed)
        player.durationChanged.connect(self._changed)
        player.seekableChanged.connect(self._changed)
        backend.currentChanged.connect(self._changed)
        backend.queueChanged.connect(self._changed)
        backend.volumeChanged.connect(self._changed)
        # Once more a moment after the start: a state set before the
        # desktop watched the new name, and a video thumbnail made since.
        from PySide6.QtCore import QTimer
        for delay in (1500, 5000):
            QTimer.singleShot(delay, self._announce)

    # --- State ------------------------------------------------------------
    def _picture(self, entry):
        """A video's thumbnail from the shared cache (Media Player makes it
        for its player bar)."""
        if not entry or entry.get("kind") != "video":
            return ""
        from . import thumbs
        return thumbs.cached(entry["path"])

    def _announce(self):
        self._last = {}
        self._changed()

    def _state(self):
        # Main.qml's `stateNumber`: PySide has no converter for
        # QMediaPlayer::PlaybackState read through property() ("Can't find
        # converter", also with PySide6.QtMultimedia loaded; VM 2026-10-25).
        return int(self.player.property("stateNumber") or STOPPED)

    def _player_props(self):
        current = self.backend.queue.current
        state = self._state()
        has = current is not None
        return {
            "PlaybackStatus": ("s", status(state)),
            "Rate": ("d", 1.0),
            "Metadata": ("a{sv}", metadata(current, self.player.property("duration") or 0, self._picture(current))),
            "Volume": ("d", max(0.0, min(1.0, self.backend.volume / 100.0))),
            "MinimumRate": ("d", 1.0),
            "MaximumRate": ("d", 1.0),
            "CanGoNext": ("b", self.backend.queue.has_next()),
            "CanGoPrevious": ("b", has),
            "CanPlay": ("b", has),
            "CanPause": ("b", has),
            "CanSeek": ("b", has and bool(self.player.property("seekable"))),
            "CanControl": ("b", True),
        }

    def _root_props(self):
        return {
            "CanQuit": ("b", True),
            "CanRaise": ("b", True),
            "HasTrackList": ("b", False),
            "Identity": ("s", self.identity),
            "DesktopEntry": ("s", DESKTOP_ENTRY),
            "SupportedUriSchemes": ("as", ["file"]),
            "SupportedMimeTypes": ("as", MIME_TYPES),
        }

    def _changed(self, *_args):
        """PropertiesChanged for what differs from the last announcement."""
        props = self._player_props()
        changed = {k: v for k, v in props.items() if self._last.get(k) != v}
        self._last = props
        if changed:
            body = self.GLib.Variant("(sa{sv}as)", (PLAYER_IFACE,
                                                    {k: variant(v) for k, v in changed.items()}, []))
            self.connection.emit_signal(None, PATH, "org.freedesktop.DBus.Properties", "PropertiesChanged", body)

    # --- D-Bus handlers ---------------------------------------------------
    def _get(self, _connection, _sender, _path, interface, name):
        props = self._root_props() if interface == ROOT_IFACE else self._player_props()
        if name == "Position":
            return self.GLib.Variant("x", int(self.player.property("position") or 0) * 1000)
        return variant(props[name]) if name in props else None

    def _set(self, _connection, _sender, _path, _interface, name, value):
        if name == "Volume":
            self.backend.setVolume(int(round(max(0.0, min(1.0, value.unpack())) * 100)))
        return True                      # Rate stays 1.0

    def _call(self, _connection, _sender, _path, _interface, method, params, invocation):
        args = params.unpack()
        has = self.backend.queue.current is not None
        if method == "Raise":
            self.window.show()
            self.window.raise_()
            self.window.requestActivate()
        elif method == "Quit":
            self.window.close()
        elif method == "Next":
            self.backend.next()
        elif method == "Previous":
            self.invoke(self.window, "previous")
        elif method == "PlayPause":
            self.invoke(self.window, "togglePlay")
        elif method == "Play" and has and self._state() != PLAYING:
            self.invoke(self.player, "play")
        elif method == "Pause" and self._state() == PLAYING:
            self.invoke(self.player, "pause")
        elif method == "Stop":
            self.invoke(self.player, "stop")
        elif method in ("Seek", "SetPosition") and has:
            if method == "SetPosition" and args[0] != track_id(self.backend.queue.current.get("path", "")):
                invocation.return_value(None)
                return
            now = int(self.player.property("position") or 0)
            target = now + args[0] // 1000 if method == "Seek" else args[1] // 1000
            length = int(self.player.property("duration") or 0)
            target = max(0, min(target, length)) if length else max(0, target)
            self.player.setProperty("position", target)
            self.connection.emit_signal(None, PATH, PLAYER_IFACE, "Seeked",
                                        self.GLib.Variant("(x)", (target * 1000,)))
        elif method == "OpenUri" and args[0].startswith("file://"):
            from PySide6.QtCore import QUrl
            self.backend.playPaths([QUrl(args[0]).toLocalFile()], 0)
        invocation.return_value(None)


def start(window, backend, identity):
    """The MPRIS service, or None where there is no session bus or GLib
    (the program plays on without it)."""
    from PySide6.QtCore import QObject
    player = window.findChild(QObject, "player")
    if player is None:
        return None
    try:
        return Service(window, player, backend, identity)
    except Exception as error:          # no D-Bus, no PyGObject: no media controls
        print(f"veltos-media: no MPRIS ({error})", flush=True)
        return None
