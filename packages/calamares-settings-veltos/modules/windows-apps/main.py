#!/usr/bin/env python3
"""VeltOS installer job: writes how Windows programs open on the new system
(/etc/veltos/windows-apps.conf), as chosen on the installer's "How should
Windows programs open?" page (packagechooser_windowsapps). With "bottles",
veltos-first-update.service installs Bottles from Flathub at the first
start and veltos-run opens Windows programs with it. A missing or unknown
choice is "wine" (VeltOS' own environment)."""

import os

import libcalamares


def pretty_name():
    return ".exe programs"


def conf_text(choice):
    runner = "bottles" if choice == "bottles" else "wine"
    return ("# How Windows programs open (VeltOS installer; Settings changes it).\n"
            "[Windows programs]\n"
            f"runner={runner}\n")


def run():
    choice = (libcalamares.globalstorage.value("packagechooser_windowsapps") or "wine").split(",")[0]
    root = libcalamares.globalstorage.value("rootMountPoint")
    if not root:
        return ("No target", "The new system's root is not mounted.")
    folder = os.path.join(root, "etc/veltos")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "windows-apps.conf"), "w", encoding="utf-8") as handle:
        handle.write(conf_text(choice))
    libcalamares.utils.debug(f"windows-apps: {choice}")
    return None
