"""How an update is installed, through PackageKit (`pkcon`, run in a pseudo
terminal by ptyrun.py so polkit asks for the administrator's password in
VeltOS' prompt):

  1. `pkcon refresh`: the package lists, VeltOS' own source included, so
     the newest release's packages are known;
  2. `pkcon install veltos-system` when the PC does not have it yet (PCs
     installed before VeltOS Update existed): the package that depends on
     every VeltOS app, so new apps of a release come with it;
  3. `pkcon update`: every newer package, VeltOS' and Debian's (security
     fixes too), as Windows Update installs everything at once;
  4. `pkcon install` of what veltos-system now depends on and the PC does
     not have yet (an app that is new in this release), if step 3 left any.

Packages are replaced in place, so the user's files, settings and the
programs they installed stay. pkcon exits 5 when there was nothing to do.
"""

import re
import subprocess

META = "veltos-system"


def run(command, timeout=120):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C.UTF-8"})
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return result.returncode, result.stdout


def arch(runner=run):
    code, out = runner(["dpkg", "--print-architecture"])
    return out.strip() if code == 0 and out.strip() else "amd64"


def installed(name, runner=run):
    code, out = runner(["dpkg-query", "-W", "-f=${Status}", name])
    return code == 0 and "install ok installed" in out


def missing_apps(runner=run):
    """What veltos-system depends on and is not installed (new apps)."""
    code, out = runner(["apt-cache", "depends", "--no-recommends", "--no-suggests", "--no-conflicts",
                        "--no-breaks", "--no-replaces", "--no-enhances", META])
    if code != 0:
        return []
    names = re.findall(r"^\s+Depends: ([a-z0-9][a-z0-9+.-]*)\s*$", out, re.M)
    return [n for n in names if not installed(n, runner)]


def update_names(output):
    """The package ids `pkcon -p get-updates` lists ("libfoo-1.2-3.amd64")."""
    _, found, results = output.partition("Results:")
    if not found:
        return []
    return [match.group(1) for line in results.splitlines()
            if (match := re.search(r"(\S+\.\S+) \(.*\)\s*$", line))]


def count_updates(output):
    """Number of packages `pkcon -p get-updates` lists (as VeltOS Store counts them)."""
    return len(update_names(output))


def split_updates(output):
    """(others, veltos): Debian's updates and VeltOS' own packages, which
    belong to a VeltOS release (the page's "N other updates come with it"
    counted VeltOS' own before, dev VM 2026-11-02)."""
    names = update_names(output)
    veltos = sum(1 for name in names if name.startswith(("veltos-", "calamares-settings-veltos-")))
    return len(names) - veltos, veltos


def plan(have_meta, native="amd64"):
    """[(step, pkcon arguments)] for an update."""
    steps = [("refresh", ["-p", "refresh"])]
    if not have_meta:
        steps.append(("system", ["-p", "install", f"{META}:{native}"]))
    steps.append(("update", ["-p", "update"]))
    steps.append(("apps", []))           # filled in when it runs: missing_apps()
    return steps


def progress(line):
    """("percent", N), ("status", text) or None for a line of `pkcon -p`."""
    match = re.match(r"^Percentage:\s*(\d+)", line)
    if match:
        return ("percent", min(100, int(match.group(1))))
    match = re.match(r"^Status:\s*(.+?)\s*$", line)
    if match:
        return ("status", match.group(1))
    if line.startswith(("Fatal error:", "Command failed:")):
        return ("error", line.partition(":")[2].strip())
    return None
