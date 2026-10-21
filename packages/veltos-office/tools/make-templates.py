#!/usr/bin/python3
"""Build VeltOS' own document templates (the ones Microsoft 365 shows on
its Home page: meeting notes, a report, a to-do list; a monthly budget, an
invoice, an expense tracker, a weekly schedule).

    make-templates.py OUT_DIR [--soffice PATH]

Writes flat ODF documents (.fodt / .fods, plain XML written here) and
converts them with LibreOffice into template files (.ott / .ots) in
OUT_DIR/word and OUT_DIR/sheet, each with a thumbnail inside (LibreOffice
stores Thumbnails/thumbnail.png when it saves; if a headless run leaves it
out, a page picture rendered by LibreOffice is put in). The text in the
templates is English, like LibreOffice's own templates; the start page
shows their names in the user's language (strings.TEMPLATE_NAMES).

Colours are Microsoft 365's app colours (Word blue, Excel green) so the
documents look at home next to the start pages.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

WORD_BLUE = "#185ABD"
EXCEL_GREEN = "#107C41"
GREY = "#D9D9D9"
LIGHT = "#F2F4F8"

NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
      'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
      'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" '
      'xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" '
      'office:version="1.3"')


# --- Writer (flat .fodt) --------------------------------------------------------------------------

class Doc:
    """A flat Writer document built from paragraphs, headings, lists and tables."""

    def __init__(self, accent=WORD_BLUE):
        self.accent = accent
        self.body = []
        self.auto = []
        self.tables = 0

    def p(self, text="", style="Standard"):
        self.body.append(f'<text:p text:style-name="{style}">{escape(text)}</text:p>')

    def title(self, text):
        self.body.append(f'<text:p text:style-name="Title">{escape(text)}</text:p>')

    def subtitle(self, text):
        self.body.append(f'<text:p text:style-name="Subtitle">{escape(text)}</text:p>')

    def h(self, text, level=1):
        self.body.append(f'<text:h text:style-name="Heading_20_{level}" text:outline-level="{level}">{escape(text)}</text:h>')

    def items(self, entries, numbered=False):
        style = "LNum" if numbered else "LBul"
        parts = [f'<text:list text:style-name="{style}">']
        for entry in entries:
            parts.append(f'<text:list-item><text:p text:style-name="Standard">{escape(entry)}</text:p></text:list-item>')
        parts.append("</text:list>")
        self.body.append("".join(parts))

    def table(self, header, rows, widths, total_width=17.0, header_fill=True):
        """A table with a coloured header row; widths are relative."""
        self.tables += 1
        name = f"Table{self.tables}"
        scale = total_width / sum(widths)
        self.auto.append(f'<style:style style:name="{name}" style:family="table">'
                         f'<style:table-properties style:width="{total_width}cm" table:align="margins"/></style:style>')
        for index, width in enumerate(widths):
            self.auto.append(f'<style:style style:name="{name}.{chr(65 + index)}" style:family="table-column">'
                             f'<style:table-column-properties style:column-width="{width * scale:.2f}cm"/></style:style>')
        fill = f' fo:background-color="{self.accent}"' if header_fill else f' fo:background-color="{LIGHT}"'
        self.auto.append(f'<style:style style:name="{name}.H" style:family="table-cell">'
                         f'<style:table-cell-properties fo:padding="0.12cm" fo:border="0.5pt solid {GREY}"{fill}/></style:style>')
        self.auto.append(f'<style:style style:name="{name}.C" style:family="table-cell">'
                         f'<style:table-cell-properties fo:padding="0.12cm" fo:border="0.5pt solid {GREY}"/></style:style>')
        parts = [f'<table:table table:name="{name}" table:style-name="{name}">']
        for index in range(len(widths)):
            parts.append(f'<table:table-column table:style-name="{name}.{chr(65 + index)}"/>')
        head_style = "TableHeadLight" if header_fill else "TableHeadDark"
        parts.append("<table:table-header-rows><table:table-row>")
        for text in header:
            parts.append(f'<table:table-cell table:style-name="{name}.H" office:value-type="string">'
                         f'<text:p text:style-name="{head_style}">{escape(text)}</text:p></table:table-cell>')
        parts.append("</table:table-row></table:table-header-rows>")
        for row in rows:
            parts.append("<table:table-row>")
            for text in row:
                parts.append(f'<table:table-cell table:style-name="{name}.C" office:value-type="string">'
                             f'<text:p text:style-name="TableText">{escape(text)}</text:p></table:table-cell>')
            parts.append("</table:table-row>")
        parts.append("</table:table>")
        self.body.append("".join(parts))

    def xml(self):
        accent = self.accent
        styles = f"""
  <office:font-face-decls>
    <style:font-face style:name="Carlito" svg:font-family="Carlito" style:font-family-generic="swiss"/>
  </office:font-face-decls>
  <office:styles>
    <style:default-style style:family="paragraph">
      <style:paragraph-properties fo:margin-bottom="0.2cm" fo:line-height="115%"/>
      <style:text-properties style:font-name="Carlito" fo:font-size="11pt" fo:language="en" fo:country="US"/>
    </style:default-style>
    <style:style style:name="Standard" style:family="paragraph" style:class="text"/>
    <style:style style:name="Title" style:family="paragraph" style:parent-style-name="Standard" style:class="chapter">
      <style:paragraph-properties fo:margin-top="0.4cm" fo:margin-bottom="0.15cm"/>
      <style:text-properties fo:font-size="26pt" fo:font-weight="bold" fo:color="{accent}"/>
    </style:style>
    <style:style style:name="Subtitle" style:family="paragraph" style:parent-style-name="Standard" style:class="chapter">
      <style:paragraph-properties fo:margin-bottom="0.6cm"/>
      <style:text-properties fo:font-size="13pt" fo:color="#5F6069"/>
    </style:style>
    <style:style style:name="Heading_20_1" style:display-name="Heading 1" style:family="paragraph" style:parent-style-name="Standard" style:next-style-name="Standard" style:default-outline-level="1" style:class="text">
      <style:paragraph-properties fo:margin-top="0.6cm" fo:margin-bottom="0.2cm" fo:keep-with-next="always"/>
      <style:text-properties fo:font-size="16pt" fo:font-weight="bold" fo:color="{accent}"/>
    </style:style>
    <style:style style:name="Heading_20_2" style:display-name="Heading 2" style:family="paragraph" style:parent-style-name="Standard" style:next-style-name="Standard" style:default-outline-level="2" style:class="text">
      <style:paragraph-properties fo:margin-top="0.4cm" fo:margin-bottom="0.15cm" fo:keep-with-next="always"/>
      <style:text-properties fo:font-size="13pt" fo:font-weight="bold" fo:color="#2F3A4A"/>
    </style:style>
    <style:style style:name="Placeholder" style:family="paragraph" style:parent-style-name="Standard">
      <style:text-properties fo:color="#8A8F9C" fo:font-style="italic"/>
    </style:style>
    <style:style style:name="TableHeadLight" style:family="paragraph" style:parent-style-name="Standard">
      <style:paragraph-properties fo:margin-bottom="0cm"/>
      <style:text-properties fo:color="#FFFFFF" fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="TableHeadDark" style:family="paragraph" style:parent-style-name="Standard">
      <style:paragraph-properties fo:margin-bottom="0cm"/>
      <style:text-properties fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="TableText" style:family="paragraph" style:parent-style-name="Standard">
      <style:paragraph-properties fo:margin-bottom="0cm" fo:line-height="100%"/>
    </style:style>
    <text:list-style style:name="LNum">
      <text:list-level-style-number text:level="1" style:num-format="1" style:num-suffix=".">
        <style:list-level-properties text:list-level-position-and-space-mode="label-alignment">
          <style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="0.8cm" fo:text-indent="-0.6cm" fo:margin-left="0.8cm"/>
        </style:list-level-properties>
      </text:list-level-style-number>
    </text:list-style>
    <text:list-style style:name="LBul">
      <text:list-level-style-bullet text:level="1" text:bullet-char="•">
        <style:list-level-properties text:list-level-position-and-space-mode="label-alignment">
          <style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="0.8cm" fo:text-indent="-0.6cm" fo:margin-left="0.8cm"/>
        </style:list-level-properties>
      </text:list-level-style-bullet>
    </text:list-style>
  </office:styles>
  <office:automatic-styles>
    {"".join(self.auto)}
  </office:automatic-styles>
"""
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n<office:document {NS} '
                f'office:mimetype="application/vnd.oasis.opendocument.text">{styles}'
                f'<office:body><office:text>{"".join(self.body)}</office:text></office:body></office:document>\n')


def meeting_notes():
    d = Doc()
    d.title("Meeting notes")
    d.subtitle("Project or team name")
    d.table(["Date", "Time", "Location"], [["", "", ""]], [1, 1, 1.4], header_fill=False)
    d.p()
    d.table(["Attendees", "Facilitator", "Note taker"], [["", "", ""]], [1.6, 1, 1], header_fill=False)
    d.h("Agenda")
    d.items(["First topic", "Second topic", "Third topic"], numbered=True)
    d.h("Discussion")
    d.p("Key points, decisions and open questions from the meeting.", "Placeholder")
    d.h("Action items")
    d.table(["Action", "Owner", "Due date"], [["", "", ""], ["", "", ""], ["", "", ""]], [2.6, 1, 1])
    d.h("Next meeting")
    d.p("Date, time and place of the next meeting.", "Placeholder")
    return d


def report():
    d = Doc()
    d.title("Report title")
    d.subtitle("Subtitle, project or course")
    d.p("Prepared by: Your name    ·    Date: ")
    d.h("Summary")
    d.p("Two or three sentences on what this report is about and what it found.", "Placeholder")
    d.h("Background")
    d.p("Why the work was done and what was known before.", "Placeholder")
    d.h("Findings")
    d.table(["Item", "Result", "Note"], [["", "", ""], ["", "", ""], ["", "", ""]], [1.4, 1, 1.8])
    d.h("Recommendations")
    d.items(["First recommendation", "Second recommendation", "Third recommendation"])
    d.h("Conclusion")
    d.p("What follows from the findings.", "Placeholder")
    return d


def todo_list():
    d = Doc()
    d.title("To-do list")
    d.subtitle("Week of ")
    rows = [["☐", "", "", ""] for _ in range(10)]
    d.table(["Done", "Task", "Priority", "Due"], rows, [0.5, 3.2, 0.9, 1])
    d.h("Notes")
    d.p("Anything to remember.", "Placeholder")
    return d


# --- Calc (flat .fods) ------------------------------------------------------------------------------

class Sheet:
    """A flat Calc document: one table built row by row."""

    def __init__(self, name, columns, accent=EXCEL_GREEN):
        self.name = name
        self.columns = columns              # column widths in cm
        self.accent = accent
        self.rows = []

    @staticmethod
    def cell(text="", style="c", span=1):
        extra = f' table:number-columns-spanned="{span}"' if span > 1 else ""
        value = f'<text:p>{escape(text)}</text:p>' if text else ""
        covered = '<table:covered-table-cell/>' * (span - 1)
        return f'<table:table-cell table:style-name="{style}" office:value-type="string"{extra}>{value}</table:table-cell>{covered}'

    @staticmethod
    def number(value, style="n"):
        return (f'<table:table-cell table:style-name="{style}" office:value-type="float" office:value="{value}">'
                f'<text:p>{value}</text:p></table:table-cell>')

    @staticmethod
    def formula(expr, style="n"):
        return (f'<table:table-cell table:style-name="{style}" table:formula="of:={escape(expr)}" '
                f'office:value-type="float" office:value="0"><text:p>0</text:p></table:table-cell>')

    @staticmethod
    def empty(count=1):
        return f'<table:table-cell table:number-columns-repeated="{count}"/>' if count > 1 else "<table:table-cell/>"

    def row(self, *cells, style="r"):
        self.rows.append(f'<table:table-row table:style-name="{style}">{"".join(cells)}</table:table-row>')

    def blank(self, count=1):
        for _ in range(count):
            self.rows.append('<table:table-row table:style-name="r"><table:table-cell/></table:table-row>')

    def xml(self):
        accent = self.accent
        columns = "".join(f'<style:style style:name="co{i}" style:family="table-column">'
                          f'<style:table-column-properties style:column-width="{w}cm"/></style:style>'
                          for i, w in enumerate(self.columns))
        column_tags = "".join(f'<table:table-column table:style-name="co{i}"/>' for i in range(len(self.columns)))
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document {NS} office:mimetype="application/vnd.oasis.opendocument.spreadsheet">
  <office:font-face-decls>
    <style:font-face style:name="Carlito" svg:font-family="Carlito" style:font-family-generic="swiss"/>
  </office:font-face-decls>
  <office:styles>
    <style:default-style style:family="table-cell">
      <style:text-properties style:font-name="Carlito" fo:font-size="11pt" fo:language="en" fo:country="US"/>
    </style:default-style>
    <number:number-style style:name="N2">
      <number:number number:decimal-places="2" number:min-decimal-places="2" number:min-integer-digits="1" number:grouping="true"/>
    </number:number-style>
    <number:percentage-style style:name="NP">
      <number:number number:decimal-places="0" number:min-integer-digits="1"/><number:text>%</number:text>
    </number:percentage-style>
    <style:style style:name="Default" style:family="table-cell"/>
  </office:styles>
  <office:automatic-styles>
    {columns}
    <style:style style:name="r" style:family="table-row"><style:table-row-properties style:row-height="0.6cm" style:use-optimal-row-height="false"/></style:style>
    <style:style style:name="rt" style:family="table-row"><style:table-row-properties style:row-height="1.1cm" style:use-optimal-row-height="false"/></style:style>
    <style:style style:name="t" style:family="table" style:master-page-name="Default"><style:table-properties table:display="true"/></style:style>
    <style:style style:name="title" style:family="table-cell"><style:table-cell-properties style:vertical-align="middle"/><style:text-properties fo:font-size="20pt" fo:font-weight="bold" fo:color="{accent}"/></style:style>
    <style:style style:name="sub" style:family="table-cell"><style:text-properties fo:color="#5F6069"/></style:style>
    <style:style style:name="sec" style:family="table-cell"><style:text-properties fo:font-size="12pt" fo:font-weight="bold" fo:color="{accent}"/></style:style>
    <style:style style:name="h" style:family="table-cell"><style:table-cell-properties fo:background-color="{accent}" fo:border="0.5pt solid {GREY}" style:vertical-align="middle"/><style:text-properties fo:color="#FFFFFF" fo:font-weight="bold"/></style:style>
    <style:style style:name="hr" style:family="table-cell"><style:table-cell-properties fo:background-color="{accent}" fo:border="0.5pt solid {GREY}" style:vertical-align="middle"/><style:paragraph-properties fo:text-align="end"/><style:text-properties fo:color="#FFFFFF" fo:font-weight="bold"/></style:style>
    <style:style style:name="c" style:family="table-cell"><style:table-cell-properties fo:border="0.5pt solid {GREY}" style:vertical-align="middle"/></style:style>
    <style:style style:name="cl" style:family="table-cell"><style:table-cell-properties fo:border="0.5pt solid {GREY}" fo:background-color="{LIGHT}" style:vertical-align="middle"/></style:style>
    <style:style style:name="n" style:family="table-cell" style:data-style-name="N2"><style:table-cell-properties fo:border="0.5pt solid {GREY}" style:vertical-align="middle"/></style:style>
    <style:style style:name="pct" style:family="table-cell" style:data-style-name="NP"><style:table-cell-properties fo:border="0.5pt solid {GREY}" style:vertical-align="middle"/></style:style>
    <style:style style:name="tl" style:family="table-cell"><style:table-cell-properties fo:border="0.5pt solid {GREY}" fo:background-color="{LIGHT}" style:vertical-align="middle"/><style:text-properties fo:font-weight="bold"/></style:style>
    <style:style style:name="tn" style:family="table-cell" style:data-style-name="N2"><style:table-cell-properties fo:border="0.5pt solid {GREY}" fo:background-color="{LIGHT}" style:vertical-align="middle"/><style:text-properties fo:font-weight="bold"/></style:style>
    <style:style style:name="big" style:family="table-cell" style:data-style-name="N2"><style:table-cell-properties fo:border="0.5pt solid {GREY}" fo:background-color="{LIGHT}" style:vertical-align="middle"/><style:text-properties fo:font-size="14pt" fo:font-weight="bold" fo:color="{accent}"/></style:style>
    <style:style style:name="lbl" style:family="table-cell"><style:text-properties fo:font-weight="bold"/></style:style>
    <style:style style:name="plain" style:family="table-cell"/>
  </office:automatic-styles>
  <office:body><office:spreadsheet>
    <table:table table:name="{escape(self.name)}" table:style-name="t">
      {column_tags}
      {"".join(self.rows)}
    </table:table>
  </office:spreadsheet></office:body>
</office:document>
'''


def monthly_budget():
    s = Sheet("Budget", [4.2, 3.0, 3.0, 3.0, 1.0, 4.2, 3.0])
    c, n, f, e = s.cell, s.number, s.formula, s.empty
    s.row(c("Monthly budget", "title", span=4), style="rt")
    s.row(c("Month:", "sub"), c("", "plain"))
    s.blank()
    s.row(c("Income", "sec", span=3), e(2), c("Summary", "sec", span=2))                      # row 4
    s.row(c("Source", "h"), c("Planned", "hr"), c("Actual", "hr"), e(2), c("Total income", "cl"), f("C10", "n"))
    s.row(c("Salary", "c"), n(0), n(0), e(2), c("Total expenses", "cl"), f("D24", "n"))
    s.row(c("Other income", "c"), n(0), n(0), e(2), c("Balance", "tl"), f("G5-G6", "big"))
    s.row(c("", "c"), n(0), n(0))
    s.row(c("", "c"), n(0), n(0))
    s.row(c("Total", "tl"), f("SUM([.B6:.B9])", "tn"), f("SUM([.C6:.C9])", "tn"))           # row 10
    s.blank()
    s.row(c("Expenses", "sec", span=4))                                                        # row 12
    s.row(c("Category", "h"), c("Planned", "hr"), c("Actual", "hr"), c("Difference", "hr"))   # row 13
    categories = ["Housing", "Utilities", "Groceries", "Transport", "Insurance", "Health", "Phone & internet",
                  "Entertainment", "Savings", "Other"]
    for index, category in enumerate(categories):
        r = 14 + index
        s.row(c(category, "c"), n(0), n(0), f(f"[.B{r}]-[.C{r}]", "n"))
    s.row(c("Total", "tl"), f("SUM([.B14:.B23])", "tn"), f("SUM([.C14:.C23])", "tn"), f("SUM([.D14:.D23])", "tn"))  # row 24
    return s


def invoice():
    s = Sheet("Invoice", [1.2, 7.0, 2.2, 3.0, 3.2])
    c, n, f, e = s.cell, s.number, s.formula, s.empty
    s.row(e(1), c("Your company", "title", span=2), e(1), c("INVOICE", "title"), style="rt")
    s.row(e(1), c("Street address", "sub", span=2), e(1), c("Invoice no.", "lbl"))
    s.row(e(1), c("City, postal code", "sub", span=2), e(1), c("Date", "lbl"))
    s.row(e(1), c("Phone · e-mail", "sub", span=2), e(1), c("Due date", "lbl"))
    s.blank()
    s.row(e(1), c("Bill to", "sec", span=2))
    s.row(e(1), c("Customer name", "plain", span=2))
    s.row(e(1), c("Customer address", "plain", span=2))
    s.blank()
    s.row(e(1), c("Description", "h"), c("Qty", "hr"), c("Unit price", "hr"), c("Amount", "hr"))   # row 10
    for r in range(11, 19):
        s.row(e(1), c("", "c"), n(0), n(0), f(f"[.C{r}]*[.D{r}]", "n"))
    s.row(e(1), e(2), c("Subtotal", "tl"), f("SUM([.E11:.E18])", "tn"))                          # row 19
    s.row(e(1), e(2), c("Tax rate", "cl"), n(0.2, "pct"))                                         # row 20
    s.row(e(1), e(2), c("Tax", "cl"), f("[.E19]*[.E20]", "n"))                                     # row 21
    s.row(e(1), e(2), c("Total", "tl"), f("[.E19]+[.E21]", "big"))                                 # row 22
    s.blank()
    s.row(e(1), c("Payment terms", "sec", span=2))
    s.row(e(1), c("Payable within 30 days. Thank you for your business.", "plain", span=4))
    return s


def expense_tracker():
    s = Sheet("Expenses", [2.8, 6.0, 3.2, 3.2, 2.8, 1.0, 3.2, 2.8])
    c, n, f, e = s.cell, s.number, s.formula, s.empty
    s.row(c("Expense tracker", "title", span=4), style="rt")
    s.row(c("Period:", "sub"), c("", "plain"))
    s.blank()
    s.row(c("Date", "h"), c("Description", "h"), c("Category", "h"), c("Payment method", "h"), c("Amount", "hr"),
          e(1), c("By category", "h"), c("Total", "hr"))                                                   # row 4
    categories = ["Groceries", "Transport", "Dining", "Bills", "Shopping", "Health", "Other"]
    for index in range(20):
        r = 5 + index
        side = ()
        if index < len(categories):
            side = (e(1), c(categories[index], "c"), f(f'SUMIF([.C5:.C24];[.G{r}];[.E5:.E24])', "n"))
        elif index == len(categories):
            side = (e(1), c("Total", "tl"), f("SUM([.H5:.H11])", "tn"))
        s.row(c("", "c"), c("", "c"), c("", "c"), c("", "c"), n(0), *side)
    s.row(c("", "tl"), c("Total", "tl"), c("", "tl"), c("", "tl"), f("SUM([.E5:.E24])", "big"))       # row 25
    return s


def weekly_schedule():
    s = Sheet("Schedule", [2.0] + [3.1] * 7)
    c, e = s.cell, s.empty
    s.row(c("Weekly schedule", "title", span=4), style="rt")
    s.row(c("Week of:", "sub"), c("", "plain"))
    s.blank()
    s.row(c("Time", "h"), *[c(day, "h") for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")])
    for hour in range(7, 22):
        s.row(c(f"{hour:02d}:00", "cl"), *[c("", "c") for _ in range(7)])
    return s


WORD = {"Meeting_notes": meeting_notes, "Report": report, "To-do_list": todo_list}
SHEET = {"Monthly_budget": monthly_budget, "Invoice": invoice, "Expense_tracker": expense_tracker,
         "Weekly_schedule": weekly_schedule}


# --- Conversion ------------------------------------------------------------------------------------

def soffice_command(soffice, profile):
    return [soffice, "--headless", "--norestore", f"-env:UserInstallation=file://{profile}"]


def convert(soffice, profile, source, target_dir, filter_name):
    subprocess.run(soffice_command(soffice, profile) + ["--convert-to", filter_name, "--outdir", str(target_dir),
                                                        str(source)],
                   check=True, stdout=subprocess.DEVNULL, timeout=600)


def ensure_thumbnail(soffice, profile, template, source):
    """LibreOffice stores Thumbnails/thumbnail.png when it saves; if a
    headless conversion left it out, render the first page and add it."""
    with zipfile.ZipFile(template) as archive:
        if "Thumbnails/thumbnail.png" in archive.namelist():
            return
    with tempfile.TemporaryDirectory() as tmp:
        convert(soffice, profile, source, tmp, "png")
        pictures = list(Path(tmp).glob("*.png"))
        if not pictures:
            raise SystemExit(f"{source}: LibreOffice rendered no page picture for the thumbnail")
        data = pictures[0].read_bytes()
    rebuilt = template.with_suffix(template.suffix + ".tmp")
    with zipfile.ZipFile(template) as old, zipfile.ZipFile(rebuilt, "w") as new:
        for item in old.infolist():
            new.writestr(item, old.read(item.filename),
                         compress_type=zipfile.ZIP_STORED if item.filename == "mimetype" else zipfile.ZIP_DEFLATED)
        new.writestr("Thumbnails/thumbnail.png", data, compress_type=zipfile.ZIP_DEFLATED)
    rebuilt.replace(template)


def build(out_dir, soffice="soffice"):
    out_dir = Path(out_dir)
    with tempfile.TemporaryDirectory() as tmp:
        profile = Path(tmp) / "profile"
        sources = Path(tmp) / "sources"
        sources.mkdir()
        jobs = [("word", WORD, "fodt", "ott:writer8_template", ".ott"),
                ("sheet", SHEET, "fods", "ots:calc8_template", ".ots")]
        for kind, makers, extension, filter_name, suffix in jobs:
            target = out_dir / kind
            target.mkdir(parents=True, exist_ok=True)
            for stem, maker in makers.items():
                source = sources / f"{stem}.{extension}"
                source.write_text(maker().xml(), encoding="utf-8", newline="\n")
                convert(soffice, profile, source, target, filter_name)
                template = target / (stem + suffix)
                if not template.exists():
                    raise SystemExit(f"{source}: LibreOffice did not write {template}")
                ensure_thumbnail(soffice, profile, template, source)
                print(f"built {template}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("out_dir")
    parser.add_argument("--soffice", default=shutil.which("soffice") or "soffice")
    parser.add_argument("--sources-only", action="store_true",
                        help="write the flat ODF sources into out_dir and stop (no LibreOffice needed)")
    args = parser.parse_args(argv)
    if args.sources_only:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for stem, maker in WORD.items():
            (out / f"{stem}.fodt").write_text(maker().xml(), encoding="utf-8", newline="\n")
        for stem, maker in SHEET.items():
            (out / f"{stem}.fods").write_text(maker().xml(), encoding="utf-8", newline="\n")
        return 0
    build(args.out_dir, args.soffice)
    return 0


if __name__ == "__main__":
    sys.exit(main())
