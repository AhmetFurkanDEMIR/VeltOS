# veltos-office

VeltOS Office: LibreOffice's word processor (Writer), spreadsheet (Calc)
and presentation program (Impress) from Debian, set up for people who come
from Microsoft Office. VeltOS does not write its own office suite; this
package only depends on LibreOffice and adds one configuration layer.

- `registry/veltos-office.xcd`, installed in LibreOffice's
  `share/registry` (read with LibreOffice's own defaults; what users change
  in LibreOffice is stored on top and wins):
  - the ribbon-like **Tabbed** interface in all three programs;
  - the **Colibre** icons (LibreOffice's icon set in Microsoft Office's
    style);
  - new documents are saved as **.docx, .xlsx, .pptx**, without the "Keep
    current format?" question;
  - text in new documents, spreadsheets and presentations is Carlito
    (Calibri's metrics), 11 pt in the word processor;
  - no Tip of the Day, no donation, "get involved" or release-notes bars;
    crash reports to The Document Foundation off.
- Debian's own presentation template ("DebianTalk") is diverted out of
  LibreOffice's template folders (`dpkg-divert`, preinst/postrm).
- Dependencies: `libreoffice-kf6` (Qt 6/Plasma integration, so the VeltOS
  Kvantum style and Plasma's file dialogs apply), the Colibre icons, and
  fonts with the metrics of Calibri/Cambria (Carlito, Caladea) and Arial/
  Times New Roman/Courier New (Liberation), so documents from Windows keep
  their layout.

Elsewhere (veltos-desktop `update-app-names`, veltos-fluent-icons): the
apps are called "Word Processor", "Spreadsheet" and "Presentation" in
Start ("Kelime İşlemci", "Hesap Tablosu", "Sunu"); "Word", "Excel" and
"PowerPoint" are only search words. They start without LibreOffice's
splash (`--nologo`), Office documents open in them by default, and they
have VeltOS icons drawn in the family style (a page, a sheet and a slide;
no letters, no Microsoft artwork). The Start Center and Math are hidden
from Start. Window titles and About still say LibreOffice: it is
LibreOffice.

Tests: `tests/test_config.py` checks every setting of the layer against
the schema and data of the LibreOffice it is built with (Build-Depends):
components, groups, properties, the "Tabbed" mode, the document factories,
the Word/Excel/PowerPoint filters and the Colibre icons.

Not yet: Office-like start screen (Home with recent files and templates),
templates, dark mode icons (untested), checking real Office documents.
