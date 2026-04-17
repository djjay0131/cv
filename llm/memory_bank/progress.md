# Progress

Last updated: 2026-04-17

## Built & Working

### CV Repo (`djjay0131/cv`)
- **Data-driven CV pipeline** (M1): YAML content pool with stable IDs (`data/content/`) + variant selector (`data/variants/academic.yaml`) → Python generator (`tools/render.py` with Pydantic validation + Jinja2 templates) → LaTeX fragments (`build/<variant>/tex/`) → PDF via `latexmk`.
- **Makefile**: `make academic` runs lint → render → compile end-to-end.
- **CI** (`.github/workflows/build-cv.yml`): on push → lint bib → pytest (112 tests, 100% coverage) → ruff → render → compile PDF → publish PDF + `cv-data.zip` to `latest` GitHub Release.
- **`\mynames` fix**: author-bolding in bibliography now uses `Cusati/Jason` from the data layer, not the Overleaf template's Lim/Wong placeholders.
- **Hand-authored section files removed** (`summary.tex`, `employment.tex`, etc.) — content lives in YAML; files preserved in git history via `b89c380`.
- **Bib linting**: `tools/lint_bib.py` validates `own-bib.bib` for missing years, required fields.

### Website Repo (`djjay0131/website`)
- **Landing page** (`/`): photo, bio, contact links, CTA buttons to CV/papers/PDF.
- **CV page** (`/cv/academic`): full academic CV rendered from YAML data, with JSON-LD Person schema.
- **Papers page** (`/papers`): publications parsed from `own-bib.bib`, grouped by type, year-descending, with GitHub links where present.
- **Projects page** (`/projects` + detail pages): 4 project entries from content pool with GitHub links.
- **SEO**: OpenGraph, Twitter cards, canonical URLs, JSON-LD, sitemap, robots.txt on every page.
- **Accessibility**: skip-to-main link, ARIA landmarks, WCAG AA color contrast.
- **Print CSS**: hides chrome, shows PDF download banner.
- **CI** (`.github/workflows/build.yml`): fetch data from cv repo release → vitest (20 tests) → Astro build (8 pages) → deploy to GitHub Pages → smoke test (5 routes, HTTP 200 + body size).
- **Live at** https://djjay0131.github.io/website/
- **Feature status**: VERIFIED (all 4 quality gates passed, all 16 acceptance criteria validated).

## Remaining To Build
- **Variant selector DSL**: bullet-level inclusion/exclusion, per-variant overrides/rewording — designed when Jason uploads existing resume versions.
- **Additional CV variants** (industry resume, short CV): requires the selector DSL + new `data/variants/*.yaml` files.
- **Sync enforcement skill**: `constellize`-style skill checking CV↔website alignment.
- **Formal Lighthouse CI gate**: WCAG AA colors and semantic HTML are in place; `@axe-core/playwright` integration deferred.
- **Custom domain or root-level hosting**: site is at `djjay0131.github.io/website/`; could rename repo to `djjay0131.github.io` or add a CNAME.
- **`repository_dispatch` activation**: PAT needed for automated cv → website triggering.
- **`NOTIFICATION_WEBHOOK` configuration**: failure notifications are wired but gated on this secret.

## Known Issues / Tech Debt
- Local MacTeX (TeX Live 2025) can't install `cochineal`/`cabin`/`zi4` due to TeX Live version mismatch with remote repo (2026). PDF compiles in CI only. Not a blocker.
- `cv_tools.egg-info/` directory in the repo root (artifact of early `pip install -e .` attempt). Harmless but should be gitignored or cleaned.
- `@citation-js/core` has no published TypeScript types; custom `.d.ts` maintained in `src/lib/citation-js.d.ts`.
- Node.js 20 deprecation warnings in CI for `actions/checkout@v4` etc. — will need v5 upgrades before Sept 2026.

## Milestones
- **2026-04-15** — Initial Overleaf import; LLM workflow scaffolding established.
- **2026-04-16** — M1 implemented: data-driven CV pipeline. M2 implemented: Astro website deployed.
- **2026-04-17** — M3 implemented: projects page, SEO, a11y, print CSS, smoke tests. Feature VERIFIED.
