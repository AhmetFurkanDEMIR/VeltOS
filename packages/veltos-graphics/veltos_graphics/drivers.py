"""Which driver a graphics card uses and which Debian packages give it the
best one, checked against Debian 13 ("trixie", 2026-10-24):

  * NVIDIA: the proprietary driver from Debian's non-free archive,
    `nvidia-driver` (550.163.01) for current cards, `nvidia-tesla-535-driver`
    for some older data-centre ones; `nvidia-detect` (non-free) says which
    one a card needs. Debian builds its kernel module with DKMS, which needs
    `linux-headers-amd64`. Without it the card uses the open-source Nouveau
    driver from the kernel.
  * AMD and Intel: the drivers are in the kernel (amdgpu, i915/xe) and Mesa;
    the card needs its firmware (`firmware-amd-graphics`,
    `firmware-intel-graphics`, non-free-firmware) and Mesa's Vulkan and
    OpenGL drivers, which "install" makes sure of and "update" updates.
  * Virtual machines: the host's virtual card; nothing to install.

With Secure Boot, the NVIDIA module DKMS builds is signed with
/var/lib/dkms/mok.key; the firmware accepts it once that key is enrolled
(mokutil --import, confirmed in the firmware's MOK manager at the next
start).
"""

import re
import shutil
import subprocess
from pathlib import Path

NVIDIA_DRIVERS = ("nvidia-driver", "nvidia-tesla-535-driver")
NVIDIA_DEFAULT = "nvidia-driver"
KERNEL_HEADERS = "linux-headers-amd64"
OPEN_PACKAGES = {
    "amd": ("firmware-amd-graphics", "mesa-vulkan-drivers", "libgl1-mesa-dri"),
    "intel": ("firmware-intel-graphics", "mesa-vulkan-drivers", "libgl1-mesa-dri"),
}
MOK_KEY = Path("/var/lib/dkms/mok.pub")


def run(command, timeout=60):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env={"LC_ALL": "C", "LANGUAGE": "C", "PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout + result.stderr


def installed_packages(runner=run):
    code, out = runner(["dpkg-query", "-W", "-f", "${Package}\t${db:Status-Abbrev}\t${Version}\n"])
    found = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[1].startswith("ii"):
            found[parts[0].split(":")[0]] = parts[2]
    return found


def loaded_modules(path=Path("/proc/modules")):
    try:
        return {line.split()[0] for line in path.read_text().splitlines() if line.strip()}
    except OSError:
        return set()


def nvidia_detect(runner=run):
    """The driver package nvidia-detect recommends, "unsupported" when the
    card needs a driver Debian 13 no longer has, or "" when it cannot tell
    (nvidia-detect not installed)."""
    if not shutil.which("nvidia-detect"):
        return ""
    code, out = runner(["nvidia-detect"])
    # "It is recommended to install the\n    nvidia-driver\npackage."
    match = re.search(r"install the\s+(nvidia-[a-z0-9.-]+)\s+package", out)
    if match:
        return match.group(1)
    if "Uh oh." in out:
        return "unsupported"
    return ""


def available(package, runner=run):
    """Whether Debian's archive (as configured) offers the package: cards
    that need a legacy series (390, 340, 470) have none in Debian 13."""
    code, out = runner(["apt-cache", "policy", package])
    match = re.search(r"^\s*Candidate:\s*(\S+)", out, re.M)
    return bool(match) and match.group(1) != "(none)"


def outdated(packages, runner=run):
    """The installed packages of `packages` that have a newer version in the
    package lists (`pkcon update NAME` fails with "No packages were found"
    when a package has no update, so only these are passed to it)."""
    if not packages:
        return []
    code, out = runner(["apt-cache", "policy", *packages])
    found = []
    for block in re.split(r"\n(?=\S)", out):
        # "name:" is the native package, "name:i386:" a foreign copy.
        name = block.splitlines()[0].strip().removesuffix(":") if block.strip() else ""
        installed = re.search(r"^\s*Installed:\s*(\S+)", block, re.M)
        candidate = re.search(r"^\s*Candidate:\s*(\S+)", block, re.M)
        if name in packages and installed and candidate and "(none)" not in (installed.group(1), candidate.group(1)) \
                and installed.group(1) != candidate.group(1) and name not in found:
            found.append(name)
    return found


def secure_boot(runner=run):
    """True when Secure Boot is on."""
    if not shutil.which("mokutil"):
        return False
    code, out = runner(["mokutil", "--sb-state"])
    return "SecureBoot enabled" in out


def key_enrolled(runner=run, key=MOK_KEY):
    """Whether the firmware accepts modules signed with DKMS's key (True when
    there is no key yet: nothing to enrol)."""
    if not key.exists() or not shutil.which("mokutil"):
        return True
    code, out = runner(["mokutil", "--test-key", str(key)])
    return "is already enrolled" in out


def plan(card, installed, modules, recommendation=""):
    """What the window shows for one card and what its button does:

    state:    "proprietary" (NVIDIA's driver in use), "restart" (installed,
              starts after a restart), "available" (NVIDIA's driver can be
              installed), "missing" (AMD/Intel firmware or Mesa parts not
              installed), "ready" (open drivers complete), "unsupported",
              "virtual" or "unknown";
    action:   "install", "update" or "" with its packages;
    driver:   the driver in use, for "Driver: …".
    """
    kind = card["kind"]
    in_use = card.get("driver", "")
    result = {"state": "unknown", "action": "", "packages": [], "driver": in_use, "openDriver": False}
    if kind == "nvidia":
        proprietary = next((p for p in NVIDIA_DRIVERS if p in installed), "")
        if proprietary:
            active = in_use == "nvidia" or "nvidia" in modules
            result.update(state="proprietary" if active else "restart", action="update" if active else "",
                          packages=[proprietary], version=installed.get(proprietary, ""),
                          driver="nvidia" if active else in_use, openDriver=True)
        elif recommendation == "unsupported":
            result.update(state="unsupported")
        else:
            result.update(state="available", action="install",
                          packages=[recommendation or NVIDIA_DEFAULT, KERNEL_HEADERS])
        return result
    if kind in OPEN_PACKAGES:
        needed = OPEN_PACKAGES[kind]
        missing = [p for p in needed if p not in installed]
        if missing:
            result.update(state="missing", action="install", packages=missing)
        else:
            result.update(state="ready", action="update", packages=list(needed))
        return result
    if kind == "virtual":
        result.update(state="virtual")
    return result


# Every package NVIDIA's driver brings (550 and Tesla 535 series, amd64 and
# the i386 libraries for Wine), seen in the dev VM on 2026-10-24: removing
# only nvidia-driver left 37 of them (pkcon's --autoremove kept them, as
# they recommend each other), among them the GLX alternative and Xorg's
# NVIDIA driver. nvidia-detect stays (it only reads the PCI ids).
NVIDIA_STACK = re.compile(r"^(nvidia-(?!detect$).+|libnvidia-.+|libcuda1|libnvcuvid1|libnvoptix1|libglx-nvidia0|"
                          r"libegl-nvidia0|libgles-nvidia.+|libgl1-nvidia-glvnd-glx|glx-alternative-nvidia|"
                          r"xserver-xorg-video-nvidia.*)$")


def open_driver_packages(runner=run):
    """NVIDIA's installed packages to remove to go back to Nouveau, as
    "name:arch" (the i386 libraries too)."""
    code, out = runner(["dpkg-query", "-W", "-f", "${Package}\t${Architecture}\t${db:Status-Abbrev}\n"])
    found = []
    for line in out.splitlines() if code == 0 else []:
        parts = line.split("\t")
        if len(parts) == 3 and parts[2].startswith("ii") and NVIDIA_STACK.match(parts[0]):
            found.append(f"{parts[0]}:{parts[1]}")
    return found


def native_arch(runner=run):
    """dpkg's architecture ("amd64")."""
    code, out = runner(["dpkg", "--print-architecture"])
    return out.strip() if code == 0 and out.strip() else "amd64"
