"""Run pkcon in a pseudo terminal and say "yes" to its confirmation.

`pkcon -y` makes the PackageKit transaction non-interactive ("interactive"
is `!noninteractive` in pk-console.c, PackageKit 1.3.1), and polkit then
refuses at once whatever needs a password: a standard user (or an
administrator outside the live system's blanket rule) never saw the
password prompt and the Store said "Permission was not given" (product
owner, 2026-10-23). Without -y pkcon asks "Proceed with changes? [N/y]"
on its controlling terminal (pk_readline_unbuffered opens ctermid()), so
it runs here in a pty that answers that question; the transaction stays
interactive and polkit asks through the session's agent (VeltOS' prompt).

Usage: python3 -m PACKAGE.ptyrun pkcon -p install NAME (VeltOS Store,
VeltOS Graphics Cards and VeltOS Keyboard Lighting each carry this file, as
packages build on their own; tests/repo checks that the copies match). Everything pkcon prints is
passed on to standard output; the exit code is pkcon's.

One installation after another (product owner, 2026-11-01: the graphics
driver and .deb installs hung while something else held APT's lock).
PackageKit waits for dpkg's lock only a while and then fails ("Could not
get lock /var/lib/dpkg/lock-frontend. It is held by process ...", dev VM),
and the lock file is readable by root only. So before pkcon starts, and
again when it failed for the lock, this waits while an apt-get, apt or
dpkg process runs (the first start's update, a terminal), printing
PackageKit's own "Waiting for package manager lock" status for the
windows. PackageKit's own transactions queue by themselves ("Waiting in
queue"). When dpkg was interrupted (a PC turned off during an install),
`pkcon repair` runs first and the command once more.
"""

import os
import pty
import re
import sys
import time
from pathlib import Path

# The questions pkcon may ask and the answer VeltOS gives: go ahead with the
# changes the user chose; never install unsigned packages or accept
# licences on the user's behalf.
ANSWERS = [
    (re.compile(rb"Proceed with changes\?[^\n]*\[[YN]/[yn]\]\s*$"), b"y\n"),
    (re.compile(rb"\[[YN]/[yn]\]\s*$"), b"n\n"),
]


# pkcon's temporary folder: one where nothing can be made (see below).
NO_TMP = "/nonexistent/veltos-no-debconf"


def child_environment(environ=None):
    """pkcon's environment: its messages in English, whatever the session's
    language. In a Turkish session pkcon asked "Değişikliklerle devam
    edilsin mi?", which the answers above did not know, so every install
    was answered "no" and nothing was installed (installed dev VM,
    2026-10-31); its "Fatal error:" lines are read in English too. The
    password prompt is VeltOS' own window and keeps the session's language.

    And no debconf questions: an interactive pkcon makes a socket in TMPDIR
    for debconf (libpackagekit-glib2's client helper, "gpk-*.socket") and
    PackageKit then runs packages' questions with DEBIAN_FRONTEND=passthrough
    on it. Nothing ever answered there: NVIDIA's driver hung for good in
    `dpkg-preconfigure --apt` (dev VM, 2026-11-01; the product owner's
    "stuck on the loading screen"). Where the socket cannot be made, the
    client gives none and PackageKit's apt backend uses the noninteractive
    frontend: the packages' defaults, as Windows installers that ask nothing."""
    env = dict(os.environ if environ is None else environ)
    env.pop("LANGUAGE", None)
    env["LC_ALL"] = "C.UTF-8"
    env["TMPDIR"] = NO_TMP
    return env


def answer_for(tail):
    """The answer to the question at the end of `tail`, or None."""
    for pattern, answer in ANSWERS:
        if pattern.search(tail):
            return answer
    return None


APT_PROGRAMS = ("apt-get", "apt", "aptitude", "dpkg", "unattended-upgr")
WAITING = b"Status: \tWaiting for package manager lock\n"
LOCKED = re.compile(rb"Could not get lock|held by process|Unable to acquire the dpkg")
INTERRUPTED = re.compile(rb"dpkg was interrupted|dpkg --configure -a")
WAIT_STEP = 5                  # seconds between looks
WAIT_LIMIT = 3 * 3600          # an apt-get that runs longer is stuck: try anyway
LOCK_RETRIES = 3


def apt_busy(proc=Path("/proc")):
    """The name of a running apt-get/apt/dpkg process ("" if none): such a
    process holds, or is about to take, dpkg's lock."""
    me = os.getpid()
    for entry in proc.glob("[0-9]*/comm"):
        try:
            if int(entry.parent.name) == me:
                continue
            name = entry.read_text(encoding="utf-8", errors="replace").strip()
        except (OSError, ValueError):
            continue
        if name in APT_PROGRAMS:
            return name
    return ""


def wait_for_apt(out, busy=apt_busy, sleep=time.sleep, limit=WAIT_LIMIT):
    """Waits while another program uses APT, telling the window so once."""
    waited, said = 0, False
    while busy() and waited < limit:
        if not said:
            out.write(WAITING)
            out.flush()
            said = True
        sleep(WAIT_STEP)
        waited += WAIT_STEP


def run(command, out=None, busy=apt_busy, sleep=time.sleep):
    out = out or sys.stdout.buffer
    if os.path.basename(command[0]) != "pkcon":
        return run_once(command, out)[0]
    wait_for_apt(out, busy, sleep)
    repaired = False
    for _attempt in range(LOCK_RETRIES + 1):
        code, output = run_once(command, out)
        if code == 0:
            return code
        if INTERRUPTED.search(output) and not repaired and "repair" not in command:
            repaired = True
            run_once([command[0], "-p", "repair"], out)
            continue
        if not LOCKED.search(output):
            return code
        wait_for_apt(out, busy, sleep)
        sleep(WAIT_STEP)
    return code


def run_once(command, out):
    """(exit code, the output's last 64 KB)."""
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.execvpe(command[0], command, child_environment())
        finally:
            os._exit(127)
    tail, output = b"", b""
    while True:
        try:
            data = os.read(fd, 4096)
        except OSError:          # EIO: the child closed the terminal
            break
        if not data:
            break
        out.write(data)
        out.flush()
        output = (output + data)[-65536:]
        tail = (tail + data)[-512:]
        reply = answer_for(tail)
        if reply:
            os.write(fd, reply)
            tail = b""
    os.close(fd)
    _pid, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status), output


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python3 -m PACKAGE.ptyrun COMMAND...", file=sys.stderr)
        return 2
    return run(argv)


if __name__ == "__main__":
    sys.exit(main())
