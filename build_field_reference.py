#!/usr/bin/env python3
"""Build plain-text (.txt) and contracted-UEB Braille (.brf) editions of the
AB9MZ Master Field Reference from master.json.

One .txt and one .brf per section (22 sections), plus a whole-book .txt and
.brf. The .txt is rendered first from master.json; each .brf is translated
from the same paragraph list, so the two match exactly.

Render rules:
- Section heading first, then each page's title as a subheading (skipped
  when the page title repeats the section title), then the page's
  paragraphs, table, note, and references, in that order.
- Tables are linearized: 2-column tables one line per row (cells joined
  with a space); 3-column tables one line per row (cells joined with
  ", "); the two 4-column side-by-side tables are split into their two
  logical pairs (two lines per row). Header rows become lines in the same
  form as the data rows.
- Morse dot/dash patterns are spelled as words ("dit dah") wherever they
  appear as standalone tokens, in tables and in prose. A table cell that
  IS a pattern — even a single dot (E) or dash (T) — is spelled out; in
  prose only runs of two or more are converted, so real periods and
  hyphens are left alone. Raw dots and dashes read as punctuation in
  Braille.
- References are expanded from source numbers to source titles
  ("References: Morse code; Q signals").

Output: txt/<section-id>_v2.0-YYYYMMDD-HHMM-AB9MZ.txt,
braille/<section-id>_v2.0-YYYYMMDD-HHMM-AB9MZ.brf, and the whole-book
files under the same scheme (stem AB9MZ_Amateur_Radio_Field_Reference).
40 cells per line, 25 lines per page, form feed between pages.
Tables: en-us-brf.dis + en-ueb-g2.ctb (contracted grade 2 UEB).

FILENAMES (Gregory, 2026-11-16): file-name_v99.99-YYYYMMDD-HHMM-AUTHOR.xxx
— version with no leading zeros, revision date, 24-hour Central time,
author call sign. The scheme applies to these .txt/.brf files only; the
71 kit files already on group Files keep their names. Version follows
the book edition (2.0); author is AB9MZ. All output filenames go through
output_name() below — change the VERSION/AUTHOR constants and re-run to
regenerate under a new revision.

Usage: python3 build_field_reference.py
"""
import datetime
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

import louis

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "master.json")
TXT_DIR = os.path.join(HERE, "txt")
BRF_DIR = os.path.join(HERE, "braille")
REPORT = os.path.join(HERE, "BUILD-REPORT.md")

TABLES = ["en-us-brf.dis", "en-ueb-g2.ctb"]
WIDTH = 40
LINES_PER_PAGE = 25
PAGE_BREAK = "\f"
BOOK_FILE = "AB9MZ_Amateur_Radio_Field_Reference"


# File-naming scheme (Gregory, 2026-11-16): the .txt/.brf outputs carry
# a version, revision date/time, and author stamp. One timestamp for the
# whole build so a revision is one coherent set.
VERSION = "2.0"
AUTHOR = "AB9MZ"
STAMP = datetime.datetime.now(ZoneInfo("America/Chicago")).strftime(
    "%Y%m%d-%H%M")


def output_name(stem, ext):
    """Output filename under Gregory's naming scheme:
    file-name_v99.99-YYYYMMDD-HHMM-AUTHOR.xxx."""
    return "%s_v%s-%s-%s.%s" % (stem, VERSION, STAMP, AUTHOR, ext)

# A standalone token of two or more dots/dashes (a Morse pattern). Single
# "." and "-" are punctuation and are left alone; "3.900" contains digits
# and cannot match.
MORSE_TOKEN = re.compile(r"(?<![\w.])[.-]{2,}(?![\w.])")


def morse_words(token):
    """'.-' -> 'dit dah'; '-----' -> 'dah dah dah dah dah'."""
    return " ".join("dit" if ch == "." else "dah" for ch in token)


def convert_morse_tokens(text):
    """Spell out every standalone Morse pattern in a string as words."""
    return MORSE_TOKEN.sub(lambda m: morse_words(m.group(0)), text)


def convert_cell(cell):
    """Convert one table cell: a cell that IS a Morse pattern (even a
    single dot or dash, E and T) becomes dit/dah words; anything else
    gets the standalone-token treatment."""
    text = str(cell)
    if re.fullmatch(r"[.-]+", text.strip()):
        return morse_words(text.strip())
    return convert_morse_tokens(text)


def render_table(table):
    """A master.json table -> plain-text lines, one row per line."""
    lines = []
    cols = len(table[0])
    for row in table:
        cells = [convert_cell(c) for c in row]
        if cols == 4:
            # Side-by-side pairs (phonetics, Morse letters): split into
            # the two logical pairs, two lines per row.
            lines.append("%s %s" % (cells[0], cells[1]))
            lines.append("%s %s" % (cells[2], cells[3]))
        elif cols == 3:
            # Commas keep the three columns apart (e.g. "AR, dit dah dit
            # dah dit, End of message"; "3.900, 120.0, 60.0").
            lines.append(", ".join(cells))
        else:
            # 1- and 2-column tables: cells joined with a space.
            lines.append(" ".join(cells))
    return lines


def render_page(page, section_title, sources):
    """One page -> paragraph list ("" marks a blank line)."""
    paragraphs = []
    if page.get("title") and page["title"] != section_title:
        paragraphs.append(page["title"])
        paragraphs.append("")
    for para in page.get("paragraphs", []):
        paragraphs.append(convert_morse_tokens(para))
        paragraphs.append("")
    table = page.get("table")
    if table:
        paragraphs.extend(render_table(table))
        paragraphs.append("")
    note = page.get("note")
    if note:
        paragraphs.append(convert_morse_tokens(note))
        paragraphs.append("")
    refs = page.get("refs")
    if refs:
        titles = []
        for part in str(refs).split(","):
            part = part.strip()
            try:
                titles.append(sources[int(part)])
            except (ValueError, KeyError):
                titles.append("Source %s" % part)
        paragraphs.append("References: " + "; ".join(titles))
        paragraphs.append("")
    return paragraphs


def render_section(section, sources):
    """One section -> paragraph list, self-identifying for standalone use."""
    paragraphs = [
        "AB9MZ Master Field Reference, Edition 2.0",
        "",
        section["title"],
        "",
    ]
    for page in section.get("pages", []):
        paragraphs.extend(render_page(page, section["title"], sources))
    # Trim trailing blank lines.
    while paragraphs and paragraphs[-1] == "":
        paragraphs.pop()
    return paragraphs


def render_book(master, sources):
    """The whole book -> paragraph list, one section per Braille page run."""
    paragraphs = [
        "Amateur Radio Field Reference",
        "Edition 2.0, October 31, 2026",
        "Gregory David Rosenberg, AB9MZ",
        "",
    ]
    sections = master["sections"]
    for i, section in enumerate(sections):
        if i:
            paragraphs.append(PAGE_BREAK)
        paragraphs.append(section["title"])
        paragraphs.append("")
        for page in section.get("pages", []):
            paragraphs.extend(
                render_page(page, section["title"], sources)
            )
    while paragraphs and paragraphs[-1] == "":
        paragraphs.pop()
    return paragraphs


def txt_from_paragraphs(paragraphs):
    """Paragraph list -> plain-text file content.

    A forced page break is a blank line in the .txt; the text content is
    identical to the .brf's.
    """
    return "\n".join("" if p == PAGE_BREAK else p for p in paragraphs) + "\n"


def wrap(braille, width=WIDTH):
    """Word-wrap one translated paragraph to lines of at most `width` cells."""
    words = braille.split(" ")
    lines = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    # A single word longer than a line (should not happen here) is
    # hard-split rather than allowed to overflow.
    split = []
    for line in lines:
        while len(line) > width:
            split.append(line[:width])
            line = line[width:]
        split.append(line)
    return split


def prepare_text(text):
    """Braille typography tweaks, applied before translation.

    liblouis's UEB table mishandles a spaced slash inside a formula
    ("I = E / R" loses capitals); the unspaced form translates and
    round-trips exactly. No spaced slash occurs in this book, but the
    rule is kept for safety.
    """
    return text.replace(" / ", "/")


def brf_from_paragraphs(paragraphs):
    """Translate a paragraph list to .brf lines; returns (lines, plain_text)."""
    lines = []
    plain_parts = []
    for para in paragraphs:
        if para == PAGE_BREAK:
            lines.append(PAGE_BREAK)
            continue
        if para == "":
            lines.append("")
            plain_parts.append("")
            continue
        text = prepare_text(para)
        lines.extend(wrap(louis.translateString(TABLES, text)))
        plain_parts.append(text)
    # Paginate: a form feed after every 25 lines, plus the forced breaks.
    out = []
    on_page = 0
    for line in lines:
        if line == PAGE_BREAK:
            if on_page:
                out.append(PAGE_BREAK)
                on_page = 0
            continue
        out.append(line)
        on_page += 1
        if on_page == LINES_PER_PAGE:
            out.append(PAGE_BREAK)
            on_page = 0
    # No trailing form feed.
    while out and out[-1] == PAGE_BREAK:
        out.pop()
    plain = "\n".join(plain_parts)
    return out, plain


def validate_brf(label, lines, plain):
    """Validate one .brf file; returns a list of problems (empty = valid)."""
    problems = []
    content = [ln for ln in lines if ln != PAGE_BREAK]
    for ln in content:
        if len(ln) > WIDTH:
            problems.append("%s: line over %d cells: %r" % (label, WIDTH, ln))
        for ch in ln:
            if not (0x20 <= ord(ch) <= 0x5F):
                problems.append(
                    "%s: char outside Braille range: %r" % (label, ch)
                )
                break
    joined = " ".join(content)
    # Contraction spot checks, only where the words occur: short sections
    # (a table and little prose) may not contain "the" or "and" at all.
    if re.search(r"\bthe\b", plain, re.IGNORECASE) and "!" not in joined:
        problems.append("%s: 'the' present but no contracted 'the' (!)" % label)
    if re.search(r"\band\b", plain, re.IGNORECASE) and "&" not in joined:
        problems.append("%s: 'and' present but no contracted 'and' (&)" % label)
    # Round-trip: back-translate and compare against the assembled text.
    # Lines are joined with spaces, not newlines: the back-translator
    # glues a line-final contraction to the next line's first word across
    # a newline, while a space is the true word boundary the wrap broke at.
    back = louis.backTranslateString(TABLES, " ".join(content))
    norm_back = " ".join(back.split())
    norm_plain = " ".join(
        plain.replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .split()
    )
    # Known liblouis back-translation artifacts, each verified forward-
    # correct. The plain text is the authority: a normalization only ever
    # repairs the back-translation toward it, and the full comparison
    # below still has to match.
    # 1. "AC": forward Braille is ;,,AC — grade-1 + caps-word. The
    #    grade-1 mark is REQUIRED (bare ,,AC reads as "according", the
    #    UEB contraction for it); the back-translator renders it "Ac".
    assert not re.search(r"\bAc\b", norm_plain), "plain text has 'Ac'"
    norm_back = re.sub(r"\bAc\b", "AC", norm_back)
    # 2. "FCC's": forward Braille reads the possessive s as capital
    #    (,,FCC'S); the meaning is clear in context.
    norm_back = norm_back.replace("FCC'S", "FCC's")
    # 3. Dotted initials ("U.S.", "p.m.", "a.m."): forward Braille is
    #    correct, unambiguous UEB. The back-translator reads the second
    #    initial as a whole-word contraction ("U.So.", "p.more.").
    assert "U.So." not in norm_plain, "plain text has 'U.So.'"
    assert "p.more." not in norm_plain, "plain text has 'p.more.'"
    assert "a.more." not in norm_plain, "plain text has 'a.more.'"
    norm_back = norm_back.replace("U.So.", "U.S.")
    norm_back = norm_back.replace("p.more.", "p.m.")
    norm_back = norm_back.replace("a.more.", "a.m.")
    # 4. ");" (close paren + semicolon): forward Braille is ">2 —
    #    close paren, then the semicolon cell — correct, unambiguous
    #    UEB. The back-translator reads the semicolon cell as the "be"
    #    groupsign and renders it ")be".
    assert ")be" not in norm_plain, "plain text has ')be'"
    norm_back = norm_back.replace(")be", ");")
    # 5. Single-capital formulas with + or - ("R = E + I"): forward
    #    Braille is a caps passage — correct, unambiguous UEB. The
    #    back-translator ignores the passage and renders the letters
    #    after the first lowercase ("R = e + i").
    assert "R = e + i" not in norm_plain, "plain text has 'R = e + i'"
    assert "R = e - i" not in norm_plain, "plain text has 'R = e - i'"
    norm_back = norm_back.replace("R = e + i", "R = E + I")
    norm_back = norm_back.replace("R = e - i", "R = E - I")
    # 6. Caps passages ("ITU R M.1677", "I SAY AGAIN", the traffic
    #    preamble): forward Braille is a caps passage (,,, opens, ,'
    #    closes) — correct, unambiguous UEB, a reader reads capitals
    #    throughout. The back-translator drops the passage and renders
    #    the words lowercase after the first letter. Each repair below
    #    was verified forward-correct by hand (the passage opens and
    #    closes properly in the cells).
    assert "Itu r m.1677" not in norm_plain, "plain text has 'Itu r m.1677'"
    norm_back = norm_back.replace("Itu r m.1677", "ITU R M.1677")
    assert "I say again: i am repeating" not in norm_plain
    norm_back = norm_back.replace(
        "I say again: i am repeating", "I SAY AGAIN: I am repeating"
    )
    assert "1 R ab9mz 10 tinley park il 0200z nov 1" not in norm_plain
    norm_back = norm_back.replace(
        "1 R ab9mz 10 tinley park il 0200z nov 1",
        "1 R AB9MZ 10 TINLEY PARK IL 0200Z NOV 1",
    )
    # 7. "RCVR": forward Braille is ;,,RCVR — grade-1 + caps-word. The
    #    grade-1 mark is REQUIRED (as for "AC" above); the
    #    back-translator renders it "Rcvr".
    assert not re.search(r"\bRcvr\b", norm_plain), "plain text has 'Rcvr'"
    norm_back = re.sub(r"\bRcvr\b", "RCVR", norm_back)
    # 8. More caps passages, same class as repair 6 (each verified
    #    forward-correct: the passage opens with ,,, and closes with ,').
    #    "S O S" is spaced single capitals in the SOS paragraph; the
    #    traffic section's message-text example, its check line, and its
    #    SAY AGAIN WORD AFTER / WORD BEFORE prowords.
    assert "There are no S o s letter gaps" not in norm_plain
    norm_back = norm_back.replace(
        "There are no S o s letter gaps", "There are no S O S letter gaps"
    )
    assert "Text: Exercise shelter one has power x no additional batteries needed" not in norm_plain
    norm_back = norm_back.replace(
        "Text: Exercise shelter one has power x no additional batteries needed",
        "Text: EXERCISE SHELTER ONE HAS POWER X NO ADDITIONAL BATTERIES NEEDED",
    )
    assert "Check is 10: Exercise 1, shelter 2, one 3, has 4, power 5, x 6, no 7, additional 8, batteries 9, needed 10." not in norm_plain
    norm_back = norm_back.replace(
        "Check is 10: Exercise 1, shelter 2, one 3, has 4, power 5, x 6, no 7, additional 8, batteries 9, needed 10.",
        "Check is 10: EXERCISE 1, SHELTER 2, ONE 3, HAS 4, POWER 5, X 6, NO 7, ADDITIONAL 8, BATTERIES 9, NEEDED 10.",
    )
    assert "Use Say again word after, word before, or the requested group" not in norm_plain
    norm_back = norm_back.replace(
        "Use Say again word after, word before, or the requested group",
        "Use SAY AGAIN WORD AFTER, WORD BEFORE, or the requested group",
    )
    # 9. The quotation-mark character: forward Braille is the UEB opening
    #    double-quote cell (dots 2-3-6, .brf "8") — the correct UEB
    #    rendering of a '"' character. The back-translator reads that
    #    cell as the legacy EBAE "his" sign and renders it "his".
    assert 'Quotation marks his dit dah dit dit dah dit' not in norm_plain
    norm_back = norm_back.replace(
        "Quotation marks his dit dah dit dit dah dit",
        'Quotation marks " dit dah dit dit dah dit',
    )
    # 10. Underscore runs (fill-in blanks in the forms section): each "_"
    #    is two Braille cells, so a long run wraps across lines, and the
    #    line-joining space above lands inside the run in the
    #    back-translation. The Braille itself is correct — a reader feels
    #    the run continue across the line break. Collapse spaces between
    #    underscores on BOTH sides, so the comparison still verifies the
    #    total count on each run. (No two runs are separated by a bare
    #    space in this book, so nothing real is hidden.)
    while "_ _" in norm_back:
        norm_back = norm_back.replace("_ _", "__")
    while "_ _" in norm_plain:
        norm_plain = norm_plain.replace("_ _", "__")
    if norm_back != norm_plain:
        for i, (a, b) in enumerate(zip(norm_back, norm_plain)):
            if a != b:
                problems.append(
                    "%s: round-trip mismatch at char %d: back %r vs plain %r"
                    % (
                        label,
                        i,
                        norm_back[max(0, i - 40):i + 40],
                        norm_plain[max(0, i - 40):i + 40],
                    )
                )
                break
        else:
            problems.append(
                "%s: round-trip length mismatch: back %d chars, plain %d"
                % (label, len(norm_back), len(norm_plain))
            )
    return problems


def main():
    with open(MASTER, encoding="utf-8") as f:
        master = json.load(f)
    sources = {s["id"]: s["title"] for s in master["sources"]}
    os.makedirs(TXT_DIR, exist_ok=True)
    os.makedirs(BRF_DIR, exist_ok=True)

    jobs = []  # (stem, paragraphs)
    for section in master["sections"]:
        jobs.append((section["id"], render_section(section, sources)))
    jobs.append((BOOK_FILE, render_book(master, sources)))

    rows = []
    all_problems = []
    for stem, paragraphs in jobs:
        txt_path = os.path.join(TXT_DIR, output_name(stem, "txt"))
        txt = txt_from_paragraphs(paragraphs)
        with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)
        lines, plain = brf_from_paragraphs(paragraphs)
        brf_path = os.path.join(BRF_DIR, output_name(stem, "brf"))
        with open(brf_path, "w", encoding="ascii", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        problems = validate_brf(stem, lines, plain)
        pages = lines.count(PAGE_BREAK) + 1
        content_lines = len([ln for ln in lines if ln != PAGE_BREAK])
        rows.append(
            (stem, len(txt.splitlines()), os.path.getsize(txt_path),
             content_lines, pages, os.path.getsize(brf_path), problems)
        )
        all_problems.extend(problems)
        print(
            "%s: txt %d lines, brf %d lines / %d pages%s"
            % (
                stem,
                len(txt.splitlines()),
                content_lines,
                pages,
                "" if not problems else " — PROBLEMS: " + "; ".join(problems),
            )
        )

    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Field Reference build report — .txt and .brf editions\n\n")
        f.write("Built from master.json (Edition 2.0, 2026-10-31) by "
                "build_field_reference.py. Each .brf is translated from "
                "the same paragraph list as its .txt, so the two match "
                "exactly. Translation: liblouis contracted grade 2 UEB "
                "(en-us-brf.dis + en-ueb-g2.ctb), 40 cells per line, "
                "25 lines per page, form feed between pages.\n\n")
        f.write("## Files\n\n")
        f.write("| File | .txt lines | .txt bytes | .brf lines | "
                ".brf pages | .brf bytes | Validation |\n")
        f.write("| --- | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for stem, t_lines, t_bytes, b_lines, b_pages, b_bytes, probs in rows:
            f.write("| %s | %d | %d | %d | %d | %d | %s |\n" % (
                stem, t_lines, t_bytes, b_lines, b_pages, b_bytes,
                "OK" if not probs else "; ".join(probs),
            ))
        f.write("\nTotals: %d .txt files, %d .brf files, %d Braille pages "
                "across the 22 section files.\n\n" % (
                    len(rows), len(rows),
                    sum(r[4] for r in rows[:-1]),
                ))
        f.write("## Judgment calls\n\n")
        f.write("- Tables are linearized one row per line. 2-column "
                "tables join cells with a space (\"A Alfa\"); 3-column "
                "tables join cells with \", \" so the columns stay apart "
                "(\"AR, dit dah dit dah dit, End of message\"); the two "
                "4-column side-by-side tables (phonetics, Morse letters) "
                "are split into their two logical pairs, two lines per "
                "row. Header rows render in the same form as data rows.\n")
        f.write("- Morse dot/dash patterns are spelled as words "
                "(\"dit dah\") wherever they appear as standalone tokens, "
                "in tables and in prose (including \"SOS is ...---...\" in "
                "the timing page). A table cell that IS a pattern is "
                "spelled out even when it is a single dot (E) or dash "
                "(T); in prose only runs of two or more are converted, so "
                "real periods and hyphens are left alone. Raw dots and "
                "dashes read as punctuation in Braille.\n")
        f.write("- Page references are expanded from source numbers to "
                "source titles (\"References: Morse code; Q signals\") "
                "instead of bare numbers.\n")
        f.write("- A page title that repeats its section title is not "
                "printed twice (7 pages: phonetics, ARES, RACES, MARS, "
                "Civil Air Patrol, SHARES, Official Observer).\n")
        f.write("- Each section file opens with \"AB9MZ Master Field "
                "Reference, Edition 2.0\" so a standalone section still "
                "says what book it came from. The whole-book file opens "
                "with the full title block and starts each section on a "
                "new Braille page.\n")
        f.write("- Validation: every .brf line at most 40 cells, every "
                "character in the Braille ASCII range, and every file "
                "back-translates to its .txt. The known liblouis "
                "back-translation artifacts repaired in validation (each "
                "verified forward-correct by hand — see "
                "build_field_reference.py validate_brf) are: the grade-1 "
                "+ caps-word words \"AC\" and \"RCVR\", which the "
                "back-translator renders \"Ac\" and \"Rcvr\"; seven caps "
                "passages the back-translator drops (\"ITU R M.1677\", "
                "\"I SAY AGAIN\", the spaced capitals \"S O S\", the "
                "traffic preamble \"1 R AB9MZ 10 TINLEY PARK IL 0200Z "
                "NOV 1\", the traffic message text \"EXERCISE SHELTER "
                "ONE HAS POWER X NO ADDITIONAL BATTERIES NEEDED\", its "
                "check line, and the \"SAY AGAIN WORD AFTER, WORD "
                "BEFORE\" prowords); the quotation-mark character, whose "
                "UEB cell the back-translator reads as the legacy EBAE "
                "\"his\" sign; and underscore runs in the forms section, "
                "which wrap across Braille lines (each \"_\" is two "
                "cells) so the line-joining space lands inside the run "
                "in the back-translation — spaces between underscores "
                "are collapsed on both sides before comparing, so the "
                "total count per run is still verified.\n")
        f.write("- Output filenames follow Gregory's naming scheme "
                "(2026-11-16): file-name_v%s-%s-%s.xxx — version %s "
                "(the book edition), revision date and 24-hour Central "
                "time, author %s. The scheme applies to these .txt/.brf "
                "files only; the kit files keep their names.\n" % (
                    VERSION, STAMP, AUTHOR, VERSION, AUTHOR))

    if all_problems:
        print("\nVALIDATION FAILED (%d problems)" % len(all_problems))
        sys.exit(1)
    print("\nAll %d .brf files valid." % len(jobs))


if __name__ == "__main__":
    main()
