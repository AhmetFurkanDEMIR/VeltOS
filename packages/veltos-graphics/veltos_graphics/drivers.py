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

Monitors on NVIDIA's driver: Debian's 550 and Tesla 535 modules leave
kernel modesetting off (nvidia-drm `modeset` defaults to false and Debian
ships no option for it, checked in nvidia-kernel-dkms 550.163.01-2 on
2026-10-27). KWin (Wayland) can only drive screens through KMS, so every
monitor connected to the NVIDIA card disappeared once its driver replaced
Nouveau (product owner's laptop). veltos-graphics ships
/usr/lib/modprobe.d/veltos-nvidia.conf, which turns it on.

Monitors on NVIDIA's driver under Wayland also need NVIDIA's GBM library
(`libnvidia-egl-gbm1`, contrib, "GBM EGL external platform library for
NVIDIA", 1.1.2.1-1): KWin allocates the buffers of every screen through
GBM, and a laptop's HDMI port is usually wired to the NVIDIA card. Debian
13's nvidia-driver 550.163.01-2 neither depends on nor recommends it
(packages.debian.org: nvidia-driver, nvidia-driver-libs, nvidia-egl-icd,
libegl-nvidia0, checked 2026-11-01), so the install and every update of
an installed driver bring it (product owner, 2026-11-01: monitors still
not seen on the NVIDIA card).

DKMS builds the module for kernels whose headers are installed. Installing
only linux-headers-amd64 gave the headers of the archive's newest kernel;
on a PC still running an older kernel no module was built for it, and
after the restart neither NVIDIA's driver (not built) nor Nouveau
(blacklisted by the driver) drove the card. The install now also brings
the newest kernel (linux-image-amd64) and the running kernel's headers.
"""

import os
import re
import shutil
import time
import subprocess
from pathlib import Path

NVIDIA_DRIVERS = ("nvidia-driver", "nvidia-tesla-535-driver")
NVIDIA_DEFAULT = "nvidia-driver"
KERNEL_HEADERS = "linux-headers-amd64"
KERNEL_IMAGE = "linux-image-amd64"
# KWin's GBM buffers on NVIDIA's driver (see above).
NVIDIA_GBM = "libnvidia-egl-gbm1"
# The packages that build NVIDIA's kernel module (their install time tells
# whether the PC has restarted since).
NVIDIA_MODULE_PACKAGES = ("nvidia-kernel-dkms", "nvidia-open-kernel-dkms", "nvidia-tesla-535-kernel-dkms")
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


def running_kernel():
    return os.uname().release


def running_headers(kernel=None):
    """The package with the running kernel's headers."""
    return f"linux-headers-{kernel or running_kernel()}"


def module_built(kernel=None, root=Path("/lib/modules")):
    """Whether DKMS built NVIDIA's module for the kernel (the running one):
    Debian names it nvidia-current, nvidia-current-open or nvidia-tesla-535
    under updates/dkms."""
    folder = root / (kernel or running_kernel()) / "updates/dkms"
    return any(re.match(r"nvidia-(current|current-open|tesla-\d+)\.ko", path.name)
               for path in (folder.iterdir() if folder.is_dir() else []))


def installed_at(packages, info=Path("/var/lib/dpkg/info")):
    """When the newest of `packages` was installed (its dpkg file list's
    time), 0 when none is."""
    times = [path.stat().st_mtime for package in packages
             for path in [*info.glob(f"{package}.list"), *info.glob(f"{package}:*.list")]]
    return max(times, default=0)


def boot_time(uptime=Path("/proc/uptime")):
    try:
        return time.time() - float(uptime.read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return 0


def health(secure_boot_on=None, enrolled=None):
    """What the window needs to tell why NVIDIA's installed driver is not in
    use: whether the PC restarted since it was installed, whether its
    module exists for the running kernel and whether Secure Boot lacks its
    key."""
    since = installed_at(NVIDIA_MODULE_PACKAGES)
    sb = secure_boot() if secure_boot_on is None else secure_boot_on
    return {"restarted": bool(since) and boot_time() > since,
            "built": module_built(),
            "keyMissing": sb and not (key_enrolled() if enrolled is None else enrolled)}


def plan(card, installed, modules, recommendation="", status=None):
    """What the window shows for one card and what its button does:

    state:    "proprietary" (NVIDIA's driver in use), "restart" (installed,
              starts after a restart), "failed" (installed, the PC restarted
              and it did not start: `reason` "key" (Secure Boot), "build"
              (no module for this kernel: action "repair") or "start"),
              "available" (NVIDIA's driver can be
              installed), "missing" (AMD/Intel firmware or Mesa parts not
              installed), "ready" (open drivers complete), "unsupported",
              "virtual" or "unknown";
    action:   "install", "update" or "" with its packages (an update
              first installs the ones in `missing`);
    driver:   the driver in use, for "Driver: …".
    """
    kind = card["kind"]
    in_use = card.get("driver", "")
    result = {"state": "unknown", "action": "", "packages": [], "driver": in_use, "openDriver": False}
    if kind == "nvidia":
        proprietary = next((p for p in NVIDIA_DRIVERS if p in installed), "")
        if proprietary:
            active = in_use == "nvidia" or "nvidia" in modules
            # Installs made before 2026-11-01 lack the GBM library: the
            # update installs it ("missing").
            missing = [NVIDIA_GBM] if NVIDIA_GBM not in installed else []
            result.update(state="proprietary" if active else "restart", action="update" if active else "",
                          packages=[proprietary] + missing, missing=missing,
                          version=installed.get(proprietary, ""),
                          driver="nvidia" if active else in_use, openDriver=True)
            if not active and status and status.get("restarted"):
                if status.get("keyMissing"):
                    result.update(state="failed", reason="key")
                elif not status.get("built"):
                    result.update(state="failed", reason="build", action="repair")
                else:
                    result.update(state="failed", reason="start")
        elif recommendation == "unsupported":
            result.update(state="unsupported")
        else:
            result.update(state="available", action="install",
                          packages=[recommendation or NVIDIA_DEFAULT, NVIDIA_GBM, KERNEL_HEADERS, KERNEL_IMAGE])
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
