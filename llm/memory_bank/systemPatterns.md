# System Patterns

Last updated: 2026-04-17

## High-Level Architecture
**Two-repo, data-driven system:**

1. **`cv` repo** — content + generation. A YAML content pool (`data/content/`) is the single source of truth. A variant selector (`data/variants/<name>.yaml`) picks which items appear. A Python generator (`tools/render.py`) resolves the selector, renders Jinja2 templates into LaTeX fragments, and `latexmk` compiles them. CI publishes the PDF + data zip as GitHub Release assets.

2. **`website` repo** — presentation. An Astro static site fetches the data artifact from the `cv` repo's release, renders HTML pages (CV, papers, projects), and deploys to GitHub Pages.

## Two-Tier Data Model
- **Content pool** (`data/content/*.yaml`): each file holds a list of items with stable `id` fields. IDs are the contract between content and selectors.
- **Variant selector** (`data/variants/<name>.yaml`): references content pool IDs, controls section order and inclusion. M1 uses "include all" — the selector DSL for bullet-level filtering is a follow-up.
- **Schema enforcement**: Pydantic models in `tools/schema.py` validate both layers before rendering. Missing IDs, type errors, and duplicate IDs fail loud with file + field context.

## Generator Pipeline (`cv` repo)
```
data/content/*.yaml + data/variants/<name>.yaml
    ↓ tools/schema.py (validate)
    ↓ tools/resolver.py (map IDs → items)
    ↓ tools/render.py + Jinja2 templates
    ↓ build/<variant>/tex/*.tex + _preamble.tex
    ↓ latexmk -xelatex (via Makefile)
    → build/<variant>/<variant>.pdf
```

## LaTeX Patterns
- **`\makerubric{path}` NOT `\input{path}`**: `curve.cls` defines `\makerubric` as `\LTXtable{\linewidth}{...}`, wrapping the file in a longtable context. Raw `\input` causes "Extra alignment tab" errors.
- **`\cvvariant` macro**: `cv-llt.tex` uses `\providecommand{\cvvariant}{academic}` to select which `build/<variant>/tex/` directory to read. The Makefile passes variant-specific `-usepretex` to override it.
- **`_preamble.tex`**: generated file containing `\mynames{Cusati/Jason}` from `meta.yaml:name_variants`. Loaded before `\begin{document}`.
- **`publications.tex`**: the one section NOT generated — it uses `biblatex` directly (`\printbibliography[...]`), reading `own-bib.bib`.
- **Rubric idioms preserved**: templates emit `\begin{rubric}{Title}`, `\entry*[dates]{...}`, `\subrubric{...}`, `\begin{itemize}`, etc. — identical to the original hand-authored style.

## Converter Pattern
- All user-content strings in YAML use Markdown-style inline formatting: `**bold**`, `*italic*`, `` `code` ``.
- `tools/converters.py` provides two functions: `md_to_latex()` and `md_to_html()`.
- Both use a 3-stage sentinel approach: (1) emphasis → sentinels, (2) escape target-specific specials, (3) sentinels → target markup. This prevents double-escaping.
- LaTeX escaping uses a single-pass regex (`re.sub` with a map) to avoid cascading replacements.
- `md_to_html()` in the website repo (`src/lib/md.ts`) mirrors the Python implementation exactly.

## Website Patterns
- **Dynamic routes**: `src/pages/cv/[variant].astro` enumerates all `.yaml` files in `data/variants/` at build time via `getStaticPaths()`. New variants appear automatically.
- **Bib parsing**: `src/lib/bib.ts` uses `@citation-js/core` to parse `.bib` → CSL JSON, then groups by type and sorts year-descending to match the LaTeX side.
- **SEO**: every page has OG/Twitter meta, canonical URL, and meta description via `Base.astro` props. CV page adds JSON-LD `Person` schema (`alumniOf`, `worksFor`, `hasCredential`). Sitemap via `@astrojs/sitemap`.
- **Accessibility**: skip-to-main link, ARIA roles (`banner`, `main`, `contentinfo`), `aria-label` on nav, WCAG AA color contrast (primary `#9e0636`, accent `#6b8a00`).
- **Print**: `@media print` hides header/footer, shows `.print-banner` with PDF download link.

## Cross-Repo Artifact Flow
1. Push to `cv/master` → CI builds PDF + `cv-data.zip` → uploads to `latest` GitHub Release.
2. `website` CI (push / `repository_dispatch` / hourly cron) → downloads artifacts → builds Astro → deploys to GitHub Pages → runs smoke tests.

## Convention Notes
- CV repo Python: `pyproject.toml`, `.venv/`, pytest + ruff. Targets py39 — uses `Optional[X]` not `X | None` for Pydantic compat.
- Website repo: `package.json`, npm, vitest, `astro check` for TypeScript strictness.
- Both repos use `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>` in commits.
