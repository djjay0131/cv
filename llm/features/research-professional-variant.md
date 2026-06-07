# Feature: Research-Professional Resume Variant + Per-Variant Theming

**Status:** SPECIFIED
**Date:** 2026-05-19
**Author:** Feature Architect (AI-assisted)

## Problem

Jason needs a new resume variant — "research-professional" — for industry research / R&D
roles. It should carry the same content as the `academic` variant but **drop the photo**
and adopt a cleaner, more modern visual treatment ("refined serif": Cochineal serif body
kept, the curve-class swish underlines replaced by flat thin rules, a single restrained
navy accent instead of the maroon + olive pair, serif small-caps section headings).

The current pipeline cannot express this:

1. **Photo is global.** `cv-llt.tex` hardcodes `\includecomment{fullonly}`; the
   `\photo[r]{photo_jason_1}` block is shown for every variant. There is no per-variant
   toggle.
2. **Visual theme is global.** `settings.sty` hardcodes the swish rubric head
   (`\@@rubrichead`, a TikZ gradient rectangle) and the two accent colors
   (`SwishLineColour` `#88AC0B`, `MarkerColour` `#B6073F`). Every variant compiled from
   `cv-llt.tex` looks identical.
3. **CI builds only `academic`.** `.github/workflows/build-cv.yml` renders, compiles, and
   publishes `academic.pdf` only. A second (or third) variant produces no artifact.
4. **No variant index.** The website exposes individual CVs at `/cv/<variant>` but has no
   page that lists the available resume variants for a visitor to browse and download.

The `academic` variant must keep its **current** look exactly (photo + maroon/olive +
swish) — so this is a *per-variant theming* problem, not a global restyle.

## Goals

- **G1**: A per-variant theming mechanism: each variant declares a `theme` (visual style
  + photo on/off). `cv-llt.tex` and the renderer honor it. Default theme reproduces
  today's look so `academic.yaml` needs no change.
- **G2**: A `refined-serif` theme: Cochineal serif body retained, swish rubric head
  replaced by a flat thin rule, single navy accent (`#22364F`) replacing
  `SwishLineColour`/`MarkerColour`, serif small-caps section headings.
- **G3**: A new `research-professional` variant: same section set as `academic`
  (summary → employment → education → projects → publications → skills → misc → referee),
  a **new research-tuned summary**, `refined-serif` theme, photo off.
- **G4**: `make research-professional` compiles a clean PDF with no photo and the
  refined-serif theme; `make academic` still produces its current PDF unchanged.
- **G5**: CI builds **all** variants in `data/variants/` (`academic`,
  `research-professional`, `sde-long`) and publishes every PDF to the `latest` release.
- **G6**: A website `/resumes` index page lists every variant with a human label,
  one-line description, a "View" link to `/cv/<variant>`, and a "Download PDF" link.

## Non-Goals

- **NG1**: Restyling the `academic` or `sde-long` variants. They keep the `classic`
  theme verbatim. No regression is the bar.
- **NG2**: Per-variant summary *authoring* in the selector YAML. The research summary is
  a new entry in the shared `summaries.yaml` pool, selected by `content_id` — consistent
  with the existing DSL (NG1 of `variant-selector-dsl.md`).
- **NG3**: Applying the refined-serif look to the **website** rendering. The website
  keeps its own CSS; `/cv/research-professional` renders with site styling. The
  refined-serif theme is a PDF/LaTeX concern only.
- **NG4**: A *user-authored* theme DSL. The named-theme mechanism is intentionally
  extensible — additional named themes (e.g., `refined-serif-dark`, `compact`) can be
  added later by committing a new `themes/<name>.sty` and extending the `Literal`
  set. What is out of scope is letting variants compose arbitrary theme settings
  (fonts, colors, spacing, rule styles) inline in their YAML.
- **NG5**: Moving the CV detail routes from `/cv/<variant>` to `/resumes/<variant>`.
  The index lives at `/resumes`; detail pages stay at `/cv/<variant>` (see OQ-1).
- **NG6**: Hard page-count enforcement. The variant should be concise, but no CI gate on
  page count.
- **NG7**: Auto-upgrading the LaTeX class/package set or auto-fixing breakage from
  upstream `curve.cls` changes. CI **detects** breakage (guard macro + visual-regression
  diff) and **fails loud**; a human or LLM-assisted change resolves it. CI does not
  silently rewrite the theme. TeXLive is pinned via the `xu-cheng/latex-action` image
  tag so upgrades are deliberate, not surprise.

## User Stories

- As Jason, I want a research-focused resume with no photo and a cleaner look, so I can
  apply to industry research / R&D roles with an artifact that reads as modern.
- As Jason, I want the `academic` variant untouched, so my existing CV link keeps
  working and looking the same.
- As Jason, I want to declare a variant's theme in its YAML file, so creating future
  styled variants is a data change, not a LaTeX edit.
- As a visitor, I want a single page listing all of Jason's resume variants with view +
  download links, so I can pick the one relevant to my context.
- As Jason, I want CI to build and publish every variant automatically, so adding a
  variant file is all it takes to get a published PDF.

## Design Approach

### A. Per-variant theming (`cv` repo)

**Schema (`tools/schema.py`).** A new `VariantTheme` model and three new optional fields
on `Variant`:

```python
from typing import Literal

class VariantTheme(_StrictModel):
    style: Literal["classic", "refined-serif"] = "classic"
    photo: bool = True

class Variant(_StrictModel):
    variant: str = Field(min_length=1)
    extends: Optional[str] = None
    label: Optional[str] = None          # human title for the /resumes index
    description: Optional[str] = None    # one-line blurb for the /resumes index
    theme: VariantTheme = Field(default_factory=VariantTheme)
    sections: list[VariantSection] = Field(min_length=1)
    raw_overrides: dict[str, RawOverride] = Field(default_factory=dict)
```

`theme` defaults to `classic` + `photo: true`. `Literal` makes an unknown `style` fail
loud at load time. `academic.yaml` and `sde-long.yaml` need no `theme` block (default
reproduces today's behavior) — but `label`/`description` are added to all three for G6.

**Renderer (`tools/render.py`).** Emit a new `_theme.tex` fragment next to the existing
`_preamble.tex`, derived from the variant's `theme`:

```python
def _render_theme(variant: Variant) -> str:
    photo = "true" if variant.theme.photo else "false"
    return f"\\def\\cvtheme{{{variant.theme.style}}}\n\\def\\cvphoto{{{photo}}}\n"
# render(): (output_dir / "_theme.tex").write_text(_render_theme(variant), "utf-8")
```

`render()` already holds the `variant` object, so no signature change is needed.

**`cv-llt.tex`.** Replace the hardcoded `\includecomment{fullonly}` line. After
`\usepackage{settings}`:

```latex
\input{build/\cvvariant/tex/_theme}                         % defines \cvtheme, \cvphoto
\ifdefstring{\cvtheme}{refined-serif}{\usepackage{themes/refined-serif}}{}
\ifdefstring{\cvphoto}{false}{\excludecomment{fullonly}}{\includecomment{fullonly}}
```

`\ifdefstring` is provided by `etoolbox` (already pulled in by `curve.cls`). `classic`
loads no extra package — byte-identical to today. `\excludecomment{fullonly}` drops the
existing `\photo[r]{...}` block with no further edits.

**New file `themes/refined-serif.sty`.** Loaded *after* `settings.sty`, so its
`\renewcommand` / `\definecolor` win. `.sty` files treat `@` as a letter, so the
curve-internal `\@@rubrichead` is editable directly. The theme uses **two** colors:
navy for structural accents (headings, header icons, circled bib numbers) and a
muted grey for inline body accents (bullet prefix, DOI/URL link glyphs) so the body
stays calm and the eye goes to structure, not dots. A guard fails loud if curve
ever renames the internal we depend on:

```latex
\ProvidesPackage{themes/refined-serif}[2026/05/19 refined serif CV theme]
% Fail loud if curve.cls renames its private rubric-head macro — better than
% silently emitting broken output. EC-11 / NG7.
\ifdefined\@@rubrichead\else
  \PackageError{themes/refined-serif}%
    {curve internal \string\@@rubrichead\space missing -- theme needs updating}%
    {curve.cls may have been updated; the refined-serif theme's section-head
     override depends on this internal. Patch the theme to track the new API.}%
\fi
% Single restrained navy accent for STRUCTURAL elements:
% section heading rule + heading text, header contact icons, circled bib numbers.
\definecolor{SwishLineColour}{HTML}{22364F}
\definecolor{MarkerColour}{HTML}{22364F}
% Muted neutral grey for INLINE BODY accents:
% bullet prefix marker, DOI/URL link glyphs in the publication list.
\definecolor{MarkerMutedColour}{HTML}{555555}
% Serif small-caps section headings (drop \sffamily from the classic rubricfont).
\rubricfont{\large\bfseries\scshape}
\subrubricfont{\normalsize\scshape}
% Replace the gradient "swish" rubric head with a flat thin rule.
\renewcommand\@@rubrichead[1]{%
  {\@rubricfont\color{MarkerColour}#1}\par\vskip 1.5pt
  {\color{MarkerColour}\hrule height 0.6pt}%
  \vspace\rubricspace%
}
% Re-tint inline body accents to the muted grey (overrides settings.sty defaults).
\prefix{\hspace*{-1ex}\color{MarkerMutedColour}\@prefixmarker\hspace*{1ex}}
% DOI/URL link glyphs: override the field formats from settings.sty to use the
% muted color. Exact \DeclareFieldFormat / \xpretofieldformat patch chosen at
% integration time.
```

`MarkerColour` (navy) flows through `\makefield` (header icons) and `\circled` (bib
numbers) automatically — no extra edits. The `\prefix` and bib-link recoloring above
re-routes only the inline body accents to the muted grey.

### B. New `research-professional` variant (`cv` repo)

**New summary** appended to `data/content/summaries.yaml` (id `research-professional`):

> Computer Science PhD candidate and applied researcher who bridges large-scale software
> engineering with empirical AI/ML research. Two decades architecting Azure data
> platforms and SaaS systems now grounds research that is reproducible, deployable, and
> measured against real workloads, spanning LLM-assisted software engineering, security
> classification, and mechanistic interpretability. Published at ICSE 2026, with
> hands-on depth in ML pipelines, evaluation design, and the engineering rigor that
> industry R&D depends on.

**New file `data/variants/research-professional.yaml`** — same section set, roles,
education, projects, and skills as `academic.yaml`; `refined-serif` theme; photo off:

```yaml
variant: research-professional
label: "Research Professional"
description: "Research-focused resume for industry R&D and applied-research roles."
theme:
  style: refined-serif
  photo: false

sections:
  - type: summary
    content_id: research-professional
  - type: employment
    include:
      - vt-gra-mrs
      - yoh-adf-architect
      - duck-creek-architect
      - blackbaud-principal
      - blackbaud-solutions
      - djjaynet-consultant
  - type: education
    include: [phd-cs-vt, meng-cs-vt, bs-econ-vt]
  - type: projects
    include: [llm-coding-assistant, security-classifier, sentiment-yelp, nfl-ml]
  - type: publications
  - type: skills
    include: [platforms, tools, languages, ai-ml]
  - type: misc
  - type: referee
    content_id: available
```

`academic.yaml` and `sde-long.yaml` each gain a `label` + `description` (and no `theme`
block — they stay `classic`).

### C. Build & publish all variants (`cv` repo)

**Makefile.** Replace the hardcoded `VARIANTS := academic` with auto-discovery:

```makefile
VARIANTS := $(basename $(notdir $(wildcard data/variants/*.yaml)))
```

`make all` then builds every variant; `make <variant>` still works per-variant.

**CI (`.github/workflows/build-cv.yml`).** The `build` job currently renders/compiles/
publishes `academic` only. Change it to iterate every variant. A shell loop over the
discovered variant slugs (render → compile via `latexmk -xelatex` with the per-variant
`-usepretex`/`-jobname` → collect `dist/<variant>.pdf`). All PDFs plus `cv-data.zip` are
uploaded as workflow artifacts and attached to the `latest` release. (A matrix is an
alternative but complicates the single-release-update step; a loop in one job keeps the
release write atomic — see OQ-3.) `halt-on-error` per compile + the loop failing the
whole job on any error guarantees no partial release.

**Visual-regression step (new).** After each variant compiles, CI rasterizes the new
PDF to per-page PNGs (e.g., `pdftoppm -r 150`) and diffs them page-by-page against a
committed baseline at `tests/baselines/<variant>/page-N.png`. Non-zero pixel diff
above a small tolerance fails the build. This is the actual proof of AC-4 (no
`academic` regression) and the structural guard for the curve-internal override:
if a future `curve.cls` update changes the swish-head rendering, the diff catches it
even when the guard macro does not.

### D. `/resumes` index page (`website` repo)

The website auto-discovers variants from `data/variants/*.yaml` (`listVariants`). The
index page reads each variant's `label` + `description`:

- **New `src/lib/cv-data.ts` helper** `loadVariantSummaries(dir)` → returns
  `{ slug, label, description }[]`, parsing each variant YAML; falls back to a titleized
  slug when `label` is absent.
- **New page `src/pages/resumes/index.astro`** — renders the list: each entry shows the
  label, description, a "View" link to `${base}cv/<slug>`, and a "Download PDF" link to
  `${base}pdfs/<slug>.pdf`.
- **Nav** — add a "Resumes" link in `Base.astro`'s navigation.
- **PDF availability** — the website build already pulls the `cv` `latest` release;
  it must place every `<variant>.pdf` under `pdfs/`. With C publishing all PDFs, this is
  a build-step glob rather than a hardcoded `academic.pdf` copy.

## Sample Implementation

```python
# tools/schema.py — new theme model + variant fields
from typing import Literal

class VariantTheme(_StrictModel):
    style: Literal["classic", "refined-serif"] = "classic"
    photo: bool = True

class Variant(_StrictModel):
    variant: str = Field(min_length=1)
    extends: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    theme: VariantTheme = Field(default_factory=VariantTheme)
    sections: list[VariantSection] = Field(min_length=1)
    raw_overrides: dict[str, RawOverride] = Field(default_factory=dict)
```

```python
# tools/render.py — emit _theme.tex alongside _preamble.tex
def _render_theme(variant: Variant) -> str:
    photo = "true" if variant.theme.photo else "false"
    return f"\\def\\cvtheme{{{variant.theme.style}}}\n\\def\\cvphoto{{{photo}}}\n"

# inside render(), after writing _preamble.tex:
(output_dir / "_theme.tex").write_text(_render_theme(variant), encoding="utf-8")
```

```latex
% cv-llt.tex — replaces the hardcoded \includecomment{fullonly}
\usepackage{settings}
\input{build/\cvvariant/tex/_theme}
\ifdefstring{\cvtheme}{refined-serif}{\usepackage{themes/refined-serif}}{}
\ifdefstring{\cvphoto}{false}{\excludecomment{fullonly}}{\includecomment{fullonly}}
```

```jsx
// website src/pages/resumes/index.astro — variant index
---
import Base from "../../layouts/Base.astro";
import { loadVariantSummaries } from "../../lib/cv-data";
import path from "node:path";
const base = import.meta.env.BASE_URL;
const variants = loadVariantSummaries(path.resolve("data/variants"));
---
<Base title="Jason Cusati — Resumes" description="Resume variants by Jason Cusati.">
  <h1>Resumes</h1>
  {variants.map((v) => (
    <div class="resume-entry">
      <h2>{v.label}</h2>
      <p>{v.description}</p>
      <div class="resume-links">
        <a href={`${base}cv/${v.slug}`}>View</a>
        <a href={`${base}pdfs/${v.slug}.pdf`}>Download PDF</a>
      </div>
    </div>
  ))}
</Base>
```

## Edge Cases & Error Handling

### EC-1: Variant with no `theme` block
- **Scenario**: `academic.yaml` / `sde-long.yaml` have no `theme:` key.
- **Behavior**: `theme` defaults to `classic` + `photo: true`; `_theme.tex` emits
  `\def\cvtheme{classic}\def\cvphoto{true}`; `cv-llt.tex` loads no extra package and
  includes the photo. Output byte-identical to today.
- **Test**: Render `academic`; assert `_theme.tex` content; assert no theme package
  loaded. Golden-compare the `academic` `.tex` fragments to pre-change output.

### EC-2: Unknown `theme.style` value
- **Scenario**: A variant sets `theme: {style: brutalist}`.
- **Behavior**: Pydantic `Literal` rejects it at `load_variant`; error names the file and
  the bad value.
- **Test**: Fixture variant with bad style; assert `ValueError` mentions the file.

### EC-3: `photo: false` with `style: classic`
- **Scenario**: A classic-themed variant turns the photo off.
- **Behavior**: Allowed — photo and style are independent. Classic look, no photo.
- **Test**: Fixture variant `classic` + `photo: false`; assert `\cvphoto{false}` emitted.

### EC-4: `_theme.tex` missing at compile time
- **Scenario**: `cv-llt.tex` `\input`s `_theme` but `tools.render` was not run.
- **Behavior**: `latexmk` fails with a missing-file error naming `_theme`. The renderer
  always writes the file, so this only occurs on a stale/partial build dir.
- **Test**: Covered indirectly — the Makefile runs `render` before `latexmk`.

### EC-5: refined-serif body accents — two-color split
- **Scenario**: `research-professional` includes `publications` and bulleted role
  experience; both biblatex circled markers and `\prefix` bullet markers exist.
- **Behavior**: `MarkerColour` (navy) drives circled bib numbers and the header
  contact icons — restrained structural accent. `MarkerMutedColour` (grey) drives
  the inline bullet `\prefix` and DOI/URL link glyphs — body stays calm. White-on-
  navy circles stay legible; grey body marks read as neutral structure, not color.
- **Test**: Compile `research-professional`; visually confirm circles are navy,
  bullet prefixes and DOI link glyphs are grey, contact icons are navy.

### EC-6: Variant missing `label` / `description`
- **Scenario**: A variant file omits `label`.
- **Behavior**: `loadVariantSummaries` falls back to a titleized slug
  (`research-professional` → "Research Professional"); `description` falls back to "".
- **Test**: Vitest with a variant fixture lacking `label`; assert the fallback title.

### EC-7: New variant added later
- **Scenario**: A future `data/variants/foo.yaml` is committed.
- **Behavior**: Makefile `wildcard` discovers it, CI builds `foo.pdf`, `/resumes` lists
  it, `/cv/foo` renders it — all with no further code change.
- **Test**: Add a throwaway fixture variant in a test; assert it is discovered.

### EC-8: One variant fails to compile in CI
- **Scenario**: `sde-long` (built in CI for the first time) hits a LaTeX error.
- **Behavior**: The CI loop must `halt-on-error` and fail the whole job — no partial
  release where some PDFs are stale. The release update is a single step after all
  compiles succeed.
- **Test**: N/A in unit tests; enforced by CI step ordering (compile-all → publish-once).

### EC-9: `/resumes` lists a variant whose PDF is not in the artifact
- **Scenario**: The website builds before the `cv` release has the new PDF.
- **Behavior**: "View" (HTML) still works; "Download PDF" 404s until the release
  catches up. Acceptable transient; G5 ensures CI publishes all PDFs on every push.
- **Test**: N/A — cross-repo timing; documented, not gated.

### EC-10: `make academic` no-regression
- **Scenario**: After the theming change, the `academic` PDF must be unchanged.
- **Behavior**: `classic` path loads no theme package; `\includecomment{fullonly}` keeps
  the photo. Only addition is the `\input{_theme}` line, which defines two macros and
  emits nothing visible.
- **Test**: Visual-regression pixel-diff of the new `academic` PDF against the
  committed pre-change baseline must be zero (see AC-4 and AC-11). The `.tex`
  fragments themselves are also byte-identical to today — a complementary check but
  not the primary guarantee.

### EC-11: curve internal `\@@rubrichead` renamed or removed upstream
- **Scenario**: A future `curve.cls` update renames or removes the private
  `\@@rubrichead` macro that `themes/refined-serif.sty` overrides.
- **Behavior**: The `\ifdefined\@@rubrichead` guard raises `\PackageError` naming
  the missing macro and the theme file to patch. CI fails loud with that error
  instead of producing broken output. The visual-regression step provides a second
  line of defense: even a *redefined* (not just missing) internal would surface as a
  non-zero pixel diff.
- **Test**: Unit-style: render a fixture document with `\let\@@rubrichead\undefined`
  before loading the theme; assert the error message contains "`\@@rubrichead`" and
  "refined-serif".

## Prerequisites

### P1: validate and baseline `sde-long`
`data/variants/sde-long.yaml` was authored in the variant-DSL feature but has never
been compiled end-to-end. Before the CI changes in G5/AC-7/AC-11 land, `make sde-long`
must succeed locally, any LaTeX errors must be fixed (touching the variant file or the
content pool as needed), and a visual baseline must be committed at
`tests/baselines/sde-long/`. Without this, the multi-variant CI gate would go red on a
never-validated variant the first time it runs — failing master CI for reasons
unrelated to this feature.

### P2: commit pre-change `academic` baseline
Before any theming code lands on master, render the *current* `academic.pdf` and
commit per-page PNGs to `tests/baselines/academic/`. AC-4 / AC-11 use this as the
anchor for the "no regression" guarantee. Once landed, the baseline can only be
updated by an intentional, reviewed change.

## Acceptance Criteria

### AC-1: Per-variant theme schema
- **Given** `tools/schema.py`
- **When** a variant declares `theme: {style: refined-serif, photo: false}`
- **Then** it loads into a `VariantTheme`; an unknown `style` fails loud with the file
  name; a variant with no `theme` defaults to `classic` + `photo: true`.

### AC-2: Theme fragment emission
- **Given** `tools.render research-professional`
- **When** rendering completes
- **Then** `build/research-professional/tex/_theme.tex` contains
  `\def\cvtheme{refined-serif}` and `\def\cvphoto{false}`.

### AC-3: refined-serif theme renders
- **Given** `themes/refined-serif.sty`
- **When** `make research-professional` compiles
- **Then** the PDF has no swish (flat thin navy rule under headings), navy accent
  throughout, serif small-caps headings, Cochineal serif body, and **no photo**.

### AC-4: academic no-regression (visual baseline)
- **Given** `data/variants/academic.yaml` (no `theme` block) and a committed pre-change
  baseline of the academic PDF rasterized to per-page PNGs at a fixed DPI under
  `tests/baselines/academic/`
- **When** `make academic` compiles and CI rasterizes the new PDF at the same DPI
- **Then** the page-by-page pixel-diff against the baseline is zero (or below a small
  tolerance for font-rasterization noise, set on the first baseline run). This — not
  a `.tex`-fragment compare — is the binding regression check.

### AC-5: new research-professional variant
- **Given** `data/variants/research-professional.yaml` and the new `summaries.yaml` entry
- **When** the variant is rendered
- **Then** it contains the research-tuned summary and the same section set as `academic`
  (summary, employment ×6, education, projects, publications, skills, misc, referee).

### AC-6: Makefile builds all variants
- **Given** the auto-discovering `VARIANTS`
- **When** `make all` runs
- **Then** `academic`, `research-professional`, and `sde-long` each compile to
  `build/<variant>/<variant>.pdf`.

### AC-7: CI publishes all variant PDFs
- **Given** `.github/workflows/build-cv.yml`
- **When** the workflow runs on `master`
- **Then** `academic.pdf`, `research-professional.pdf`, and `sde-long.pdf` are all
  attached to the `latest` release and uploaded as workflow artifacts.

### AC-8: /resumes index page
- **Given** the website with the `cv` data artifact
- **When** `/resumes` is built
- **Then** it lists every variant with its `label`, `description`, a working "View" link
  to `/cv/<variant>`, and a "Download PDF" link to `/pdfs/<variant>.pdf`.

### AC-9: variant metadata fallback
- **Given** a variant file with no `label`
- **When** `/resumes` renders
- **Then** the entry shows a titleized slug instead of crashing.

### AC-10: tests and lint pass
- **Given** the full change set
- **When** `pytest` and `ruff check` run in the `cv` repo and `vitest` + `astro check`
  run in the `website` repo
- **Then** all pass, including new tests for `VariantTheme`, `_render_theme`,
  `loadVariantSummaries`, and the curve-internal guard (EC-11).

### AC-11: visual-regression CI step
- **Given** committed baselines for every variant under `tests/baselines/<variant>/`
  (page-by-page PNGs at a fixed DPI)
- **When** the CI build job runs after compiling each variant
- **Then** a rasterize-and-diff step compares the new PDF pages against the baseline.
  Non-zero diff above tolerance fails the job. `academic` must diff to zero (proves no
  regression and detects curve-class drift); `research-professional` and `sde-long`
  baselines are established once (committed as part of this feature) and re-asserted
  on every subsequent push.

### AC-12: small-caps manual verification (one-shot)
- **Given** the first successful compile of `research-professional.pdf`
- **When** Jason reviews the rendered section headings
- **Then** the small caps must be **designed Cochineal small-caps** (real OpenType
  `smcp` glyphs), not faked geometric scaling of full-size caps. If they render as
  faked, `themes/refined-serif.sty` is updated to load Cochineal via fontspec with
  explicit small-caps features (e.g., `\setmainfont[SmallCapsFeatures={Letters=SmallCaps}]
  {Cochineal}` or the cochineal-package equivalent) before AC-3 is signed off. This is
  a one-shot human check at first compile; once confirmed, the visual-regression step
  (AC-11) protects against drift.

## Technical Notes

### Affected components

**`cv` repo**
- **Modified**: `tools/schema.py` (`VariantTheme`, `label`/`description`/`theme` on
  `Variant`), `tools/render.py` (`_render_theme`, write `_theme.tex`), `cv-llt.tex`
  (conditional theme load + photo), `Makefile` (`VARIANTS` auto-discovery),
  `.github/workflows/build-cv.yml` (build/publish all variants + visual-regression
  step), `data/variants/academic.yaml` + `data/variants/sde-long.yaml` (add `label`/
  `description`), `data/content/summaries.yaml` (new `research-professional` entry).
- **New**: `themes/refined-serif.sty`, `data/variants/research-professional.yaml`,
  `tests/baselines/<variant>/` (per-variant page PNGs), a script (or CI step) that
  rasterizes PDFs and pixel-diffs against baselines, a guard-macro unit test fixture
  for EC-11.
- **Unchanged**: `tools/resolver.py`, `tools/converters.py`, `tools/lint_bib.py`,
  `settings.sty` (theme overrides happen in the theme `.sty`, not here).

**`website` repo**
- **Modified**: `src/lib/cv-data.ts` (`loadVariantSummaries`), `src/layouts/Base.astro`
  (nav link), website build step (glob all variant PDFs into `pdfs/`).
- **New**: `src/pages/resumes/index.astro`.

### Patterns to follow
- `_StrictModel` (`extra="forbid"`) for `VariantTheme`; `Literal` for the closed `style`
  set, mirroring how the codebase fails loud on bad data.
- `_theme.tex` follows the existing `_preamble.tex` precedent: a renderer-generated
  fragment `\input` before `\begin{document}`.
- Theme `.sty` loaded after `settings.sty` so `\renewcommand` / `\definecolor` win —
  no edits to `settings.sty`, keeping `classic` provably unchanged.
- Website `getStaticPaths`/`listVariants` already enumerate `data/variants/`; the index
  reuses that discovery.

### Data model changes
- `Variant` gains `label`, `description` (optional) and `theme` (`VariantTheme`,
  defaulted). Existing variant files remain valid without edits; `label`/`description`
  are added for presentation.
- New renderer output file per variant: `build/<variant>/tex/_theme.tex`.

## Dependencies

- No new Python or LaTeX packages. `etoolbox` (`\ifdefstring`) and `comment`
  (`\includecomment`/`\excludecomment`) are already loaded via `curve.cls` / `settings.sty`.
- The `website` repo consumes the `cv` `latest` release; G5 (CI publishes all PDFs) is a
  prerequisite for AC-8's "Download PDF" links to resolve.
- Cochineal provides true small caps — required for the refined-serif headings
  (verified by AC-12 on first compile).
- A PDF-rasterization tool in CI (e.g., `poppler-utils` `pdftoppm`) plus an image-
  diff tool (e.g., ImageMagick `compare` or `pixelmatch`) for the visual-regression
  step. TeXLive image is pinned via `xu-cheng/latex-action@v3` to keep `curve.cls`
  reproducible (NG7).

## Open Questions

- **OQ-1**: Move CV detail routes to `/resumes/<variant>` for URL nesting consistency, or
  keep `/cv/<variant>` with the index at `/resumes`? Recommendation: keep `/cv/<variant>`
  now (no broken links), revisit if desired. Deferred.
- **OQ-2**: refined-serif heading size/letterspacing — `\large\bfseries\scshape` is the
  proposed start; exact size and any `\addfontfeature{LetterSpace}` tuning to be settled
  by eye on the first compile.
- **OQ-3**: CI shape — single job with a shell loop over variants (recommended, atomic
  release write) vs. a build matrix (parallel, but needs a separate publish job).
  Decide at implementation.
- **OQ-4**: Should the `/resumes` page mark one variant as "default/recommended"? Decided
  no for now (G6 scope); easy to add a boolean later.
- **OQ-5**: Exact navy hex — `#22364F` proposed; confirm against print contrast on the
  first compiled PDF.
- **OQ-6**: Final wording of the `research-professional` summary — drafted above, subject
  to Jason's review when the draft variant is generated.
