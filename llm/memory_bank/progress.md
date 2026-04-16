# Progress

Last updated: 2026-04-15

## Built & Working
- Compilable LaTeX CV based on the `curve` document class (Overleaf import).
- Header with name, email, X/Twitter, LinkedIn, GitHub, and conditional photo (`cv-llt.tex:70-90`).
- Section content in place:
  - Professional Summary (`summary.tex`).
  - Professional Experience — 2005–2025, five roles from DJJayNet → Yoh/Core Specialty Insurance (`employment.tex`).
  - Education — PhD CS (SE with AI/ML/MI) exp. 2027 at Virginia Tech; M.Eng. CS exp. 2025; prior M.I.T. + B.S. Economics at Virginia Tech (`education.tex`).
  - Selected Projects & Research — 4 entries (`projects.tex`).
  - Publications — dispatch to journal articles / conference proceedings / books via `biblatex` (`publications.tex`) against `own-bib.bib`.
  - Technical Skills — Platforms, Tools, Languages, AI/ML (`skills.tex`).
  - Awards & Certifications (`misc.tex`).
  - Referee section — "Available on Request" variant active; full variant (`referee-full.tex`) present but commented out (`cv-llt.tex:110-111`).
- LLM workflow scaffolding: `.claude/agents/` and `.claude/skills/` populated; `llm/memory_bank/` and `llm/features/` initialized.

## Remaining To Build
- Additional CV variants (industry/resume, short CV) in their own folders.
- Folder-based layout migration once a second variant is introduced.
- Decision + implementation for shared assets (`own-bib.bib`, photos, `settings.sty`) across variants.
- Build automation (e.g., `latexmk` rule or `Makefile`) for local reproducible builds.
- Tailored versions of the academic CV for specific research roles / internships.
- Content review: `own-bib.bib` contents have not been inspected in this memory bank pass — publication list accuracy/coverage is unverified.

## Known Issues / Tech Debt
- `\mynames{...}` in `cv-llt.tex:32-35` still contains the template's example names ("Lim/Lian Tze", "Wong/Lian Tze", "Lim/Tracy", "Lim/L.T.") rather than Jason's own name variants. Result: author bolding in the bibliography will not match Jason's entries until this is updated.
- Two photo files exist (`photo.jpg`, `photo_jason_1.jpeg`); only `photo_jason_1` is referenced. The unused `photo.jpg` is likely cruft.
- Commented `% \mynames{Lim/Lian\bibnamedelima Tze}` on `cv-llt.tex:29` is legacy from the template.
- No Makefile / build script; builds rely on Overleaf or manual `xelatex` + `biber` invocations.
- Flat directory layout will need reorganization once a second CV variant is added.

## Milestones
- **2026-04-15** — Initial Overleaf import committed; LLM workflow scaffolding (agents, skills, memory bank) established.
