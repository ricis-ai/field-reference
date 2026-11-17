AB9MZ MASTER FIELD REFERENCE
Edition 2.0, 2026-10-31
REVIEW DRAFT FOR GREGG AND PATRICIA

OPEN AB9MZ_Master.html IN A FULL BROWSER
Use the native section checkboxes, then Download selected PDF or Download
selected Word. Tab moves between controls; Space toggles a checkbox.
The selector works offline and includes its own document-generation code.
A Files or ChatGPT preview may disable JavaScript or downloads; use a full
browser. The ready-made files in sections/ remain usable without scripts.

WHAT IS INCLUDED
22 section PDF and DOCX pairs, generated from one master.json source.
The complete book is 112 pages, or 56 double-sided letter-size sheets.
The complete phonetic alphabet is one page, without any Morse column.
The Morse section is ten pages: letters, numbers, ITU punctuation,
procedural signals, accented and regional extensions, software punctuation
conventions, symbols sent as sequences, and timing and distress.
CW abbreviations and Q signals are separately selectable sections.

TYPEFACE AND PRINTING
Helvetica throughout, including the master reading interface and exported
Word documents. PDF faces are Helvetica and Helvetica Bold. Main print
type is 22 points, headings 28, Morse patterns 26 bold, table notes 20,
reference descriptions 18, and running information 14. No DejaVu fonts
are used or bundled. Word may substitute an installed sans serif font on
systems without Helvetica; the PDF preserves the fixed Helvetica layout.
Print US Letter, portrait, actual size or 100 percent, duplex, long edge.
The mirrored margins reserve 1.1 inches inside and 0.6 inch outside.
Test AB9MZ_Print_Test.pdf before printing or laminating the entire book.

CUSTOM EDITIONS
Cover and contents, cited reference pages, and front-facing section starts
are optional. Contents page numbers and PDF bookmarks are rebuilt for each
selection. Save my section choices creates a small JSON profile that can
be loaded later. Your choices may also persist in the same browser.
Single-section download buttons create that section alone, with no cover
or extra source appendix. The source directory remains in the master.

MAINTAINING THE MASTER
master.json is the authoritative content source. Edit it to update shared
text or tables, keeping section and page identifiers stable. Run:

python3 rebuild.py

Requirements: Python 3 with ReportLab, and Node.js. The JavaScript libraries
are bundled; no npm install or network connection is required for rebuild.
ReportLab can be installed in a suitable Python environment with:
python3 -m pip install reportlab

To build a saved custom selection as the main exported edition, run:
python3 rebuild.py --selection AB9MZ_Selection.json

A rebuild regenerates the master selector, complete PDF and Word editions,
all section PDF and Word files, and the print test. It validates identifiers,
source references and table geometry before creating the archive. Exported
Word/PDF files are snapshots; editing one does not update the master.
Downloaded copies do not synchronize automatically. Rebuild and distribute
new versions after master edits. The same revision appears in metadata.

ACCESSIBILITY AND VERIFICATION
Read ACCESSIBILITY_REVIEW.html before release. It records three review
passes, repairs, evidence and open manual checks. The selector passed live
browser axe checks in light and dark modes. Narrow-screen testing included
twice-default text and WCAG text spacing. Keyboard checkbox use, reading
links, PDF generation and focus restoration were exercised in the browser.

The tagged/ folder includes the full book and all 22 individual tagged PDF
review editions. Their language, structure trees and table-header scope
were inspected. These are not independently certified PDF/UA documents.
The tagged conversion embeds Nimbus Sans, a Helvetica-compatible font,
because Helvetica is not installed in the conversion environment.

Root and sections/ PDF files, including browser-generated custom PDFs, are
fixed-layout PRINT editions and are not tagged. Use HTML, Word or tagged/
for semantic reading. To make a tagged custom edition, download selected
Word and use a document application with tagged PDF export. The HTML
provides spoken dit/dah equivalents for the Morse patterns.

VoiceOver, NVDA and JAWS review remains open. No blanket WCAG 2.2 AA claim
is made. The report also lists 11 contrast items requiring human review
in the enlarged/spacing audit, browser-zoom checks, and cognitive review.

After changing master.json, rebuild first, then refresh tagged PDFs with:
python3 build_tagged.py
This optional step requires LibreOffice. If it is not on PATH, use:
python3 build_tagged.py --soffice /path/to/soffice
Review the new PDFs before replacing distributed copies.

SCOPE AND SOURCES
Band privileges target the contiguous United States and require current
local verification. The master includes 37 source references. ITU core
Morse symbols are distinguished from regional and software conventions;
there is no single Morse signal for every Unicode character. MARS, CAP
and SHARES operating assignments remain in their authorized program plans.
ICS worksheets are large-print adaptations, not official FEMA forms.

LICENSES
The original field-reference content and scripts are included for your
maintenance. Third-party library license notices are included separately.
