#!/usr/bin/env python3
"""VeltOS installer job: what "If you forget your password" asked for
(branding/veltos/recovery.qml). The password hint goes to the new user's
AccountsService file (PasswordHint, as AccountsService itself writes it);
the password reset USB is made by veltos-auth's password-recovery, which
writes the key to the chosen drive and only its hash to the new system.

Neither may stop the installation: a drive that could not be written is
reported on the last page (veltosRecoveryResult "failed"), where VeltOS
says to make one in Settings."""

import json
import os
import re
import subprocess

import libcalamares

COMMAND = "/usr/libexec/veltos/password-recovery"
ACCOUNTS = "var/lib/AccountsService/users"


def pretty_name():
    return "Password reset"


def with_hint(text, hint):
    """An AccountsService user file with PasswordHint set in [User]."""
    hint = re.sub(r"[\r\n]", " ", hint).strip()
    lines = text.splitlines() if text.strip() else ["[User]"]
    if "[User]" not in lines:
        lines.insert(0, "[User]")
    lines = [line for line in lines if not line.startswith("PasswordHint=")]
    lines.insert(lines.index("[User]") + 1, f"PasswordHint={hint}")
    return "\n".join(lines) + "\n"


def write_hint(root, user, hint):
    folder = os.path.join(root, ACCOUNTS)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    path = os.path.join(folder, user)
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        text = ""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(with_hint(text, hint))
    os.chmod(path, 0o644)


def make_drive(root, user, host, device, exclude, runner=subprocess.run):
    command = [COMMAND, "create", user, device, "--root", root, "--host", host or "PC"]
    if exclude:
        command += ["--exclude", exclude]
    try:
        result = runner(command, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        return str(error)
    return "" if result.returncode == 0 else (result.stdout + result.stderr).strip() or "failed"


def page_choices(environ=None):
    """What "If you forget your password" chose: install-veltos' helper keeps
    it in the signed-in user's runtime folder (Calamares' QML cannot write
    its global storage); PKEXEC_UID is that user (Calamares runs through
    pkexec)."""
    environ = os.environ if environ is None else environ
    uid = environ.get("PKEXEC_UID", "")
    path = environ.get("VELTOS_CHOICES") or (f"/run/user/{uid}/veltos-installer.json" if uid.isdigit() else "")
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def run():
    storage = libcalamares.globalstorage
    root = storage.value("rootMountPoint")
    user = storage.value("username")
    if not root or not user:
        return None
    choices = page_choices()
    for key, name in (("hint", "veltosPasswordHint"), ("device", "veltosRecoveryDevice"),
                      ("exclude", "veltosRecoveryExclude")):
        if key not in choices and storage.value(name):
            choices[key] = storage.value(name)
    hint = str(choices.get("hint") or "").strip()
    if hint:
        try:
            write_hint(root, user, hint)
        except OSError as error:
            libcalamares.utils.warning(f"password-recovery: hint not written: {error}")
    device = str(choices.get("device") or "")
    if device:
        error = make_drive(root, user, storage.value("hostname") or "", device, str(choices.get("exclude") or ""))
        storage.insert("veltosRecoveryResult", "failed" if error else "ok")
        if error:
            libcalamares.utils.warning(f"password-recovery: {device}: {error}")
        else:
            libcalamares.utils.debug(f"password-recovery: reset drive made on {device}")
    return None
