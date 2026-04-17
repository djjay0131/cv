"""Variant selector resolution.

Takes a validated ContentPool and a Variant selector and produces the
rendered-data shape consumed by the Jinja templates — a flat dict keyed
by section type. Missing or misconfigured selector entries fail loud
with a path-qualified error.

Supports the extended DSL: bullet-level filtering, role collapse flags,
skills item subsetting, and context-aware include parsing (employment
sections parse objects as EmploymentSelector, skills as SkillSelector).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.schema import (
    ContentPool,
    EmploymentRole,
    EmploymentSelector,
    SkillGroup,
    SkillSelector,
    Variant,
    VariantSection,
)


class MissingContentIdError(KeyError):
    """A variant selector references an id that does not exist in the content pool."""


@dataclass
class ResolvedEmploymentEntry:
    role: EmploymentRole
    collapse: bool


def _require_content_id(section: VariantSection) -> str:
    if not section.content_id:
        raise ValueError(
            f"section type {section.type!r} requires a `content_id` selector"
        )
    return section.content_id


def _require_include(section: VariantSection) -> list:
    if not section.include:
        raise ValueError(
            f"section type {section.type!r} requires an `include` list of ids"
        )
    return section.include


def _lookup_one(pool_section: dict, cid: str, section_type: str) -> Any:
    if cid not in pool_section:
        raise MissingContentIdError(
            f"section {section_type!r}: unknown content id {cid!r}"
        )
    return pool_section[cid]


def _lookup(pool_section: dict, ids: list[str], section_type: str) -> list:
    return [_lookup_one(pool_section, cid, section_type) for cid in ids]


def _parse_employment_include(raw_include: list) -> list[EmploymentSelector]:
    selectors = []
    for item in raw_include:
        if isinstance(item, str):
            selectors.append(EmploymentSelector(id=item))
        elif isinstance(item, dict):
            selectors.append(EmploymentSelector(**item))
        else:
            raise ValueError(
                f"employment include entry must be a string or object, got {type(item)}"
            )
    return selectors


def _parse_skills_include(raw_include: list) -> list[SkillSelector]:
    selectors = []
    for item in raw_include:
        if isinstance(item, str):
            selectors.append(SkillSelector(id=item))
        elif isinstance(item, dict):
            selectors.append(SkillSelector(**item))
        else:
            raise ValueError(
                f"skills include entry must be a string or object, got {type(item)}"
            )
    return selectors


def _resolve_employment(
    pool: ContentPool, section: VariantSection
) -> list[ResolvedEmploymentEntry]:
    selectors = _parse_employment_include(_require_include(section))
    entries: list[ResolvedEmploymentEntry] = []
    for sel in selectors:
        role = _lookup_one(pool.employment, sel.id, "employment")
        if sel.bullets is not None:
            if len(sel.bullets) != len(set(sel.bullets)):
                dupes = [b for b in sel.bullets if sel.bullets.count(b) > 1]
                raise ValueError(
                    f"duplicate bullet IDs in selector for role '{sel.id}': {dupes[0]!r}"
                )
            bullet_map = {b.id: b for b in role.bullets}
            filtered = []
            for bid in sel.bullets:
                if bid not in bullet_map:
                    raise MissingContentIdError(
                        f"employment role '{sel.id}': unknown bullet '{bid}'"
                    )
                filtered.append(bullet_map[bid])
            role = role.model_copy(update={"bullets": filtered})
        entries.append(ResolvedEmploymentEntry(role=role, collapse=sel.collapse))
    return entries


def _resolve_skills(pool: ContentPool, section: VariantSection) -> list[SkillGroup]:
    selectors = _parse_skills_include(_require_include(section))
    groups: list[SkillGroup] = []
    for sel in selectors:
        group = _lookup_one(pool.skills, sel.id, "skills")
        if sel.items is not None:
            pool_items = set(group.items)
            for requested in sel.items:
                if requested not in pool_items:
                    raise ValueError(
                        f"skill group '{sel.id}': unknown item '{requested}'"
                    )
            group = group.model_copy(update={"items": sel.items})
        groups.append(group)
    return groups


def _resolve_education(
    pool: ContentPool, section: VariantSection
) -> list:
    return _lookup(pool.education, _require_include(section), "education")


def _resolve_projects(
    pool: ContentPool, section: VariantSection
) -> list:
    return _lookup(pool.projects, _require_include(section), "projects")


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
            result[t] = _resolve_employment(pool, section)
        elif t == "education":
            result[t] = _resolve_education(pool, section)
        elif t == "projects":
            result[t] = _resolve_projects(pool, section)
        elif t == "skills":
            result[t] = _resolve_skills(pool, section)
        elif t == "misc":
            result[t] = pool.misc
        elif t == "referee":
            result[t] = _lookup_one(pool.referees, _require_content_id(section), t)
        elif t == "publications":
            result[t] = True
        else:
            raise ValueError(f"unknown section type: {t!r}")

    return result
