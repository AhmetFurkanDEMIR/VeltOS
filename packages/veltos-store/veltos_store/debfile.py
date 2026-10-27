"""What a .deb file is, for the package installer window (double-clicking a
.deb, product owner 2026-10-27): its name, version, publisher, size and
description from the control file (`dpkg-deb -f`), the apps it adds and
their icon from its files (`dpkg-deb --fsys-tarfile`, read as a stream,
nothing is unpacked on disk except the icon), and how it compares with an
installed package of the same name (`dpkg-query`, `dpkg --compare-versions`).
No administrator rights; nothing of the package runs."""

import configparser
import re
import subprocess
import tarfile
from pathlib import Path

FIELDS = ("Package", "Version", "Architecture", "Maintainer", "Description", "Installed-Size", "Homepage",
          "Depends", "Section")
ICON_SUFFIXES = (".svg", ".svgz", ".png", ".xpm")
MAX_ICON = 2 * 1024 * 1024


def run(command, timeout=60):
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout,
                                env={"LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})
    except (OSError, subprocess.SubprocessError):
        return 1, b""
    return result.returncode, result.stdout


def parse_control(text):
    """The control file's fields; Description is split into summary and the
    long text (" ." lines are empty lines)."""
    fields, key = {}, None
    for line in text.splitlines():
        if line.startswith((" ", "\t")) and key:
            fields[key] += "\n" + line[1:]
        elif ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip()
    summary, _, long = fields.get("Description", "").partition("\n")
    lines = ["" if line.strip() == "." else line.strip() for line in long.split("\n")]
    fields["Summary"] = summary.strip()
    fields["LongDescription"] = "\n".join(lines).strip()
    return fields


def publisher(maintainer):
    """"Name <mail>" -> "Name"."""
    return re.sub(r"\s*<[^>]*>\s*$", "", maintainer or "").strip()


def desktop_entry(data):
    parser = configparser.RawConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read_string(data.decode("utf-8", "replace"))
    except configparser.Error:
        return None
    if not parser.has_section("Desktop Entry"):
        return None
    entry = dict(parser.items("Desktop Entry"))
    if entry.get("Type", "Application") != "Application" or entry.get("NoDisplay", "").lower() == "true" \
            or entry.get("Hidden", "").lower() == "true" or not entry.get("Exec"):
        return None
    return entry


def icon_rank(path):
    """Bigger is better: scalable, then the largest size."""
    if "/scalable/" in path or path.endswith((".svg", ".svgz")):
        return 10000
    match = re.search(r"/(\d+)x\d+/", path)
    return int(match.group(1)) if match else (1 if "/pixmaps/" in path else 0)


def read_files(path, runner=run):
    """(desktop entries [(file id, entry)], {archive path: icon bytes}) of a
    .deb, reading its data archive as a stream."""
    try:
        process = subprocess.Popen(["dpkg-deb", "--fsys-tarfile", str(path)], stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
    except OSError:
        return [], {}
    entries, icons = [], {}
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|*") as archive:
            for member in archive:
                name = member.name.lstrip("./")
                if not member.isfile():
                    continue
                if name.startswith("usr/share/applications/") and name.endswith(".desktop"):
                    entry = desktop_entry(archive.extractfile(member).read())
                    if entry:
                        entries.append((Path(name).name, entry))
                elif (name.startswith(("usr/share/icons/", "usr/share/pixmaps/")) or "/icons/" in name) \
                        and name.endswith(ICON_SUFFIXES) and member.size <= MAX_ICON:
                    icons[name] = archive.extractfile(member).read()
    except (tarfile.TarError, OSError, EOFError):
        pass
    finally:
        process.stdout.close()
        process.wait()
    return entries, icons


def best_icon(entries, icons):
    """(archive path, bytes) of the first app's icon, or ("", b"")."""
    for _id, entry in entries:
        icon = entry.get("Icon", "")
        if not icon:
            continue
        if icon.startswith("/"):
            data = icons.get(icon.lstrip("/"))
            if data:
                return icon.lstrip("/"), data
            continue
        stem = icon.rsplit(".", 1)[0] if icon.endswith(ICON_SUFFIXES) else icon
        candidates = [p for p in icons if Path(p).stem == stem and "/apps/" in p or
                      (p.startswith("usr/share/pixmaps/") and Path(p).stem == stem)]
        candidates = [p for p in candidates if not p.endswith(".xpm")] or candidates
        if candidates:
            chosen = max(candidates, key=icon_rank)
            return chosen, icons[chosen]
    return "", b""


def installed_version(package, runner=run):
    code, out = runner(["dpkg-query", "-W", "-f", "${db:Status-Abbrev}\t${Version}", package])
    status, _, version = out.decode("utf-8", "replace").partition("\t")
    return version.strip() if code == 0 and status.startswith("ii") else ""


def compare(installed, offered, runner=run):
    """"new", "same", "newer" (the file is newer: an update) or "older"
    (the file is older than what is installed)."""
    if not installed:
        return "new"
    if installed == offered:
        return "same"
    code, _ = runner(["dpkg", "--compare-versions", offered, "gt", installed])
    return "newer" if code == 0 else "older"


def native_arch(runner=run):
    code, out = runner(["dpkg", "--print-architecture"])
    return out.decode().strip() if code == 0 and out.strip() else "amd64"


def foreign_archs(runner=run):
    code, out = runner(["dpkg", "--print-foreign-architectures"])
    return out.decode().split() if code == 0 else []


def read(path, runner=run, files=read_files):
    """Everything the window shows about a .deb, or None when the file is not
    a Debian package dpkg can read."""
    code, out = runner(["dpkg-deb", "-f", str(path), *FIELDS])
    if code != 0 or not out.strip():
        return None
    fields = parse_control(out.decode("utf-8", "replace"))
    name = fields.get("Package", "")
    if not name or not fields.get("Version"):
        return None
    entries, icons = files(path)
    icon_path, icon_data = best_icon(entries, icons)
    arch = fields.get("Architecture", "")
    native = native_arch(runner)
    installed = installed_version(name, runner)
    try:
        size = int(fields.get("Installed-Size", "0")) * 1024
    except ValueError:
        size = 0
    apps = [{"id": desktop_id, "name": entry.get("Name", desktop_id)} for desktop_id, entry in entries]
    return {
        "package": name,
        "version": fields["Version"],
        "arch": arch,
        "archOk": arch in ("all", native) or arch in foreign_archs(runner),
        "nativeArch": native,
        "publisher": publisher(fields.get("Maintainer", "")),
        "summary": fields.get("Summary", ""),
        "description": fields.get("LongDescription", ""),
        "homepage": fields.get("Homepage", ""),
        "size": size,
        "displayName": apps[0]["name"] if apps else name,
        "apps": apps,
        "iconName": Path(icon_path).name if icon_path else "",
        "iconData": icon_data,
        "installed": installed,
        "status": compare(installed, fields["Version"], runner),
    }
