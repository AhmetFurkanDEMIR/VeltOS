"""MSI laptops' keyboard light through MSI's embedded-controller driver,
msi-ec, built on the PC with DKMS.

Checked on 2026-10-28 against Debian 13's kernel 6.12.113+deb13-amd64:
Debian builds the kernel's own msi-ec (CONFIG_MSI_EC=m, loaded on MSI
laptops by DMI), but that version offers only the battery charge limits.
Its tables know where the keyboard light is, yet it registers no LED, so
VeltOS Keyboard Lighting found nothing on an MSI Katana (product owner,
2026-10-28). The driver's own project (github.com/BeardOverflow/msi-ec,
GPL-2.0-or-later) registers "msiacpi::kbd_backlight" (brightness 0-3) for
the EC firmware versions it knows, Katana GF66/GF76, Katana 15/17 B11-B13
and many others among them; Keyboard Lighting and UPower then find it like
any other keyboard light. Newer RGB models (Katana 15 HX B14W, Katana 17
B13V, Katana A15/A17 AI) have no keyboard light in its tables either.

VeltOS ships that source at a pinned commit (upstream.json) and builds it
when the user asks for it (Keyboard Lighting): dkms and the kernel headers
come from Debian through PackageKit first. With Secure Boot, Debian's DKMS
signs the module with its own key (/var/lib/dkms/mok.key), which the
firmware accepts once it is enrolled (mokutil, as for NVIDIA's driver).

The upstream module has no DMI table and does not load by itself; on the
MSI laptop it was built on, /etc/modules-load.d/veltos-msi-ec.conf loads it
at every start. The EC's firmware version (12 characters at 0xa0, read the
same way as msi-ec reads it) comes from the kernel's EC debug file, which
Debian builds in (CONFIG_ACPI_EC_DEBUGFS=y, read-only without the
ec_sys.write_support boot option): Keyboard Lighting can tell before any
download whether msi-ec knows the laptop. Nothing here writes to the EC.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

NAME = "msi-ec"
MODULE = "msi_ec"
SHARE = Path("/usr/share/veltos-msi-ec")
SOURCE = SHARE / "src"
SUPPORT = SHARE / "support.json"
USR_SRC = Path("/usr/src")
EC_IO = Path("/sys/kernel/debug/ec/ec0/io")
FW_ADDRESS, FW_LENGTH = 0xA0, 12            # ec_memory_configuration.h
DMI = Path("/sys/class/dmi/id")
PLATFORM = Path("/sys/devices/platform/msi-ec")
LED = Path("/sys/class/leds/msiacpi::kbd_backlight")
MODULES_LOAD = Path("/etc/modules-load.d/veltos-msi-ec.conf")
MOK_KEY = Path("/var/lib/dkms/mok.pub")
# The packages DKMS needs (Debian 13), without the running kernel's headers,
# which headers_package() adds.
PACKAGES = ("dkms", "linux-headers-amd64")
PATH = "/usr/sbin:/usr/bin:/sbin:/bin"


def run(command, timeout=1800):
    """(exit code, stdout + stderr) of a command, in the C locale."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env={"PATH": PATH, "LC_ALL": "C", "LANGUAGE": "C"})
    except (OSError, subprocess.SubprocessError) as error:
        return 1, str(error)
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def version(source=SOURCE):
    """The pinned driver's version, as its dkms.conf names it."""
    match = re.search(r'^PACKAGE_VERSION="([^"]+)"', read(Path(source) / "dkms.conf"), re.M)
    return match.group(1) if match else ""


def is_msi(dmi=DMI):
    return "micro-star" in read(Path(dmi) / "sys_vendor").lower()


def model(dmi=DMI):
    return read(Path(dmi) / "product_name")


def headers_package(kernel=None):
    return f"linux-headers-{kernel or os.uname().release}"


def firmware(io=EC_IO, platform=PLATFORM):
    """The EC firmware version ("1585EMS1.112"), or "" when it cannot be
    read (not root, no EC, not an MSI EC)."""
    text = read(Path(platform) / "fw_version")       # msi-ec's own, once it runs
    if not text:
        try:
            with open(io, "rb") as fh:
                fh.seek(FW_ADDRESS)
                text = fh.read(FW_LENGTH).decode("ascii", "replace")
        except OSError:
            text = ""
    text = text.strip("\x00 \n")
    return text if re.fullmatch(r"[\x21-\x7e]{%d}" % FW_LENGTH, text) else ""


def support(fw, table=SUPPORT):
    """What the pinned msi-ec offers for a firmware version:
    {"known": bool, "keyboard": bool, "models": "Katana GF66 11UC / 11UD"}."""
    try:
        data = json.loads(Path(table).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    entry = data.get(fw) if fw else None
    if not isinstance(entry, dict):
        return {"known": False, "keyboard": False, "models": ""}
    return {"known": True, "keyboard": bool(entry.get("keyboard")), "models": str(entry.get("models", ""))}


def dkms_versions(runner=run):
    """The msi-ec versions DKMS knows ("dkms status": "msi-ec/0.13, 6.12...: installed")."""
    code, out = runner(["dkms", "status", NAME])
    if code != 0:
        return []
    found = re.findall(rf"^{re.escape(NAME)}[/,]\s*([^,:\s]+)", out, re.M)
    return sorted(set(found))


def status(io=EC_IO, platform=PLATFORM, led=LED, dmi=DMI, table=SUPPORT, modules_load=MODULES_LOAD):
    """What Keyboard Lighting shows before and after the installation."""
    fw = firmware(io, platform) if is_msi(dmi) else ""
    return {"msi": is_msi(dmi), "model": model(dmi), "firmware": fw, "support": support(fw, table),
            "installed": Path(modules_load).exists(), "running": Path(platform).is_dir(),
            "light": Path(led).is_dir()}


def install(runner=run, kernel=None, source=SOURCE, usr_src=USR_SRC, modules_load=MODULES_LOAD, led=LED):
    """Builds msi-ec for the running kernel with DKMS and loads it in place
    of the kernel's own. Returns {"ok", "reason", "log"}: reason "" (the
    keyboard light is there), "nolight" (msi-ec runs, the laptop's firmware
    has no keyboard light in it), "unsupported" (msi-ec does not know the
    firmware), "key" (Secure Boot refused the module: its key is not
    enrolled), "nodkms", "build", "load" or "source"."""
    log = []

    def step(command):
        code, out = runner(command)
        log.append(f"$ {' '.join(command)}\n{out.rstrip()}\n(exit {code})\n")
        return code, out

    def result(reason):
        return {"ok": reason in ("", "nolight"), "reason": reason, "log": "".join(log)}

    ver = version(source)
    if not ver:
        return result("source")
    if step(["dkms", "--version"])[0] != 0:
        return result("nodkms")
    kernel = kernel or os.uname().release
    for old in dkms_versions(runner):
        if old != ver:
            step(["dkms", "remove", f"{NAME}/{old}", "--all"])
            shutil.rmtree(Path(usr_src) / f"{NAME}-{old}", ignore_errors=True)
    target = Path(usr_src) / f"{NAME}-{ver}"
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(source, target)
    if ver not in dkms_versions(runner):
        step(["dkms", "add", "-m", NAME, "-v", ver])
    if step(["dkms", "install", "-m", NAME, "-v", ver, "-k", kernel, "--force"])[0] != 0:
        return result("build")
    Path(modules_load).parent.mkdir(parents=True, exist_ok=True)
    Path(modules_load).write_text("# MSI's keyboard light and battery limits (veltos-msi-ec, VeltOS Keyboard "
                                  "Lighting)\nmsi-ec\n", encoding="utf-8")
    step(["modprobe", "-r", MODULE])           # the kernel's own msi-ec, loaded on MSI laptops
    code, out = step(["modprobe", MODULE])
    if code == 0:
        return result("" if Path(led).is_dir() else "nolight")
    if "Key was rejected" in out or "Required key not available" in out:
        return result("key")                   # loads once the key is enrolled (next start)
    # It cannot run on this laptop: take it out again, or it would stay in
    # place of the kernel's own msi-ec and the battery charge limits with it
    # (dev VM, 2026-10-28: "No such device" without an MSI EC).
    log.append(remove(runner, usr_src, modules_load)["log"])
    return result("unsupported" if "Operation not supported" in out else "load")


def remove(runner=run, usr_src=USR_SRC, modules_load=MODULES_LOAD):
    """Takes msi-ec out again; the kernel's own msi-ec comes back."""
    log = [runner(["modprobe", "-r", MODULE])[1]]
    for ver in dkms_versions(runner):
        log.append(runner(["dkms", "remove", f"{NAME}/{ver}", "--all"])[1])
    for folder in Path(usr_src).glob(f"{NAME}-*"):
        shutil.rmtree(folder, ignore_errors=True)
    Path(modules_load).unlink(missing_ok=True)
    runner(["modprobe", MODULE])
    return {"ok": True, "reason": "", "log": "\n".join(log)}


def upgrade(runner=run, **paths):
    """After a package update: builds the new pinned version where msi-ec
    was installed before (nothing on other PCs)."""
    modules_load = paths.get("modules_load", MODULES_LOAD)
    if not Path(modules_load).exists():
        return {"ok": True, "reason": "", "log": ""}
    if version(paths.get("source", SOURCE)) in dkms_versions(runner):
        return {"ok": True, "reason": "", "log": ""}
    return install(runner, **paths)
