# System Patterns

## Two-Tier YAML Data Model

**Pool** (`data/content/*.yaml`): single source of truth for every fact.
- `meta.yaml` — name, contact, social URLs
- `summaries.yaml` — per-target summary paragraphs (id'd)
- `employment.yaml` — every role ever held, with bullet pool per role
- `education.yaml` — degrees + dates
- `projects.yaml` — project descriptions
- `skills.yaml` — grouped skill items (`ai-ml`, `languages`, `tools`, `platforms`)
- `misc.yaml` — awards, certifications

**Selector** (`data/variants/*.yaml`): one file per variant, picks from the pool.

Example (`anthropic-fellow.yaml`):
```yaml
variant: anthropic-fellow
label: "Anthropic Fellow application"
theme:
  style: refined-serif    # or "classic"
  photo: false
sections:
  - type: summary
    content_id: fellowship           # picks summaries.yaml entry by id
  - type: employment
    include:
      - vt-doctoral-research         # full include, all bullets
      - id: yoh-adf-architect
        bullets: [yoh-llm, yoh-api]  # filter to named bullets
      - id: blackbaud-principal
        collapse: true               # render in "Earlier roles..." paragraph
  - type: skills
    include:
      - ai-ml                        # full group
      - id: languages
        items: [Python, C#, Java]    # subset of items
```

## Variant Selector DSL

Three composable selectors implemented in `tools/resolver.py`:

| Selector | Purpose | Where supported |
|---|---|---|
| `bullets: [id, id]` | Pick named bullets from a role's pool | `employment` |
| `collapse: true` | Render role in single "Earlier roles..." paragraph instead of full block | `employment` |
| `items: [name, name]` | Pick subset of items from a skill group | `skills` |

The resolver lives at `tools/resolver.py:_resolve_employment` (line 95). The rendering for the collapsed paragraph is in `templates/tex/employment.tex.j2` line 24.

## Per-Variant Theming

`Variant.theme.style` selects between:
- `classic` — sans-serif, contemporary, default for industry
- `refined-serif` — Cochineal serif, traditional, used for academic + fellowship variants

`Variant.theme.photo: false` suppresses the headshot in variants where it's culturally inappropriate (US research positions).

Themes are LaTeX preambles included via `templates/tex/_theme.tex` resolved per variant.

## Visual Regression Testing

CI rasterizes each variant's PDF and compares against `tests/baselines/<variant>/page-N.png`:

```bash
pdftoppm -r 150 build/<variant>/<variant>.pdf tests/baselines/<variant>/page -png
compare -metric AE tests/baselines/<variant>/page-N.png dist/<variant>/page-N.png /dev/null
```

**Tolerance:** ~10000 pixels per page. Above that = visual regression failure.

**Critical pattern: "no baseline → warn + skip"** — if `tests/baselines/<variant>/` is missing entirely, the workflow logs a warning and skips the diff. This lets us merge content changes that invalidate baselines, then regenerate from the fresh CI artifact.

When intentionally invalidating a baseline:
1. Delete `tests/baselines/<variant>/` in the same PR as the content change.
2. After merge, download the fresh artifact from the master CI run.
3. Re-rasterize: `pdftoppm -r 150 /tmp/cv-artifacts/variant-<v>/<v>.pdf tests/baselines/<v>/page -png`
4. Commit fresh baseline.

Reference precedent: `d0dfce1` (academic + research-professional baselines refreshed after GRA-date propagation).

## CI / Release / Website Chain

```
cv repo PR → CI: build-cv workflow
  ├── Python tests & lint
  ├── Discover variants
  ├── Compile <each variant>      ← visual regression here
  └── Publish release + cv-data   ← only runs on master, NOT on PRs
       └── (intended) Notify website repo via repository_dispatch

website repo
  ├── Scheduled rebuild (every ~2hr)
  └── workflow_dispatch (manual trigger via gh workflow run build.yml)
       ├── Fetch CV data (scripts/fetch-data.sh — gh release download "latest")
       ├── Run tests (cv-data.test.ts asserts pool shape)
       ├── Build Astro
       ├── Deploy to GitHub Pages
       └── Smoke-test live routes
```

**Known gap:** The cv repo's "Notify website repo" step exists but does NOT actually trigger a website build. Website rebuilds happen only via schedule or manual dispatch. After every cv master release, run `gh workflow run build.yml --repo djjay0131/website` to refresh the site.

## PR Flow Convention

For the Anthropic Fellows initiative, the rule has been **small atomic PRs**, each one reversible:
- PR #2: add anthropic-fellow variant + doctoral-research role + GRA-date fix
- PR #3: trim fellowship summary + de-name mech-interp bullet
- PR #4: drop two weak doctoral-research bullets
- PR #5: rename LimeLeap titles + include in anthropic-fellow

Each PR was squash-merged with `--delete-branch`. Local master is sync'd via `git pull --ff-only origin master` after every merge.

## Where Things Render

| Source file | Renders to |
|---|---|
| `templates/tex/employment.tex.j2` | "Professional Experience" section incl. collapsed paragraph |
| `templates/tex/education.tex.j2` | "Education" section |
| `templates/tex/projects.tex.j2` | "Selected Projects & Research" section |
| `templates/tex/publications.tex.j2` | Pulls from `own-bib.bib` |
| `templates/tex/skills.tex.j2` | "Technical Skills" — AI/ML, Languages, Tools, Platforms |
| `templates/tex/misc.tex.j2` | "Awards" + "Certifications" |

The render entry point is `python -m tools.render <variant>` (positional arg, NOT `--variant`).
