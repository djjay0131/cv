# Feature: Agentic-Principal Resume Variant

**Status:** IMPLEMENTED
**Date:** 2026-07-27
**Author:** Feature Architect (AI-assisted)

## Problem

Jason is targeting **Principal Agentic Engineer** roles — the immediate instance being
FullStack's remote US posting (LinkedIn 4433881514). The role is a client-facing
consulting position: assess enterprise engineering organizations, define agentic-adoption
roadmaps, defend architecture decisions to CTOs and VPs, and *design development processes
where AI systems generate the majority of implementation code under human validation*.

Hard requirements: 8–10+ years professional development, full-stack architecture
(Java, Python, C#, React, Node, React Native), a Solution Architect or Principal Engineer
track record, and deep fluency with agentic tools (Claude Code, Cursor, Codex, Copilot).
Preferred: structuring codebases for reliable AI output, developer-productivity metrics,
large complex systems, Agile/Scrum, extreme ownership.

No existing variant fits:

1. **`anthropic-fellow`** has the right agentic emphasis but is research-led — it collapses
   Blackbaud and Duck Creek to one-liners, which forfeits exactly the Principal/Solution
   Architect record this role gates on.
2. **`sde-long`** and **`research-professional`** carry the architect record but have no
   agentic spine at all; their summaries lead with Azure/ETL and empirical research
   respectively.
3. **No summary in the pool** frames Jason as an architect who designs agentic development
   processes.
4. **No skills group** covers agentic tooling. `skills.yaml` has no Claude Code, no MCP,
   and — despite ~106 React components across seven of Jason's repositories — no React,
   React Native, TypeScript, or Next.js.
5. **No employment bullets** describe the *method*: the pool documents agentic
   **outputs** (Claude-built systems) but never the spec-driven workflow, the validation
   gates, or the enablement of other engineers in that practice.

## Goals

- **G1**: A new `agentic-principal` variant — agentic spine threaded through an expanded
  architect body. PhD research present as methodological credibility, not as the lead.
- **G2**: New pool content, all of it verified against Jason's own repositories or
  confirmed directly by him: an `agentic-principal` summary, an `agentic` skills group,
  React/React Native/TypeScript/Next.js in `languages`, and new employment bullets for
  agentic team leadership, spec-driven validation gates, GenAI-evaluation research, and
  mentorship.
- **G3**: Publications render **after** Projects and Skills for this variant, so the
  agentic project portfolio lands before the academic record.
- **G4**: `make agentic-principal` renders and compiles to a two-page PDF.
- **G5**: No regression — `academic`, `sde-long`, `research-professional`, and
  `anthropic-fellow` produce byte-identical PDFs.

## Non-Goals

- **NG1**: Claiming unverified skills. React and React Native are included only because
  they are evidenced in the repositories (below). Nothing is listed that Jason has not used.
- **NG2**: Per-variant bullet rewording. Following `variant-selector-dsl.md` NG2, new
  phrasings become new bullet IDs in the pool.
- **NG3**: A global change to publications placement. See "Design Approach — publications
  ordering" for why existing variants are pinned instead.
- **NG4**: Employer-specific naming. The variant is named for the role class so it is
  reusable across the Principal Agentic Engineer market.

## Evidence Base

### React / React Native — verified by repository scan (2026-07-27)

A scan of all 43 repositories under `~/code` found React in seven applications:

| Repository | Stack | `.tsx`/`.jsx` files |
|---|---|---|
| `holiday-social/src/frontend` | React Native 0.73.2, React Navigation, Maps, AsyncStorage | 31 |
| `baseball-ai` | React 19, Next 16, Tailwind 4, TypeScript 5.9 | 29 |
| `agentic-kg/packages/ui` | React 18, Next 14, React Query, react-force-graph-2d | 14 |
| `my.tv` | React 19, Next 16, Tailwind 4 | 12 |
| `holiday-social/src/admin-dashboard` | React 18, React Router, Headless UI, Vite | 10 |
| `construction-ai/frontend` | React 18, react-three-fiber, React Query, React Router | 8 |
| `cs6604-trafficsafety/frontend` | React 18, Vite, TypeScript | 2 |

`holiday-social/src/frontend` is a genuine React Native mobile application, not a web
shim — it carries native navigation, maps, gesture-handler, reanimated, and mobile-ads
dependencies.

### Agentic toolchain — confirmed by Jason

Jason has used **Cursor**, **OpenAI Codex**, and **GitHub Copilot** in practice, and
moved off all three for stated reasons: Cursor and Codex were too resource-intensive and
too interventionist; Copilot underperformed Claude. He standardized on **Claude Code at
the command line**, using GPT to assist in prompt construction.

This is treated as a strength rather than a gap. Evaluating a tool category in practice
and defending a standardization decision is precisely what the role asks a principal to
do with client engineering leadership, so the evaluation appears in the summary rather
than being flattened into an undifferentiated tool list.

### Enablement — confirmed by Jason

| Setting | Substance |
|---|---|
| Virginia Tech | Supervising an undergraduate researcher on `agentic-kg`: evaluation testing, ground-truth development, and literature organization and review |
| Yoh | Led a **senior technical team** on the Insurance Data Ingestion Platform |
| Blackbaud | Mentored offshore engineers and team members while owning the enterprise conversion tools |
| LimeLeap | Hired from campus and developed talent across Team Leader → Manager → Director |

The LimeLeap talent-development record is acknowledged but **not surfaced** in this
variant — LimeLeap stays collapsed, conveying progression through its title list only.
Early-2000s campus hiring is the correct thing to cut for a two-page agentic resume.

## Design Approach

### Variant shape

`refined-serif` theme, photo off, two-page target — matching the senior, non-academic
register of `anthropic-fellow` and `research-professional`.

```
SUMMARY
EMPLOYMENT   VT Doctoral Researcher .......... 2 bullets
             Yoh ADF Solution Architect ...... 4 bullets
             Duck Creek Sr Technical Architect 4 bullets
             Blackbaud Principal Engineer .... 3 bullets
             Blackbaud Solution Architect .... 3 bullets
             DJJayNet + LimeLeap ............. collapsed
EDUCATION
PROJECTS     4 agentic entries
SKILLS       agentic → languages → tools → ai-ml → platforms
PUBLICATIONS
```

The Miscellaneous section is dropped. CSSLP and Certified Scrum Master survive inline in
the summary — the same technique `anthropic-fellow` uses to hold two pages, and it also
covers the JD's Agile/Scrum preferred qualification without spending six lines on an
awards block.

### Publications ordering

`cv-llt.tex:110` hardcodes `\input{publications}` between Education and Projects. This
variant needs Publications last.

Considered and rejected: deriving placement from the position of `type: publications`
in the variant's `sections` list. It is the cleaner data model, but `sde-long` and
`research-professional` already *declare* projects before publications while *rendering*
publications early — so making the renderer honor declared order would silently change
two of Jason's existing PDFs.

Adopted instead: emit a `\cvpubslate` flag from an explicit `publications_late` boolean
on the variant, defaulting false. `agentic-principal` sets it true; every existing
variant is untouched and byte-identical. The declaration is explicit rather than
positional, which suits a field that changes rendering order.

### New pool content

**`summaries.yaml` — `agentic-principal`**: opens on the two-decade architect record,
pivots to agentic process design, closes with the PhD as the reason the method is
trustworthy rather than as an academic credential. Carries CSSLP and Scrum Master inline,
and states the toolchain evaluation.

**`skills.yaml`**:
- New `agentic` group (rendered first): Claude Code, Claude API, MCP, agent orchestration,
  spec-driven development, LLM evaluation, Cursor, OpenAI Codex, GitHub Copilot, RAG,
  knowledge graphs.
- `languages` gains React, React Native, TypeScript, Next.js — placed here following the
  existing precedent that `Vue.js` and `Node.js` live in `languages`.
- `tools` gains Tailwind CSS, Vite, Neo4j, Google Cloud, Terraform.

**`employment.yaml` — new bullet IDs**:

| ID | Role | Substance |
|---|---|---|
| `vt-research-genai-evidence` | VT Doctoral | ICSE 2026 + arXiv work framed as empirical evaluation of GenAI coding tools — the JD's process-design question asked academically |
| `vt-mentoring-agentic-kg` | VT Doctoral | Supervising an undergraduate researcher: evaluation testing, ground truth, literature review |
| `yoh-mvp-senior` | Yoh | `yoh-mvp` restated with the accurate senior-technical-team framing |
| `yoh-agentic-team` | Yoh | Established the LLM-assisted conventions the team worked under |
| `yoh-spec-gates` | Yoh | Spec-first → agent-implements → tests-as-gate, with complex transformation logic hand-implemented and reviewed |
| `bb-offshore-mentoring` | Blackbaud Principal | Mentored offshore engineers while owning the enterprise conversion tools |

**`projects.yaml` — `cv-pipeline`**: this repository as the public, inspectable exhibit of
a codebase structured for reliable agentic output — YAML content pool, strict Pydantic
schemas, Jinja template contracts, and pytest gates, so an agent can author a new resume
variant without touching rendering logic.

### Project selection

1. `remote-robotics-control` — solo cloud-and-edge architecture, LLM-assisted throughout
2. `llm-data-importer` — insurance domain, matching the JD's regulated-industry emphasis
3. `vttsi` — grounding guardrails and deterministic fallback: reliability engineering for
   LLM output, the JD's "structure codebases to optimize AI output reliability"
4. `agentic-kg` — multi-agent orchestration (Navigator / Extractor / Continuation)

`cv-pipeline` and `construction-ai` are added to the pool and available but held out of
the four to protect the two-page budget.

### Pool growth leaks into existing variants (discovered during implementation)

A variant that includes a role or skill group *without* a filter means "include
everything," so any addition to the shared pool silently propagates into every such
variant. Adding the agentic bullets and React/Terraform skills changed all four existing
resumes: `academic` and `research-professional` gained three Yoh bullets plus
`bb-offshore-mentoring` and nine skill items, `sde-long` gained the Yoh bullets, and
`anthropic-fellow` — the resume submitted today — gained two VT bullets. `yoh-mvp-senior`
also rendered alongside the `yoh-mvp` it restates.

Fix: pin the affected roles and skill groups in the four existing variants to explicit
lists reproducing their current output, following the precedent `sde-long` already sets.
Verified by rendering every variant from a detached worktree at `HEAD` and diffing
fragments — all four are byte-identical apart from the additive `\cvpubslate{false}` line.

This is a structural property of the DSL, not a one-off: any future pool growth will hit
it again. A regression test that renders every variant against a golden fixture would
catch it automatically and is the recommended follow-up.

### Local compile fixed: cabin/cochineal load order (TeX Live 2026)

Local `make <variant>` failed for **every** variant on macOS with TeX Live 2026 —
including variants untouched by this work — so PDF verification had been routing through
CI. Root cause, traced by bisection:

- `cochineal.sty:277` sets a global `\defaultfontfeatures{... Extension = .otf ...}`.
- `cabin.sty:71` overwrites that, then `cabin.sty:123` clears it outright
  (`\defaultfontfeatures{}`, commented "turn off defaults in case other fonts are
  selected").
- Loaded cochineal-first, Cochineal's families lose `Extension = .otf`, so
  `\begin{document}` attempts a bare-name lookup — `Requested font "Cochineal-Roman"
  -> font not found, using "nullfont"` — which XeTeX cannot resolve for a texmf-only
  font. Fatal.

Bisection evidence: cochineal alone compiles; cochineal + cabin fails at any font size
and with any cabin option set; **cabin before cochineal compiles**. `zi4` is not
involved.

Fix: swap the load order in `cv-llt.tex` so cabin precedes cochineal, letting cochineal
establish its defaults last. Only the XeLaTeX/LuaLaTeX branch is changed; the pdfLaTeX
branch uses Type 1 fonts, does not involve fontspec, and is not exercised by the Makefile.

Verified no rendering change: the embedded font set is identical between the
old-compatible order (cochineal + zi4, no cabin) and the new order. The absence of
Inconsolata from the output is **pre-existing and unrelated** — `zi4` loaded alone,
with neither cabin nor cochineal present, also falls back to LMRoman10 on this machine.

All five variants now compile locally: academic 4pp, sde-long 3pp,
research-professional 4pp, anthropic-fellow 2pp, agentic-principal 2pp.

**Follow-up not taken:** CI's visual-regression step (`tests/baselines/<variant>`) has no
committed baselines, so it warns and skips. Baselines generated on TeX Live 2026 locally
would not match CI's pinned TeX Live and would produce false failures, so they must be
generated from a CI run.

## Acceptance Criteria

- **AC-1**: `data/variants/agentic-principal.yaml` exists and validates.
- **AC-2**: `python -m tools.render agentic-principal` renders all fragments with no
  missing-content errors.
- **AC-3**: The rendered summary contains no skill or tool Jason has not used; React and
  React Native appear only as supported by the repository scan above.
- **AC-4**: Publications render after Skills in `agentic-principal`, and before Projects
  in every other variant.
- **AC-5**: `make test` passes, including a new test covering the `publications_late` flag.
- **AC-6**: `make academic`, `make sde-long`, `make research-professional`, and
  `make anthropic-fellow` produce unchanged output.
- **AC-7**: The compiled `agentic-principal` PDF is two pages.

## Technical Notes

- **Modified**: `tools/schema.py` (`publications_late` on `Variant`), `tools/render.py`
  (`_render_theme` emits `\cvpubslate`), `cv-llt.tex` (two conditional publication slots),
  `data/content/summaries.yaml`, `data/content/skills.yaml`,
  `data/content/employment.yaml`, `data/content/projects.yaml`.
- **New**: `data/variants/agentic-principal.yaml`, a `tools/tests` case for the flag.
- **Unchanged**: `tools/resolver.py`, all templates, all existing variant files,
  `settings.sty`, `themes/refined-serif.sty`.
- Local compilation is expected to fail at the Cochineal font-cache step on this macOS
  machine; PDF verification routes through CI per established practice.

## Open Questions

- **OQ-1**: Whether to swap `agentic-kg` for `cv-pipeline` in the project four. The KG
  project is heavier research; the CV pipeline is a more literal answer to the JD's
  codebase-structuring ask. Recommendation: keep `agentic-kg`, mention the pipeline in
  conversation. Decide after seeing the compiled page break.
