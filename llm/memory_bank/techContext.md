# Tech Context

## Language & Format
- **LaTeX** source, using the `curve` document class (a CV-oriented class popularized by LianTze Lim's Overleaf template). Entry point: `cv-llt.tex`.
- Bibliography managed with `biblatex` + `biber` backend; entries live in `own-bib.bib`.

## Toolchain
- Preferred engine: **XeLaTeX** or **LuaLaTeX** (enables the `fontspec` font stack: `cochineal`, `cabin`, `zi4` — see `cv-llt.tex:39-50`).
- Fallback: pdfLaTeX with T1 fontenc.
- Bibliography: run `biber cv-llt` after the first LaTeX pass.

## Build
Typical build sequence (no Makefile present yet):
```
xelatex cv-llt.tex
biber cv-llt
xelatex cv-llt.tex
xelatex cv-llt.tex
```
Produces `cv-llt.pdf`. Overleaf handles this automatically; locally, a LaTeX installation (TeX Live / MacTeX) is required.

## Key Dependencies (LaTeX packages)
- `curve` — document class providing `\makerubric`, `\entry*`, `\leftheader`, `\photo`, etc.
- `biblatex` + `csquotes` — publication list formatting (IEEE style, `cv-llt.tex:16`).
- `fontawesome5`, `simpleicons` — icons (envelope, LinkedIn, GitHub, X/Twitter).
- `tikz` — used for the "swish" rubric header shade and the circled numbers on bibliography entries (`settings.sty:50-92`).
- `hyperref` with `colorlinks=true,allcolors=black` (`settings.sty:147`).
- `cochineal`, `cabin`, `zi4` — OpenType font packages (XeLaTeX/LuaLaTeX path).

## Structure on Disk (current)
```
cv/
├── cv-llt.tex        # main entry
├── settings.sty      # style / package setup
├── summary.tex       # Professional Summary rubric
├── employment.tex    # Professional Experience rubric
├── education.tex     # Education rubric
├── projects.tex      # Selected Projects & Research
├── publications.tex  # bibliography dispatch (journal/conf/books)
├── skills.tex        # Technical Skills
├── misc.tex          # Awards / Certifications
├── referee.tex       # "Available on request"
├── referee-full.tex  # full referee list (currently commented out in main)
├── own-bib.bib       # bibliography entries
├── photo.jpg         # photo asset (unused name variant)
└── photo_jason_1.jpeg  # photo referenced by \photo[r]{photo_jason_1}
```

## Deployment / Hosting
- Origin: Overleaf import (see `b89c380 Initial Overleaf Import`).
- Distribution: compiled PDF shared manually. No CI/CD, no hosting infra.

## Technical Constraints
- `curve` class customizations flow through `settings.sty`; ad-hoc redefinitions in `cv-llt.tex` must come **after** `\usepackage{settings}` (already true for the `\DefineBibliographyStrings` override on `cv-llt.tex:22`).
- The `\mynames{...}` list bolding only works when `.bib` author names use `\bibnamedelima` (for space) or `\bibnamedelimi` (for initials) — see comment at `cv-llt.tex:27-36`.
- Photo display is toggled via `\includecomment{fullonly}` / `\excludecomment{fullonly}` (`cv-llt.tex:63-64`).
