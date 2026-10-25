"""Blank Office documents for the "New" menus of File Explorer and the
desktop (product owner, 2026-10-23: New > Word, Excel and PowerPoint
documents, as on Windows 11).

Like Windows, a new Word document and a new PowerPoint presentation are
empty files: LibreOffice opens an empty .docx or .pptx as a new document of
that type, with the user's defaults (language, paper size, VeltOS' fonts),
and saves it in that format without asking. A new Excel worksheet is a
small workbook, as Windows copies a template for it: Calc opened an empty
.xlsx without its app icon in the title bar and on the taskbar (dev VM,
2026-10-25).

    blank-document PATH...   fills each new, empty file according to its
                             extension (.docx and .pptx stay empty)
"""

import io
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

from . import strings

# New-menu kinds -> extension, in Windows' order (by extension).
KINDS = {"word": ".docx", "slides": ".pptx", "sheet": ".xlsx"}

# The first sheet's name as Calc names it in a new workbook.
SHEET_NAMES = {"en": "Sheet1", "tr": "Sayfa1"}

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def workbook(sheet_name="Sheet1"):
    """An empty workbook (.xlsx) with one sheet, Calibri 11 like Excel's
    (shown with the metric-compatible Carlito on VeltOS)."""
    parts = {
        "[Content_Types].xml": (
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'),
        "_rels/.rels": (
            f'<Relationships xmlns="{RELS}">'
            f'<Relationship Id="rId1" Type="{DOC_RELS}/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'),
        "xl/workbook.xml": (
            f'<workbook xmlns="{MAIN}" xmlns:r="{DOC_RELS}">'
            '<bookViews><workbookView/></bookViews>'
            f'<sheets><sheet name={quoteattr(sheet_name)} sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'),
        "xl/_rels/workbook.xml.rels": (
            f'<Relationships xmlns="{RELS}">'
            f'<Relationship Id="rId1" Type="{DOC_RELS}/worksheet" Target="worksheets/sheet1.xml"/>'
            f'<Relationship Id="rId2" Type="{DOC_RELS}/styles" Target="styles.xml"/>'
            '</Relationships>'),
        "xl/worksheets/sheet1.xml": (
            f'<worksheet xmlns="{MAIN}"><sheetViews><sheetView tabSelected="1" workbookViewId="0"/></sheetViews>'
            '<sheetData/></worksheet>'),
        "xl/styles.xml": (
            f'<styleSheet xmlns="{MAIN}">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/><family val="2"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>'),
    }
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, xml in parts.items():
            # A fixed time: the same workbook every time.
            archive.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), HEAD + xml,
                             compress_type=zipfile.ZIP_DEFLATED)
    return data.getvalue()


def fill(path, lang=None):
    """Gives a new, empty file the content of a blank document of its type.
    Files that already have content are left alone."""
    path = Path(path)
    if path.suffix.lower() != ".xlsx" or path.stat().st_size:
        return
    lang = lang or strings.language()
    path.write_bytes(workbook(SHEET_NAMES.get(lang, SHEET_NAMES["en"])))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: blank-document PATH...", file=sys.stderr)
        return 2
    code = 0
    for name in argv:
        try:
            fill(name)
        except OSError as error:
            print(f"blank-document: {name}: {error}", file=sys.stderr)
            code = 1
    return code
