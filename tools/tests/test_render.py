"""Tests for the rendering orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools.render import render


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _setup_content(base: Path) -> Path:
    """Create a minimal valid content pool at base/content/."""
    cd = base / "content"
    _write(
        cd / "meta.yaml",
        'name: "Jason Cusati"\n'
        'contact:\n  email: "djjay@vt.edu"\n  github: "djjay0131"\n'
        'photo: "photo.jpg"\n'
        'name_variants:\n  - family: "Cusati"\n    given: "Jason"\n',
    )
    _write(cd / "summaries.yaml", '- id: s-a\n  text: "Pro summary."\n')
    _write(
        cd / "employment.yaml",
        "- id: yoh\n"
        '  dates: "2024-2025"\n'
        '  company: "Yoh"\n'
        '  location: "SC"\n'
        '  title: "Architect"\n'
        "  bullets:\n"
        '    - id: b1\n      text: "Delivered **MVP** fast."\n',
    )
    _write(
        cd / "education.yaml",
        '- id: phd\n  dates: "2027"\n  degree: "Ph.D."\n'
        '  institution: "Virginia Tech"\n  location: "VA"\n',
    )
    _write(cd / "projects.yaml", '- id: p1\n  name: "LLM Asst"\n  summary: "Py+FastAPI"\n')
    _write(
        cd / "skills.yaml",
        '- id: langs\n  group: "Languages"\n  items: ["Python"]\n',
    )
    _write(
        cd / "misc.yaml",
        'awards:\n  - id: a1\n    dates: "2008"\n    text: "**Award** at X."\n'
        'certifications:\n  - id: c1\n    text: "CSSLP"\n',
    )
    _write(cd / "referees.yaml", '- id: avail\n  text: "Available on Request"\n')
    return cd


def _setup_variant(base: Path, overrides: str = "") -> Path:
    vd = base / "variants"
    _write(
        vd / "academic.yaml",
        "variant: academic\n"
        "sections:\n"
        "  - type: summary\n    content_id: s-a\n"
        "  - type: employment\n    include: [yoh]\n"
        "  - type: education\n    include: [phd]\n"
        "  - type: projects\n    include: [p1]\n"
        "  - type: publications\n"
        "  - type: skills\n    include: [langs]\n"
        "  - type: misc\n"
        "  - type: referee\n    content_id: avail\n"
        + overrides,
    )
    return vd


def _setup_templates(base: Path) -> Path:
    td = base / "templates" / "tex"
    # Minimal templates that exercise rendered data shape + md_to_latex.
    _write(td / "summary.tex.j2", "SUMMARY: {{ summary.text | md_to_latex }}\n")
    _write(
        td / "employment.tex.j2",
        "EMP:{% for entry in employment %} {{ entry.role.company }}"
        "{% for b in entry.role.bullets %} [{{ b.text | md_to_latex }}]{% endfor %}{% endfor %}\n",
    )
    _write(
        td / "education.tex.j2",
        "EDU:{% for e in education %} {{ e.degree }}@{{ e.institution }}{% endfor %}\n",
    )
    _write(
        td / "projects.tex.j2",
        "PROJ:{% for p in projects %} {{ p.name }}{% endfor %}\n",
    )
    _write(
        td / "skills.tex.j2",
        "SKILLS:{% for g in skills %} {{ g.group }}{% endfor %}\n",
    )
    _write(
        td / "misc.tex.j2",
        "MISC:"
        "{% for a in misc.awards %} A:{{ a.text | md_to_latex }}{% endfor %}"
        "{% for c in misc.certifications %} C:{{ c.text }}{% endfor %}\n",
    )
    _write(td / "referee.tex.j2", "REFEREE: {{ referee.text }}\n")
    return td


def test_renders_all_sections(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )

    for name in ("summary", "employment", "education", "projects", "skills", "misc", "referee"):
        assert (output_dir / f"{name}.tex").exists(), f"missing {name}.tex"


def test_md_to_latex_filter_applied(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )

    # bullet "Delivered **MVP** fast." → "Delivered \textbf{MVP} fast."
    emp = (output_dir / "employment.tex").read_text()
    assert r"\textbf{MVP}" in emp
    assert "**" not in emp


def test_preamble_file_written_with_name_variants(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )

    preamble = (output_dir / "_preamble.tex").read_text()
    assert r"\mynames{Cusati/Jason}" in preamble


def test_raw_override_bypasses_template(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(
        tmp_path,
        overrides='raw_overrides:\n  skills:\n    tex: "% hand-written skills\\n"\n',
    )
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )

    skills = (output_dir / "skills.tex").read_text()
    assert skills == "% hand-written skills\n"
    # Other sections still rendered normally.
    assert "Pro summary" in (output_dir / "summary.tex").read_text()


def test_missing_template_raises(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    # Templates dir is missing the required files.
    templates_dir = tmp_path / "templates" / "tex"
    templates_dir.mkdir(parents=True)
    output_dir = tmp_path / "out"

    with pytest.raises(Exception) as exc:
        render(
            "academic",
            content_dir=content_dir,
            variants_dir=variants_dir,
            templates_dir=templates_dir,
            output_dir=output_dir,
        )
    # Message should reference the missing section or template.
    assert "summary" in str(exc.value).lower() or "template" in str(exc.value).lower()


def test_unknown_variant_raises(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    with pytest.raises(FileNotFoundError):
        render(
            "does-not-exist",
            content_dir=content_dir,
            variants_dir=variants_dir,
            templates_dir=templates_dir,
            output_dir=output_dir,
        )


def test_bad_content_id_error_message_is_useful(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    vd = tmp_path / "variants"
    _write(
        vd / "academic.yaml",
        "variant: academic\n"
        "sections:\n"
        "  - type: employment\n    include: [yoh, ghost-role]\n",
    )
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    with pytest.raises(Exception) as exc:
        render(
            "academic",
            content_dir=content_dir,
            variants_dir=vd,
            templates_dir=templates_dir,
            output_dir=output_dir,
        )
    assert "ghost-role" in str(exc.value)


def test_empty_name_variants_writes_placeholder(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    # Override meta.yaml to have no name_variants.
    _write(
        content_dir / "meta.yaml",
        'name: "J"\ncontact:\n  email: "a@b.c"\nphoto: "p.jpg"\n',
    )
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )

    preamble = (output_dir / "_preamble.tex").read_text()
    assert r"\mynames" not in preamble
    assert "no name variants" in preamble


def test_default_output_dir_used_when_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)

    monkeypatch.chdir(tmp_path)
    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
    )
    assert (tmp_path / "build" / "academic" / "tex" / "summary.tex").exists()


def test_section_not_declared_produces_empty_file(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    vd = tmp_path / "variants"
    # Variant declares only summary — skills, employment, etc. are absent.
    _write(
        vd / "academic.yaml",
        "variant: academic\nsections:\n  - type: summary\n    content_id: s-a\n",
    )
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "out"

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=vd,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )

    # Summary is rendered; undeclared sections are empty files.
    assert "Pro summary" in (output_dir / "summary.tex").read_text()
    assert (output_dir / "employment.tex").read_text() == ""
    assert (output_dir / "skills.tex").read_text() == ""


class TestMain:
    def test_main_with_variant_arg_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tools import render as render_module

        content_dir = _setup_content(tmp_path)
        variants_dir = _setup_variant(tmp_path)
        templates_dir = _setup_templates(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(render_module, "_DEFAULT_CONTENT_DIR", content_dir)
        monkeypatch.setattr(render_module, "_DEFAULT_VARIANTS_DIR", variants_dir)
        monkeypatch.setattr(render_module, "_DEFAULT_TEMPLATES_DIR", templates_dir)

        rc = render_module.main(["academic"])
        assert rc == 0
        assert (tmp_path / "build" / "academic" / "tex" / "summary.tex").exists()

    def test_main_without_args_returns_usage_code(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from tools.render import main

        rc = main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "usage" in err.lower()

    def test_main_falls_back_to_sys_argv(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from tools.render import main

        monkeypatch.setattr(sys, "argv", ["tools.render"])
        rc = main()
        assert rc == 2


def test_two_variants_from_same_pool(tmp_path: Path) -> None:
    """AC-3: adding a second variant file produces a second rendered output
    from the same content pool without code changes."""
    content_dir = _setup_content(tmp_path)
    vd = tmp_path / "variants"
    # Variant 1: everything
    _write(
        vd / "academic.yaml",
        "variant: academic\nsections:\n"
        "  - type: summary\n    content_id: s-a\n"
        "  - type: employment\n    include: [yoh]\n",
    )
    # Variant 2: summary only
    _write(
        vd / "short.yaml",
        "variant: short\nsections:\n  - type: summary\n    content_id: s-a\n",
    )
    templates_dir = _setup_templates(tmp_path)

    render(
        "academic",
        content_dir=content_dir,
        variants_dir=vd,
        templates_dir=templates_dir,
        output_dir=tmp_path / "out-a",
    )
    render(
        "short",
        content_dir=content_dir,
        variants_dir=vd,
        templates_dir=templates_dir,
        output_dir=tmp_path / "out-s",
    )

    assert (tmp_path / "out-a" / "employment.tex").read_text().startswith("EMP: Yoh")
    # Short variant didn't declare employment: empty file.
    assert (tmp_path / "out-s" / "employment.tex").read_text() == ""
    # Both summaries point at the same content pool item.
    assert "Pro summary" in (tmp_path / "out-a" / "summary.tex").read_text()
    assert "Pro summary" in (tmp_path / "out-s" / "summary.tex").read_text()


def test_output_dir_created_if_missing(tmp_path: Path) -> None:
    content_dir = _setup_content(tmp_path)
    variants_dir = _setup_variant(tmp_path)
    templates_dir = _setup_templates(tmp_path)
    output_dir = tmp_path / "deeply" / "nested" / "out"

    assert not output_dir.exists()
    render(
        "academic",
        content_dir=content_dir,
        variants_dir=variants_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )
    assert output_dir.exists()
    assert (output_dir / "summary.tex").exists()
