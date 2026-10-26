# File Explorer shortcuts

Item 43 of the product owner's ordered list. Tested in the isolated QEMU
development VM after installing the rebuilt `veltos-explorer` and
`veltos-desktop` packages and restarting Plasma.

- `item43-explorer-context.png`: Explorer's file menu offers **Create
  shortcut on desktop**.
- `item43-explorer-shortcut-created.png`: Explorer returns to the file
  after the shortcut is created.
- `item43-start-recent-menu.png` and `item43-start-shortcut-created.png`:
  Start offers the action for a recent local file and creates the link.
- `item43-search-file-menu.png` and
  `item43-search-shortcut-created.png`: taskbar Search offers the same
  action for a local file result and creates the link.
- `item43-start-app-menu.png` and `item43-search-app-menu.png`: app menus
  retain Plasma's existing **Add to Desktop** action.

All three entry points created a symlink to
`/home/velt/Documents/shortcut-item43.txt`. Repeated creations used
distinct names rather than replacing an existing desktop item. The test
links and source file were temporary VM fixtures.
