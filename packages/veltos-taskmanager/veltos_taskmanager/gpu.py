"""GPU figures for Task Manager (Windows 11's "GPU 0" in Performance and
the GPU column of Processes), read without administrator rights:

* DRM fdinfo: the kernel counts, per client of a graphics device, the time
  each engine (3D, compute, video...) was busy (`/proc/PID/fdinfo/FD`,
  `drm-engine-<engine>: <ns> ns`; the xe driver counts cycles instead,
  `drm-cycles-<engine>` / `drm-total-cycles-<engine>`). Busy time over
  elapsed time is an engine's utilization; a GPU's and a process's figure
  is its busiest engine, as in Windows' Task Manager. Only processes of the
  user can be read, which in a desktop session are the ones that draw
  (KWin, Plasma, the apps). amdgpu, i915, xe and others publish it;
  nouveau and the virtual machines' drivers do not.
* amdgpu's own counters: `gpu_busy_percent` (the whole GPU), dedicated
  (`mem_info_vram_*`) and shared (`mem_info_gtt_*`) memory, temperature.
* NVIDIA's driver: `nvidia-smi`.
"""

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

DRM = Path("/sys/class/drm")
PROC = Path("/proc")
VENDORS = {"0x10de": "NVIDIA", "0x1002": "AMD", "0x8086": "Intel"}
# How often the list of each process' graphics file descriptors is read
# again (reading every fd link of every process each second costs time).
RESCAN_SECONDS = 5.0
ENGINE = re.compile(r"^drm-engine-(?!capacity-)([\w-]+):\s*(\d+)\s*ns", re.M)
CAPACITY = re.compile(r"^drm-engine-capacity-([\w-]+):\s*(\d+)", re.M)
CYCLES = re.compile(r"^drm-cycles-([\w-]+):\s*(\d+)", re.M)
TOTAL_CYCLES = re.compile(r"^drm-total-cycles-([\w-]+):\s*(\d+)", re.M)


def read(path, default=""):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeDecodeError):
        return default


def read_int(path):
    try:
        return int(read(path, "x"))
    except ValueError:
        return None


def nice_name(device):
    """"GeForce RTX 4060" from lspci's "AD107 [GeForce RTX 4060]"."""
    match = re.search(r"\[([^\[\]]+)\]\s*$", device)
    return match.group(1) if match else device


def lspci_name(slot, runner=subprocess.run):
    try:
        out = runner(["lspci", "-vmm", "-s", slot], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    vendor = device = ""
    for line in out.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "Vendor":
            vendor = value.strip()
        elif key.strip() == "Device":
            device = value.strip()
    if not device:
        return ""
    name = nice_name(device)
    # "NVIDIA GeForce RTX 4060", "AMD Radeon ..."; others (virtual machines'
    # cards) keep their own name ("Virtio 1.0 GPU", not "Red Hat, Inc. ...").
    short = {"Advanced": "AMD", "NVIDIA": "NVIDIA", "Intel": "Intel"}.get(vendor.split()[0] if vendor else "")
    if short and not name.lower().startswith(short.lower()):
        name = f"{short} {name}"
    return name


def find_cards(drm=DRM, name_of=lspci_name):
    """[{card, slot, driver, vendor, name}] of the graphics devices."""
    cards = []
    for path in sorted(drm.glob("card[0-9]*")):
        if not re.fullmatch(r"card\d+", path.name):
            continue
        device = path / "device"
        try:
            slot = os.path.basename(os.path.realpath(device))
            driver = os.path.basename(os.path.realpath(device / "driver"))
        except OSError:
            continue
        vendor = VENDORS.get(read(device / "vendor"), "")
        cards.append({"card": path.name, "slot": slot, "driver": driver, "vendor": vendor,
                      "name": name_of(slot) or vendor or driver, "device": device})
    return cards


def parse_fdinfo(text):
    """{pdev, client, engines: {engine: (busy, capacity, kind)}} of one DRM
    fdinfo, or None for other files. busy is nanoseconds (kind "ns") or
    cycles with the total cycles (kind "cycles": busy is (cycles, total))."""
    fields = dict(line.split(":", 1) for line in text.splitlines() if ":" in line)
    if "drm-driver" not in fields:
        return None
    capacity = {e: int(c) for e, c in CAPACITY.findall(text)}
    engines = {e: (int(ns), capacity.get(e, 1), "ns") for e, ns in ENGINE.findall(text)}
    totals = dict(TOTAL_CYCLES.findall(text))
    for engine, cycles in CYCLES.findall(text):
        if engine in totals:
            engines[engine] = ((int(cycles), int(totals[engine])), capacity.get(engine, 1), "cycles")
    return {"pdev": fields.get("drm-pdev", "").strip(), "client": fields.get("drm-client-id", "").strip(),
            "driver": fields["drm-driver"].strip(), "engines": engines}


class Clients:
    """The DRM clients of the user's processes, with each engine's busy
    counter, read every sample; which fds are DRM is looked up again only
    every RESCAN_SECONDS."""

    def __init__(self, proc=PROC, uid=None):
        self.proc = proc
        self.uid = os.getuid() if uid is None else uid
        self._fds = {}          # pid -> [fd numbers that are /dev/dri/*]
        self._scanned = None

    def _rescan(self):
        fds = {}
        for entry in self.proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                if entry.stat().st_uid != self.uid:
                    continue
                found = []
                for fd in os.listdir(entry / "fd"):
                    try:
                        if os.readlink(entry / "fd" / fd).startswith("/dev/dri/"):
                            found.append(fd)
                    except OSError:
                        continue
            except OSError:
                continue
            if found:
                fds[int(entry.name)] = found
        self._fds = fds

    def read(self, now):
        """{(pid, pdev, client): info} for the known DRM fds."""
        if self._scanned is None or now - self._scanned >= RESCAN_SECONDS:
            self._rescan()
            self._scanned = now
        clients = {}
        for pid, fds in list(self._fds.items()):
            for fd in fds:
                info = parse_fdinfo(read(self.proc / str(pid) / "fdinfo" / fd))
                if info and info["engines"]:
                    clients[(pid, info["pdev"], info["client"])] = info
        return clients


def utilization(old, new, elapsed_ns):
    """Per-engine busy share (0-100) between two readings of one client."""
    result = {}
    for engine, (busy, capacity, kind) in new["engines"].items():
        before = old["engines"].get(engine)
        if not before or before[2] != kind:
            continue
        if kind == "ns":
            share = (busy - before[0]) / max(1.0, elapsed_ns * max(1, capacity))
        else:
            cycles, total = busy[0] - before[0][0], busy[1] - before[0][1]
            share = cycles / total if total > 0 else 0.0
        result[engine] = max(0.0, min(1.0, share)) * 100
    return result


def nvidia_smi(runner=subprocess.run):
    """{slot: {busy, used, total, temp}} from nvidia-smi (bytes, °C)."""
    if not shutil.which("nvidia-smi"):
        return {}
    try:
        out = runner(["nvidia-smi", "--query-gpu=pci.bus_id,utilization.gpu,memory.used,memory.total,"
                      "temperature.gpu", "--format=csv,noheader,nounits"],
                     capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    result = {}
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 5:
            continue
        slot = parts[0].lower()[-12:] if len(parts[0]) >= 12 else parts[0].lower()
        try:
            result[slot] = {"busy": float(parts[1]), "used": int(parts[2]) << 20, "total": int(parts[3]) << 20,
                            "temp": float(parts[4])}
        except ValueError:
            continue
    return result


class Gpus:
    """Samples every graphics device once a second: utilization (the
    busiest engine), memory and temperature where the driver tells, and
    each process' GPU share (pid -> percent)."""

    def __init__(self, cards=None, clients=None, clock=time.monotonic, smi=nvidia_smi):
        self.cards = find_cards() if cards is None else cards
        self.clients = clients or Clients()
        self.clock = clock
        self.smi = smi
        self._last = None
        self.per_process = {}
        self.tracking = False

    def sample(self):
        now = self.clock()
        clients = self.clients.read(now) if self.cards else {}
        engines = {card["slot"]: {} for card in self.cards}
        per_process = {}
        if self._last is not None:
            then, old_clients = self._last
            elapsed = max(1.0, (now - then) * 1e9)
            counted = set()      # a client shared by two processes counts once for its GPU
            for key, info in clients.items():
                old = old_clients.get(key)
                if not old:
                    continue
                shares = utilization(old, info, elapsed)
                if not shares:
                    continue
                if key[1:] not in counted:
                    counted.add(key[1:])
                    per_gpu = engines.setdefault(info["pdev"], {})
                    for engine, share in shares.items():
                        per_gpu[engine] = min(100.0, per_gpu.get(engine, 0.0) + share)
                pid = key[0]
                per_process[pid] = min(100.0, max(per_process.get(pid, 0.0), max(shares.values())))
        self._last = (now, clients)
        self.per_process = per_process
        # Processes' GPU shares exist only where a driver publishes fdinfo;
        # otherwise the Processes page leaves the GPU column empty.
        self.tracking = bool(clients)
        smi = self.smi() if any(c["driver"] == "nvidia" for c in self.cards) else {}
        result = []
        for card in self.cards:
            device = card["device"]
            busy, source = None, ""
            if card["slot"] in engines and engines[card["slot"]]:
                busy, source = max(engines[card["slot"]].values()), "fdinfo"
            amd_busy = read_int(device / "gpu_busy_percent")
            if amd_busy is not None:
                busy, source = float(amd_busy), "amdgpu"
            figures = smi.get(card["slot"].lower()[-12:], {})
            if figures:
                busy, source = figures["busy"], "nvidia-smi"
            if busy is None and self._has_fdinfo_driver(card, clients):
                busy, source = 0.0, "fdinfo"
            temp = figures.get("temp")
            if temp is None:
                for hwmon in sorted((Path(device) / "hwmon").glob("hwmon*")):
                    value = read_int(hwmon / "temp1_input")
                    if value is not None:
                        temp = value / 1000
                        break
            result.append({
                "slot": card["slot"], "name": card["name"], "driver": card["driver"],
                "busy": busy, "source": source,
                "engines": dict(engines.get(card["slot"], {})),
                "dedicatedUsed": figures.get("used", read_int(device / "mem_info_vram_used")),
                "dedicatedTotal": figures.get("total", read_int(device / "mem_info_vram_total")),
                "sharedUsed": read_int(device / "mem_info_gtt_used"),
                "sharedTotal": read_int(device / "mem_info_gtt_total"),
                "temperature": temp,
            })
        return result

    def _has_fdinfo_driver(self, card, clients):
        return any(info["pdev"] == card["slot"] for info in clients.values())
