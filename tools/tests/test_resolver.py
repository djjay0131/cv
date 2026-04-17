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
        assert [e.role.id for e in result["employment"]] == ["duck", "yoh"]
        assert all(not e.collapse for e in result["employment"])

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


class TestBulletFiltering:
    def test_filter_bullets_by_id(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh", "bullets": ["b1"]}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        entry = result["employment"][0]
        assert len(entry.role.bullets) == 1
        assert entry.role.bullets[0].id == "b1"
        assert not entry.collapse

    def test_bullet_order_follows_selector(self) -> None:
        """Bullets appear in the order listed in the selector, not pool order."""
        pool = _minimal_pool()
        # Add a second bullet to the yoh role.
        pool.employment["yoh"] = pool.employment["yoh"].model_copy(
            update={
                "bullets": [
                    Bullet(id="b1", text="first"),
                    Bullet(id="b2", text="second"),
                ]
            }
        )
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh", "bullets": ["b2", "b1"]}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        ids = [b.id for b in result["employment"][0].role.bullets]
        assert ids == ["b2", "b1"]

    def test_unknown_bullet_id_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh", "bullets": ["nonexistent"]}],
                )
            ],
        )
        with pytest.raises(MissingContentIdError) as exc:
            resolve_variant(pool, variant)
        assert "yoh" in str(exc.value)
        assert "nonexistent" in str(exc.value)

    def test_duplicate_bullet_ids_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh", "bullets": ["b1", "b1"]}],
                )
            ],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "duplicate" in str(exc.value).lower()
        assert "b1" in str(exc.value)

    def test_empty_bullets_list_gives_role_without_bullets(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh", "bullets": []}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert result["employment"][0].role.bullets == []

    def test_omitting_bullets_key_includes_all(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh"}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert len(result["employment"][0].role.bullets) == 1
        assert result["employment"][0].role.bullets[0].id == "b1"


class TestCollapseFlag:
    def test_collapse_flag_passed_through(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[{"id": "yoh", "collapse": True}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert result["employment"][0].collapse is True

    def test_mixed_collapse_and_normal(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[
                        "yoh",
                        {"id": "duck", "collapse": True},
                    ],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert not result["employment"][0].collapse
        assert result["employment"][1].collapse


class TestSkillsSubsetting:
    def test_subset_skill_items(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="skills",
                    include=[{"id": "langs", "items": ["Python"]}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert result["skills"][0].items == ["Python"]

    def test_unknown_skill_item_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="skills",
                    include=[{"id": "langs", "items": ["Nonexistent"]}],
                )
            ],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "langs" in str(exc.value)
        assert "Nonexistent" in str(exc.value)

    def test_omitting_items_includes_all(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="skills",
                    include=[{"id": "langs"}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert result["skills"][0].items == ["Python"]

    def test_mixed_string_and_object_skills(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="skills",
                    include=["langs", {"id": "langs", "items": ["Python"]}],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert len(result["skills"]) == 2
        assert result["skills"][0].items == ["Python"]  # full
        assert result["skills"][1].items == ["Python"]  # subset (same here, pool only has 1)


class TestInvalidIncludeTypes:
    def test_employment_include_with_invalid_type_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[VariantSection(type="employment", include=[42])],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "string or object" in str(exc.value)

    def test_skills_include_with_invalid_type_raises(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[VariantSection(type="skills", include=[True])],
        )
        with pytest.raises(ValueError) as exc:
            resolve_variant(pool, variant)
        assert "string or object" in str(exc.value)


class TestMixedIncludeEntries:
    def test_mixed_string_and_object_employment(self) -> None:
        pool = _minimal_pool()
        variant = Variant(
            variant="test",
            sections=[
                VariantSection(
                    type="employment",
                    include=[
                        "yoh",
                        {"id": "duck", "bullets": []},
                    ],
                )
            ],
        )
        result = resolve_variant(pool, variant)
        assert len(result["employment"]) == 2
        assert len(result["employment"][0].role.bullets) == 1  # yoh: all
        assert len(result["employment"][1].role.bullets) == 0  # duck: empty
