# Tech Context

Last updated: 2026-04-17

## Languages & Formats
- **YAML** — canonical content source (`data/content/*.yaml`, `data/variants/*.yaml`).
- **Python 3.9+** — generator tooling (`tools/`): schema validation (Pydantic), Jinja2 template rendering, Markdown→LaTeX/HTML converters, bib linter.
- **LaTeX** — `curve` document class. Driver: `cv-llt.tex`. Styling: `settings.sty`. Bib: `own-bib.bib` via `biblatex`/`biber`.
- **TypeScript + Astro** — website repo (`djjay0131/website`). Data loading, bib parsing, Markdown→HTML.

## CV Repo (`djjay0131/cv`)

### Build
```bash
make academic          # lint bib → render YAML→tex → latexmk → PDF
.venv/bin/pytest       # 112 tests, 100% coverage
.venv/bin/ruff check . # lint
```

### Python Dependencies
Declared in `pyproject.toml`:
- `pyyaml`, `jinja2`, `pydantic` (>=2.5), `bibtexparser` (>=1.4)
- Dev: `pytest`, `pytest-cov`, `ruff`

### LaTeX Dependencies
- TeX Live / MacTeX with `xelatex`, `biber`, `latexmk`
- Packages: `curve`, `biblatex`, `fontspec`, `cochineal`, `cabin`, `zi4` (Inconsolata), `fontawesome5`, `simpleicons`, `tikz`, `hyperref`

### Structure on Disk
```
cv/
├── cv-llt.tex              # LaTeX driver (\makerubric's generated fragments)
├── settings.sty            # style / package setup (unchanged from Overleaf)
├── publications.tex        # biblatex dispatch (journal/conf/books)
├── own-bib.bib             # single source of truth for publications
├── photo_jason_1.jpeg      # photo asset
├── data/
│   ├── content/            # canonical YAML content pool (each item has stable ID)
│   │   ├── meta.yaml       # name, contact, photo, name_variants
│   │   ├── summaries.yaml
│   │   ├── employment.yaml
│   │   ├── education.yaml
│   │   ├── projects.yaml
│   │   ├── skills.yaml
│   │   ├── misc.yaml
│   │   └── referees.yaml
│   └── variants/
│       └── academic.yaml   # selector: references content pool IDs
├── templates/tex/          # Jinja2 templates → .tex fragments
│   ├── summary.tex.j2
│   ├── employment.tex.j2
│   ├── education.tex.j2
│   ├── projects.tex.j2
│   ├── skills.tex.j2
│   ├── misc.tex.j2
│   └── referee.tex.j2
├── tools/                  # Python generator + linter
│   ├── schema.py           # Pydantic models + content/variant loaders
│   ├── converters.py       # md_to_latex, md_to_html
│   ├── resolver.py         # maps variant selector → content pool items
│   ├── render.py           # orchestrator: load → validate → resolve → render
│   ├── lint_bib.py         # validates own-bib.bib
│   └── tests/              # 112 pytest tests
├── build/                  # gitignored; generated .tex + compiled PDFs
├── Makefile                # `make academic` → lint + render + latexmk
├── .github/workflows/
│   └── build-cv.yml        # CI: lint, test, render, compile, publish release
├── pyproject.toml
└── llm/                    # memory bank + feature specs
```

### CI / Deployment
- GitHub Actions (`build-cv.yml`): on push to master → lint bib → pytest → ruff → render → compile PDF (via `xu-cheng/latex-action` with full TeX Live) → upload PDF + `cv-data.zip` to rolling `latest` release.
- `repository_dispatch` to website repo is wired but gated on `WEBSITE_DISPATCH_PAT` secret.

## Website Repo (`djjay0131/website`)

### Build
```bash
npm test              # 20 vitest tests
npm run build         # 8 Astro pages
```

### Dependencies
- Node 22+, Astro 6+, `@citation-js/core`, `@citation-js/plugin-bibtex`, `js-yaml`, `vitest`, `@astrojs/sitemap`

### Structure
```
website/
├── src/
│   ├── pages/          # index, cv/[variant], papers/, projects/
│   ├── layouts/        # Base.astro (OG, Twitter, JSON-LD, a11y)
│   └── lib/            # cv-data.ts, bib.ts, md.ts + tests
├── public/             # static assets (photo, favicon, PDFs, robots.txt)
├── .github/workflows/
│   └── build.yml       # fetch data → test → build → deploy → smoke test
└── astro.config.mjs    # site + base URL + sitemap
```

### CI / Deployment
- GitHub Actions: on push / `repository_dispatch` / hourly cron → fetch `cv-data.zip` + `academic.pdf` from cv repo's `latest` release → npm test → npm build → deploy to GitHub Pages → smoke test (5 routes).
- Live at https://djjay0131.github.io/website/

## Technical Constraints
- `curve.cls` defines `\makerubric` as `\LTXtable{\linewidth}{...}` — raw `\input` does NOT work; always use `\makerubric` for section files.
- `\mynames` is generated into `build/<variant>/tex/_preamble.tex` from `meta.yaml:name_variants`.
- Python targets 3.9 (system Python on the dev machine); `Optional[X]` syntax used instead of `X | None` for Pydantic compat.
- `@citation-js/core` has no published TypeScript types; custom declarations in `src/lib/citation-js.d.ts`.
