.pragma library
/*
    The installer's colours. They follow the live session's theme like the
    rest of VeltOS: install-veltos reads the signed-in user's light or dark
    mode and accent colour, and start-calamares passes them on with whether
    the screen is drawn in software, as one argument Calamares itself
    ignores (it only parses options):

        veltos-theme=dark=1;accent=#E81123;software=1

    Without it (tests, Calamares started by hand) the light VeltOS look.
    Every installer QML file imports this as `Theme`.

    SPDX-License-Identifier: GPL-3.0-or-later
*/

var DEFAULT_ACCENT = "#2F5EE6";

function parse(args) {
    var options = { dark: false, accent: DEFAULT_ACCENT, software: false };
    for (var i = 0; i < args.length; i++) {
        var arg = String(args[i]);
        if (arg.indexOf("veltos-theme=") !== 0)
            continue;
        var parts = arg.substring("veltos-theme=".length).split(";");
        for (var j = 0; j < parts.length; j++) {
            var pair = parts[j].split("=");
            if (pair.length !== 2)
                continue;
            if (pair[0] === "dark")
                options.dark = pair[1] === "1";
            else if (pair[0] === "software")
                options.software = pair[1] === "1";
            else if (pair[0] === "accent" && /^#[0-9A-Fa-f]{6}$/.test(pair[1]))
                options.accent = pair[1].toUpperCase();
        }
    }
    return options;
}

function channels(hex) {
    return [parseInt(hex.substring(1, 3), 16) / 255,
            parseInt(hex.substring(3, 5), 16) / 255,
            parseInt(hex.substring(5, 7), 16) / 255];
}

// WCAG relative luminance: text on the accent is dark on light accents.
function luminance(hex) {
    var c = channels(hex).map(function (v) {
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}

function tint(hex, alpha) {
    var c = channels(hex);
    return Qt.rgba(c[0], c[1], c[2], alpha);
}

var options = parse(Qt.application.arguments);
var dark = options.dark;
var software = options.software;     // no GPU: Qt Quick draws in software

// Windows 11's light and dark setup colours, matched to VeltOS' themes.
var light = {
    window: "#F3F5FA", sidebar: "#EBEFF7", card: "#FFFFFF", cardHover: "#F7F8FC",
    cardPressed: "#EEF1F7", fill: "#F1F3F9", text: "#1B1D24", subtext: "#5D6475",
    muted: "#8A90A2", border: "#E3E6EE", control: "#D5DAE5", line: "#C9CFDC",
    focus: "#1B1D24", knob: "#5D6475", pictureTop: "#E8EEFC", pictureBottom: "#D7E2FA",
    glow: "#FFFFFF", shadow: "#2F4FD6",
    error: "#C42B1C", errorBack: "#FDE7E9", warning: "#9D5D00", warningBack: "#FFF4CE",
    success: "#0F7B0F", successBack: "#DFF6DD", celebrate: "#1E9E5A"
};
var darkColours = {
    window: "#1C1E24", sidebar: "#16171C", card: "#2A2C33", cardHover: "#31343C",
    cardPressed: "#383B44", fill: "#26282F", text: "#F3F4F8", subtext: "#A9AFBD",
    muted: "#80869A", border: "#383B44", control: "#4A4E59", line: "#4A4E59",
    focus: "#FFFFFF", knob: "#C9CDD8", pictureTop: "#282C39", pictureBottom: "#20232E",
    glow: "#3DFFFFFF", shadow: "#000000",
    error: "#FF99A4", errorBack: "#442726", warning: "#FCE100", warningBack: "#433519",
    success: "#6CCB5F", successBack: "#393D1B", celebrate: "#6CCB5F"
};
var c = dark ? darkColours : light;

var accent = options.accent;
var accentHover = Qt.lighter(accent, 1.12);
var accentPressed = Qt.darker(accent, 1.18);
var onAccent = luminance(accent) > 0.45 ? "#1B1D24" : "#FFFFFF";
// Accent text and links: a lighter shade on dark backgrounds, as Windows does.
var accentText = dark ? Qt.lighter(accent, 1.45) : accent;
var accentOnDark = Qt.lighter(accent, 1.45);             // the slideshow is always dark
var accentSoft = tint(accent, dark ? 0.26 : 0.13);      // the chosen row
var accentFaint = tint(accent, dark ? 0.16 : 0.08);
