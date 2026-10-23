/*
    VeltOS toast animation: notification pop-ups slide in from the right
    edge of the screen while they fade in, and slide back out to the right
    when they close, like Windows 11 toasts. KWin's "Fading Popups" effect
    would only fade them; this effect takes the animation over (a forced
    grab, which makes Fading Popups cancel its own).

    SPDX-License-Identifier: GPL-3.0-or-later
*/

"use strict";

function isToast(window) {
    return window.notification || window.criticalNotification;
}

// How far the window is from the right edge of its screen, plus a little,
// so that it starts (or ends) just outside the screen.
function distanceToEdge(window) {
    var screen = window.screen && window.screen.geometry ? window.screen.geometry : effects.virtualScreenGeometry;
    return Math.max(0, screen.x + screen.width - window.geometry.x) + 8;
}

var toastEffect = {
    loadConfig: function () {
        toastEffect.inDuration = animationTime(280);
        toastEffect.outDuration = animationTime(220);
    },
    slotWindowAdded: function (window) {
        if (effects.hasActiveFullScreenEffect || !isToast(window) || !window.visible) {
            return;
        }
        if (!effect.grab(window, Effect.WindowAddedGrabRole, true)) {
            return;
        }
        window.veltosToastIn = animate({
            window: window,
            duration: toastEffect.inDuration,
            curve: QEasingCurve.OutCubic,
            animations: [{
                type: Effect.Translation,
                from: { value1: distanceToEdge(window), value2: 0 },
                to: { value1: 0, value2: 0 }
            }, {
                type: Effect.Opacity,
                from: 0.0,
                to: 1.0
            }]
        });
    },
    slotWindowClosed: function (window) {
        if (effects.hasActiveFullScreenEffect || !isToast(window)) {
            return;
        }
        if (!window.visible || window.skipsCloseAnimation) {
            return;
        }
        if (window.veltosToastIn) {
            cancel(window.veltosToastIn);
            delete window.veltosToastIn;
        }
        if (!effect.grab(window, Effect.WindowClosedGrabRole, true)) {
            return;
        }
        window.veltosToastOut = animate({
            window: window,
            duration: toastEffect.outDuration,
            curve: QEasingCurve.InCubic,
            animations: [{
                type: Effect.Translation,
                from: { value1: 0, value2: 0 },
                to: { value1: distanceToEdge(window), value2: 0 }
            }, {
                type: Effect.Opacity,
                from: 1.0,
                to: 0.0
            }]
        });
    },
    slotWindowDataChanged: function (window, role) {
        // Another effect took the window over: stop ours.
        if (role === Effect.WindowAddedGrabRole && window.veltosToastIn && effect.isGrabbed(window, role)) {
            cancel(window.veltosToastIn);
            delete window.veltosToastIn;
        } else if (role === Effect.WindowClosedGrabRole && window.veltosToastOut && effect.isGrabbed(window, role)) {
            cancel(window.veltosToastOut);
            delete window.veltosToastOut;
        }
    },
    init: function () {
        toastEffect.loadConfig();
        effect.configChanged.connect(toastEffect.loadConfig);
        effects.windowAdded.connect(toastEffect.slotWindowAdded);
        effects.windowClosed.connect(toastEffect.slotWindowClosed);
        effects.windowDataChanged.connect(toastEffect.slotWindowDataChanged);
    }
};

toastEffect.init();
