# Active Context

Last updated: 2026-04-16

## Current Focus
M1 and M2 of the `cv-website` feature are implemented and deployed. M3 (polish pass) remains.

## Recent Significant Changes
- M1 landed across 3 commits on `cv` repo (`e01c4f0`, `6de457d`, `3620d99`): data-driven CV pipeline, \makerubric fix, deprecated .tex cleanup.
- M1 CI is green — PDF artifact published at https://github.com/djjay0131/cv/releases/tag/latest
- **M2 landed**: new `website` repo at https://github.com/djjay0131/website
  - Astro-based static site deployed to GitHub Pages at https://djjay0131.github.io/website/
  - Pages: landing (`/`), CV (`/cv/academic`), papers (`/papers`), PDF download (`/pdfs/academic.pdf`)
  - Lib: `cv-data.ts` (YAML loader + resolver), `bib.ts` (bibtex parser), `md.ts` (Markdown → HTML)
  - 20 vitest tests passing
  - CI: push + `repository_dispatch` + hourly cron triggers; fetches data/PDF from cv repo release

## Open Decisions / Questions
- **M3 items**: projects page, print CSS, accessibility gate (Lighthouse ≥95), SEO (OG/JSON-LD/sitemap), smoke tests, build-failure notifications — all deferred to M3.
- **repository_dispatch from cv → website**: the cv repo's workflow has the dispatch step gated on a `WEBSITE_DISPATCH_PAT` secret. Need to create a PAT and configure it for automated triggering.
- **Custom domain**: site is at `djjay0131.github.io/website/`; could move to a custom domain or rename repo to `djjay0131.github.io` for root-level hosting.

## Immediate Next Steps
1. Optionally start M3 (polish pass) — or ship M2 as-is and iterate.
2. Create a PAT for the cv → website `repository_dispatch` trigger.
3. Consider variant selector DSL follow-up once additional resume versions are provided.
