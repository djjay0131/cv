"""Pydantic schemas for the CV content pool and variant selectors.

Every content item has a stable `id`. The content pool is indexed by id per section
so variant selectors can reference items by id. Schema errors fail loud with the
file and field context so broken data never reaches the Jinja layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class NameVariant(_StrictModel):
    family: str = Field(min_length=1)
    given: str = Field(min_length=1)


class Contact(_StrictModel):
    email: str = Field(min_length=1)
    linkedin: Optional[str] = None
    github: Optional[str] = None
    x: Optional[str] = None


class Meta(_StrictModel):
    name: str = Field(min_length=1)
    contact: Contact
    photo: str = Field(min_length=1)
    include_photo: bool = True
    name_variants: list[NameVariant] = Field(default_factory=list)


class _IdItem(_StrictModel):
    id: str = Field(min_length=1)


class Summary(_IdItem):
    text: str = Field(min_length=1)


class Bullet(_IdItem):
    text: str = Field(min_length=1)


class EmploymentRole(_IdItem):
    dates: Optional[str] = None
    company: str = Field(min_length=1)
    location: str = Field(min_length=1)
    title: str = Field(min_length=1)
    bullets: list[Bullet] = Field(default_factory=list)

    @field_validator("bullets")
    @classmethod
    def _no_duplicate_bullet_ids(cls, v: list[Bullet]) -> list[Bullet]:
        seen: set[str] = set()
        for b in v:
            if b.id in seen:
                raise ValueError(f"duplicate bullet id: {b.id}")
            seen.add(b.id)
        return v


class EducationEntry(_IdItem):
    dates: Optional[str] = None
    degree: str = Field(min_length=1)
    institution: str = Field(min_length=1)
    location: str = Field(min_length=1)


class Project(_IdItem):
    name: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    github: Optional[str] = None


class SkillGroup(_IdItem):
    group: str = Field(min_length=1)
    items: list[str] = Field(min_length=1)


class Award(_IdItem):
    dates: Optional[str] = None
    text: str = Field(min_length=1)


class Certification(_IdItem):
    text: str = Field(min_length=1)


class Misc(_StrictModel):
    awards: list[Award] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)


class Referee(_IdItem):
    text: str = Field(min_length=1)


class ContentPool(_StrictModel):
    meta: Meta
    summaries: dict[str, Summary]
    employment: dict[str, EmploymentRole]
    education: dict[str, EducationEntry]
    projects: dict[str, Project]
    skills: dict[str, SkillGroup]
    misc: Misc
    referees: dict[str, Referee]


class EmploymentSelector(_StrictModel):
    id: str = Field(min_length=1)
    bullets: Optional[list[str]] = None
    collapse: bool = False


class SkillSelector(_StrictModel):
    id: str = Field(min_length=1)
    items: Optional[list[str]] = None


class VariantSection(_StrictModel):
    type: str = Field(min_length=1)
    include: Optional[list] = None
    content_id: Optional[str] = None


class RawOverride(BaseModel):
    # Raw overrides preserve whitespace verbatim — they're dropped into LaTeX/HTML
    # as-is, so stripping trailing newlines would corrupt the emitted fragment.
    model_config = ConfigDict(extra="forbid")
    tex: Optional[str] = None
    html: Optional[str] = None


class Variant(_StrictModel):
    variant: str = Field(min_length=1)
    extends: Optional[str] = None
    sections: list[VariantSection] = Field(min_length=1)
    raw_overrides: dict[str, RawOverride] = Field(default_factory=dict)


_CONTENT_FILES = (
    "meta.yaml",
    "summaries.yaml",
    "employment.yaml",
    "education.yaml",
    "projects.yaml",
    "skills.yaml",
    "misc.yaml",
    "referees.yaml",
)


def _read_yaml(path: Path) -> object:
    if not path.exists():
        raise FileNotFoundError(f"required content file missing: {path}")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error in {path}: {e}") from e


def _index_by_id(items: list[dict], source: Path, cls: type) -> dict:
    result: dict[str, object] = {}
    for raw in items or []:
        try:
            model = cls(**raw)
        except Exception as e:
            raise ValueError(f"validation error in {source} item {raw!r}: {e}") from e
        if model.id in result:
            raise ValueError(f"duplicate id {model.id!r} in {source}")
        result[model.id] = model
    return result


def load_content(content_dir: Path) -> ContentPool:
    """Load and validate the content pool from a directory of YAML files."""
    meta_path = content_dir / "meta.yaml"
    meta_raw = _read_yaml(meta_path)
    try:
        meta = Meta(**meta_raw)  # type: ignore[arg-type]
    except Exception as e:
        raise ValueError(f"validation error in {meta_path}: {e}") from e

    summaries_raw = _read_yaml(content_dir / "summaries.yaml") or []
    employment_raw = _read_yaml(content_dir / "employment.yaml") or []
    education_raw = _read_yaml(content_dir / "education.yaml") or []
    projects_raw = _read_yaml(content_dir / "projects.yaml") or []
    skills_raw = _read_yaml(content_dir / "skills.yaml") or []
    misc_raw = _read_yaml(content_dir / "misc.yaml") or {"awards": [], "certifications": []}
    referees_raw = _read_yaml(content_dir / "referees.yaml") or []

    try:
        misc = Misc(**misc_raw)  # type: ignore[arg-type]
    except Exception as e:
        raise ValueError(f"validation error in {content_dir / 'misc.yaml'}: {e}") from e

    return ContentPool(
        meta=meta,
        summaries=_index_by_id(summaries_raw, content_dir / "summaries.yaml", Summary),
        employment=_index_by_id(
            employment_raw, content_dir / "employment.yaml", EmploymentRole
        ),
        education=_index_by_id(education_raw, content_dir / "education.yaml", EducationEntry),
        projects=_index_by_id(projects_raw, content_dir / "projects.yaml", Project),
        skills=_index_by_id(skills_raw, content_dir / "skills.yaml", SkillGroup),
        misc=misc,
        referees=_index_by_id(referees_raw, content_dir / "referees.yaml", Referee),
    )


def load_variant(path: Path) -> Variant:
    """Load and validate a variant selector file."""
    raw = _read_yaml(path)
    try:
        return Variant(**raw)  # type: ignore[arg-type]
    except Exception as e:
        raise ValueError(f"validation error in {path}: {e}") from e
