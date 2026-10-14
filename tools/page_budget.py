"""Enforce per-variant PDF page budgets (owner D22, website ADR-0024).

Entry point: ``python -m tools.page_budget [--dist dist] [--variants-dir data/variants]``.

The owner fixed a page budget for each CV document:

* ``one-page`` — exactly 1 page;
* ``two-page`` — at most 2 pages;
* ``full``     — no limit.

The budget lives on the variant selector as ``length`` (the same field the hub
reads to group the one CV section), so this check needs no hand-maintained list:
it discovers variants exactly as ``tools.manifest`` does and reads each one's
budget from its own file. Counts the real built PDF, so a variant that renders
longer than its selector claims fails CI rather than shipping.

Page counting prefers ``pypdf`` (a pinned dev/runtime dependency for the check
job) and falls back to poppler's ``pdfinfo`` when pypdf is unavailable.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from tools.manifest import ManifestError, variant_names
from tools.schema import load_variant

_DEFAULT_DIST = Path("dist")
_DEFAULT_VARIANTS_DIR = Path("data/variants")

# length selector -> maximum page count. Absent means "no limit".
_MAX_PAGES: dict[str, Optional[int]] = {
    "one-page": 1,
    "two-page": 2,
    "full": None,
}


class BudgetError(ValueError):
    """A built PDF exceeds the page budget its variant selector declares."""


# The slug names the budget, so a selector cannot buy headroom by relabelling
# its `length`. A `*-2p` slug MUST declare `two-page`; the `one-page` slug MUST
# declare `one-page`. Without this, a 5-page `research-2p.yaml` declaring
# `length: full` would pass while its name promised 2 pages.
def expected_length_for_slug(slug: str) -> Optional[str]:
    if slug == "one-page":
        return "one-page"
    if slug.endswith("-2p"):
        return "two-page"
    return None


def count_pages(pdf: Path) -> int:
    """Number of pages in ``pdf``; pypdf if importable, else ``pdfinfo``."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return _count_pages_pdfinfo(pdf)
    try:
        return len(PdfReader(str(pdf)).pages)
    except Exception as e:  # pypdf raises a variety; surface the file name
        raise BudgetError(f"cannot read {pdf} as a PDF: {e}") from e


def _count_pages_pdfinfo(pdf: Path) -> int:
    try:
        completed = subprocess.run(
            ["pdfinfo", str(pdf)], capture_output=True, text=True, check=False
        )
    except OSError as e:
        raise BudgetError(f"cannot run pdfinfo to count pages of {pdf}: {e}") from e
    if completed.returncode != 0:
        raise BudgetError(f"pdfinfo failed on {pdf}: {completed.stderr.strip()}")
    for line in completed.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise BudgetError(f"pdfinfo reported no page count for {pdf}")


def budget_for(length: str, variant: str) -> Optional[int]:
    if length not in _MAX_PAGES:
        raise BudgetError(
            f"variant {variant!r} declares length {length!r}; "
            f"expected one of {sorted(_MAX_PAGES)}"
        )
    return _MAX_PAGES[length]


def violation(length: str, pages: int, variant: str) -> Optional[str]:
    """Return a human message if ``pages`` breaks the budget, else None."""
    limit = budget_for(length, variant)
    if limit is None:
        return None
    if length == "one-page" and pages != 1:
        return f"{variant}: length 'one-page' must be exactly 1 page, built {pages}"
    if pages > limit:
        return f"{variant}: length {length!r} allows at most {limit} pages, built {pages}"
    return None


def check(
    dist: Path = _DEFAULT_DIST,
    variants_dir: Path = _DEFAULT_VARIANTS_DIR,
    count: Callable[[Path], int] = count_pages,
) -> list[str]:
    """Return one message per budget violation found under ``dist``."""
    violations: list[str] = []
    for name in variant_names(variants_dir):
        variant = load_variant(variants_dir / f"{name}.yaml")
        expected = expected_length_for_slug(name)
        if expected is not None and variant.length != expected:
            violations.append(
                f"{name}: the slug implies length {expected!r}, but the selector "
                f"declares {variant.length!r} — a slug cannot relabel its budget"
            )
        pdf = dist / f"{name}.pdf"
        if not pdf.exists():
            violations.append(f"{name}: expected built PDF at {pdf}, which is missing")
            continue
        pages = count(pdf)
        message = violation(variant.length, pages, name)
        if message:
            violations.append(message)
    return violations


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.page_budget",
        description="Fail when a built CV PDF exceeds its variant's page budget.",
    )
    parser.add_argument("--dist", type=Path, default=_DEFAULT_DIST)
    parser.add_argument("--variants-dir", type=Path, default=_DEFAULT_VARIANTS_DIR)
    args = parser.parse_args(argv)

    try:
        violations = check(dist=args.dist, variants_dir=args.variants_dir)
    except (BudgetError, ManifestError, ValueError, FileNotFoundError) as e:
        print(f"page-budget check failed: {e}", file=sys.stderr)
        return 1

    if violations:
        print("page-budget check FAILED:", file=sys.stderr)
        for message in violations:
            print(f"  - {message}", file=sys.stderr)
        return 1

    print(f"page-budget check passed ({len(variant_names(args.variants_dir))} variants)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
