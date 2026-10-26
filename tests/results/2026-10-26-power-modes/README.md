# Power modes

Item 44 of the product owner's ordered list. Verified in the isolated QEMU
development VM after building the Settings and desktop packages and
installing them in the guest.

- `quicksettings.png`: Quick Settings with the Power mode tile.
- `quicksettings-power-mode.png`: the power-profile choices.
- `settings-power-mode.png`: Settings > System > Power & battery and its
  profile selection.
- `settings-power-saver-selected.png`: Settings after selecting Best power
  efficiency.

The VM had `power-profiles-daemon` 0.30-1.1 and exposed `balanced` and
`power-saver`, but not `performance`. Selecting power-saver through both
Settings and Quick Settings was confirmed with `powerprofilesctl get`.
The automatic helper's AC policy selected balanced because performance was
unavailable; its battery policy selected power-saver. Unsupported-profile
fallback behavior is covered by unit tests.

The VM had no battery, so the helper's AC and battery policies were
exercised directly rather than through real power-source signals. Physical
hardware and actual AC/battery transitions remain untested. These are
screenshots from the development VM, not a real-device test.
