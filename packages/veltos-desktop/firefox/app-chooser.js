// VeltOS: Firefox's "Choose an application" ("Open with" > "Other…" for a
// download) opens VeltOS File Explorer's "Select an app to open this file"
// window instead of GTK's application chooser (product owner, 2026-10-27:
// "Firefox's Open with window is very bad, make it like File Explorer's").
//
// Firefox makes that dialog through the @mozilla.org/applicationchooser;1
// component (widget/gtk/nsApplicationChooser.cpp: GtkAppChooserDialog);
// this script, run by Firefox's autoconfig at start-up, registers a
// component of its own for that name. It runs
//   veltos-explorer --open-with --choose --type MIME
// which prints the chosen app's desktop file name (an empty line when
// cancelled), and hands Firefox that app as GTK's dialog did
// (nsIGIOService.createHandlerAppFromAppId).
try {
  const { Subprocess } = ChromeUtils.importESModule("resource://gre/modules/Subprocess.sys.mjs");
  const Ci = Components.interfaces;

  function VeltosAppChooser() {}
  VeltosAppChooser.prototype = {
    QueryInterface: ChromeUtils.generateQI(["nsIApplicationChooser"]),
    init(parent, title) {
      this.title = title;
    },
    open(contentType, callback) {
      const finish = app => {
        if (typeof callback === "function") {
          callback(app);
        } else {
          callback.done(app);
        }
      };
      (async () => {
        let app = null;
        try {
          const process = await Subprocess.call({
            command: "/usr/bin/veltos-explorer",
            arguments: ["--open-with", "--choose", "--type", contentType || "application/octet-stream"],
            stderr: "pipe",
          });
          let output = "";
          let chunk;
          while ((chunk = await process.stdout.readString())) {
            output += chunk;
          }
          await process.wait();
          const chosen = output.trim().split("\n").pop().trim();
          if (chosen) {
            app = Components.classes["@mozilla.org/gio-service;1"]
                .getService(Ci.nsIGIOService).createHandlerAppFromAppId(chosen);
          }
        } catch (e) {
          Components.utils.reportError("VeltOS app chooser: " + e);
        }
        finish(app);
      })();
    },
  };

  const factory = {
    QueryInterface: ChromeUtils.generateQI(["nsIFactory"]),
    createInstance(iid) {
      return new VeltosAppChooser().QueryInterface(iid);
    },
  };
  Components.manager.QueryInterface(Ci.nsIComponentRegistrar).registerFactory(
      Components.ID("{3c5f7d2a-6b1e-4f0a-9d8c-5e2b7a4c1f60}"), "VeltOS application chooser",
      "@mozilla.org/applicationchooser;1", factory);
} catch (e) {
  Components.utils.reportError("VeltOS app chooser: " + e);
}
