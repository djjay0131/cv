"""CV fragment generator: YAML data + Jinja templates → LaTeX fragments.

Entry point: `python -m tools.render <variant>`.

Outputs `build/<variant>/tex/<section>.tex` for each section in the variant,
plus `_preamble.tex` containing the `\\mynames{...}` declaration derived from
`meta.name_variants` in the content pool.
"""

from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from tools.converters import md_to_html, md_to_latex
from tools.resolver import resolve_variant
from tools.schema import load_content, load_variant

_DEFAULT_CONTENT_DIR = Path("data/content")
_DEFAULT_VARIANTS_DIR = Path("data/variants")
_DEFAULT_TEMPLATES_DIR = Path("templates/tex")

# Sections that have a rendered template file; "publications" is rendered by
# biblatex directly and has no Jinja template here.
_SECTIONS_WITH_TEMPLATE = (
    "summary",
    "employment",
    "education",
    "projects",
    "skills",
    "misc",
    "referee",
)


def _build_env(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["md_to_latex"] = md_to_latex
    env.filters["md_to_html"] = md_to_html
    return env


def _render_preamble(resolved: dict) -> str:
    """Build a LaTeX preamble fragment containing \\mynames for bib author bolding."""
    meta = resolved["meta"]
    if not meta.name_variants:
        return "% no name variants defined\n"
    entries = ",\n  ".join(f"{nv.family}/{nv.given}" for nv in meta.name_variants)
    return f"\\mynames{{{entries}}}\n"


def _render_theme(variant) -> str:
    """Build a LaTeX fragment declaring the variant's theme style + photo flag.

    cv-llt.tex \\input's this file before \\begin{document} and dispatches on
    \\cvtheme / \\cvphoto via \\ifdefstring.
    """
    photo = "true" if variant.theme.photo else "false"
    return f"\\def\\cvtheme{{{variant.theme.style}}}\n\\def\\cvphoto{{{photo}}}\n"


def render(
    variant_name: str,
    *,
    content_dir: Path | None = None,
    variants_dir: Path | None = None,
    templates_dir: Path | None = None,
    output_dir: Path | None = None,
) -> None:
    """Render a variant to LaTeX fragments under output_dir.

    Raises:
        FileNotFoundError: variant file does not exist.
        MissingContentIdError: variant references an unknown content id.
        ValueError: schema or resolution failures.
        TemplateNotFound: a required template is missing.
    """
    content_dir = content_dir or _DEFAULT_CONTENT_DIR
    variants_dir = variants_dir or _DEFAULT_VARIANTS_DIR
    templates_dir = templates_dir or _DEFAULT_TEMPLATES_DIR
    if output_dir is None:
        output_dir = Path("build") / variant_name / "tex"

    content = load_content(Path(content_dir))
    variant = load_variant(Path(variants_dir) / f"{variant_name}.yaml")
    resolved = resolve_variant(content, variant)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Write preamble (name variants → \mynames).
    (output_dir / "_preamble.tex").write_text(_render_preamble(resolved), encoding="utf-8")

    # Write theme fragment (\cvtheme + \cvphoto for cv-llt.tex to dispatch on).
    (output_dir / "_theme.tex").write_text(_render_theme(variant), encoding="utf-8")

    env = _build_env(Path(templates_dir))
    overrides = variant.raw_overrides or {}

    declared_types = {s.type for s in variant.sections}
    for section_type in _SECTIONS_WITH_TEMPLATE:
        if section_type not in declared_types:
            # Variant did not declare this section; write an empty file so the
            # main .tex can \input it unconditionally.
            (output_dir / f"{section_type}.tex").write_text("", encoding="utf-8")
            continue

        override = overrides.get(section_type)
        if override and override.tex is not None:
            (output_dir / f"{section_type}.tex").write_text(override.tex, encoding="utf-8")
            continue

        try:
            tmpl = env.get_template(f"{section_type}.tex.j2")
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"required template missing: {section_type}.tex.j2 in {templates_dir}"
            ) from e
        (output_dir / f"{section_type}.tex").write_text(tmpl.render(**resolved), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("usage: python -m tools.render <variant-name>", file=sys.stderr)
        return 2
    render(argv[0])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
