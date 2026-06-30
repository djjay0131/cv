# Project Brief

## What This Project Is

A **data-driven CV/resume generation system** that compiles per-role-targeted PDFs from a shared content pool, plus a companion website that publishes selected variants. The repository owner is **Jason Cusati** (PhD candidate, Virginia Tech CS — SE with AI/ML/MI; 20+ years prior industry experience).

## Two Repositories

- **`djjay0131/cv`** (this repo) — content pool, variant selectors, LaTeX templates, build tooling (`tools/render.py`, `tools/resolver.py`), CI that compiles every variant and publishes a release artifact.
- **`djjay0131/website`** — separate Astro site that fetches the cv repo's latest release and renders `/cv/<variant>` + `/pdfs/<variant>.pdf` routes. Deployed via GitHub Pages.

## Current Major Initiative (2026-06)

Building an **Anthropic Fellows Program 2026 application package**. The fellowship has 4-month duration, ~$3,850/wk + ~$15k/mo compute, ~25-50% convert to full-time. Application administered via Greenhouse; reviewers want a researcher-first CV plus prose answers grounded in concrete artifacts.

**Deliverables in flight:**
- `data/variants/anthropic-fellow.yaml` — fellowship-targeted variant (researcher-first, refined-serif theme, no photo)
- `data/content/summaries.yaml` `fellowship` entry — PhD-candidate-first framing
- `llm/features/anthropic-fellowship-application.md` — spec with full form-answer matrix, prose drafts, references, OQs
- Live at `https://djjay0131.github.io/website/cv/anthropic-fellow` (unlinked page per OQ-7)

## Target

- **Cohort:** July 20, 2026 (rolling review accepted since post-start)
- **Today:** 2026-06-24 — ~26 days to cohort
- **Submission target:** First week of July 2026

## Scope Boundaries

**In scope:** First-submission drafts of every form field; the new variant; the spec doc.

**Out of scope (NG1–NG7 in spec):** Reviewer-feedback iteration, interview prep, take-home assessments, generic "fellowship" variant for other programs (MATS/Astra), modifying other variants beyond the GRA-date fix, rewriting published papers, the actual submission button (user does that).

## Other Existing Variants

- `academic` (academic faculty search)
- `research-professional` (industry research / R&D)
- `sde-long` (pure-industry SDE)
- `anthropic-fellow` (this initiative)
