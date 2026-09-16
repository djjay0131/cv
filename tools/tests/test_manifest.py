"""Tests for the research hub manifest generator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import manifest as m

_MINIMAL_VARIANT = """\
variant: {name}
label: "{label}"
description: "{description}"

sections:
  - type: summary
    content_id: academic
"""


def _write_variant(
    variants_dir: Path,
    name: str,
    label: str = "A Label",
    description: str = "A description.",
    body: str | None = None,
) -> Path:
    variants_dir.mkdir(parents=True, exist_ok=True)
    path = variants_dir / f"{name}.yaml"
    path.write_text(
        body
        if body is not None
        else _MINIMAL_VARIANT.format(name=name, label=label, description=description)
    )
    return path


def _stage(dist: Path, *names: str) -> Path:
    """Create the files a manifest for ``names`` will promise."""
    dist.mkdir(parents=True, exist_ok=True)
    for name in names:
        (dist / f"{name}.pdf").write_bytes(b"%PDF-1.7\n")
    (dist / "cv-data").mkdir(exist_ok=True)
    return dist


class TestUtcNowIso:
    def test_ends_with_z_and_has_no_microseconds(self) -> None:
        value = m.utc_now_iso()
        assert value.endswith("Z")
        assert "." not in value
        # The hub schema's `published` pattern.
        assert m.re.match(
            r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", value
        )


class TestGitContentDate:
    def test_returns_a_date_in_this_repository(self) -> None:
        value = m.git_content_date(Path(__file__).resolve().parents[2])
        assert value is None or m._DATE_RE.match(value)

    def test_returns_none_outside_a_repository(self, tmp_path: Path) -> None:
        assert m.git_content_date(tmp_path) is None

    def test_returns_none_when_git_is_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _boom(*_a, **_k):
            raise OSError("git not found")

        monkeypatch.setattr(m.subprocess, "run", _boom)
        assert m.git_content_date(None) is None


class TestVariantNames:
    def test_discovers_and_sorts(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "sde-long")
        _write_variant(variants, "academic")
        assert m.variant_names(variants) == ["academic", "sde-long"]

    def test_missing_directory_fails_loud(self, tmp_path: Path) -> None:
        with pytest.raises(m.ManifestError, match="variants directory not found"):
            m.variant_names(tmp_path / "nope")

    def test_empty_directory_fails_loud(self, tmp_path: Path) -> None:
        (tmp_path / "variants").mkdir()
        with pytest.raises(m.ManifestError, match="no variant files found"):
            m.variant_names(tmp_path / "variants")


class TestBuildManifest:
    def test_shape_matches_the_hub_contract(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic", label="Academic CV", description="Full CV.")
        dist = _stage(tmp_path / "dist", "academic")

        manifest = m.build_manifest(
            dist=dist, variants_dir=variants, published="2026-09-15T00:00:00Z", date="2026-09-14"
        )

        assert manifest["source"] == "cv"
        assert manifest["published"] == "2026-09-15T00:00:00Z"
        assert [i["slug"] for i in manifest["items"]] == ["academic", "cv-data"]

        pdf = manifest["items"][0]
        assert pdf == {
            "slug": "academic",
            "title": "Academic CV",
            "section": "cv",
            "format": "pdf",
            "path": "academic.pdf",
            "visibility": "public",
            "date": "2026-09-14",
            "summary": "Full CV.",
        }

    def test_cv_data_item_carries_schema_version_and_nothing_else_does(
        self, tmp_path: Path
    ) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        dist = _stage(tmp_path / "dist", "academic")

        manifest = m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

        data_items = [i for i in manifest["items"] if i["format"] == "data"]
        assert len(data_items) == 1
        assert data_items[0]["slug"] == "cv-data"
        assert data_items[0]["path"] == "cv-data/"
        assert data_items[0]["schema_version"] == "1"
        for other in manifest["items"]:
            if other["format"] != "data":
                assert "schema_version" not in other

    def test_every_item_is_public_and_in_the_cv_section(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        _write_variant(variants, "sde-long")
        dist = _stage(tmp_path / "dist", "academic", "sde-long")

        manifest = m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

        assert {i["visibility"] for i in manifest["items"]} == {"public"}
        assert {i["section"] for i in manifest["items"]} == {"cv"}

    def test_description_is_optional(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(
            variants,
            "academic",
            body='variant: academic\nlabel: "Academic CV"\n\nsections:\n  - type: summary\n',
        )
        dist = _stage(tmp_path / "dist", "academic")

        manifest = m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")
        assert "summary" not in manifest["items"][0]

    def test_missing_label_fails_loud(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(
            variants,
            "academic",
            body="variant: academic\n\nsections:\n  - type: summary\n",
        )
        dist = _stage(tmp_path / "dist", "academic")

        with pytest.raises(m.ManifestError, match="has no 'label'"):
            m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

    def test_overlong_label_fails_loud(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic", label="x" * 201)
        dist = _stage(tmp_path / "dist", "academic")

        with pytest.raises(m.ManifestError, match="the hub allows at most 200"):
            m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

    def test_overlong_description_fails_loud(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic", description="x" * 501)
        dist = _stage(tmp_path / "dist", "academic")

        with pytest.raises(m.ManifestError, match="at most 500"):
            m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

    def test_variant_name_that_is_not_a_slug_fails_loud(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(
            variants,
            "Academic_CV",
            body='variant: Academic_CV\nlabel: "X"\n\nsections:\n  - type: summary\n',
        )
        dist = tmp_path / "dist"
        _stage(dist, "Academic_CV")

        with pytest.raises(m.ManifestError, match="not a usable manifest slug"):
            m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

    def test_unstaged_file_fails_loud(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "cv-data").mkdir()

        with pytest.raises(m.ManifestError, match="academic.pdf"):
            m.build_manifest(dist=dist, variants_dir=variants, date="2026-09-14")

    def test_staged_check_can_be_skipped(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")

        manifest = m.build_manifest(
            dist=tmp_path / "dist",
            variants_dir=variants,
            date="2026-09-14",
            check_staged=False,
        )
        assert len(manifest["items"]) == 2

    def test_bad_date_fails_loud(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        with pytest.raises(m.ManifestError, match="date must be YYYY-MM-DD"):
            m.build_manifest(
                dist=tmp_path / "dist", variants_dir=variants, date="15-09-2026",
                check_staged=False,
            )

    def test_date_defaults_to_the_commit_date(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        monkeypatch.setattr(m, "git_content_date", lambda repo_root=None: "2026-01-02")

        manifest = m.build_manifest(
            dist=tmp_path / "dist", variants_dir=variants, check_staged=False
        )
        assert {i["date"] for i in manifest["items"]} == {"2026-01-02"}

    def test_date_falls_back_to_the_publish_date(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        monkeypatch.setattr(m, "git_content_date", lambda repo_root=None: None)

        manifest = m.build_manifest(
            dist=tmp_path / "dist",
            variants_dir=variants,
            published="2026-03-04T05:06:07Z",
            check_staged=False,
        )
        assert {i["date"] for i in manifest["items"]} == {"2026-03-04"}


class TestRealRepositoryData:
    """The manifest cv actually publishes, from cv's actual variant files."""

    def test_the_four_variants_and_cv_data(self, tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        manifest = m.build_manifest(
            variants_dir=repo_root / "data" / "variants",
            date="2026-09-14",
            check_staged=False,
        )
        assert [i["slug"] for i in manifest["items"]] == [
            "academic",
            "anthropic-fellow",
            "research-professional",
            "sde-long",
            "cv-data",
        ]
        assert manifest["items"][0]["title"] == "Academic CV"


class TestWriteManifest:
    def test_writes_to_the_root_of_dist(self, tmp_path: Path) -> None:
        dist = tmp_path / "dist"
        target = m.write_manifest({"source": "cv", "published": "x", "items": []}, dist)
        assert target == dist / "manifest.json"
        assert json.loads(target.read_text())["source"] == "cv"
        assert target.read_text().endswith("\n")


class TestMain:
    def test_writes_a_manifest_and_returns_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        dist = _stage(tmp_path / "dist", "academic")

        code = m.main(
            [
                "--dist",
                str(dist),
                "--variants-dir",
                str(variants),
                "--date",
                "2026-09-14",
            ]
        )
        assert code == 0
        assert "2 items" in capsys.readouterr().out
        assert json.loads((dist / "manifest.json").read_text())["source"] == "cv"

    def test_reports_failure_and_returns_one(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        code = m.main(["--dist", str(tmp_path), "--variants-dir", str(tmp_path / "nope")])
        assert code == 1
        assert "manifest generation failed" in capsys.readouterr().err

    def test_skip_staged_check_flag(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "academic")
        code = m.main(
            [
                "--dist",
                str(tmp_path / "dist"),
                "--variants-dir",
                str(variants),
                "--skip-staged-check",
            ]
        )
        assert code == 0
