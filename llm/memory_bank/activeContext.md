# Active Context

Last updated: 2026-04-17

## Current Focus
All three milestones (M1, M2, M3) of the `cv-website` feature are implemented and deployed. The data-driven CV pipeline and personal website are fully operational.

## Recent Significant Changes
- **M1**: Data-driven CV pipeline in `cv` repo — YAML content pool + variant selectors + Python generator + Jinja templates + CI producing PDF artifact. 112 pytest tests, 100% coverage.
- **M2**: Astro website at https://djjay0131.github.io/website/ — landing page, CV page, papers page, PDF download. 20 vitest tests.
- **M3**: Polish pass — projects page (index + 4 detail pages), print CSS, accessibility (skip-link, ARIA landmarks, WCAG AA colors), SEO (OG/Twitter cards, canonical URLs, JSON-LD Person schema, sitemap, robots.txt), post-deploy smoke tests (HTTP 200 + body size), build-failure notification webhook (gated on NOTIFICATION_WEBHOOK secret).

## Live URLs
- https://djjay0131.github.io/website/ (landing)
- https://djjay0131.github.io/website/cv/academic (CV)
- https://djjay0131.github.io/website/papers (papers)
- https://djjay0131.github.io/website/projects (projects)
- https://djjay0131.github.io/website/pdfs/academic.pdf (PDF download)
- https://github.com/djjay0131/cv/releases/tag/latest (CV artifacts)

## Open Decisions / Questions
- **repository_dispatch from cv → website**: still gated on WEBSITE_DISPATCH_PAT secret. Create a PAT to enable automated triggering when cv content changes.
- **NOTIFICATION_WEBHOOK**: smoke test and failure notifications are wired but gated on this secret. Configure when ready.
- **Custom domain**: site is at `djjay0131.github.io/website/`; could rename repo to `djjay0131.github.io` for root-level hosting or add a CNAME.
- **Variant selector DSL**: follow-up task for bullet-level filtering/overrides once additional resume versions are provided.
- **Lighthouse CI gate (AC-13 formal)**: WCAG AA colors and semantic HTML are in place; formal `@axe-core/playwright` CI gate deferred — can be added when Playwright is integrated.

## Immediate Next Steps
1. Optionally configure the PAT for cv → website repository_dispatch.
2. Optionally configure the NOTIFICATION_WEBHOOK secret.
3. Content work: upload existing resume versions for the variant selector DSL.
4. Consider renaming repo for root-level hosting or adding a custom domain.
