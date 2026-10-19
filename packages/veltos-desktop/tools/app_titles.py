"""Windows-familiar program names inside the programs themselves.

KDE programs show their name in every window title ("Home — Dolphin") and
in their About dialogs; Qt appends it from the program's own (translated)
display name. VeltOS ships tiny message catalogs for the pseudo-languages
"en@veltos" and "tr@veltos" that translate only those names, and the
session script puts the matching pseudo-language first in LANGUAGE
("tr@veltos:tr"). For every other text KDE falls through to the real
language, so nothing else changes and no package file is modified.

The message ids and contexts were read from the Debian trixie catalogs of
these programs (2026-10-19); tests/test_build_assets.py checks the table.
"""

import subprocess
from pathlib import Path

PSEUDO_LANGUAGES = {"en": "en@veltos", "tr": "tr@veltos"}

# (translation domain, msgctxt or None, msgid) -> (English, Turkish)
TITLES = {
    ("dolphin", None, "Dolphin"): ("File Explorer", "Dosya Gezgini"),
    ("kate", None, "KWrite"): ("Text Editor", "Metin Düzenleyici"),
    ("kwrite", None, "KWrite"): ("Text Editor", "Metin Düzenleyici"),
    ("kate", None, "KWrite - Text Editor"): ("Text Editor", "Metin Düzenleyici"),
    ("dolphin", "@info:status", "Dolphin does not support web pages, the web browser has been launched"):
        ("File Explorer does not open web pages; the web browser has been started",
         "Dosya Gezgini web sayfalarını açmaz; web tarayıcısı başlatıldı"),
    ("konsole", "@title", "Konsole"): ("Terminal", "Terminal"),
    ("konsole", None, "Konsole"): ("Terminal", "Terminal"),
    ("gwenview", None, "Gwenview"): ("Photos", "Fotoğraflar"),
    ("okular", None, "Okular"): ("Document Viewer", "Belge Görüntüleyici"),
    ("ark", None, "Ark"): ("Archive Manager", "Arşiv Yöneticisi"),
    ("spectacle", None, "Spectacle"): ("Screenshot", "Ekran Görüntüsü"),
    ("plasma-systemmonitor", None, "System Monitor"): ("Task Manager", "Görev Yöneticisi"),
    ("kinfocenter", None, "Info Center"): ("System Information", "Sistem Bilgisi"),
    ("systemsettings", None, "Info Center"): ("System Information", "Sistem Bilgisi"),
    ("systemsettings", None, "System Settings"): ("Control Panel", "Denetim Masası"),
    ("plasma-discover", None, "Discover"): ("Store", "Mağaza"),
    ("partitionmanager", "@title:window", "KDE Partition Manager"): ("Disk Management", "Disk Yönetimi"),
}


def po_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def catalog_po(entries):
    """A minimal .po file for one domain and language."""
    lines = ['msgid ""', 'msgstr ""', '"Content-Type: text/plain; charset=UTF-8\\n"', ""]
    for context, msgid, translation in entries:
        if context:
            lines.append(f'msgctxt "{po_escape(context)}"')
        lines += [f'msgid "{po_escape(msgid)}"', f'msgstr "{po_escape(translation)}"', ""]
    return "\n".join(lines)


def build(root, tmp_dir):
    """Compile the catalogs into <root>/usr/share/locale/<pseudo>/LC_MESSAGES/."""
    by_catalog = {}
    for (domain, context, msgid), names in TITLES.items():
        for index, (lang, pseudo) in enumerate(PSEUDO_LANGUAGES.items()):
            by_catalog.setdefault((pseudo, domain), []).append((context, msgid, names[index]))
    written = []
    for (pseudo, domain), entries in sorted(by_catalog.items()):
        po = Path(tmp_dir) / f"{pseudo}-{domain}.po"
        po.write_bytes(catalog_po(entries).encode("utf-8"))
        mo = Path(root) / "usr/share/locale" / pseudo / "LC_MESSAGES" / f"{domain}.mo"
        mo.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["msgfmt", "--check", "--output-file", str(mo), str(po)], check=True)
        written.append(mo)
    return written
