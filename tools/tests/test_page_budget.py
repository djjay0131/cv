"""Tests for the per-variant PDF page-budget checker (owner D22, ADR-0024)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import page_budget as pb

pypdf = pytest.importorskip("pypdf")


def _write_pdf(path: Path, pages: int) -> Path:
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


def _write_variant(variants_dir: Path, name: str, length: str) -> Path:
    variants_dir.mkdir(parents=True, exist_ok=True)
    path = variants_dir / f"{name}.yaml"
    path.write_text(
        f'variant: {name}\nlabel: "{name}"\nlength: {length}\n'
        "sections:\n  - type: summary\n    content_id: academic\n",
        encoding="utf-8",
    )
    return path


class TestViolation:
    def test_one_page_exactly_one_passes(self) -> None:
        assert pb.violation("one-page", 1, "one-page") is None

    def test_one_page_too_short_fails(self) -> None:
        assert pb.violation("one-page", 0, "one-page") is not None

    def test_one_page_overflows_fails(self) -> None:
        message = pb.violation("one-page", 2, "one-page")
        assert message is not None and "exactly 1" in message

    def test_two_page_at_limit_passes(self) -> None:
        assert pb.violation("two-page", 2, "research-2p") is None

    def test_two_page_over_limit_fails(self) -> None:
        message = pb.violation("two-page", 3, "research-2p")
        assert message is not None and "at most 2" in message

    def test_full_has_no_limit(self) -> None:
        assert pb.violation("full", 99, "research-full") is None

    def test_unknown_length_fails_loud(self) -> None:
        with pytest.raises(pb.BudgetError, match="declares length"):
            pb.violation("three-page", 1, "x")


class TestCountPages:
    def test_counts_a_one_page_pdf(self, tmp_path: Path) -> None:
        assert pb.count_pages(_write_pdf(tmp_path / "a.pdf", 1)) == 1

    def test_counts_a_three_page_pdf(self, tmp_path: Path) -> None:
        assert pb.count_pages(_write_pdf(tmp_path / "b.pdf", 3)) == 3


class TestExpectedLengthForSlug:
    def test_one_page_slug(self) -> None:
        assert pb.expected_length_for_slug("one-page") == "one-page"

    def test_two_page_slugs(self) -> None:
        assert pb.expected_length_for_slug("research-2p") == "two-page"
        assert pb.expected_length_for_slug("professional-2p") == "two-page"

    def test_full_slugs_have_no_implied_budget(self) -> None:
        assert pb.expected_length_for_slug("research-full") is None
        assert pb.expected_length_for_slug("anthropic-fellow") is None


class TestCheck:
    def test_passes_when_every_variant_is_within_budget(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "one-page")
        _write_variant(variants, "research-2p", "two-page")
        _write_variant(variants, "research-full", "full")
        dist = tmp_path / "dist"
        _write_pdf(dist / "one-page.pdf", 1)
        _write_pdf(dist / "research-2p.pdf", 2)
        _write_pdf(dist / "research-full.pdf", 7)

        assert pb.check(dist=dist, variants_dir=variants) == []

    def test_flags_a_two_page_overflow(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "research-2p", "two-page")
        dist = tmp_path / "dist"
        _write_pdf(dist / "research-2p.pdf", 3)

        violations = pb.check(dist=dist, variants_dir=variants)
        assert len(violations) == 1
        assert "at most 2" in violations[0]

    def test_flags_a_one_page_that_is_two(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "one-page")
        dist = tmp_path / "dist"
        _write_pdf(dist / "one-page.pdf", 2)

        violations = pb.check(dist=dist, variants_dir=variants)
        assert len(violations) == 1
        assert "exactly 1" in violations[0]

    def test_missing_pdf_is_a_violation(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "one-page")
        violations = pb.check(dist=tmp_path / "dist", variants_dir=variants)
        assert len(violations) == 1
        assert "missing" in violations[0]

    def test_a_two_page_slug_cannot_relabel_itself_full(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "research-2p", "full")
        dist = tmp_path / "dist"
        _write_pdf(dist / "research-2p.pdf", 5)

        violations = pb.check(dist=dist, variants_dir=variants)
        assert len(violations) == 1
        assert "slug implies length 'two-page'" in violations[0]

    def test_one_page_slug_cannot_declare_two_page(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "two-page")
        dist = tmp_path / "dist"
        _write_pdf(dist / "one-page.pdf", 2)

        violations = pb.check(dist=dist, variants_dir=variants)
        assert len(violations) == 1
        assert "slug implies length 'one-page'" in violations[0]

    def test_injected_counter_is_used(self, tmp_path: Path) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "one-page")
        dist = tmp_path / "dist"
        # Not a real PDF: the injected counter proves the policy runs without
        # depending on pypdf/pdfinfo.
        (dist).mkdir(parents=True, exist_ok=True)
        (dist / "one-page.pdf").write_bytes(b"stub")

        assert pb.check(dist=dist, variants_dir=variants, count=lambda _p: 1) == []
        violations = pb.check(dist=dist, variants_dir=variants, count=lambda _p: 3)
        assert violations and "exactly 1" in violations[0]


class TestMain:
    def test_returns_zero_when_clean(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "one-page")
        dist = tmp_path / "dist"
        _write_pdf(dist / "one-page.pdf", 1)

        code = pb.main(["--dist", str(dist), "--variants-dir", str(variants)])
        assert code == 0
        assert "passed" in capsys.readouterr().out

    def test_returns_one_on_violation(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        variants = tmp_path / "variants"
        _write_variant(variants, "one-page", "one-page")
        dist = tmp_path / "dist"
        _write_pdf(dist / "one-page.pdf", 2)

        code = pb.main(["--dist", str(dist), "--variants-dir", str(variants)])
        assert code == 1
        assert "FAILED" in capsys.readouterr().err
