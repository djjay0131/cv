# Active Context

## Current Focus

**Anthropic Fellows Program 2026 application** — building the targeted CV variant + form-answer drafts. The variant compiles, deploys, and is live; layout polish and bug fixes are the remaining work before user voice-pass + submission.

## State of the Application Package (2026-06-24)

- ✅ Variant `anthropic-fellow` exists, compiles, 3 pages, live at `https://djjay0131.github.io/website/cv/anthropic-fellow`
- ✅ All 8 spec OQs resolved
- ✅ Form-answer drafts written for all required fields in `llm/features/anthropic-fellowship-application.md`
- ⚠️ **PR #5 master CI FAILED** — deployed PDF is missing the LimeLeap rename changes (Chief Architect / Director of Professional Services not yet showing). User-visible bug.
- ⚠️ Layout has structural issues user hasn't loved (see below).
- ⏳ User-side blockers (R3 identification, R1/R2 emails, voice pass on prose) still pending.

## Recent Decisions (Chronological — 2026-06-20 through 2026-06-24)

### Open the PR even before page-count locked (2026-06-22)
**Decision:** Squash-merge PR #2 (anthropic-fellow variant + doctoral-research role) to master without committing the visual-regression baseline first.
**Rationale:** User wanted public URL to share/review against; "no baseline → warn + skip" workflow branch absorbed the missing baseline; trim decisions can ship as follow-up PRs without rework.
**Trade-off:** Visual regression won't catch unintentional changes to anthropic-fellow until the baseline is committed (still untracked at `tests/baselines/anthropic-fellow/`).

### Drop Nanda mentions for staleness (2026-06-23, PR #3)
**Decision:** Removed "Currently studying mechanistic interpretability via Neel Nanda's curriculum and TransformerLens..." from the fellowship summary, and de-named Nanda in the `vt-research-mech-interp` employment bullet.
**Rationale:** User pushback — Nanda's ARENA curriculum was the entry point in late 2024; MI has moved through SAEs / attribution graphs / dictionary learning since. Naming the curriculum dates the framing.
**Also dropped:** The "Seeking to bring an empirical-claims-and-evidence methodology..." closing sentence; reads as canned ("pulled from the job posting" per user).
**Result:** PDF unchanged at 4 pages — the trim freed lines but didn't collapse a page.

### Drop two weak doctoral-research bullets (2026-06-24, PR #4)
**Decision:** Removed `vt-research-mech-interp` and `vt-research-knowledge-accumulation` bullets entirely. Doctoral-research now has 3 bullets (agentic-KG, construction-AI, VVUQ).
**Rationale:**
- Mech-interp: self-directed study sits awkwardly next to funded research projects.
- Knowledge-accumulation: "two-paper line on evidence accumulation" describes the *output* (papers) without naming the *research*; Publications section right below duplicates without adding info.
**Trade-off:** Lost a reference to ICSE 2026 + arXiv preprint in the employment section. Publications section is supposed to carry that load, but currently only 1 of 2 papers is rendering (see Bug #3 below).
**Result:** PDF dropped from 4 → 3 pages.

### Rename LimeLeap titles + include in anthropic-fellow (2026-06-24, PR #5 — MASTER CI FAILED)
**Decision:** Renamed `limeleap-chief-engineer` title `Chief Engineer` → `Chief Architect`; renamed `limeleap-director-productivity` title `Director of Productivity Solutions` → `Director of Professional Services`. Added both (collapsed) to the anthropic-fellow variant's employment include list.
**Rationale:** User wanted these titles surfaced for the fellowship variant — Director + Chief Architect signal leadership/architect-level seniority that "Senior Architect" alone doesn't, strengthening the mid-career-pivot narrative for fellowship reviewers.
**Scope:** anthropic-fellow only (per user). Other variants unchanged.
**FAILED:** master CI run 28077646395 — `Compile sde-long` visual regression: 10265 pixels differ on page-3. The title rename affected sde-long (which includes both LimeLeap roles) and invalidated its baseline. **Not yet fixed.**

## Recent Learnings

### Race hazard with `gh run list --limit 1`
After merging a PR, master CI takes a few seconds to enqueue. Querying immediately can return the *previous* master run's ID. This caused us to "watch the wrong run" after PR #5 merge — got a green watch from PR #4's stale run, declared success, deployed a stale website build. **Always match by commit SHA or sleep a few seconds.**

### Visual regression baselines invalidate easily on content changes
Any title or text change in a role included by multiple variants will invalidate every variant's baseline that shows that role. The fix is mechanical (delete baselines, let workflow skip-and-warn, regenerate from fresh artifacts post-merge) but easy to forget when bundling content changes.

### Website's `cv-data.test.ts` pins exact pool counts
Adding 3 projects to `data/content/projects.yaml` broke the website's test (`expect(pool.projects.length).toBe(4)` failed when count became 7). Fix: switch exact counts to `toBeGreaterThanOrEqual(N)` to absorb future additions. Same pattern was already in place for employment (`>= 5`). This is now done for projects (`>= 7`) but other counts (`education: 3`, `skills: 4`) still pin exact values.

### The cv-to-website notify is silently broken
cv repo's "Notify website repo" step in `Publish release + cv-data` is supposed to trigger a website rebuild via `repository_dispatch` but doesn't. Website only rebuilds on schedule (~2hr) or manual `gh workflow run build.yml --repo djjay0131/website`. Tracked as task #38.

## Open Issues / Bugs Discovered in PDF Review

1. **LimeLeap roles missing from deployed PDF** — fixable; PR #5's master CI failed on sde-long baseline. Drop the baseline, re-trigger.
2. **Education line reads "M.I.T. and B.S., Economics"** — source is literally `degree: "M.I.T. and B.S., Economics"` in `data/content/education.yaml` (id: `bs-econ-vt`). Unverified whether M.I.T. is a real VT credential (could be a minor abbreviation) or a data error. **Needs user confirmation.**
3. **Only 1 of 2 publications renders** — `own-bib.bib` contains both `cusati2026papers` (ICSE) and `brown2025exploringevidencebasedsebeliefs` (arXiv) but the deployed PDF only shows the ICSE entry on page 3. Filter logic in `templates/tex/publications.tex.j2` or its data source is dropping the arXiv preprint. **Not investigated yet.**
4. **Projects section duplicates 3 of 5 doctoral-research bullets** — agentic-KG, construction-AI, VVUQ appear word-similar in both the employment bullets AND the projects section. Reads as padding rather than two perspectives.
5. **Publications buried on page 3** (after Skills) — wrong placement for a fellowship reviewer. Should be after Doctoral Researcher or after Education.
6. **5 collapsed earlier-roles → one dense paragraph** — works for 2-3 roles, gets unreadable at 5. Lower priority than the others.

## Immediate Next Steps

1. **Fix PR #5 master CI failure** — branch `fix-sde-long-baseline`, delete `tests/baselines/sde-long/` (workflow skip-and-warn carries), PR + merge. After merge, download fresh sde-long artifact and commit refreshed baseline.

2. **Re-trigger cv→website chain** — after step 1 merges to master, run `gh workflow run build.yml --repo djjay0131/website`, watch, verify LimeLeap roles render in the live PDF.

3. **Verify "M.I.T. and B.S., Economics"** — ask user what M.I.T. abbreviates (likely a VT minor); fix the data if needed.

4. **Investigate missing arXiv preprint** — read `templates/tex/publications.tex.j2`, check `tools/resolver.py` publication handling, and the bib entry's fields. Likely a filter on `@article` vs `@inproceedings` or a missing field.

5. **Layout proposal** — after bugs are clean, propose moving Publications section earlier (after Doctoral Researcher or after Education) and trimming Projects to drop the 3 entries that duplicate doctoral-research bullets. Possibly A/B `classic` vs `refined-serif` theme.

6. **(User side)** ~~Identify R3, supply R1/R2 emails.~~ ✅ done 2026-06-30: R1 Chris Brown dcbrown@vt.edu; R2 **Kereshmeh Afsari** keresh@vt.edu (NOT Burcin — that was a guess that turned out wrong); R3 Dave Hollander davidhollander@gmail.com (Yoh senior). Final voice pass on prose drafts still pending.

## Current Blockers

- **PR #5 sde-long baseline** — only blocker for getting LimeLeap renames live. ~5 min fix.
- **User-side reference identifications** — required before submission; not blocking anything code-side.

## Open Questions

- **M.I.T. in education** — what does this abbreviate? Is it real?
- **Layout polish** — user said "don't love the layout" without specifics. Bugs may be the actual source; need clean PDF before re-evaluating.
- **Theme choice** — refined-serif locked currently; worth A/B with classic?
