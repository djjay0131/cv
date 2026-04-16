"""Tests for Pydantic schemas and content/variant loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tools.schema import (
    Bullet,
    Contact,
    ContentPool,
    EducationEntry,
    EmploymentRole,
    Meta,
    NameVariant,
    Project,
    SkillGroup,
    Variant,
    VariantSection,
    load_content,
    load_variant,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


class TestMeta:
    def test_minimal_valid_meta(self) -> None:
        m = Meta(
            name="Jason Cusati",
            contact=Contact(email="djjay@vt.edu"),
            photo="photo.jpg",
        )
        assert m.name == "Jason Cusati"
        assert m.contact.email == "djjay@vt.edu"
        assert m.include_photo is True
        assert m.name_variants == []

    def test_meta_with_name_variants(self) -> None:
        m = Meta(
            name="Jason Cusati",
            contact=Contact(email="x@y.z"),
            photo="p.jpg",
            name_variants=[NameVariant(family="Cusati", given="Jason")],
        )
        assert m.name_variants[0].family == "Cusati"

    def test_meta_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Meta(contact=Contact(email="a@b.c"), photo="p.jpg")
        assert "name" in str(exc.value)

    def test_contact_requires_email(self) -> None:
        with pytest.raises(ValidationError):
            Contact()


class TestBullet:
    def test_valid(self) -> None:
        b = Bullet(id="yoh-mvp", text="Delivered **MVP** in 3 months.")
        assert b.id == "yoh-mvp"

    def test_missing_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            Bullet(text="anything")

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            Bullet(id="", text="anything")


class TestEmploymentRole:
    def test_valid(self) -> None:
        r = EmploymentRole(
            id="yoh",
            dates="2024-2025",
            company="Yoh",
            location="Remote",
            title="Architect",
            bullets=[Bullet(id="b1", text="x")],
        )
        assert r.id == "yoh"
        assert len(r.bullets) == 1

    def test_empty_bullets_allowed(self) -> None:
        r = EmploymentRole(
            id="a",
            dates="2020",
            company="c",
            location="l",
            title="t",
            bullets=[],
        )
        assert r.bullets == []

    def test_duplicate_bullet_ids_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            EmploymentRole(
                id="a",
                dates="2020",
                company="c",
                location="l",
                title="t",
                bullets=[Bullet(id="dup", text="x"), Bullet(id="dup", text="y")],
            )
        assert "duplicate" in str(exc.value).lower()


class TestEducationEntry:
    def test_valid_with_dates(self) -> None:
        e = EducationEntry(
            id="phd",
            dates="2027 (exp.)",
            degree="Ph.D.",
            institution="Virginia Tech",
            location="Blacksburg, VA",
        )
        assert e.dates == "2027 (exp.)"

    def test_optional_dates(self) -> None:
        e = EducationEntry(
            id="bs",
            degree="B.S.",
            institution="Virginia Tech",
            location="Blacksburg, VA",
        )
        assert e.dates is None


class TestProject:
    def test_valid_no_github(self) -> None:
        p = Project(id="x", name="X", summary="s")
        assert p.github is None

    def test_with_github(self) -> None:
        p = Project(id="x", name="X", summary="s", github="https://github.com/x/y")
        assert p.github == "https://github.com/x/y"


class TestSkillGroup:
    def test_valid(self) -> None:
        s = SkillGroup(id="langs", group="Languages", items=["Python", "Go"])
        assert len(s.items) == 2

    def test_empty_items_raises(self) -> None:
        with pytest.raises(ValidationError):
            SkillGroup(id="langs", group="Languages", items=[])


class TestVariantSection:
    def test_section_with_include(self) -> None:
        s = VariantSection(type="employment", include=["yoh", "duck-creek"])
        assert s.include == ["yoh", "duck-creek"]

    def test_section_with_content_id(self) -> None:
        s = VariantSection(type="summary", content_id="summary-academic")
        assert s.content_id == "summary-academic"

    def test_section_type_required(self) -> None:
        with pytest.raises(ValidationError):
            VariantSection(include=["x"])

    def test_publications_section_needs_neither(self) -> None:
        s = VariantSection(type="publications")
        assert s.include is None and s.content_id is None


class TestVariant:
    def test_valid(self) -> None:
        v = Variant(
            variant="academic",
            sections=[VariantSection(type="summary", content_id="s-a")],
        )
        assert v.variant == "academic"

    def test_missing_sections_raises(self) -> None:
        with pytest.raises(ValidationError):
            Variant(variant="academic")

    def test_empty_sections_raises(self) -> None:
        with pytest.raises(ValidationError):
            Variant(variant="academic", sections=[])


class TestLoadContent:
    def test_item_validation_error_includes_path_and_item(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "meta.yaml",
            'name: "J"\ncontact:\n  email: "a@b.c"\nphoto: "p.jpg"\n',
        )
        # summaries.yaml: valid yaml, but item missing required `text` field
        _write(tmp_path / "summaries.yaml", "- id: s-a\n")
        _write(tmp_path / "employment.yaml", "[]\n")
        _write(tmp_path / "education.yaml", "[]\n")
        _write(tmp_path / "projects.yaml", "[]\n")
        _write(tmp_path / "skills.yaml", "[]\n")
        _write(tmp_path / "misc.yaml", "awards: []\ncertifications: []\n")
        _write(tmp_path / "referees.yaml", "[]\n")

        with pytest.raises(ValueError) as exc:
            load_content(tmp_path)
        assert "summaries.yaml" in str(exc.value)
        assert "s-a" in str(exc.value)

    def test_meta_validation_error_includes_path(self, tmp_path: Path) -> None:
        # meta.yaml parses but has wrong types
        _write(tmp_path / "meta.yaml", "name: 123\n")
        for name in ("summaries", "employment", "education", "projects", "skills", "referees"):
            _write(tmp_path / f"{name}.yaml", "[]\n")
        _write(tmp_path / "misc.yaml", "awards: []\ncertifications: []\n")

        with pytest.raises(ValueError) as exc:
            load_content(tmp_path)
        assert "meta.yaml" in str(exc.value)

    def test_misc_validation_error_includes_path(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "meta.yaml",
            'name: "J"\ncontact:\n  email: "a@b.c"\nphoto: "p.jpg"\n',
        )
        for name in ("summaries", "employment", "education", "projects", "skills", "referees"):
            _write(tmp_path / f"{name}.yaml", "[]\n")
        # misc.yaml: wrong structure
        _write(tmp_path / "misc.yaml", "awards: not-a-list\ncertifications: []\n")

        with pytest.raises(ValueError) as exc:
            load_content(tmp_path)
        assert "misc.yaml" in str(exc.value)

    def test_loads_all_sections(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "meta.yaml",
            'name: "Jason"\ncontact:\n  email: "j@v.edu"\nphoto: "p.jpg"\n',
        )
        _write(
            tmp_path / "summaries.yaml",
            '- id: s-a\n  text: "Professional."\n',
        )
        _write(
            tmp_path / "employment.yaml",
            '- id: yoh\n  dates: "2024"\n  company: "Yoh"\n  location: "SC"\n'
            '  title: "Arch"\n  bullets:\n    - id: b1\n      text: "did x"\n',
        )
        _write(
            tmp_path / "education.yaml",
            '- id: phd\n  degree: "Ph.D."\n  institution: "VT"\n  location: "VA"\n',
        )
        _write(tmp_path / "projects.yaml", '- id: p1\n  name: "P"\n  summary: "s"\n')
        _write(
            tmp_path / "skills.yaml",
            '- id: langs\n  group: "Languages"\n  items: ["Python"]\n',
        )
        _write(
            tmp_path / "misc.yaml",
            'awards:\n  - id: a1\n    text: "Award"\n'
            'certifications:\n  - id: c1\n    text: "CSSLP"\n',
        )
        _write(tmp_path / "referees.yaml", '- id: available\n  text: "Available on Request"\n')

        pool = load_content(tmp_path)
        assert isinstance(pool, ContentPool)
        assert pool.meta.name == "Jason"
        assert pool.summaries["s-a"].text == "Professional."
        assert pool.employment["yoh"].company == "Yoh"
        assert pool.education["phd"].degree == "Ph.D."
        assert pool.projects["p1"].name == "P"
        assert pool.skills["langs"].group == "Languages"
        assert pool.misc.awards[0].text == "Award"
        assert pool.referees["available"].text == "Available on Request"

    def test_missing_meta_raises(self, tmp_path: Path) -> None:
        # No meta.yaml at all.
        with pytest.raises(FileNotFoundError) as exc:
            load_content(tmp_path)
        assert "meta" in str(exc.value).lower()

    def test_invalid_yaml_raises_with_path(self, tmp_path: Path) -> None:
        _write(tmp_path / "meta.yaml", "not: [valid: yaml")
        with pytest.raises(Exception) as exc:
            load_content(tmp_path)
        assert "meta.yaml" in str(exc.value)

    def test_duplicate_id_within_section_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path / "meta.yaml",
            'name: "J"\ncontact:\n  email: "a@b.c"\nphoto: "p.jpg"\n',
        )
        _write(tmp_path / "summaries.yaml", '- id: dup\n  text: "a"\n- id: dup\n  text: "b"\n')
        _write(tmp_path / "employment.yaml", "[]\n")
        _write(tmp_path / "education.yaml", "[]\n")
        _write(tmp_path / "projects.yaml", "[]\n")
        _write(tmp_path / "skills.yaml", "[]\n")
        _write(tmp_path / "misc.yaml", "awards: []\ncertifications: []\n")
        _write(tmp_path / "referees.yaml", "[]\n")

        with pytest.raises(ValueError) as exc:
            load_content(tmp_path)
        assert "duplicate" in str(exc.value).lower()
        assert "dup" in str(exc.value)


class TestLoadVariant:
    def test_loads_valid_variant(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path / "academic.yaml",
            "variant: academic\nsections:\n"
            "  - type: summary\n    content_id: s-a\n"
            "  - type: employment\n    include: [yoh]\n",
        )
        v = load_variant(path)
        assert v.variant == "academic"
        assert v.sections[0].type == "summary"

    def test_invalid_variant_raises(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", "variant: x\n")  # no sections
        with pytest.raises(Exception) as exc:
            load_variant(path)
        assert "bad.yaml" in str(exc.value) or "sections" in str(exc.value).lower()

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_variant(tmp_path / "nope.yaml")
