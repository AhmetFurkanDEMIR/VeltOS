# veltos-update

VeltOS Update: new VeltOS releases reach installed PCs as package updates,
without a new installation and with the user's files, settings and
programs left as they are.

## How a release reaches a PC

1. A release is a GitHub release of the project, made by GitHub Actions
   (`.github/workflows/release.yml`) when `VERSION` changes on `main`. It
   carries the ISO (new installations) and every VeltOS package with a
   flat APT index signed by VeltOS' archive key
   (`build/scripts/make-apt-repo.sh`; GitHub renames assets with `~`, so the
   files are named `veltos-ai_1.1.0_all.deb` style and the index names them
   so).
2. `veltos-update-source.timer` (system, 2 minutes after the start, then
   every 12 hours) runs `/usr/libexec/veltos/update-source`: while
   `https://github.com/AhmetFurkanDEMIR/VeltOS/releases/latest/download/InRelease`
   exists and carries a good signature of the key in
   `/usr/share/keyrings/veltos-archive-keyring.gpg`, it writes
   `/etc/apt/sources.list.d/veltos.sources`; while the newest release has
   no index (a 404, as VeltOS 1.0's release) it removes the file. When
   GitHub cannot be reached nothing changes. A fixed source file made every
   `apt update` and PackageKit refresh fail ("does not have a Release
   file") while the newest release had no index.
3. `veltos-update-check.timer` (every user, 15 minutes after signing in,
   then daily; the check skips when the last one is less than 20 hours
   old) runs `/usr/libexec/veltos/update-check`: it asks GitHub's API for
   the newest release (`releases/latest`, no key) and compares it with
   `VERSION_ID` of `/etc/os-release`. A newer release is told once per
   version as a notification ("VeltOS 1.1 is ready", "View update" opens
   VeltOS Settings > Windows Update > VeltOS Update); other updates (Debian's)
   once a day. The state is `~/.local/state/veltos/update.json`; the
   notifications can be turned off on the Settings page
   (`~/.config/veltos/update.conf`).
4. VeltOS Settings' page shows the release's notes in the session's
   language (English before the line `<!-- tr -->` of the release text,
   Turkish after it) and installs: `pkcon refresh`, `veltos-system` when
   it is missing, `pkcon update` (PackageKit asks for the administrator's
   password once), then whatever `veltos-system` depends on that is not
   installed yet (new apps of the release). Then it asks for a restart.

`veltos-system` (its own package) depends on every VeltOS package an
installed system keeps, so a release that adds an app adds it to
`veltos-system`'s Depends and every PC gets the new app with the update.

## Files

| Path | What |
|---|---|
| `veltos_update/release.py` | The newest release from GitHub's API, version comparison, notes per language |
| `veltos_update/check.py` | The daily check's decisions (tell once, offline, notifications off) |
| `veltos_update/notify.py` | The notification (English, Turkish) and its "View update" action |
| `veltos_update/steps.py` | The install steps and pkcon's progress lines (VeltOS Settings runs them) |
| `veltos_update/source.py` | The package source while the newest release has a signed index |
| `veltos_update/ptyrun.py` | pkcon in a pseudo terminal (copy of veltos-store's; `tests/repo` checks) |
| `data/veltos-archive-keyring.gpg` | VeltOS' archive key (public; fingerprint BD18 359F 96FB 279D B805 AF77 FBE8 3B22 791B 7861) |

`/etc/veltos/update.conf` may point both at other places for tests:

```ini
[Update]
release_url = http://10.0.2.2:8080/release.json
repository = http://10.0.2.2:8080/repo/
```

## Limits

- Only systems installed from an ISO with this package (VeltOS 1.1 and
  later) update themselves; a VeltOS 1.0 installation needs one new
  installation, or `sudo dpkg -i veltos-update_*.deb` from a release.
- APT reads the newest release's files: a release published between
  `apt update` and the download makes that download fail once (the files
  changed); the next refresh works.
- The release information comes from GitHub (60 API requests an hour per
  address; one a day per PC).

## Tests

`tests/test_update.py` (standard library, no network): GitHub's JSON, the
versions, the notes, the daily check with stand-ins, the steps, the
package source with stand-in answers (signed, 404, offline, forged).
