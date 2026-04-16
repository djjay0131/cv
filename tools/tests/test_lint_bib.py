"""Tests for the bibtex linter."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.lint_bib import BibLintError, lint_bib, main


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


_VALID_ARTICLE = """\
@article{good2025,
  author = {Jane Doe and John Smith},
  title = {A Good Title},
  journal = {Nature},
  year = {2025}
}
"""

_VALID_INPROCEEDINGS = """\
@inproceedings{conf2024,
  author = {Jane Doe},
  title = {Conference Paper},
  booktitle = {Proceedings of Something},
  year = {2024}
}
"""

_MISSING_YEAR = """\
@article{noyear,
  author = {Jane Doe},
  title = {No Year},
  journal = {Nature}
}
"""

_EMPTY_YEAR = """\
@article{emptyyear,
  author = {Jane Doe},
  title = {Empty Year},
  journal = {Nature},
  year = {}
}
"""

_NONNUMERIC_YEAR = """\
@article{badyear,
  author = {Jane Doe},
  title = {Bad Year},
  journal = {Nature},
  year = {soon}
}
"""

_MISSING_AUTHOR = """\
@article{noauthor2020,
  title = {No Author},
  journal = {Nature},
  year = {2020}
}
"""

_MISSING_TITLE = """\
@article{notitle2020,
  author = {Jane Doe},
  journal = {Nature},
  year = {2020}
}
"""


class TestLintBib:
    def test_valid_single_entry(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "ok.bib", _VALID_ARTICLE)
        # Should not raise.
        lint_bib(p)

    def test_valid_multiple_entries(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "ok.bib", _VALID_ARTICLE + "\n" + _VALID_INPROCEEDINGS)
        lint_bib(p)

    def test_missing_year_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "bad.bib", _MISSING_YEAR)
        with pytest.raises(BibLintError) as exc:
            lint_bib(p)
        assert "noyear" in str(exc.value)
        assert "year" in str(exc.value).lower()

    def test_empty_year_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "bad.bib", _EMPTY_YEAR)
        with pytest.raises(BibLintError) as exc:
            lint_bib(p)
        assert "emptyyear" in str(exc.value)

    def test_nonnumeric_year_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "bad.bib", _NONNUMERIC_YEAR)
        with pytest.raises(BibLintError) as exc:
            lint_bib(p)
        assert "badyear" in str(exc.value)
        assert "numeric" in str(exc.value).lower() or "invalid" in str(exc.value).lower()

    def test_missing_author_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "bad.bib", _MISSING_AUTHOR)
        with pytest.raises(BibLintError) as exc:
            lint_bib(p)
        assert "noauthor2020" in str(exc.value)
        assert "author" in str(exc.value).lower()

    def test_missing_title_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "bad.bib", _MISSING_TITLE)
        with pytest.raises(BibLintError) as exc:
            lint_bib(p)
        assert "notitle2020" in str(exc.value)

    def test_multiple_errors_all_reported(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "bad.bib", _MISSING_YEAR + "\n" + _MISSING_AUTHOR)
        with pytest.raises(BibLintError) as exc:
            lint_bib(p)
        msg = str(exc.value)
        assert "noyear" in msg
        assert "noauthor2020" in msg

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            lint_bib(tmp_path / "nope.bib")

    def test_empty_bib_is_valid(self, tmp_path: Path) -> None:
        # An empty .bib file has no entries to lint, so it passes.
        p = _write(tmp_path / "empty.bib", "")
        lint_bib(p)

    def test_year_with_braces_accepted(self, tmp_path: Path) -> None:
        # Some bib entries use nested braces; the linter should accept "{2025}".
        content = """\
@article{brown2025exploringevidencebasedsebeliefs,
  author = {Chris Brown and Jason Cusati},
  title = {Exploring the Evidence-Based SE Beliefs of Generative AI Tools},
  journal = {arXiv preprint arXiv:2407.13900},
  year = {2025}
}
"""
        p = _write(tmp_path / "real.bib", content)
        lint_bib(p)


class TestMain:
    def test_main_valid_returns_zero(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "ok.bib", _VALID_ARTICLE)
        assert main([str(p)]) == 0

    def test_main_invalid_returns_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        p = _write(tmp_path / "bad.bib", _MISSING_YEAR)
        rc = main([str(p)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "noyear" in err

    def test_main_without_args_returns_usage(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "usage" in err.lower()

    def test_main_falls_back_to_sys_argv(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sys as _sys

        monkeypatch.setattr(_sys, "argv", ["tools.lint_bib"])
        assert main() == 2
