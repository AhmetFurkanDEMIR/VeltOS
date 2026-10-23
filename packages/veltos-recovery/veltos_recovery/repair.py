"""What VeltOS' automatic repair does: the start-up counter, the repair
steps, the previous start's problems and the ways to continue.

Commands go through `runner` (subprocess.run's signature) so the tests can
watch them. Nothing here raises for a failing command: the screen shows
what happened instead.
"""

import os
import shutil
import subprocess

GRUBENV = "/boot/grub/grubenv"
# Counted by GRUB for every VeltOS start (veltos-boot's 10_linux) and
# cleared by veltos-boot-ok.service once the sign-in screen stays up; GRUB
# starts this repair when it reaches 2.
COUNTER = "veltos_failed"
SAFE_ENTRY = "veltos-safe"
# Below this much free space on / a start can fail (logs, the session).
LOW_SPACE = 1 << 30

# (text key, command) of Startup Repair, in order; "space" is special.
STEPS = (
    ("step_packages", ["dpkg", "--configure", "-a"]),
    # Only what is already on the disk: the repair does not need a network.
    ("step_dependencies", ["apt-get", "-y", "--no-download", "--fix-broken", "install"]),
    ("step_space", None),
    ("step_initramfs", ["update-initramfs", "-u", "-k", "all"]),
    ("step_grub", ["update-grub"]),
    ("step_services", ["systemctl", "reset-failed"]),
)


def run(command, runner=subprocess.run, timeout=900):
    """(ok, output) of a command, never raising."""
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", LC_ALL="C.UTF-8")
    try:
        result = runner(command, capture_output=True, text=True, timeout=timeout, env=env)
    except (OSError, subprocess.SubprocessError) as error:
        return False, f"{' '.join(command)}: {error}"
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    return result.returncode == 0, output


def clear_counter(runner=subprocess.run):
    if not os.path.exists(GRUBENV):
        return True, ""
    return run(["grub-editenv", GRUBENV, "unset", COUNTER], runner)


def restart(runner=subprocess.run):
    """Start VeltOS normally next time, and restart now."""
    clear_counter(runner)
    return run(["systemctl", "reboot"], runner)


def safe_mode(runner=subprocess.run):
    """Start once with basic graphics (veltos-boot's "veltos-safe" entry)."""
    clear_counter(runner)
    ok, output = run(["grub-reboot", SAFE_ENTRY], runner)
    if not ok:
        return ok, output
    return run(["systemctl", "reboot"], runner)


def power_off(runner=subprocess.run):
    clear_counter(runner)
    return run(["systemctl", "poweroff"], runner)


def make_room(runner=subprocess.run, usage=shutil.disk_usage):
    """Free space when the system disk is nearly full; (ok, freed?, output)."""
    try:
        free = usage("/").free
    except OSError as error:
        return False, False, str(error)
    if free >= LOW_SPACE:
        return True, False, ""
    outputs = []
    ok = True
    for command in (["apt-get", "clean"], ["journalctl", "--vacuum-size=100M"]):
        step_ok, output = run(command, runner)
        ok = ok and step_ok
        if output:
            outputs.append(output)
    return ok, True, "\n".join(outputs)


def run_step(index, runner=subprocess.run, usage=shutil.disk_usage):
    """Startup Repair's step `index`: (ok, freed space?, output)."""
    _key, command = STEPS[index]
    if command is None:
        return make_room(runner, usage)
    ok, output = run(command, runner)
    return ok, False, output


def previous_problems(runner=subprocess.run):
    """Errors of the previous start from the journal, or "" if none was kept."""
    ok, boots = run(["journalctl", "--list-boots", "--no-pager", "-q"], runner)
    if not ok or len([line for line in boots.splitlines() if line.strip()]) < 2:
        return ""
    ok, errors = run(["journalctl", "-b", "-1", "-p", "err", "--no-pager", "-q", "-o", "short-precise",
                      "-n", "400"], runner)
    if not ok:
        return ""
    ok, failed = run(["journalctl", "-b", "-1", "--no-pager", "-q", "-o", "cat", "-n", "2000",
                      "--grep", "Failed to start|Dependency failed|entered failed state"], runner)
    parts = [errors.strip()]
    if ok and failed.strip():
        parts.append(failed.strip())
    return "\n\n".join(part for part in parts if part)


def system_language(paths=("/etc/default/locale", "/etc/locale.conf"), environ=os.environ):
    """"tr" or "en", from the system's LANG."""
    lang = environ.get("LANG", "")
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("LANG="):
                        lang = line.split("=", 1)[1].strip().strip('"')
        except OSError:
            continue
    return "tr" if lang.startswith("tr") else "en"
