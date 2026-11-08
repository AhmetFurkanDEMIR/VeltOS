/*
    VeltOS fading popups: KWin's "Fading Popups" effect (fadingpopups,
    KWin 6.3.6, by Vlad Zahorodnii) with a shorter fade-out.

    KWin's fades popups out over 600 ms with an OutQuart curve: the popup is
    nearly invisible after about 250 ms, but KWin paints it, with the blur
    and contrast behind it, for the whole 600 ms. Where KWin renders in
    software (virtual machines without 3D acceleration) that tail cost more
    than half of KWin's work when Start opened and closed (dev VM,
    2026-11-08: 87-92 % of a core with KWin's effect, 37 % without it).
    VeltOS fades out over 200 ms with an OutCubic curve, which looks the
    same; the fade-in and which windows are animated are KWin's own.

    SPDX-FileCopyrightText: 2018 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
    SPDX-FileCopyrightText: 2026 VeltOS Developers

    SPDX-License-Identifier: GPL-2.0-or-later
*/

"use strict";

var blacklist = [
    // ignore black background behind lockscreen
    "ksmserver ksmserver",
    // The logout screen has to be animated only by the logout effect.
    "ksmserver-logout-greeter ksmserver-logout-greeter",
    // The lockscreen isn't a popup window
    "kscreenlocker_greet kscreenlocker_greet",
    // KDE Plasma splash screen has to be animated only by the login effect.
    "ksplashqml ksplashqml"
];

function isPopupWindow(window) {
    // If the window is blacklisted, don't animate it.
    if (blacklist.indexOf(window.windowClass) != -1) {
        return false;
    }

    // Animate combo box popups, tooltips, popup menus, etc.
    if (window.popupWindow) {
        return true;
    }

    // Maybe the outline deserves its own effect.
    if (window.outline) {
        return true;
    }

    // Override-redirect windows are usually used for user interface
    // concepts that are expected to be animated by this effect.
    if (!window.managed) {
        // Some utility windows can look like popup windows (e.g. the
        // address bar dropdown in Firefox); they are not faded.
        if (window.utility) {
            return false;
        }

        return true;
    }

    // Notifications, on-screen displays and applet popups (Start, search,
    // the flyouts) as in KWin's effect.
    if (window.splash || window.toolbar
            || window.notification || window.onScreenDisplay
            || window.criticalNotification
            || window.appletPopup) {
        return true;
    }

    return false;
}

var fadingPopupsEffect = {
    loadConfig: function () {
        fadingPopupsEffect.fadeInDuration = animationTime(150);
        // KWin: animationTime(150) * 4 with OutQuart (see above).
        fadingPopupsEffect.fadeOutDuration = animationTime(200);
    },
    slotWindowAdded: function (window) {
        if (effects.hasActiveFullScreenEffect) {
            return;
        }
        if (!isPopupWindow(window)) {
            return;
        }
        if (!window.visible) {
            return;
        }
        if (!effect.grab(window, Effect.WindowAddedGrabRole)) {
            return;
        }
        window.fadeInAnimation = animate({
            window: window,
            curve: QEasingCurve.Linear,
            duration: fadingPopupsEffect.fadeInDuration,
            type: Effect.Opacity,
            from: 0.0,
            to: 1.0
        });
    },
    slotWindowClosed: function (window) {
        if (effects.hasActiveFullScreenEffect) {
            return;
        }
        if (!isPopupWindow(window)) {
            return;
        }
        if (!window.visible || window.skipsCloseAnimation) {
            return;
        }
        if (!effect.grab(window, Effect.WindowClosedGrabRole)) {
            return;
        }
        window.fadeOutAnimation = animate({
            window: window,
            curve: QEasingCurve.OutCubic,
            duration: fadingPopupsEffect.fadeOutDuration,
            type: Effect.Opacity,
            from: 1.0,
            to: 0.0
        });
    },
    slotWindowDataChanged: function (window, role) {
        if (role == Effect.WindowAddedGrabRole) {
            if (window.fadeInAnimation && effect.isGrabbed(window, role)) {
                cancel(window.fadeInAnimation);
                delete window.fadeInAnimation;
            }
        } else if (role == Effect.WindowClosedGrabRole) {
            if (window.fadeOutAnimation && effect.isGrabbed(window, role)) {
                cancel(window.fadeOutAnimation);
                delete window.fadeOutAnimation;
            }
        }
    },
    init: function () {
        fadingPopupsEffect.loadConfig();

        effect.configChanged.connect(fadingPopupsEffect.loadConfig);
        effects.windowAdded.connect(fadingPopupsEffect.slotWindowAdded);
        effects.windowClosed.connect(fadingPopupsEffect.slotWindowClosed);
        effects.windowDataChanged.connect(fadingPopupsEffect.slotWindowDataChanged);
    }
};

fadingPopupsEffect.init();
