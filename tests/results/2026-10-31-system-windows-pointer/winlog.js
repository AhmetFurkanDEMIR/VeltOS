// Dev aid: print every new window's identity to the journal (journalctl _UID=1000 | grep winlog)
function show(w) {
    print("winlog: app=" + w.desktopFileName + " class=" + w.resourceClass + " name=" + w.resourceName
          + " pid=" + w.pid + " caption=" + w.caption + " normal=" + w.normalWindow + " dialog=" + w.dialog
          + " skipTaskbar=" + w.skipTaskbar);
}
workspace.windowAdded.connect(show);
const all = workspace.stackingOrder;
for (let i = 0; i < all.length; i++) show(all[i]);
