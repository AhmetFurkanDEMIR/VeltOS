# veltos-system — every part of an installed VeltOS system

A metapackage: it depends on every VeltOS package an installed system
keeps (the image's package lists without the installer,
`calamares-settings-veltos`), plus `veltos-fluent-icons` and
`veltos-update`. VeltOS Update installs it on PCs that lack it and
installs whatever it depends on after an update, so an app that is new in
a VeltOS release reaches installed PCs (product owner, 2026-11-02: "a new
app I write must reach the users' PCs").

`tests/repo` checks that its list matches the image's package lists; a
new VeltOS package that installed systems keep goes into both, with a new
`veltos-system` version.
