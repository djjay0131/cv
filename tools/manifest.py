"""Generate the research hub's publishing manifest for a staged ``dist/``.

Entry point: ``python -m tools.manifest [--dist dist]``.

The hub at https://jason.cusati.us does not know how this repository builds
anything. The entire interface is a finished ``dist/`` folder whose root holds a
``manifest.json`` describing what is in it, uploaded to the hub's content bucket
by the hub's own composite action (``djjay0131/website/contract/publish``). The
authority on the manifest's shape is ``contract/manifest.schema.json`` in the
website repository; this module mirrors the handful of rules it needs so that a
bad manifest fails here, in cv's own build, instead of in the hub's action.

What cv publishes (website ADR-0008 decision 2):

* one ``format: pdf`` item per variant discovered in ``data/variants/``, at
  ``<variant>.pdf``;
* one ``format: data`` item, slug ``cv-data``, at ``cv-data/``, carrying the
  YAML content pool, the variant selectors, the bibliography and the photo.

Nothing is invented. Every slug is the variant's own directory name, every
title is that variant's ``label`` and every summary its ``description``. A
variant with no ``label`` fails the build rather than acquiring a title this
module made up.

No credential of any kind is involved here or anywhere else in cv's publish
path: authentication to the bucket is Workload Identity Federation, minted by
the hub's action at run time (website ADR-0007).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from tools.schema import load_variant

_DEFAULT_DIST = Path("dist")
_DEFAULT_VARIANTS_DIR = Path("data/variants")

# cv's assigned source name. It is the literal bucket prefix cv publishes under
# (sources/cv/) and it must equal the `source` input given to the hub's publish
# action, which rejects a mismatch before authenticating.
SOURCE = "cv"

# Every cv item belongs to the hub's `cv` section and is public. Private items
# are a hub Phase 3 capability; cv has nothing private to publish.
SECTION = "cv"
VISIBILITY = "public"

# The one `format: data` item. The hub renders exactly the (source, slug) pair
# ("cv", "cv-data") with first-party code and fails its build on any other data
# item, so neither the slug nor the path is a free choice.
CV_DATA_SLUG = "cv-data"
CV_DATA_PATH = "cv-data/"
CV_DATA_TITLE = "CV source data"
CV_DATA_SUMMARY = (
    "Content pool, variant selectors, bibliography and photo: the data the hub "
    "renders the CV pages from."
)

# Versions the *shape* of the cv-data payload, not its contents. The hub fails
# its build on a value it does not recognise, so bump it whenever the payload's
# structure changes — a renamed or removed YAML key, a moved file, a changed
# directory layout — and never for an edit to the CV's text. See
# llm/features/hub-publishing.md.
CV_DATA_SCHEMA_VERSION = "1"

# Mirrors of the hub schema's constraints, so a violation is reported here with
# cv's own file names rather than by the publish action after the fact.
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG_MAX = 64
_TITLE_MAX = 200
_SUMMARY_MAX = 500
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class ManifestError(ValueError):
    """The manifest could not be generated from the data as it stands."""


def utc_now_iso() -> str:
    """Current UTC instant in the timestamp form the hub schema requires."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def git_content_date(repo_root: Optional[Path] = None) -> Optional[str]:
    """Committer date of HEAD as ``YYYY-MM-DD``, or None if git cannot say.

    The published items all come from one commit, so the date the hub shows is
    the date that commit was made — not the date the build happened to run, so
    a re-run of an unchanged commit does not move the date.
    """
    cmd = ["git", "log", "-1", "--format=%cs"]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_root) if repo_root else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value if _DATE_RE.match(value) else None


def variant_names(variants_dir: Path = _DEFAULT_VARIANTS_DIR) -> list[str]:
    """Variant names discovered from ``data/variants/*.yaml``, sorted.

    Discovery, not a hand-maintained list: the workflow's `configure` job builds
    its matrix the same way, so the manifest and the PDF matrix cannot drift.
    """
    if not variants_dir.is_dir():
        raise ManifestError(f"variants directory not found: {variants_dir}")
    names = sorted(p.stem for p in variants_dir.glob("*.yaml"))
    if not names:
        raise ManifestError(f"no variant files found in {variants_dir}")
    return names


def _check_slug(slug: str, origin: str) -> None:
    if not _SLUG_RE.match(slug) or len(slug) > _SLUG_MAX:
        raise ManifestError(
            f"{origin}: {slug!r} is not a usable manifest slug. The hub requires "
            f"lowercase alphanumerics separated by single hyphens, at most "
            f"{_SLUG_MAX} characters."
        )


def _variant_item(variant_name: str, variants_dir: Path, date: str) -> dict:
    path = variants_dir / f"{variant_name}.yaml"
    variant = load_variant(path)

    _check_slug(variant_name, f"variant file {path}")

    label = (variant.label or "").strip()
    if not label:
        raise ManifestError(
            f"{path}: variant {variant_name!r} has no 'label'. The hub shows the "
            f"label as the item's title, and cv does not invent one."
        )
    if len(label) > _TITLE_MAX:
        raise ManifestError(
            f"{path}: 'label' is {len(label)} characters; the hub allows at most "
            f"{_TITLE_MAX}."
        )

    item = {
        "slug": variant_name,
        "title": label,
        "section": SECTION,
        "format": "pdf",
        "path": f"{variant_name}.pdf",
        "visibility": VISIBILITY,
        "date": date,
    }

    description = (variant.description or "").strip()
    if description:
        if len(description) > _SUMMARY_MAX:
            raise ManifestError(
                f"{path}: 'description' is {len(description)} characters; the hub "
                f"allows at most {_SUMMARY_MAX} in a summary."
            )
        item["summary"] = description
    return item


def _cv_data_item(date: str) -> dict:
    _check_slug(CV_DATA_SLUG, "cv-data item")
    return {
        "slug": CV_DATA_SLUG,
        "title": CV_DATA_TITLE,
        "section": SECTION,
        "format": "data",
        "path": CV_DATA_PATH,
        "visibility": VISIBILITY,
        "date": date,
        "summary": CV_DATA_SUMMARY,
        "schema_version": CV_DATA_SCHEMA_VERSION,
    }


def _check_staged(dist: Path, manifest: dict) -> None:
    """Every path the manifest promises must already exist under ``dist``.

    The hub's publish action resolves each path on disk and refuses the whole
    manifest if one is missing. Catching it here names the staging step that
    forgot the file instead.
    """
    missing = [
        item["path"] for item in manifest["items"] if not (dist / item["path"]).exists()
    ]
    if missing:
        raise ManifestError(
            "these manifest paths are not staged under "
            f"{dist}: {', '.join(sorted(missing))}. Stage dist/ before generating "
            "the manifest."
        )


def build_manifest(
    dist: Path = _DEFAULT_DIST,
    variants_dir: Path = _DEFAULT_VARIANTS_DIR,
    source: str = SOURCE,
    published: Optional[str] = None,
    date: Optional[str] = None,
    check_staged: bool = True,
) -> dict:
    """Build the manifest describing a staged ``dist/``."""
    published = published or utc_now_iso()
    date = date or git_content_date(repo_root=None) or published[:10]
    if not _DATE_RE.match(date):
        raise ManifestError(f"date must be YYYY-MM-DD, got {date!r}")

    items = [
        _variant_item(name, variants_dir, date) for name in variant_names(variants_dir)
    ]
    items.append(_cv_data_item(date))

    slugs = [item["slug"] for item in items]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    if duplicates:
        # Unreachable from filenames alone, but slug uniqueness is a contract
        # rule JSON Schema cannot express, so cv checks it rather than assuming.
        raise ManifestError(f"duplicate slug(s) in the manifest: {', '.join(duplicates)}")

    manifest = {"source": source, "published": published, "items": items}
    if check_staged:
        _check_staged(dist, manifest)
    return manifest


def write_manifest(manifest: dict, dist: Path = _DEFAULT_DIST) -> Path:
    """Write ``manifest.json`` to the root of ``dist``, where the hub looks."""
    dist.mkdir(parents=True, exist_ok=True)
    target = dist / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.manifest",
        description="Generate the research hub's manifest.json for a staged dist/.",
    )
    parser.add_argument(
        "--dist", type=Path, default=_DEFAULT_DIST, help="staged output folder (default: dist)"
    )
    parser.add_argument(
        "--variants-dir",
        type=Path,
        default=_DEFAULT_VARIANTS_DIR,
        help="directory of variant selector files (default: data/variants)",
    )
    parser.add_argument("--source", default=SOURCE, help=f"source name (default: {SOURCE})")
    parser.add_argument(
        "--published", default=None, help="ISO 8601 UTC publish timestamp (default: now)"
    )
    parser.add_argument(
        "--date",
        default=None,
        help="YYYY-MM-DD item date (default: the committer date of HEAD)",
    )
    parser.add_argument(
        "--skip-staged-check",
        action="store_true",
        help="do not require the described files to exist under dist/",
    )
    args = parser.parse_args(argv)

    try:
        manifest = build_manifest(
            dist=args.dist,
            variants_dir=args.variants_dir,
            source=args.source,
            published=args.published,
            date=args.date,
            check_staged=not args.skip_staged_check,
        )
    except (ManifestError, ValueError, FileNotFoundError) as e:
        print(f"manifest generation failed: {e}", file=sys.stderr)
        return 1

    target = write_manifest(manifest, args.dist)
    print(f"wrote {target} ({len(manifest['items'])} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
