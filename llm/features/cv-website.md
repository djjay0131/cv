# Feature: Personal Website (CV + Papers + Projects) with Data-Driven CV Pipeline

**Status:** IMPLEMENTED (M1 + M2 + M3 complete)
**Date:** 2026-04-16
**Author:** Feature Architect (AI-assisted)

## Milestone Status
- **M1** — IMPLEMENTED (uncommitted). Python generator, templates, data layer, Makefile, CI workflow all landed; 112 tests / 100% coverage / ruff clean. Final PDF compile blocked on local TeX Live missing `cochineal`/`cabin`/`inconsolata-type1` fonts — environmental, not a code defect.
- **M2** — IMPLEMENTED. Astro website deployed at https://djjay0131.github.io/website/. Landing page, CV page, papers page, PDF download — all live. 20 vitest tests passing. CI fetches data from cv repo release, builds, deploys to GitHub Pages.
- **M3** — IMPLEMENTED. Projects page, print CSS, accessibility (skip-link, ARIA, WCAG AA colors), SEO (OG/Twitter/canonical/JSON-LD/sitemap/robots.txt), post-deploy smoke tests, failure notifications. 8 pages, all live, smoke tests passing in CI.

## Problem

Jason needs a public personal website — not just a rendering of his CV, but a site that hosts his CV (ultimately in multiple variants: academic first, then industry and others), a papers page with links to GitHub repositories where applicable, project pages, and additional works over time. The site must stay in sync with his formal LaTeX CV (which remains the downloadable PDF artifact) without creating a drift-prone parallel source.

Concretely:
- Reviewers (research hiring managers, internship coordinators, collaborators) currently have to request or download a PDF to see Jason's credentials.
- Publications in `own-bib.bib` are invisible on the open web and not linked to any code/artifacts.
- Projects in `projects.tex` are one-liners with no supporting pages.
- Future CV variants will multiply the drift surface unless content is structured.

The CV must continue to compile to a high-quality PDF that is structurally and visually equivalent to the current hand-authored output.

## Goals

- **G1**: A public personal website at a stable URL, hosting the academic CV as a native HTML page, a papers page, a projects page, and room to grow.
- **G2**: A two-tier structured-data source (content pool + variant selectors) drives both the LaTeX PDF output and the website's HTML CV page. No drift between them.
- **G3**: The academic CV PDF generated from the data layer is structurally equivalent to the current hand-authored output (same rubric titles, same entries in same order, same page count ±1) and passes human visual review.
- **G4**: `own-bib.bib` remains the single source of truth for publications; both the LaTeX CV (via biblatex) and the website's papers page (via bib parsing) read from it directly.
- **G5**: Adding a new CV variant requires only a new variant selector file that references content from the pool — no per-variant folder tree of `.tex` files.
- **G6**: The PDF is published as a downloadable artifact from every commit to `master`; the website links to the latest PDF with no manual sync step.

## Non-Goals

- **NG1**: Cover letters, research statements, teaching statements. Not in this repo, not on the site.
- **NG2**: A CMS, authentication, or server-side dynamic content. The site is static.
- **NG3**: Backwards compatibility with Overleaf's "press compile and it works" workflow for this repo. The generator runs outside Overleaf. The supported build path is `make` → `python tools/render.py` → `latexmk` locally or in CI.
- **NG4**: Per-CV-type separate repositories. All variants share this one `cv` repo.
- **NG5**: A blog engine in v1. The site architecture should not preclude adding one later, but v1 ships without one.
- **NG6**: Defining specific academic-vs-industry variant mappings. The infrastructure supports variant selection; actual content mappings are a follow-up task.
- **NG7**: Author-name bolding on the website papers page. The `\mynames` mechanism stays scoped to the LaTeX PDF only.
- **NG8**: OpenGraph image design. Tags will reference a default photo; custom per-page OG images are deferred.

## User Stories

- As Jason, I want to edit content in one place and have both my CV PDF and my website's CV page update, so I never maintain two copies of my credentials.
- As Jason, I want to produce a new CV variant (e.g., industry resume) by creating a selector file that picks and optionally overrides content from the pool, so I avoid duplicating facts.
- As Jason, I want `own-bib.bib` to feed both the PDF's publication list and the website's papers page, so I add a new paper in one place.
- As a research hiring manager, I want to view Jason's CV in my browser on mobile and desktop without downloading a PDF, so I can evaluate him quickly.
- As a research hiring manager, I want a one-click link to the latest PDF of Jason's CV, so I can attach it to a candidate packet.
- As a collaborator, I want to see a paper's abstract on Jason's site and follow a link to its GitHub repository (if one exists), so I can evaluate the artifact, not just the citation.

## Delivery Milestones

### M1: Data-driven CV pipeline (`cv` repo)
- Two-tier data model: `data/content/` (canonical pool with IDs) + `data/variants/academic.yaml` (selector — initially "include all", no overrides/rewording DSL yet).
- Python generator (`tools/render.py` + `tools/converters.py`) with Jinja2 templates → `build/<variant>/tex/*.tex`.
- Makefile: `make academic` runs render + `latexmk -xelatex` → `build/academic/academic.pdf`.
- Bib linting step: validates `own-bib.bib` for missing/invalid years, missing required fields.
- CI: GitHub Actions builds PDF on push, uploads as release asset on `latest` tag, fires `repository_dispatch` to the website repo (PAT-based).
- `\mynames` in `cv-llt.tex` fixed to use Jason's actual name variants (moved into data layer under `meta.name_variants`).
- Hand-authored `.tex` section files deprecated (kept in git history, removed from working tree after parity confirmed).
- **AC-1 through AC-6, AC-9 land here.**

### M2: Website MVP (`website` repo)
- New Astro-based repo. Fetches data artifact from `cv` repo's latest release at build time (no submodule).
- Renders: landing page, `/cv/academic` (HTML CV from data), `/papers/` (from `.bib` with GitHub links where present), PDF download link.
- Cross-repo trigger: `repository_dispatch` from `cv` kicks a website rebuild. Scheduled cron fallback (hourly).
- Deploys to GitHub Pages.
- **AC-2, AC-7, AC-8, AC-10 land here.**

### M3: Polish pass
- `/projects/` page with per-project detail pages.
- Print CSS: `@media print` hides chrome, shows clean content + "Download formal PDF" link.
- Accessibility: semantic HTML, alt text, color contrast audit (web-safe variants of `SwishLineColour` / `MarkerColour`). Lighthouse accessibility score ≥ 95 as CI gate via `@axe-core/playwright` or `pa11y-ci`.
- SEO: OpenGraph + Twitter cards per route, `sitemap.xml` (Astro integration), `robots.txt`, canonical URLs, per-page meta descriptions, JSON-LD `Person` schema (`alumniOf`, `worksFor`, `hasCredential`).
- Post-deploy smoke test: CI curls `/cv/academic` and `/papers/` on the live URL, asserts HTTP 200 + non-empty body.
- Failed-build notification: `if: failure()` step POSTs to a configurable webhook (Slack/Discord/email). Fires on both `cv` and `website` repo build failures.
- **AC-11 through AC-16 land here.**

## Design Approach

### Two-repo architecture

- **`cv` (this repo)** — content-only. Holds the two-tier data layer, `own-bib.bib`, photo assets, LaTeX templates, Python generator, bib linter, and CI that builds/publishes the PDF + data artifact. Does **not** hold website code.
- **`website` (new, separate repo)** — presentation. Astro-based static site. Fetches data artifact from `cv` repo's latest GitHub release at build time. Renders native HTML pages for each CV variant and the papers/projects/other sections. Links to the latest PDF artifact for downloads.

### `cv` repo: new layout

```
cv/
├── data/
│   ├── content/                  # canonical content pool
│   │   ├── employment.yaml       # all roles, each with a stable ID
│   │   ├── education.yaml
│   │   ├── projects.yaml
│   │   ├── skills.yaml
│   │   ├── summaries.yaml        # multiple bio/summary variants
│   │   ├── misc.yaml             # awards, certifications
│   │   └── meta.yaml             # name, contact, photo, name_variants
│   └── variants/
│       └── academic.yaml         # selector: references content IDs, section order
├── templates/
│   └── tex/                      # Jinja2 templates producing .tex fragments
│       ├── summary.tex.j2
│       ├── employment.tex.j2
│       ├── education.tex.j2
│       ├── projects.tex.j2
│       ├── skills.tex.j2
│       ├── misc.tex.j2
│       └── referee.tex.j2
├── tools/
│   ├── render.py                 # loads content pool + variant selector → Jinja → .tex
│   ├── converters.py             # md_to_latex, md_to_html filters
│   ├── lint_bib.py               # bib linter
│   └── schema.py                 # Pydantic models for content + variant validation
├── build/                        # gitignored; generator output + compiled PDFs
│   └── <variant>/
│       ├── tex/*.tex
│       └── <variant>.pdf
├── cv-llt.tex                    # main LaTeX driver (\input's generated fragments)
├── settings.sty                  # unchanged
├── own-bib.bib                   # single source of truth for publications
├── publications.tex              # unchanged — biblatex dispatch
├── photo_jason_1.jpeg            # unchanged
├── Makefile                      # `make academic` → render + latexmk → PDF
├── .github/workflows/
│   └── build-cv.yml              # on push: lint bib, render, build PDF, publish artifact,
│                                 #   fire repository_dispatch to website repo
├── .gitignore                    # build/
└── llm/                          # memory bank + features (already present)
```

### Two-tier data model

**Content pool** (`data/content/*.yaml`): each file holds a list of items with stable IDs.

```yaml
# data/content/employment.yaml
- id: yoh-adf-architect
  dates: "2024–2025"
  company: "Yoh, A Day & Zimmerman Company"
  location: "Remote, SC"
  title: "ADF Solution Architect – Core Specialty Insurance"
  bullets:
    - id: yoh-mvp
      text: "Built a small SDE team and delivered an MVP Insurance Data Ingestion
             Platform using Microsoft's Common Data Model, reducing time-to-ingest
             by **50%**."
    - id: yoh-api
      text: "Architected and implemented an API to orchestrate Azure Data Factory
             pipelines and data flows."
    - id: yoh-llm
      text: "Prototyped LLM-assisted source-to-target mapping generating ADF
             transformations and derived columns."
    - id: yoh-streamlit
      text: "Built a Streamlit UI integrated with the Data Ingestion API for
             faster analyst feedback loops."
```

**Variant selector** (`data/variants/academic.yaml`): references content IDs, controls section order and inclusion.

```yaml
variant: academic
extends: null                      # future: inherit from a base variant
sections:
  - type: summary
    content_id: summary-academic   # picks one of the summaries from summaries.yaml
  - type: employment
    include:                       # list of role IDs; order here = order in output
      - yoh-adf-architect          # includes all bullets by default
      - duck-creek-architect
      - blackbaud-principal
      - blackbaud-solutions
      - djjaynet-consultant
  - type: education
    include: [phd-cs-vt, meng-cs-vt, bs-econ-vt]
  - type: projects
    include: [llm-coding-assistant, security-classifier, sentiment-yelp, nfl-ml]
  - type: publications             # special: reads own-bib.bib, no content IDs needed
  - type: skills
    include: [platforms, tools, languages, ai-ml]
  - type: misc
    include: [awards, certifications]
  - type: referee
    content_id: referee-available   # or referee-full

raw_overrides:                      # optional escape hatch, per section and target
  # skills:
  #   tex: |
  #     % hand-authored LaTeX that bypasses the template
```

**M1 simplification**: the variant selector in M1 uses "include all" — the selector DSL for bullet-level filtering and per-variant overrides/rewording is deferred to a follow-up task. The two-tier structure is in place so the follow-up only adds selector capabilities, not a data-layer refactor.

**Inline formatting convention**: Markdown-style `**bold**`, `*em*`, and `` `code` `` are allowed in any `text` field. Converters render them per target (`md_to_latex`: `**x**` → `\textbf{x}`, auto-escapes `%`, `&`, `_`, `#`; `md_to_html`: standard Markdown → HTML). Literal LaTeX/HTML is never written in data files.

### Generator flow

1. `tools/schema.py` validates content pool + variant YAML against Pydantic models. Exits non-zero with clear error on failure.
2. `tools/render.py` loads the content pool, resolves the variant selector (maps IDs → content items, applies section ordering), and renders each section through the corresponding Jinja2 template in `templates/tex/`. Output lands in `build/<variant>/tex/`.
3. `cv-llt.tex` `\input`s the generated fragments. `latexmk -xelatex` compiles the PDF.
4. Override check: if a section has a `raw_overrides.<section>.tex` entry, the override is written verbatim, bypassing the template.

### Publications (no YAML duplication)

- **LaTeX side**: `publications.tex` remains unchanged; biblatex reads `own-bib.bib` directly.
- **Website side**: Astro build step parses `own-bib.bib` with `citation-js` (or `@citation-js/plugin-bibtex`) to produce structured records. Papers page renders each with: citation, abstract (if present via `abstract = {...}` bib field), DOI link, and GitHub link (if `github = {...}` custom field present). Grouped by entry type (journal / conference / books) and sorted year-descending to match the LaTeX side. Bib linting step (in `cv` CI) validates years and required fields so ordering is reliable.
- **No author bolding on website** — decided during review. The website renders author names without special formatting.

### `website` repo: layout

```
website/
├── src/
│   ├── pages/
│   │   ├── index.astro              # landing: short bio + nav
│   │   ├── cv/
│   │   │   └── [variant].astro      # dynamic route — enumerates variants from data
│   │   ├── papers/
│   │   │   ├── index.astro          # list, generated from own-bib.bib
│   │   │   └── [slug].astro         # per-paper page (M3)
│   │   ├── projects/
│   │   │   ├── index.astro          # (M3)
│   │   │   └── [slug].astro         # (M3)
│   │   └── about.astro
│   ├── components/
│   │   ├── Header.astro
│   │   ├── Footer.astro
│   │   ├── CVSection.astro
│   │   ├── PaperCard.astro
│   │   └── PDFDownload.astro
│   ├── layouts/
│   │   └── Base.astro               # HTML head (OG, JSON-LD, print CSS link)
│   └── lib/
│       ├── cv-data.ts               # loads content pool + variant → resolved sections
│       ├── bib.ts                    # parses own-bib.bib, merges GitHub links
│       └── md.ts                     # Markdown inline → HTML
├── data/                            # fetched from cv repo's latest release artifact
│   ├── content/
│   ├── variants/
│   ├── own-bib.bib
│   └── photo_jason_1.jpeg
├── public/
│   └── pdfs/                        # PDF artifacts fetched from cv repo release
├── astro.config.mjs
├── .github/workflows/
│   ├── build.yml                    # on repository_dispatch or cron: fetch data + PDF,
│   │                                #   build Astro, deploy to GitHub Pages, smoke test
│   └── a11y.yml                     # (M3) axe/Lighthouse accessibility gate
└── README.md
```

### Cross-repo data + artifact flow

1. **Push to `cv/master`** → `.github/workflows/build-cv.yml` runs:
   - `python tools/lint_bib.py own-bib.bib` — validates bib entries.
   - `python tools/render.py academic` — generates `build/academic/tex/*.tex`.
   - `latexmk -xelatex` produces `build/academic/academic.pdf`.
   - Creates/updates a **data artifact**: zip of `data/`, `own-bib.bib`, photo assets → attached to the rolling `latest` GitHub Release tag alongside the PDF.
   - Fires **`repository_dispatch`** to `website` repo (via PAT stored in `cv` repo secrets) with event type `cv-updated`.
2. **`website` repo** receives `repository_dispatch` (or scheduled cron fallback — hourly):
   - Downloads latest release artifacts (data zip + PDF) from `cv` repo via `gh release download`.
   - Extracts data into `data/`, PDF into `public/pdfs/`.
   - Builds Astro site.
   - Deploys to GitHub Pages.
   - (M3) Runs post-deploy smoke test; on failure, fires notification webhook.

### Hosting

GitHub Pages. Cloudflare Pages is a drop-in alternative (OQ-6). Custom domain configuration is an open question (OQ-7).

## Sample Implementation

Illustrative core flow. Not shipped from this spec.

```yaml
# data/content/employment.yaml (excerpt)
- id: yoh-adf-architect
  dates: "2024–2025"
  company: "Yoh, A Day & Zimmerman Company"
  location: "Remote, SC"
  title: "ADF Solution Architect – Core Specialty Insurance"
  bullets:
    - id: yoh-mvp
      text: "Built a small SDE team and delivered an MVP Insurance Data Ingestion
             Platform using Microsoft's Common Data Model, reducing time-to-ingest
             by **50%**."
    - id: yoh-api
      text: "Architected and implemented an API to orchestrate Azure Data Factory
             pipelines and data flows."
```

```yaml
# data/variants/academic.yaml (M1: "include all" selector)
variant: academic
sections:
  - type: summary
    content_id: summary-academic
  - type: employment
    include: [yoh-adf-architect, duck-creek-architect, blackbaud-principal,
              blackbaud-solutions, djjaynet-consultant]
  - type: education
    include: [phd-cs-vt, meng-cs-vt, bs-econ-vt]
  - type: projects
    include: [llm-coding-assistant, security-classifier, sentiment-yelp, nfl-ml]
  - type: publications
  - type: skills
    include: [platforms, tools, languages, ai-ml]
  - type: misc
    include: [awards, certifications]
  - type: referee
    content_id: referee-available
```

```jinja
{# templates/tex/employment.tex.j2 #}
\begin{rubric}{Professional Experience}
{% for role in employment %}
\entry*[{{ role.dates }}]
    \textbf{ {{- role.company }} --- {{ role.location -}} }
    \emph{ {{- role.title -}} }
    \begin{itemize}
    {% for bullet in role.bullets %}
        \item {{ bullet.text | md_to_latex }}
    {% endfor %}
    \end{itemize}
{% endfor %}
\end{rubric}
```

```python
# tools/render.py (core flow)
import sys, yaml, pathlib
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from converters import md_to_latex
from schema import validate_content, validate_variant, resolve_variant

SECTIONS = ("summary","employment","education","projects",
            "skills","misc","referee")

def render(variant_name: str) -> None:
    content = validate_content(pathlib.Path("data/content"))
    variant = validate_variant(pathlib.Path(f"data/variants/{variant_name}.yaml"))
    resolved = resolve_variant(content, variant)  # maps IDs → content items per section

    env = Environment(loader=FileSystemLoader("templates/tex"),
                      undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True)
    env.filters["md_to_latex"] = md_to_latex

    out_dir = pathlib.Path(f"build/{variant_name}/tex")
    out_dir.mkdir(parents=True, exist_ok=True)

    overrides = variant.get("raw_overrides") or {}
    for section in SECTIONS:
        if section in overrides and "tex" in overrides[section]:
            (out_dir / f"{section}.tex").write_text(overrides[section]["tex"])
            continue
        tmpl = env.get_template(f"{section}.tex.j2")
        (out_dir / f"{section}.tex").write_text(tmpl.render(**resolved))

if __name__ == "__main__":
    render(sys.argv[1])
```

Key decisions:
- **`StrictUndefined`** — unknown keys raise at render time, never produce silent holes.
- **`validate_content` + `validate_variant`** — Pydantic validation before rendering; schema errors surface with clear messages, not Jinja tracebacks.
- **`resolve_variant`** — maps variant selector IDs to content pool items, producing a flat dict per section that templates consume. Templates don't know about the two-tier structure.
- **Override check** — `raw_overrides.<section>.tex` bypasses the template verbatim.

## Edge Cases & Error Handling

### EC-1: Unknown YAML key / missing required key
- **Scenario**: Content pool file has a typo in a required field.
- **Behavior**: Pydantic validation in `schema.py` catches the error before Jinja runs; exits non-zero with field name, file path, and line context.
- **Test**: Fixture YAML with missing `id` field; assert validation raises with clear message.

### EC-2: Variant references non-existent content ID
- **Scenario**: `academic.yaml` includes `employment: [nonexistent-role-id]`.
- **Behavior**: `resolve_variant` raises a `KeyError`-derived exception naming the missing ID and which variant references it. CI fails.
- **Test**: Fixture variant referencing a bad ID; assert resolution fails with the ID and variant name in the error.

### EC-3: Markdown converter on LaTeX-special characters
- **Scenario**: A bullet contains `$50k`, `&`, `_`, `#`, `%`, `^`, `~`.
- **Behavior**: `md_to_latex` escapes all LaTeX specials, preserving Markdown emphasis first. `md_to_html` HTML-escapes similarly.
- **Test**: Round-trip fixtures with each special; assert LaTeX compiles and HTML validates.

### EC-4: Visual regression vs. current PDF
- **Scenario**: Template output shifts spacing, font, or rubric layout.
- **Behavior**: Human visual review on initial migration. Optional CI step runs `diff-pdf` as a **warning** (not a gate) comparing generated PDF to a committed golden snapshot.
- **Test**: Initial golden = current hand-authored compile. Any significant visual change requires an explicit golden update.

### EC-5: Publication with no abstract or no GitHub link
- **Scenario**: `own-bib.bib` entry lacks `abstract` and `github` field.
- **Behavior**: Papers page renders citation + DOI link only; no empty headings, no dead icons.
- **Test**: Fixture bib with sparse entry; assert rendered HTML has no empty sections.

### EC-6: Unicode (en/em dashes, accented names)
- **Scenario**: Data includes `"2024–2025"` (en-dash), co-author with `é`.
- **Behavior**: YAML loaded as UTF-8; templates preserve; `xelatex`/`lualatex` handle natively.
- **Test**: Fixture with special characters; assert PDF and HTML render.

### EC-7: PDF artifact download timing
- **Scenario**: Website build triggered before `cv` artifact upload completes.
- **Behavior**: `repository_dispatch` fires only after the upload step succeeds, so the artifact exists. Cron fallback checks release timestamp; if no new release, build uses previously-fetched PDF and logs a notice.
- **Test**: Trigger website build manually; assert it fetches the correct PDF or uses the cached one.

### EC-8: Overleaf compatibility broken
- **Scenario**: Someone opens this repo in Overleaf expecting to compile.
- **Behavior**: Overleaf will fail — `build/` is gitignored. Documented in README.
- **Test**: README review item.

### EC-9: New variant auto-discovered by website
- **Scenario**: `data/variants/industry.yaml` added; website not explicitly updated.
- **Behavior**: `[variant].astro` dynamic route enumerates variant files from the data artifact at build time. New variants appear automatically. Nav component lists all discovered variants.
- **Test**: Add fixture variant; assert new route builds.

### EC-10: Bib entry with missing/invalid year
- **Scenario**: New bib entry has `year = {}` or no year field.
- **Behavior**: `lint_bib.py` flags the entry; CI fails before PDF build or data artifact publish.
- **Test**: Fixture bib with empty year; assert linter exits non-zero with entry key in the message.

## Acceptance Criteria

### M1 Acceptance Criteria

#### AC-1: Data-driven academic CV PDF
- **Given** a fresh clone of the `cv` repo with Python + TeX Live installed
- **When** the developer runs `make academic`
- **Then** `build/academic/academic.pdf` is produced; the output is structurally equivalent to the current hand-authored PDF (same rubric titles, same entries in same order, same page count ±1) and passes human visual review.

#### AC-2: Single source of truth for content
- **Given** an edit to a bullet in `data/content/employment.yaml`
- **When** the developer runs `make academic`
- **Then** the change appears in the generated PDF; and when the data reaches the website, it appears in the HTML CV page with no separate edit required.

#### AC-3: Multiple variants, one codebase
- **Given** a new file `data/variants/industry.yaml` referencing content pool IDs
- **When** the developer runs `make industry`
- **Then** an `industry.pdf` is produced; and when the website is rebuilt, `/cv/industry` renders as an HTML page automatically.

#### AC-4: Publications from `.bib` on both sides
- **Given** a new entry added to `own-bib.bib` with `github = {https://github.com/...}` custom field
- **When** the CV is rebuilt and the website is rebuilt
- **Then** the PDF publication list includes the new entry (biblatex-styled, ignoring the custom field); the website's papers page includes it with a visible GitHub link.

#### AC-5: Override escape hatch
- **Given** a section with `raw_overrides.<section>.tex` in the variant YAML
- **When** `make academic` runs
- **Then** the generator writes the override verbatim for that section; other sections render normally.

#### AC-6: CI publishes PDF + data artifact
- **Given** a push to `cv/master`
- **When** the build workflow finishes successfully
- **Then** the PDF and data zip are attached to the `latest` GitHub Release and downloadable via stable URLs; `repository_dispatch` fires to the website repo.

#### AC-9: Broken YAML / bad content ID fails loudly
- **Given** a schema error in content YAML or a bad ID reference in a variant
- **When** `make academic` runs
- **Then** it exits non-zero with a clear message identifying the file, field, and problem.

### M2 Acceptance Criteria

#### AC-7: Website fetches latest artifacts
- **Given** a successful `cv` build
- **When** the `repository_dispatch`-triggered website workflow runs
- **Then** the deployed site serves the latest PDF at `/pdfs/academic.pdf` and renders the latest data on `/cv/academic`.

#### AC-8: Papers page links to GitHub when present
- **Given** a `.bib` entry with a `github` custom field
- **When** the papers page is built
- **Then** that paper card shows a GitHub icon/link; entries without the field show no link.

#### AC-10: Mobile + desktop CV HTML
- **Given** the academic CV page at `/cv/academic`
- **When** viewed at 375px and 1440px widths
- **Then** it is readable without horizontal scroll, with legible typography and preserved section structure.

### M3 Acceptance Criteria

#### AC-11: Projects page
- **Given** project entries in the content pool with GitHub links
- **When** the website is built
- **Then** `/projects/` lists all projects; `/projects/<slug>` renders a detail page with description and GitHub link.

#### AC-12: Print CSS
- **Given** the academic CV page at `/cv/academic`
- **When** the user triggers browser print (Cmd-P)
- **Then** nav/footer/chrome are hidden; the page body prints cleanly; a "Download formal PDF" banner with link to `/pdfs/academic.pdf` is injected in print mode.

#### AC-13: Accessibility gate
- **Given** all routes on the deployed website
- **When** `@axe-core/playwright` or `pa11y-ci` runs in CI
- **Then** every route scores ≥ 95 on Lighthouse accessibility; semantic HTML (`<article>`, `<section>`, ordered headings), alt text on photo, and WCAG AA color contrast are verified.

#### AC-14: SEO metadata
- **Given** any page on the deployed website
- **When** the page is inspected
- **Then** it has: OpenGraph tags (title, description, image, url), Twitter card tags, canonical URL, meta description, and for the CV page, a JSON-LD `Person` schema with `alumniOf`, `worksFor`, `hasCredential` populated from the data layer. `sitemap.xml` and `robots.txt` are present at the site root.

#### AC-15: Post-deploy smoke test
- **Given** a successful deploy to GitHub Pages
- **When** the smoke-test CI step runs
- **Then** it curls `/cv/academic` and `/papers/` on the live URL, asserts HTTP 200 and non-empty body.

#### AC-16: Build failure notification
- **Given** a failed build or deploy in either repo
- **When** the `if: failure()` step executes
- **Then** a notification is sent to the configured webhook (Slack/Discord/email) with the repo name, workflow name, and link to the failed run.

## Technical Notes

### Affected components (this repo — M1)
- **New**: `data/content/`, `data/variants/`, `templates/tex/`, `tools/` (render.py, converters.py, lint_bib.py, schema.py), `Makefile`, `.github/workflows/build-cv.yml`, `.gitignore`.
- **Modified**: `cv-llt.tex` (input paths change to `build/<variant>/tex/`); `\mynames` fixed to Jason's actual name variants via data layer.
- **Unchanged**: `own-bib.bib`, `publications.tex`, `settings.sty`, photo assets.
- **Deprecated**: `summary.tex`, `employment.tex`, `education.tex`, `projects.tex`, `skills.tex`, `misc.tex`, `referee.tex`, `referee-full.tex` — removed from working tree after AC-1 parity confirmed; kept in git history.

### Affected components (website repo — M2/M3)
- Entirely new repo. Astro + TypeScript, GitHub Pages deploy.

### Patterns to follow
- Current `rubric` / `entry*` / `subrubric` LaTeX idioms preserved verbatim in templates (see `llm/memory_bank/systemPatterns.md`).
- `\mynames{...}` moved to data layer under `meta.name_variants`; rendered into a generated preamble fragment or directly into `cv-llt.tex`.
- `raw_overrides` escape hatch for sections that resist templating.

### Data model
- Content pool: Pydantic models in `tools/schema.py` defining each section's item shape, with `id` as required field on every item.
- Variant selector: Pydantic model defining `variant`, `sections` (list of `{type, include/content_id}`), and optional `raw_overrides`.
- Validation runs before rendering; schema errors surface before Jinja or LaTeX.

## Dependencies

### `cv` repo
- **Python 3.11+**: `pyyaml`, `jinja2`, `pydantic` (schema validation), `markdown-it-py` or a hand-rolled converter (OQ-3).
- **TeX Live / MacTeX**: `xelatex`, `biber`, `latexmk`.
- **CI**: `xu-cheng/latex-action` or equivalent Docker image with TeX Live + Python. PAT secret with write access to website repo (for `repository_dispatch`).

### `website` repo
- **Node 20+**: Astro, `@citation-js/plugin-bibtex`, `js-yaml`, `remark` / `rehype`.
- **CI**: GitHub Actions. `gh` CLI for release artifact download. (M3) `@axe-core/playwright` or `pa11y-ci` for accessibility gate.
- **Hosting**: GitHub Pages (or Cloudflare Pages).

## Follow-up Items (not in this spec)

- **Variant selector DSL**: bullet-level inclusion/exclusion, per-variant overrides/rewording. Designed when Jason uploads existing resume versions.
- **Sync enforcement skill**: a `constellize`-style Claude Code skill that checks/enforces CV↔website sync (biblatex sort policy matches website sort, schema compatibility, artifact freshness).
- **Blog engine**: site architecture supports adding later; not in v1.
- **OpenGraph image design**: per-page custom images.

## Open Questions

- **OQ-1**: One `cv-llt.tex` per variant (generated) vs. one shared `cv-llt.tex` parameterized by `\variant`? Recommendation: generate a thin per-variant driver under `build/<variant>/cv-llt.tex`; decide at implementation time.
- **OQ-2**: Are generated `.tex` files committed for Overleaf convenience or strictly gitignored? Spec says gitignored; revisit if Overleaf access becomes useful.
- **OQ-3**: Markdown parser — `markdown-it-py` (full Markdown subset) vs. ~20-line regex converter (just `**bold**`, `*em*`, `` `code` ``). Decide at implementation time.
- **OQ-4**: Visual regression tool — `diff-pdf` vs. `perceptualdiff` vs. rendered-PNG hash. Pick the one easiest in CI. Used as warning, not gate (per review).
- **OQ-5**: Hosting — GitHub Pages vs. Cloudflare Pages. Decide when deploying.
- **OQ-6**: Domain — `djjay0131.github.io`, custom domain, or existing domain? Needed at deploy time.
- **OQ-7**: Submodule pin-bump automation vs. Renovate vs. nightly action — moot now (publish-as-artifact replaces submodule), but data artifact staleness detection strategy TBD.
- **OQ-8**: Pydantic vs. JSON Schema for content validation? Spec leans Pydantic (Python-native, richer errors). Decide at implementation.
- **OQ-9**: Website notification webhook target — Slack, Discord, or email? Configured as a repo secret; decide at M3.
