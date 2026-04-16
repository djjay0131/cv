"""Lint `.bib` files for missing or invalid required fields.

Required fields per entry type are minimal on purpose — enough to guarantee
that biblatex and the website renderer both produce sensible output.

Usage: ``python -m tools.lint_bib own-bib.bib``
"""

from __future__ import annotations

import sys
from pathlib import Path

import bibtexparser


class BibLintError(ValueError):
    """One or more bib entries failed validation."""


# Fields that must be present and non-empty for each entry type.
_REQUIRED_BY_TYPE: dict[str, tuple[str, ...]] = {
    "article": ("author", "title", "journal", "year"),
    "inproceedings": ("author", "title", "booktitle", "year"),
    "book": ("author", "title", "publisher", "year"),
    "incollection": ("author", "title", "booktitle", "publisher", "year"),
    "techreport": ("author", "title", "institution", "year"),
    "misc": ("author", "title", "year"),
    "unpublished": ("author", "title", "year"),
}
# Entry types not in the map get a generic requirement.
_GENERIC_REQUIRED = ("author", "title", "year")


def _check_entry(entry: dict) -> list[str]:
    """Return a list of human-readable problems for a single entry (empty = clean)."""
    key = entry.get("ID", "<unknown>")
    etype = entry.get("ENTRYTYPE", "misc").lower()
    required = _REQUIRED_BY_TYPE.get(etype, _GENERIC_REQUIRED)

    problems: list[str] = []
    for field in required:
        value = entry.get(field, "").strip()
        if not value:
            problems.append(f"entry {key!r}: missing or empty required field {field!r}")

    # Year must be a 4-digit integer (YYYY).
    year = entry.get("year", "").strip()
    if year and not (year.isdigit() and len(year) == 4):
        problems.append(
            f"entry {key!r}: invalid year {year!r} (must be 4-digit numeric)"
        )

    return problems


def lint_bib(path: Path) -> None:
    """Validate a .bib file; raise BibLintError if any entry is invalid."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"bib file not found: {path}")

    parser = bibtexparser.bparser.BibTexParser(
        common_strings=True, ignore_nonstandard_types=False
    )
    with path.open(encoding="utf-8") as f:
        db = bibtexparser.load(f, parser=parser)

    all_problems: list[str] = []
    for entry in db.entries:
        all_problems.extend(_check_entry(entry))

    if all_problems:
        raise BibLintError(
            f"{len(all_problems)} bib validation error(s) in {path}:\n  - "
            + "\n  - ".join(all_problems)
        )


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("usage: python -m tools.lint_bib <path.bib>", file=sys.stderr)
        return 2
    try:
        lint_bib(Path(argv[0]))
    except BibLintError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
