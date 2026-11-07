"""The window draws its own frame (tabs in the title bar) with a soft shadow
around it; clicks on the shadow must reach what is behind the window."""

from PySide6.QtGui import QRegion


def follow_frame(window):
    """The input region is the frame only (the mask is an input region on
    Wayland), kept up to date while the window is resized or maximised."""
    def update(*_args):
        margin = int(window.property("shadow") or 0)
        if margin:
            window.setMask(QRegion(margin, margin, max(1, window.width() - 2 * margin),
                                   max(1, window.height() - 2 * margin)))
        else:
            window.setMask(QRegion())
    for signal in (window.widthChanged, window.heightChanged, window.visibilityChanged):
        signal.connect(update)
    update()
