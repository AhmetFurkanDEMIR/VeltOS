# VeltOS Store for a standard user: administrator password, then install (2026-10-25, dev VM)

Item 33 of the product owner's 2026-10-23 list, and their follow-up of
2026-10-25 (the prompt showed a file manager-like icon; it should show
VeltOS Store's). QEMU dev VM: a standard user "Deneme Kullanıcı" (not in
the sudo group) signed in through the sign-in screen; Velt is the
administrator. All test changes were undone afterwards. 1280x720 copies.

| Picture | What it shows |
|---|---|
| `before-no-prompt.png` | Before: Install → at once "Permission was not given. Enter the administrator password to install.", no password prompt |
| `fixed-prompt-old-icon.png` | After the first fix: VeltOS' User Account Control asks for Velt's (administrator) password; the Store says "Waiting for your permission"; the icon was PackageKit's package picture (a yellow folder in Fluent) |
| `installed.png` | Password entered: installed (Open / Uninstall; `dpkg -l` "ii freesweep") |
| `cancelled-uninstall-stays-installed.png` | Uninstall, prompt cancelled: the app stays installed with "Permission was not given. Enter the administrator password to uninstall." (before: it showed Install) |
| `uninstall-prompt-store-icon.png`, `install-prompt-store-icon.png` | Now: "Program: VeltOS Store" with the Store's icon, as Windows names the program that asks |

Causes and fixes:

- The Store ran `pkcon -y`; pkcon then makes the PackageKit transaction
  non-interactive (`"interactive", !noninteractive` in pk-console.c,
  PackageKit 1.3.1), so polkit refused without asking (journal: "uid 1001
  failed to obtain auth"). The live user never noticed: the live system's
  `sudo_on_live.rules` allows everything for "velt". Installed systems'
  administrators were affected as well (package-install is
  auth_admin_keep). Without -y pkcon asks "Proceed with changes?" on its
  controlling terminal, so `veltos_store/ptyrun.py` runs it in a pty and
  answers yes (and no to unsigned packages).
- A refused uninstall marked the app "failed", which the page drew as not
  installed.
- veltos-auth showed the polkit action's icon; it now walks from
  `polkit.subject-pid` (pkcon) up the parents to the first process started
  from an app's desktop file (`/usr/bin/veltos-store`) and shows that
  app's name and icon.
