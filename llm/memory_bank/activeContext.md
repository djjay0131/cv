# Active Context

Last updated: 2026-04-16

## Current Focus
M1 of the `cv-website` feature is implemented: the LaTeX CV is now generated from a data-driven pipeline (YAML content pool + variant selectors + Jinja2 templates). M2 (Astro website repo) and M3 (polish) remain as separate future passes.

## Recent Significant Changes
- `b89c380` — Initial Overleaf Import (only commit to date). The full Overleaf `curve`-based template and Jason's content landed together.
- Copied agents and skills from `~/code/crew` and `~/code/template-paper` into `.claude/`.
- Wrote the full `cv-website.md` spec under `llm/features/`, phased into M1/M2/M3.
- **M1 implementation landed (this session, uncommitted):**
  - Python project: `pyproject.toml`, `.venv/`, `.gitignore`.
  - `tools/` package: `schema.py`, `converters.py`, `resolver.py`, `render.py`, `lint_bib.py`, plus tests (112 passing, 100% coverage, ruff clean).
  - Data layer: `data/content/*.yaml` (content pool with stable IDs) + `data/variants/academic.yaml` (selector).
  - Templates: `templates/tex/*.tex.j2` (7 section templates).
  - `cv-llt.tex`: now `\input`s generated fragments via `\cvvariant` (default "academic"); `\mynames` sourced from data.
  - `Makefile`: `make academic` runs lint → render → latexmk.
  - `.github/workflows/build-cv.yml`: CI for lint, tests, PDF build, release artifact, and (gated) `repository_dispatch` to the future website repo.

## Open Decisions / Questions
- **PDF compile environmental gap**: local MacTeX is missing `cochineal`, `cabin`, `inconsolata-type1` font packages. The generator side works end-to-end; final PDF verification requires `sudo tlmgr install cochineal cabin inconsolata-type1` (or equivalent).
- **Deprecated hand-authored `.tex` files** (`summary.tex`, `employment.tex`, `education.tex`, `projects.tex`, `skills.tex`, `misc.tex`, `referee.tex`, `referee-full.tex`): still in working tree. Spec says remove only after AC-1 PDF parity is confirmed. Pending.
- **`\mynames` template placeholder fix**: done — `cv-llt.tex` now pulls `\mynames{Cusati/Jason}` from the generated `_preamble.tex`. The Overleaf template's Lim/Wong placeholders are gone.
- **`repository_dispatch` target**: workflow step is written but disabled by default. Will enable once the `website` repo exists and a PAT is provisioned (M2).

## Immediate Next Steps
1. Install missing TeX packages and compile: `sudo tlmgr install cochineal cabin inconsolata-type1` then `make academic`. Visually review `build/academic/academic.pdf` against the prior Overleaf output.
2. Once parity is confirmed, remove the deprecated hand-authored `.tex` files from the working tree (they remain in git history via `b89c380`).
3. Commit the M1 implementation.
4. Plan M2 (website repo) — separate repo, Astro-based, consumes this repo's published data artifact.
5. Consider a follow-up task to define the variant selector DSL (per the spec) once additional resume versions are provided for mapping.
