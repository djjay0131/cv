# Project Brief

## Name
Jason Cusati — CV + Personal Website

## Purpose
Two-repo system for Jason Cusati's professional presence:
1. **`cv` repo** — data-driven CV pipeline. Structured YAML content pool + variant selectors generate LaTeX fragments via Python/Jinja2, compiled to PDF by CI, and published as GitHub Release artifacts.
2. **`website` repo** (`djjay0131/website`) — Astro-based personal website consuming the `cv` repo's data artifact. Renders the CV as HTML, lists publications from `own-bib.bib`, and hosts project pages. Deployed to GitHub Pages.

## Target Audience
- Academic hiring committees / research groups evaluating Jason for research roles or internships — via the website's CV page or the downloadable PDF.
- Collaborators discovering Jason's publications and project artifacts via the papers and projects pages.
- Industry recruiters (once tailored industry-variant CV is created).

## Problem Being Solved
- Reviewers previously had to request or download a PDF to see Jason's credentials; now they visit the public website.
- Publications in `own-bib.bib` were invisible on the open web; now surfaced on the papers page with GitHub links.
- Future CV variants (academic, industry, short) share a canonical content pool so facts are maintained in one place.

## Scope
**In scope:**
- The `cv` repo: YAML data layer (`data/content/*.yaml`, `data/variants/*.yaml`), Python generator (`tools/`), Jinja2 LaTeX templates (`templates/tex/`), `Makefile`, CI workflow, and the LaTeX driver (`cv-llt.tex` + `settings.sty`).
- The `website` repo: Astro site with landing, CV, papers, and projects pages; CI that fetches data from the `cv` repo's release and deploys to GitHub Pages.
- Supporting bibliography (`own-bib.bib`) and photo assets.

**Out of scope:**
- Cover letters, research statements, teaching statements.
- Blog engine (site architecture supports it later, but not in v1).
- Per-page custom OpenGraph images (deferred).

## Constraints
- LaTeX side compiles with XeLaTeX via the `curve` document class; requires `cochineal`, `cabin`, `zi4` font packages.
- `cv-llt.tex` uses `\makerubric{build/\cvvariant/tex/<section>}` (NOT `\input`) — `curve.cls` defines `\makerubric` as `\LTXtable{\linewidth}{...}`, which wraps the input in a longtable context required by the `rubric` environment.
- Bibliography styled via `biblatex` with IEEE style. Author-name bolding via `\mynames{Cusati/Jason}` generated into `_preamble.tex` from `data/content/meta.yaml`.
- Website is a static Astro site deployed to GitHub Pages at `djjay0131.github.io/website/`.
