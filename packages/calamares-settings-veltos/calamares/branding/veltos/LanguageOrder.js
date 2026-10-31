// Türkçe and English first in the installer's language list (product
// owner, item 38: VeltOS' own apps speak these two); the other languages
// of Calamares' translations follow in their usual order. Rows are
// {index, label, englishLabel} read from config.languagesModel
// (WelcomePage.qml); `index` is the row in Calamares' model.
//
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

function rank(row) {
    const english = String(row.englishLabel || "");
    if (english.indexOf("Turkish") === 0)
        return 0;
    if (english === "English" || english === "American English" || english === "English (United States)")
        return 1;
    return 2;
}

function order(rows) {
    return rows.map((row, position) => ({ row: row, position: position }))
               .sort((a, b) => rank(a.row) - rank(b.row) || a.position - b.position)
               .map(item => item.row);
}

// The list position of Calamares' row `index` (-1 when it is not there).
function position(rows, index) {
    for (let i = 0; i < rows.length; ++i) {
        if (rows[i].index === index)
            return i;
    }
    return -1;
}
