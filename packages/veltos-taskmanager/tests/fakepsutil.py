"""A small stand-in for psutil with a recorded set of processes."""

from collections import namedtuple

Uids = namedtuple("Uids", "real effective saved")
Mem = namedtuple("Mem", "rss vms")
VMem = namedtuple("VMem", "total available percent used free")
Disk = namedtuple("Disk", "read_bytes write_bytes busy_time")
Net = namedtuple("Net", "bytes_sent bytes_recv")
Freq = namedtuple("Freq", "current min max")


class NoSuchProcess(Exception):
    pass


class AccessDenied(Exception):
    pass


class FakeProcess:
    def __init__(self, module, pid, ppid, name, cmdline, uid, rss, cpu=0.0):
        self.module = module
        self.info = {"pid": pid, "ppid": ppid, "name": name, "cmdline": cmdline,
                     "uids": Uids(uid, uid, uid) if uid is not None else None,
                     "memory_info": Mem(rss, rss * 2) if rss else None}
        self.pid = pid
        self.cpu = cpu
        self.signals = []

    def cpu_percent(self, interval=None):
        return self.cpu

    def send_signal(self, sig):
        self.signals.append(sig)

    def kill(self):
        self.signals.append("kill")


class FakePsutil:
    NoSuchProcess = NoSuchProcess
    AccessDenied = AccessDenied

    def __init__(self, uid=1000, stubborn=()):
        self.uid = uid
        self.stubborn = set(stubborn)
        self.procs = {}
        self.disk = Disk(0, 0, 0)
        self.net = Net(0, 0)

    def add(self, pid, ppid, name, cmdline=None, uid=1000, rss=10 << 20, cpu=0.0):
        self.procs[pid] = FakeProcess(self, pid, ppid, name, cmdline if cmdline is not None else [name],
                                      uid, rss, cpu)

    def process_iter(self, attrs=None):
        return iter(list(self.procs.values()))

    def cpu_count(self, logical=True):
        return 4 if logical else 2

    def Process(self, pid):
        if pid not in self.procs:
            raise NoSuchProcess(pid)
        return self.procs[pid]

    def wait_procs(self, procs, timeout=None):
        alive = [p for p in procs if p.pid in self.stubborn]
        return [p for p in procs if p not in alive], alive

    def virtual_memory(self):
        return VMem(8 << 30, 6 << 30, 25.0, 2 << 30, 6 << 30)

    def disk_io_counters(self):
        return self.disk

    def net_io_counters(self):
        return self.net

    def cpu_freq(self):
        return Freq(2400.0, 800.0, 3600.0)

    def cpu_percent(self, interval=None):
        return 12.5

    def boot_time(self):
        return 0.0
