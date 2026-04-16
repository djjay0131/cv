# Project Brief

## Name
Jason Cusati — CV (LaTeX)

## Purpose
Source repository for Jason Cusati's curriculum vitae, authored in LaTeX. Initial target variant is an **academic CV** for research roles and research internships. Additional variants (e.g., industry resume, short CV) will be added over time, each in its own folder so they can be tailored and built independently.

## Target Audience
- Academic hiring committees / research groups considering Jason for research roles.
- Internship programs (research-oriented) that review academic CVs.
- Secondary audience later: industry recruiters (once tailored variants exist).

## Problem Being Solved
Keep a single, version-controlled source of truth for the CV so that:
- Content edits (employment, education, publications) are tracked in git.
- Multiple tailored variants can share underlying content without drift.
- The document is reproducible via LaTeX (originally imported from Overleaf).

## Scope
**In scope:**
- The current top-level academic CV (based on the `curve` LaTeX class, Overleaf import).
- Future sibling folders for additional CV/resume variants.
- Supporting bibliography (`own-bib.bib`) and section files (`education.tex`, `employment.tex`, `publications.tex`, etc.).
- Tailoring content for specific research roles / internships.

**Out of scope:**
- Cover letters, research statements, teaching statements (not handled here unless explicitly added later).
- Hosting or public web distribution of the compiled PDF.
- Non-CV documents.

## Constraints
- Must compile with a standard LaTeX toolchain; the template prefers XeLaTeX/LuaLaTeX for OpenType font support but falls back to pdfLaTeX (see `cv-llt.tex:39-50`).
- Uses the `curve` document class (imported from Overleaf) and custom styling in `settings.sty` — changes should respect that class's commands (`\makerubric`, `\entry*`, etc.).
- Bibliography styled via `biblatex` with IEEE style (`cv-llt.tex:16`). Author-name bolding depends on `\mynames{...}` being kept in sync with Jason's name variants.
- Photo is included only when the `fullonly` environment is active (`cv-llt.tex:63,87-90`).
