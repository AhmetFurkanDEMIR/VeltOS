#!/usr/bin/env python3
"""End-to-end test of Windows program support in a VeltOS live VM.

    winapps_vmtest.py --iso veltos.iso --exe 7z2604-x64.exe --sha256 <sum> \
        --expect-shortcut "7-Zip File Manager" --results /out/test-results

Boots the ISO, copies a Windows installer into ~/Downloads, opens it with
veltos-run exactly as a double-click would, accepts the VeltOS dialog,
confirms the installer's default button, and checks that the program was
installed into its own Wine environment and appears as a Start menu
shortcut. Screenshots of every step are saved. The installer file is
checked against a pinned SHA-256 first.
"""

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

from vmlib import LIVE_USER, start_qemu, wait_for

HOME = f"/home/{LIVE_USER}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--expect-shortcut", required=True)
    parser.add_argument("--results", type=Path, default=Path("/out/test-results"))
    args = parser.parse_args()

    digest = hashlib.sha256(args.exe.read_bytes()).hexdigest()
    if digest != args.sha256:
        raise SystemExit(f"{args.exe}: sha256 {digest} does not match the pinned {args.sha256}")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = args.results / f"{stamp}-winapps"
    out.mkdir(parents=True)
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True)
        return ok

    workdir = Path(tempfile.mkdtemp(prefix="winapps-"))
    proc = None
    t0 = time.monotonic()
    try:
        # Windows programs in the live session need RAM (files live in a tmpfs).
        proc, qmp, agent = start_qemu(args.iso, "uefi", out, workdir, memory=8192)
        time.sleep(8)
        qmp.key("ret")
        if not check("system booted", agent.connect(time.monotonic() + 300)):
            return 1
        if not check("desktop running",
                     wait_for(agent, f"pgrep -u {LIVE_USER} -x plasmashell", 240) is not None):
            return 1
        time.sleep(20)

        target = f"{HOME}/Downloads/{args.exe.name}"
        agent.run(f"mkdir -p {HOME}/Downloads")
        agent.upload(args.exe, target)
        agent.run(f"chown -R {LIVE_USER}: {HOME}/Downloads")

        # What a double-click does: the default handler for .exe files.
        code, out_default, _ = agent.run_as_user(
            "xdg-mime query default application/x-ms-dos-executable")
        check(".exe opens with veltos-run by default", "veltos-run.desktop" in out_default,
              out_default.strip())
        agent.run_as_user(f"nohup veltos-run '{target}' >/tmp/veltos-run.out 2>&1 &")
        time.sleep(8)
        qmp.screenshot(out / "01-confirm.png")

        qmp.key("ret")  # "Install" is the default button
        time.sleep(5)
        qmp.screenshot(out / "02-preparing.png")
        t_prep = time.monotonic()
        ready = wait_for(agent, f"test -f {HOME}/.local/share/veltos/windows-apps/*/prefix/system.reg "
                                f"&& pgrep -u {LIVE_USER} -f '{args.exe.name}'", 600, interval=5)
        check("Windows environment prepared and installer started", ready is not None,
              f"{time.monotonic() - t_prep:.0f}s")
        time.sleep(10)
        qmp.screenshot(out / "03-installer.png")

        # Confirm the installer's default button(s) (e.g. "Install", then "Close").
        for i in range(4):
            qmp.key("ret")
            time.sleep(12)
            qmp.screenshot(out / f"04-installer-step{i + 1}.png")
            _, running, _ = agent.run(f"pgrep -u {LIVE_USER} -f '{args.exe.name}' || true")
            if not running.strip():
                break

        time.sleep(15)
        qmp.screenshot(out / "05-result.png")
        _, shortcuts, _ = agent.run(
            f"grep -rl 'WINEPREFIX' {HOME}/.local/share/applications/wine 2>/dev/null | "
            f"xargs -r grep -h '^Name=' | sort -u")
        check(f"Start menu shortcut '{args.expect_shortcut}' created",
              args.expect_shortcut in shortcuts, shortcuts.replace("\n", "; "))
        _, record, _ = agent.run(f"cat {HOME}/.local/share/veltos/windows-apps/*/app.json")
        check("program recorded in its own environment", '"name"' in record, record.strip()[:300])

        # The new program in VeltOS Start search.
        qmp.key("esc")
        time.sleep(1)
        qmp.key("meta_l")
        time.sleep(3)
        qmp.type_text("7-zip")
        time.sleep(4)
        qmp.screenshot(out / "06-start-search.png")
        qmp.key("esc")

        _, crashes, _ = agent.run("coredumpctl list --no-legend --no-pager 2>/dev/null")
        check("no crashed processes", crashes.strip() == "", crashes.strip())
        _, log, _ = agent.run(f"cat /tmp/veltos-run.out; tail -n 40 {HOME}/.local/share/veltos/windows-apps/*/logs/*.log")
        (out / "veltos-run.log").write_text(log)
    finally:
        if proc and proc.poll() is None:
            proc.kill()
        shutil.rmtree(workdir, ignore_errors=True)
        result = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS"
        (out / "report.json").write_text(json.dumps({
            "result": result, "exe": args.exe.name, "sha256": args.sha256,
            "duration_s": round(time.monotonic() - t0), "checks": checks}, indent=2) + "\n")
        print(f"{result}: {out}")
    return 1 if any(c["status"] == "FAIL" for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
