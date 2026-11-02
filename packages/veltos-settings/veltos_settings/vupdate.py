"""Settings > VeltOS Update (UpdatePage.qml): the state of VeltOS Update and
its work, in the order of Windows 11's Windows Update.

veltos-update (veltos_update) knows the newest release and the steps; this
module shows them: on opening, the last daily check (its state file) at
once, then a new check when that one is older than a day; "Download &
install" runs the steps one after another through pkcon (ptyrun, so the
administrator's password is asked in VeltOS' prompt) with their progress;
"Restart now" when something was installed.

States: "unavailable" (veltos-update missing), "checking", "uptodate",
"available", "offline", "installing", "restart", "failed".
"""

import sys
import time

from PySide6.QtCore import QDateTime, QLocale, QObject, QProcess, QProcessEnvironment, Qt, Signal

from . import strings, sysinfo

REBOOT = ["dbus-send", "--session", "--print-reply", "--type=method_call", "--dest=org.kde.Shutdown", "/Shutdown",
          "org.kde.Shutdown.logoutAndReboot"]
STALE = 24 * 3600


def modules():
    try:
        from veltos_update import check, release, steps
    except ImportError:
        return None
    return check, release, steps


class Updater(QObject):
    changed = Signal()

    def __init__(self, lang, jobs, start, parent=None, mods=None, run_process=None):
        super().__init__(parent)
        self.lang, self.jobs, self._start = lang, jobs, start
        self._mods = modules() if mods is None else mods
        self._run_process = run_process or self._qprocess
        self.data = {"state": "unavailable" if not self._mods else "", "notify": True, "percent": -1,
                     "step": "", "detail": ""}
        self._steps, self._changed_any, self._process = [], False, None

    def t(self, key):
        return strings.text(self.lang, key)

    def _set(self, **values):
        self.data = dict(self.data, **values)
        self.changed.emit()

    # --- what the page shows -------------------------------------------------------------

    def _date(self, iso):
        dt = QDateTime.fromString(iso, Qt.DateFormat.ISODate)
        if not dt.isValid():
            return ""
        locale = QLocale(QLocale.Language.Turkish if self.lang == "tr" else QLocale.Language.English)
        return locale.toString(dt.toLocalTime().date(), "d MMMM yyyy")

    def view(self):
        u = dict(self.data)
        state = u.get("state", "")
        latest = u.get("latest") or {}
        installed = u.get("installed", "")
        release_ready = bool(self._mods and latest and self._mods[1].newer(latest.get("version", ""), installed))
        # With a new release VeltOS' own packages are the release; "other
        # updates" are Debian's. Without one, every update counts.
        others = int(u.get("others") or 0) + (0 if release_ready else int(u.get("veltos") or 0))
        t = self.t
        checked = t("last_checked").replace("{when}", sysinfo.ago(u["checked"], self.lang)) if u.get("checked") else ""
        system = t("vu_installed").replace("{version}", installed) if installed else ""
        title = subtitle = button = ""
        if state == "unavailable":
            title, subtitle = t("vu_unavailable"), t("vu_unavailable_desc")
        elif state == "checking":
            title, subtitle = t("vu_checking"), system
        elif state == "installing":
            title = (t("vu_installing_release").replace("{version}", latest.get("version", ""))
                     if release_ready else t("vu_installing"))
            subtitle = u.get("step", "")
        elif state == "restart":
            title, subtitle, button = t("vu_restart"), t("vu_restart_desc"), t("vu_restart_now")
        elif state == "failed":
            title, subtitle, button = t("vu_failed"), u.get("detail", ""), t("vu_try_again")
        elif state == "offline":
            title, subtitle, button = t("vu_offline"), t("vu_offline_desc"), t("vu_try_again")
        elif release_ready:
            title = t("vu_release").replace("{version}", latest.get("version", ""))
            subtitle = t("vu_release_desc")
            if others:
                subtitle += " " + t("vu_and_others").replace("{count}", str(others))
            button = t("vu_install")
        elif others:
            title = t("vu_others")
            subtitle = (t("vu_others_desc_1") if others == 1 else t("vu_others_desc").replace("{count}", str(others)))
            button = t("vu_install")
        else:
            title = t("vu_uptodate")
            subtitle = " · ".join(p for p in (system, checked) if p)
            button = t("vu_check")
        u.update(title=title, subtitle=subtitle, button=button,
                 state=("available" if state in ("", "uptodate") and (release_ready or others)
                        else ("uptodate" if state == "" else state)))
        if latest and self._mods:
            u["notes"] = self._mods[1].notes(latest.get("body", ""), self.lang)
            u["notesTitle"] = t("vu_whats_new").replace("{version}", latest.get("version", ""))
            u["published"] = self._date(latest.get("published", ""))
        return u

    # --- checking --------------------------------------------------------------------------

    def open(self):
        """The page was opened: the last check at once, a new one when old."""
        if not self._mods:
            return self._set(state="unavailable")
        check, release, _steps = self._mods
        saved = check.load()
        self._set(installed=release.installed_version(), latest=saved.get("latest") or {},
                  others=int(saved.get("others") or 0), veltos=int(saved.get("veltos") or 0),
                  checked=saved.get("checked") or 0,
                  notify=check.notify_enabled())
        if self.data.get("state") in ("installing", "checking", "restart"):
            return
        if not saved.get("checked") or time.time() - float(saved["checked"]) > STALE:
            self.check()
        else:
            self._set(state="")

    def check(self):
        if not self._mods or self.data.get("state") in ("checking", "installing"):
            return
        check, release, _steps = self._mods
        self._set(state="checking", percent=-1)

        def work():
            try:
                latest = release.fetch()
            except (OSError, ValueError):
                latest = None
            others, veltos = check.other_updates()
            saved = check.load()
            saved.update(checked=time.time(), others=others, veltos=veltos)
            if latest:
                saved["latest"] = latest
            check.save(saved)
            return {"latest": latest, "others": others, "veltos": veltos, "checked": saved["checked"]}

        def done(result):
            result = result or {}
            values = {"others": result.get("others", 0), "veltos": result.get("veltos", 0),
                      "checked": result.get("checked", 0),
                      "installed": release.installed_version()}
            if result.get("latest"):
                values["latest"] = result["latest"]
            self._set(state="" if result.get("latest") else "offline", **values)
        self.jobs.submit(work, done)

    # --- installing ------------------------------------------------------------------------

    def action(self):
        state = self.view()["state"]
        if state == "available":
            self.install()
        elif state == "restart":
            self._start(REBOOT)
        elif state not in ("checking", "installing", "unavailable"):
            self.check()

    def install(self):
        if not self._mods or self.data.get("state") in ("installing", "checking"):
            return
        _check, _release, steps = self._mods
        self._steps = steps.plan(steps.installed(steps.META), steps.arch())
        self._changed_any = False
        self._set(state="installing", percent=-1, detail="")
        self._next()

    def _next(self):
        _check, _release, steps = self._mods
        if not self._steps:
            installed = self._mods[1].installed_version()
            if self._changed_any:
                # Installed: the saved counts are old now (the page opened
                # again showed "4 updates" after the update, dev VM 2026-11-02).
                saved = _check.load()
                saved.update(others=0, veltos=0)
                _check.save(saved)
            return self._set(state="restart" if self._changed_any else "", installed=installed, percent=-1,
                             others=0 if self._changed_any else self.data.get("others", 0),
                             veltos=0 if self._changed_any else self.data.get("veltos", 0))
        step, arguments = self._steps.pop(0)
        if step == "apps":
            missing = steps.missing_apps()
            if not missing:
                return self._next()
            native = steps.arch()
            arguments = ["-p", "install", *[f"{name}:{native}" for name in missing]]
        self._set(step=self.t("vu_step_" + step), percent=-1)
        self._run_process(step, arguments)

    def _qprocess(self, step, arguments):
        process = QProcess(self)
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("LC_ALL", "C.UTF-8")
        process.setProcessEnvironment(environment)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        output = []

        def read():
            data = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            output.append(data)
            for line in data.splitlines():
                self.progress(line)

        def ended(code=1, status=QProcess.ExitStatus.CrashExit):
            if self._process is not process:
                return
            self._process = None
            process.deleteLater()
            self.finished(step, code if status == QProcess.ExitStatus.NormalExit else 1, "".join(output))
        process.readyReadStandardOutput.connect(read)
        process.finished.connect(ended)
        process.errorOccurred.connect(lambda error: error == QProcess.ProcessError.FailedToStart and ended())
        self._process = process
        process.start(sys.executable, ["-m", "veltos_update.ptyrun", "pkcon", *arguments])
        process.closeWriteChannel()

    def progress(self, line):
        parsed = self._mods[2].progress(line)
        if parsed and parsed[0] == "percent":
            self._set(percent=parsed[1])

    def finished(self, step, code, output):
        """One step ended (pkcon exits 5 when there was nothing to do)."""
        if code == 0:
            self._changed_any = self._changed_any or step != "refresh"
            return self._next()
        if code == 5:
            return self._next()
        self._steps = []
        lower = output.lower()
        if "authoriz" in lower or "authentic" in lower or "not authorised" in lower:
            detail = self.t("vu_failed_auth")
        elif any(w in lower for w in ("download", "network", "resolve", "fetch", "connect")):
            detail = self.t("vu_failed_network")
        else:
            lines = [line for line in output.strip().splitlines() if line.strip()]
            detail = lines[-1] if lines else ""
        self._set(state="failed", detail=detail, percent=-1)

    def set_notify(self, on):
        if self._mods and self._mods[0].set_notify(bool(on)):
            self._set(notify=bool(on))

    def release_page(self):
        latest = self.data.get("latest") or {}
        url = latest.get("url") or (self._mods[1].RELEASES_PAGE if self._mods else "")
        if url:
            self._start(["xdg-open", url])
