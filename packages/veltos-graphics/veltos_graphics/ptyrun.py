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

Usage: python3 -m PACKAGE.ptyrun pkcon -p install NAME (VeltOS Store and
VeltOS Graphics Cards each carry this file, as packages build on their
own; tests/repo checks that the copies match). Everything pkcon prints is
passed on to standard output; the exit code is pkcon's.
"""

import os
import pty
import re
import sys

# The questions pkcon may ask and the answer VeltOS gives: go ahead with the
# changes the user chose; never install unsigned packages or accept
# licences on the user's behalf.
ANSWERS = [
    (re.compile(rb"Proceed with changes\?[^\n]*\[[YN]/[yn]\]\s*$"), b"y\n"),
    (re.compile(rb"\[[YN]/[yn]\]\s*$"), b"n\n"),
]


def answer_for(tail):
    """The answer to the question at the end of `tail`, or None."""
    for pattern, answer in ANSWERS:
        if pattern.search(tail):
            return answer
    return None


def run(command, out=None):
    out = out or sys.stdout.buffer
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.execvp(command[0], command)
        finally:
            os._exit(127)
    tail = b""
    while True:
        try:
            data = os.read(fd, 4096)
        except OSError:          # EIO: the child closed the terminal
            break
        if not data:
            break
        out.write(data)
        out.flush()
        tail = (tail + data)[-512:]
        reply = answer_for(tail)
        if reply:
            os.write(fd, reply)
            tail = b""
    os.close(fd)
    _pid, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python3 -m PACKAGE.ptyrun COMMAND...", file=sys.stderr)
        return 2
    return run(argv)


if __name__ == "__main__":
    sys.exit(main())
