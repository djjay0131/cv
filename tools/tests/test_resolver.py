"""Tests for variant selector → rendered data shape resolution."""

from __future__ import annotations

import pytest

from tools.resolver import MissingContentIdError, resolve_variant
from tools.schema import (
    Award,
    Bullet,
    Certification,
    Contact,
    ContentPool,
    EducationEntry,
    EmploymentRole,
    Meta,
    Misc,
    Project,
    Referee,
    SkillGroup,
    Summary,
    Variant,
    VariantSection,
)


def _minimal_pool() -> ContentPool:
    return ContentPool(
        meta=Meta(name="J", contact=Contact(email="a@b.c"), photo="p.jpg"),
        summaries={"s-a": Summary(id="s-a", text="Academic summary.")},
        employment={
            "yoh": EmploymentRole(
                id="yoh",
                dates="2024",
                company="Yoh",
                location="SC",
                title="Arch",
                bullets=[Bullet(id="b1", text="did x")],
            ),
            "duck": EmploymentRole(
                id="duck",
                dates="2021",
                company="Duck Creek",
                location="SC",
                title="Senior",
                bullets=[],
            ),
        },
        education={
            "phd": EducationEntry(
                id="phd",
                dates="2027",
                degree="Ph.D.",
                institution="VT",
                location="VA",
            )
        },
        projects={"p1": Project(id="p1", name="LLM Asst", summary="Py+Streamlit")},
        skills={"langs": SkillGroup(id="langs", group="Languages", items=["Python"])},
        misc=Misc(
            awards=[Award(id="a1", text="Award 1")],
            certifications=[Certification(id="c1", text="CSSLP")],
        ),
        referees={"avail": Referee(id="avail", text="Available on Request")},
    )


class TestResolveVariant:
    def test_summary_section_resolves_by_content_id(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="summary", content_id="s-a")],
        )
        result = resolve_variant(pool, variant)
        assert result["summary"].text == "Academic summary."
        assert result["meta"].name == "J"

    def test_employment_section_preserves_order(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="employment", include=["duck", "yoh"])],
        )
        result = resolve_variant(pool, variant)
        assert [r.id for r in result["employment"]] == ["duck", "yoh"]

    def test_education_section(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="education", include=["phd"])],
        )
        result = resolve_variant(pool, variant)
        assert [e.id for e in result["education"]] == ["phd"]

    def test_projects_section(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="projects", include=["p1"])],
        )
        result = resolve_variant(pool, variant)
        assert [p.id for p in result["projects"]] == ["p1"]

    def test_skills_section(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="skills", include=["langs"])],
        )
        result = resolve_variant(pool, variant)
        assert result["skills"][0].group == "Languages"

    def test_misc_section_is_flat(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="misc")],
        )
        result = resolve_variant(pool, variant)
        assert result["misc"].awards[0].text == "Award 1"
        assert result["misc"].certifications[0].text == "CSSLP"

    def test_referee_section_resolves_by_content_id(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="referee", content_id="avail")],
        )
        result = resolve_variant(pool, variant)
        assert result["referee"].text == "Available on Request"

    def test_publications_section_is_placeholder(self) -> None:
        # Publications are rendered directly from .bib on the LaTeX side;
        # resolve_variant passes through a simple flag so templates know.
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="publications")],
        )
        result = resolve_variant(pool, variant)
        assert result["publications"] is True

    def test_multiple_sections_all_present(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[
                VariantSection(type="summary", content_id="s-a"),
                VariantSection(type="employment", include=["yoh"]),
                VariantSection(type="education", include=["phd"]),
            ],
        )
        result = resolve_variant(pool, variant)
        assert "summary" in result
        assert "employment" in result
        assert "education" in result

    def test_section_order_preserved(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[
                VariantSection(type="education", include=["phd"]),
                VariantSection(type="summary", content_id="s-a"),
            ],
        )
        result = resolve_variant(pool, variant)
        # Order appears in result["section_order"] for templates that care.
        assert result["section_order"] == ["education", "summary"]


class TestMissingIds:
    def test_unknown_summary_id_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="summary", content_id="nope")],
        )
        with pytest.raises(MissingContentIdError) as exc:
            resolve_variant(pool, variant)
        assert "nope" in str(exc.value)
        assert "summary" in str(exc.value).lower()

    def test_unknown_employment_id_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="employment", include=["yoh", "ghost"])],
        )
        with pytest.raises(MissingContentIdError) as exc:
            resolve_variant(pool, variant)
        assert "ghost" in str(exc.value)

    def test_unknown_education_id_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="education", include=["phantom"])],
        )
        with pytest.raises(MissingContentIdError) as exc:
            resolve_variant(pool, variant)
        assert "phantom" in str(exc.value)

    def test_unknown_referee_id_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="referee", content_id="unknown-ref")],
        )
        with pytest.raises(MissingContentIdError) as exc:
            resolve_variant(pool, variant)
        assert "unknown-ref" in str(exc.value)


class TestSectionRequirements:
    def test_summary_without_content_id_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="summary")],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "summary" in str(exc.value).lower()
        assert "content_id" in str(exc.value).lower()

    def test_employment_without_include_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="employment")],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "employment" in str(exc.value).lower()
        assert "include" in str(exc.value).lower()

    def test_unknown_section_type_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="academic",
            sections=[VariantSection(type="unknown-section")],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "unknown-section" in str(exc.value)
