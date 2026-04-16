# System Patterns

## High-Level Architecture
Single-document LaTeX project with a **main file + section includes** pattern. `cv-llt.tex` is the orchestrator; each CV section is a standalone `.tex` file included via `\makerubric{section}` (which wraps `\input{section}` with rubric styling) or, for the publications section, directly via `\input{publications}` because it can't be modeled as simple `\entry*` items.

## Directory / Module Structure
Currently flat — all `.tex` files live at the repo root alongside `settings.sty` and assets. Planned evolution (per user): **one folder per CV variant** (e.g., `academic/`, `industry/`, `short/`), each containing its own main `.tex`, section files, and `settings.sty` (or sharing one). Shared bibliography (`own-bib.bib`) and photo assets are candidates to live at the root and be referenced by each variant.

## Key Patterns In Use
- **Rubric-per-section**: each content file wraps content in `\begin{rubric}{Title} ... \end{rubric}`. See `summary.tex:1,4`, `education.tex:1,5`, `employment.tex:1,46`, `skills.tex:4,16`, `misc.tex:1,11`, `projects.tex:1,6`.
- **Dated entries** via `\entry*[YYYY]{...}`, undated via `\entry*{...}`. Example: `education.tex:2-4`, `employment.tex:3,14,...`.
- **Sub-rubrics** for grouped lists inside a rubric: `\subrubric{Platforms}`, `\subrubric{Tools}`, etc. (`skills.tex:5-15`, `misc.tex:2,6`).
- **Manual rubric head** for sections not modeled by rubric/entry (publications): `\makerubrichead{Research Publications}` in `publications.tex:2`, followed by `\printbibliography[...]` calls that filter by entry type.
- **Author-name bolding** via `\mynames{Family/Given,...}` in `cv-llt.tex:32-35`, which toggles `\textbf` around matching authors in the bibliography (`settings.sty:122-144`).
- **Conditional photo** via `comment` package's `fullonly` environment (`cv-llt.tex:63,87-90`).
- **Style isolation**: colors (`SwishLineColour`, `MarkerColour`), fonts, spacing, and bib formatting all live in `settings.sty`. `cv-llt.tex` is meant for content/top-level config only.

## Data Flow (primary use case — compile the CV)
1. LaTeX engine reads `cv-llt.tex`.
2. Document class `curve` + `settings.sty` establish layout, colors, rubric macros, and biblatex setup.
3. `\addbibresource{own-bib.bib}` registers the bibliography.
4. `\mynames{...}` seeds the author-bolding toggle.
5. `\begin{document}` → `\makeheaders[c]` renders name/contact/photo.
6. `\makerubric{summary|employment|education|projects|skills|misc|referee}` inputs each section `.tex`.
7. `\input{publications}` renders the bibliography groups (articles, proceedings, books).
8. `biber` resolves citations; second+ LaTeX passes finalize references and links.

## Conventions Observed
- Every section file is UTF-8 LaTeX; some include `%!TEX encoding = UTF8` and `%!TEX root = cv-llt.tex` hints (`skills.tex:1-2`, `referee.tex:1-2`).
- Percent signs inside values are escaped (e.g., `\textbf{50\%}` in `employment.tex:5`).
- Multi-name / name-variant handling uses `\bibnamedelima` / `\bibnamedelimi` separators in the bib file to keep `\mynames` matching robust.
- Bullet lists inside an entry use plain `itemize` (`employment.tex:4-12`, etc.).
- Colors and markers are **not** redefined per file — change them in `settings.sty` or via the commented overrides in `cv-llt.tex:56-60`.
- Referee section has two variants (`referee.tex` "Available on Request", `referee-full.tex` full list); the main file toggles between them by commenting one of the two lines (`cv-llt.tex:110-111`).
