#!/usr/bin/env python3
"""After a release (GitHub Actions): the website and the README name the new
release, its ISO, size, date and SHA-256.

    update-site.py --version 1.2 --iso-url URL --size BYTES --sha256 HEX [--date 2026-12-01]

Only marked places change, so no other text is rewritten by accident (a
measurement "on VeltOS 1.0" stays as it was):

- docs/index.html: the meta tags `veltos-version`, `veltos-release-date`,
  `veltos-iso-url`, `veltos-iso-sha256` and `veltos-iso-size` (main.js
  fills the page's texts from them in English and Turkish, and shows what
  a release adds, `data-since`, once it is released), the English text of
  every element with `data-release="version|size|sha256|iso-name|date"`
  and the `href` of `data-release="sha-url"` links (the page without
  JavaScript, search engines), and the structured data's softwareVersion,
  datePublished, downloadUrl and fileSize;
- README.md: the block between `<!-- release:start -->` and
  `<!-- release:end -->`;
- docs/sitemap.xml: `<lastmod>`, the release's date.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December")


def size_text(size, lang="en"):
    """2.1 GB (main.js writes the same, 2,1 GB in Turkish)."""
    text = f"{size / 1e9:.1f} GB"
    return text.replace(".", ",") if lang == "tr" else text


def date_text(day):
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def values(version, url, size, sha, day):
    name = url.rsplit("/", 1)[-1]
    tag = f"https://github.com/AhmetFurkanDEMIR/VeltOS/releases/tag/v{version}"
    return {"version": version, "iso-url": url, "iso-name": name, "size": size_text(size),
            "sha256": sha, "sha-url": url + ".sha256", "bytes": str(size), "release-url": tag,
            "date": day.isoformat(), "date-text": date_text(day)}


def update_html(html, v):
    def meta(text, name, value):
        new, count = re.subn(rf'(<meta name="{name}" content=")[^"]*(")', rf"\g<1>{value}\g<2>", text)
        if count != 1:
            raise SystemExit(f"docs/index.html: meta {name} not found once ({count})")
        return new
    html = meta(html, "veltos-version", v["version"])
    html = meta(html, "veltos-release-date", v["date"])
    html = meta(html, "veltos-iso-url", v["iso-url"])
    html = meta(html, "veltos-iso-sha256", v["sha256"])
    html = meta(html, "veltos-iso-size", v["bytes"])
    for key, value in (("version", v["version"]), ("size", v["size"]), ("sha256", v["sha256"]),
                       ("iso-name", v["iso-name"]), ("date", v["date-text"])):
        html = re.sub(rf'(<(\w+)\b[^>]*\bdata-release="{key}"[^>]*>)[^<]*(</\2>)',
                      lambda m, value=value: m.group(1) + value + m.group(3), html)
    html = re.sub(r'(<a\b[^>]*\bdata-release="sha-url"[^>]*\bhref=")[^"]*(")', rf"\g<1>{v['sha-url']}\g<2>", html)
    for field, value in (("softwareVersion", v["version"]), ("datePublished", v["date"]),
                         ("downloadUrl", v["iso-url"]), ("fileSize", v["size"])):
        html, count = re.subn(rf'("{field}": ")[^"]*(")', rf"\g<1>{value}\g<2>", html)
        if count != 1:
            raise SystemExit(f"docs/index.html: structured data {field} not found once ({count})")
    return html


def readme_block(v):
    return (f"<!-- release:start -->\n"
            f"| | |\n|---|---|\n"
            f"| ISO | [{v['iso-name']}]({v['iso-url']}) ({v['size']}, 64-bit) |\n"
            f"| SHA-256 | `{v['sha256']}` |\n"
            f"| Release notes | [GitHub release v{v['version']}]({v['release-url']}) ({v['date-text']}) |\n\n"
            f"Check the download: `sha256sum -c {v['iso-name']}.sha256` (Linux, with\n"
            f"the [.sha256 file]({v['sha-url']}))\n"
            f"or `Get-FileHash {v['iso-name']}` (Windows PowerShell).\n"
            f"<!-- release:end -->")


def update_readme(text, v):
    new, count = re.subn(r"<!-- release:start -->.*?<!-- release:end -->", lambda _m: readme_block(v), text,
                         flags=re.S)
    if count != 1:
        raise SystemExit("README.md: the release block (<!-- release:start --> ... end) not found once")
    return new


def update_sitemap(text, v):
    new, count = re.subn(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{v['date']}</lastmod>", text)
    if not count:
        raise SystemExit("docs/sitemap.xml: no <lastmod>")
    return new


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True)
    parser.add_argument("--iso-url", required=True)
    parser.add_argument("--size", required=True, type=int)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).date().isoformat())
    parser.add_argument("--root", default=str(REPO))
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
        raise SystemExit("--sha256: 64 hexadecimal digits")
    if not re.fullmatch(r"\d+\.\d+", args.version):
        raise SystemExit("--version: MAJOR.MINOR (1.2)")
    v = values(args.version, args.iso_url, args.size, args.sha256, datetime.date.fromisoformat(args.date))
    root = Path(args.root)
    for rel, update in (("docs/index.html", update_html), ("README.md", update_readme),
                        ("docs/sitemap.xml", update_sitemap)):
        path = root / rel
        path.write_text(update(path.read_text(encoding="utf-8"), v), encoding="utf-8", newline="\n")
        print(f"{rel}: VeltOS {v['version']}, {v['size']}, {v['date']}, {v['sha256'][:12]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
