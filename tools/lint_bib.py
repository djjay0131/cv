"""Lint `.bib` files for missing or invalid fields.

Required-field checks (per entry type) + stricter rules for author format,
URL well-formedness, year sanity, DOI format, non-empty title, and GitHub
URL format. Applied to every entry so mistakes — whether hand-typed or
produced by a fetch-based skill — cannot reach master.

Usage: ``python -m tools.lint_bib own-bib.bib``
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

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

_YEAR_MIN = 1900
# Upper bound is computed at runtime so "in press" entries up to 2 years out
# remain valid as time passes.
_YEAR_MAX_OFFSET = 2

_DOI_RE = re.compile(r"^10\.\d+/.+")
_GITHUB_PREFIX = "https://github.com/"
_AUTHOR_SEP_RE = re.compile(r"\s+and\s+")


def _year_max() -> int:
    return datetime.datetime.now().year + _YEAR_MAX_OFFSET


def _check_authors(key: str, authors: str) -> list[str]:
    problems: list[str] = []
    s = authors.strip()
    if s.lower().endswith(" and") or s.lower() == "and":
        problems.append(f"entry {key!r}: author field ends with 'and' (trailing separator)")
    parts = [p.strip() for p in _AUTHOR_SEP_RE.split(s)]
    for part in parts:
        if "," in part:
            last, _, first = part.partition(",")
            if not last.strip() or not first.strip():
                problems.append(
                    f"entry {key!r}: malformed author {part!r} (comma form requires both sides)"
                )
    return problems


def _check_url(key: str, url: str) -> list[str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return [f"entry {key!r}: url malformed (bad scheme): {url!r}"]
    if not parsed.netloc:
        return [f"entry {key!r}: url malformed (no host): {url!r}"]
    return []


def _check_year_sanity(key: str, year: str) -> list[str]:
    # Caller guarantees `year` is 4-digit numeric (see _check_entry).
    y = int(year)
    ymax = _year_max()
    if not (_YEAR_MIN <= y <= ymax):
        return [f"entry {key!r}: year out of range [{_YEAR_MIN}, {ymax}]: {y}"]
    return []


def _check_doi(key: str, doi: str) -> list[str]:
    if not _DOI_RE.match(doi):
        return [f"entry {key!r}: doi malformed: {doi!r}"]
    return []


def _check_github(key: str, gh: str) -> list[str]:
    if not gh.startswith(_GITHUB_PREFIX):
        return [f"entry {key!r}: github field must start with {_GITHUB_PREFIX!r}: {gh!r}"]
    return _check_url(key, gh)


def _check_non_empty_title(key: str, title: str) -> list[str]:
    if not title.strip():
        return [f"entry {key!r}: title missing or empty"]
    return []


def _check_entry(entry: dict) -> list[str]:
    """Return a list of human-readable problems for a single entry (empty = clean)."""
    key = entry.get("ID", "<unknown>")
    etype = entry.get("ENTRYTYPE", "misc").lower()
    required = _REQUIRED_BY_TYPE.get(etype, _GENERIC_REQUIRED)

    problems: list[str] = []

    # Required fields present + non-empty.
    for field in required:
        value = entry.get(field, "").strip()
        if not value:
            problems.append(f"entry {key!r}: missing or empty required field {field!r}")

    # Year: both 4-digit-numeric (shape) and range (sanity).
    year = entry.get("year", "").strip()
    if year:
        if not (year.isdigit() and len(year) == 4):
            problems.append(f"entry {key!r}: invalid year {year!r} (must be 4-digit numeric)")
        else:
            problems.extend(_check_year_sanity(key, year))

    # Title: explicit non-empty check (complements required-fields check by
    # also validating after stripping special whitespace).
    title = entry.get("title", "")
    if title:
        problems.extend(_check_non_empty_title(key, title))

    # Author format: only if author field is present (required check catches absence).
    authors = entry.get("author", "")
    if authors.strip():
        problems.extend(_check_authors(key, authors))

    # Optional fields: only validate if present and non-empty.
    url = entry.get("url", "").strip()
    if url:
        problems.extend(_check_url(key, url))

    doi = entry.get("doi", "").strip()
    if doi:
        problems.extend(_check_doi(key, doi))

    github = entry.get("github", "").strip()
    if github:
        problems.extend(_check_github(key, github))

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
