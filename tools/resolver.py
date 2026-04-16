"""Variant selector resolution.

Takes a validated ContentPool and a Variant selector and produces the
rendered-data shape consumed by the Jinja templates — a flat dict keyed
by section type. Missing or misconfigured selector entries fail loud
with a path-qualified error.
"""

from __future__ import annotations

from typing import Any

from tools.schema import ContentPool, Variant, VariantSection


class MissingContentIdError(KeyError):
    """A variant selector references an id that does not exist in the content pool."""


_ID_REQUIRED = ("summary", "employment", "education", "projects", "skills", "referee")


def _require_content_id(section: VariantSection) -> str:
    if not section.content_id:
        raise ValueError(
            f"section type {section.type!r} requires a `content_id` selector"
        )
    return section.content_id


def _require_include(section: VariantSection) -> list[str]:
    if not section.include:
        raise ValueError(
            f"section type {section.type!r} requires an `include` list of ids"
        )
    return section.include


def _lookup(pool_section: dict, ids: list[str], section_type: str) -> list:
    out = []
    for cid in ids:
        if cid not in pool_section:
            raise MissingContentIdError(
                f"section {section_type!r}: unknown content id {cid!r}"
            )
        out.append(pool_section[cid])
    return out


def _lookup_one(pool_section: dict, cid: str, section_type: str) -> Any:
    if cid not in pool_section:
        raise MissingContentIdError(
            f"section {section_type!r}: unknown content id {cid!r}"
        )
    return pool_section[cid]


def resolve_variant(pool: ContentPool, variant: Variant) -> dict:
    """Map a variant selector against the content pool.

    Returns a dict that templates consume:
      - meta: the content pool's Meta
      - section_order: list of section types in the order declared by the variant
      - <section_type>: the resolved content for that section
    """
    result: dict[str, Any] = {
        "meta": pool.meta,
        "section_order": [s.type for s in variant.sections],
    }

    for section in variant.sections:
        t = section.type
        if t == "summary":
            result[t] = _lookup_one(pool.summaries, _require_content_id(section), t)
        elif t == "employment":
            result[t] = _lookup(pool.employment, _require_include(section), t)
        elif t == "education":
            result[t] = _lookup(pool.education, _require_include(section), t)
        elif t == "projects":
            result[t] = _lookup(pool.projects, _require_include(section), t)
        elif t == "skills":
            result[t] = _lookup(pool.skills, _require_include(section), t)
        elif t == "misc":
            result[t] = pool.misc
        elif t == "referee":
            result[t] = _lookup_one(pool.referees, _require_content_id(section), t)
        elif t == "publications":
            result[t] = True
        else:
            raise ValueError(f"unknown section type: {t!r}")

    return result
