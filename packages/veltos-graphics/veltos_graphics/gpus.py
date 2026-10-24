"""The PC's graphics cards, read without administrator rights: lspci's
machine-readable list (names, PCI ids, the driver in use), sysfs (video
memory, driver version) and Mesa's renderer (eglinfo, mesa-utils)."""

import os
import re
import shutil
import subprocess
from pathlib import Path

# VGA, 3D and display controllers (PCI class 03xx).
GPU_CLASSES = ("0300", "0302", "0380")
VENDORS = {
    "10de": "nvidia",
    "1002": "amd", "1022": "amd",
    "8086": "intel",
    # Virtual machines: QEMU, virtio, VMware, VirtualBox, Hyper-V, Red Hat QXL.
    "1234": "virtual", "1af4": "virtual", "15ad": "virtual", "80ee": "virtual", "1414": "virtual",
    "1b36": "virtual",
}
VENDOR_NAMES = {"nvidia": "NVIDIA", "amd": "AMD", "intel": "Intel"}
ID = re.compile(r"^(.*?)\s*\[([0-9a-fA-F]{4})\]$")


def run(command, timeout=20):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env=dict(os.environ, LC_ALL="C", LANGUAGE="C"))
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout


def split_id(value):
    """("NVIDIA Corporation", "10de") from "NVIDIA Corporation [10de]"."""
    match = ID.match(value.strip())
    return (match.group(1), match.group(2).lower()) if match else (value.strip(), "")


def parse_lspci(text):
    """Graphics cards in `lspci -vmmnnk` output."""
    cards = []
    for block in re.split(r"\n\s*\n", text.strip()):
        fields, modules = {}, []
        for line in block.splitlines():
            key, sep, value = line.partition(":")
            if not sep:
                continue
            key, value = key.strip(), value.strip()
            if key == "Module":
                modules.append(value)
            else:
                fields.setdefault(key, value)
        _, class_id = split_id(fields.get("Class", ""))
        if class_id[:4] not in GPU_CLASSES:
            continue
        vendor_name, vendor_id = split_id(fields.get("Vendor", ""))
        device_name, device_id = split_id(fields.get("Device", ""))
        sub_vendor, _ = split_id(fields.get("SVendor", ""))
        sub_device, _ = split_id(fields.get("SDevice", ""))
        kind = VENDORS.get(vendor_id, "other")
        cards.append({
            "slot": fields.get("Slot", ""),
            "kind": kind,
            "vendor": vendor_name,
            "vendorId": vendor_id,
            "device": device_name,
            "deviceId": device_id,
            "subsystem": " ".join(p for p in (sub_vendor, sub_device) if p),
            "driver": fields.get("Driver", ""),
            "modules": modules,
            "name": nice_name(kind, vendor_name, device_name),
        })
    return cards


def nice_name(kind, vendor, device):
    """The name people know: "NVIDIA GeForce RTX 4060" from "AD107
    [GeForce RTX 4060]", "AMD Radeon RX 6600 XT", "Intel Iris Xe Graphics"."""
    match = re.search(r"\[([^\[\]]+)\]\s*$", device)
    name = match.group(1) if match else device
    if kind == "virtual":
        # "VirtualBox Graphics Adapter", not "InnoTek Systemberatung GmbH ...".
        return name
    short = VENDOR_NAMES.get(kind)
    if short and not name.lower().startswith(short.lower()):
        return f"{short} {name}"
    if not short and vendor and not name.lower().startswith(vendor.split()[0].lower()):
        return f"{vendor} {name}"
    return name


def video_memory(slot, sysfs=Path("/sys/bus/pci/devices"), runner=run):
    """Video memory in bytes (AMD from sysfs, NVIDIA from nvidia-smi), or 0."""
    full = slot if slot.count(":") == 2 else f"0000:{slot}"
    try:
        return int((sysfs / full / "mem_info_vram_total").read_text().strip())
    except (OSError, ValueError):
        pass
    if shutil.which("nvidia-smi"):
        code, out = runner(["nvidia-smi", "--query-gpu=pci.bus_id,memory.total", "--format=csv,noheader,nounits"])
        if code == 0:
            for line in out.splitlines():
                bus, _, mib = line.partition(",")
                if bus.strip().lower().endswith(slot.lower()) and mib.strip().isdigit():
                    return int(mib.strip()) * 1024 * 1024
    return 0


def driver_version(driver, modules_dir=Path("/sys/module")):
    """The kernel driver's own version (NVIDIA's has one), else ""."""
    try:
        return (modules_dir / driver / "version").read_text().strip()
    except OSError:
        return ""


def renderer(runner=run):
    """OpenGL renderer, version and Mesa's version as the PC draws now
    (eglinfo's GBM platform: no window needed)."""
    code, out = runner(["eglinfo", "-B"])
    if code != 0:
        return {}
    block = out.split("GBM platform", 1)[-1].split(" platform", 1)[0] if "GBM platform" in out else out
    found = {}
    for key, label in (("renderer", "OpenGL core profile renderer"), ("glVersion", "OpenGL core profile version"),
                       ("glVendor", "OpenGL core profile vendor")):
        match = re.search(rf"^{label}: (.+)$", block, re.M)
        if match:
            found[key] = match.group(1).strip()
    mesa = re.search(r"Mesa ([0-9][0-9.]*\S*)", found.get("glVersion", ""))
    if mesa:
        found["mesa"] = mesa.group(1)
    return found


def vulkan_devices(runner=run):
    """Vulkan device names (vulkaninfo, when vulkan-tools is installed)."""
    if not shutil.which("vulkaninfo"):
        return []
    code, out = runner(["vulkaninfo", "--summary"], timeout=30)
    if code != 0:
        return []
    return re.findall(r"^\s*deviceName\s*=\s*(.+)$", out, re.M)


def detect(runner=run):
    code, out = runner(["lspci", "-vmmnnk"])
    return parse_lspci(out) if code == 0 else []
