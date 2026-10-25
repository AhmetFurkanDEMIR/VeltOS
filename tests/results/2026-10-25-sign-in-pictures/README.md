# Sign-in screen: account pictures in the user list (2026-10-25, dev VM)

Item 32 of the product owner's 2026-10-23 list. QEMU dev VM with this
change's `veltos-desktop`; a second user "Ayşe Yılmaz" made with `useradd`
and given an account picture through AccountsService (`SetIconFile`), the
live system's autologin moved aside to show SDDM (both undone afterwards).
1280x720 copies.

| Picture | What it shows |
|---|---|
| `sign-in-user-list.png` | Velt selected; at the bottom left Ayşe Yılmaz with her picture and Velt with the default VeltOS picture |
| `user-list-zoomed.png` | The list, zoomed 2x |
| `sign-in-second-user.png` | Ayşe chosen: her picture large in the middle, highlighted in the list |

Before, the list showed only each user's initial in a circle. The package
test (`test_sddm.py`) loads the theme offscreen with a user who has a
picture and checks that exactly that list picture loads.
