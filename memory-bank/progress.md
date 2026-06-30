# Progress

## Completed This Initiative (Anthropic Fellows Application)

### PR #2 — Add anthropic-fellow variant (2026-06-22, merged)
- [x] Created `data/variants/anthropic-fellow.yaml` (refined-serif theme, no photo, researcher-first sections)
- [x] Added `fellowship` summary to `data/content/summaries.yaml`
- [x] Added `vt-doctoral-research` employment role with 5 in-flight research bullets
- [x] Added 3 projects to `data/content/projects.yaml`: `agentic-kg`, `construction-ai`, `vvuq-beam-solver`
- [x] Fixed GRA dates: `vt-gra-mrs` "April 2026 -- Present" → "April 2026 -- May 2026"
- [x] Refreshed baselines for `academic` + `research-professional` (GRA-date change propagated)
- [x] Created spec doc `llm/features/anthropic-fellowship-application.md` — full form-answer matrix, prose drafts, references, OQs all resolved
- **Commit:** `a450d39` (squash of `685c9fc`, `d0dfce1`, `e78d561`)

### website PR #2 — Fix projects pool test (2026-06-22, merged)
- [x] Updated `src/lib/cv-data.test.ts` — `pool.projects.length` exact 4 → `>= 7`
- [x] Caused by cv PR #2 adding 3 new projects (4 → 7); test crashed website build
- **Commit:** `5f8786a`

### PR #3 — Trim fellowship summary + de-name mech-interp bullet (2026-06-23, merged)
- [x] Dropped "Currently studying mechanistic interpretability via Neel Nanda's curriculum..." from `summaries.yaml` fellowship entry
- [x] Dropped "Seeking to bring an empirical-claims-and-evidence methodology..." closing
- [x] Revised `vt-research-mech-interp` bullet to remove "Neel Nanda's ARENA curriculum" name (kept TransformerLens + hand-built transformer detail)
- **Result:** PDF still 4 pages (trim freed lines, didn't collapse a page)
- **Commit:** `73952a8`

### PR #4 — Drop two weak doctoral-research bullets (2026-06-24, merged)
- [x] Removed `vt-research-mech-interp` bullet (self-directed study sits awkwardly in employment)
- [x] Removed `vt-research-knowledge-accumulation` bullet ("two-paper line on evidence accumulation" duplicates Publications section without naming research)
- [x] Doctoral Researcher now has 3 bullets: agentic-KG, construction-AI, VVUQ
- **Result:** PDF dropped 4 → 3 pages
- **Commit:** `d9d8a74`

### PR #5 — Rename LimeLeap titles + include in anthropic-fellow (2026-06-24, merged BUT master CI FAILED)
- [x] `limeleap-chief-engineer` title: "Chief Engineer" → "Chief Architect"
- [x] `limeleap-director-productivity` title: "Director of Productivity Solutions" → "Director of Professional Services"
- [x] Added both (collapsed) to anthropic-fellow employment include
- [!] **master CI FAILED on `Compile sde-long` visual regression** (10265 px diff page-3) — title change invalidated sde-long baseline; deployed PDF is missing the LimeLeap changes
- **Commit:** `83d05360` (on master, but artifacts not published due to failure)

## Status Changes (Tasks)

| # | Task | Status |
|---|---|---|
| 24 | Merge cv PR #1 + website PR #1 | ✅ completed |
| 25 | Create anthropic-fellow-application branch | ✅ completed |
| 26 | Resolve OQs in fellowship spec | ✅ completed |
| 27 | Create data/variants/anthropic-fellow.yaml | ✅ completed |
| 28 | Add fellowship summary to summaries.yaml | ✅ completed |
| 29 | Fix GRA date: April--May 2026 | ✅ completed |
| 30 | CI-compile fellowship variant + verify pages | ✅ completed |
| 31 | Refresh academic + research-professional baselines | ✅ completed |
| 32 | Decide final page count | 🔄 in_progress (currently 3p, layout review pending) |
| 33 | Merge PR #2 once page count locked | ✅ completed |
| 34 | Identify R3 Yoh senior name + email | ✅ completed 2026-06-30 — Dave Hollander, davidhollander@gmail.com |
| 35 | Supply R1 Brown + R2 Afsari emails | ✅ completed 2026-06-30 — R1 dcbrown@vt.edu; R2 **Kereshmeh** Afsari (not Burcin) keresh@vt.edu |
| 36 | Final voice pass on prose drafts | ⏳ pending (user) |
| 37 | Submit Anthropic Fellows application | ⏳ pending (user) |
| 38 | Fix cv-to-website notify step | ⏳ pending (low priority) |

## In Progress

- **Fix PR #5 master CI failure** — drop sde-long baseline, re-merge, refresh baseline post-master-build. ~5 min.
- **Layout review** — bugs found in deployed PDF (missing LimeLeap, possibly-broken education line, missing arXiv preprint, duplicated projects). User asked "what do you think so far?"; assessment delivered, awaiting prioritization.

## New Issues Discovered (This Session)

- **Issue:** `Compile sde-long` visual regression baseline doesn't survive LimeLeap title rename.
  **Severity:** Medium (blocks PR #5 from publishing).
  **Resolution:** Drop sde-long baseline, regen from fresh artifact.

- **Issue:** Only 1 of 2 publications renders in deployed PDF.
  **Severity:** Medium (publications are credibility anchor for fellowship).
  **Resolution:** Not yet investigated; check `templates/tex/publications.tex.j2` and resolver publication handling.

- **Issue:** Education line reads "M.I.T. and B.S., Economics" (data is literal `degree: "M.I.T. and B.S., Economics"`).
  **Severity:** Low-Medium (could be real or could be data error).
  **Resolution:** Confirm with user what M.I.T. abbreviates.

- **Issue:** Projects section duplicates 3 of 5 doctoral-research bullets.
  **Severity:** Low-Medium (structural / readability).
  **Resolution:** Restructure projects section to exclude agentic-KG, construction-AI, VVUQ (already covered by employment bullets).

- **Issue:** Publications section sits on page 3 after Skills.
  **Severity:** Medium (wrong placement for fellowship).
  **Resolution:** Reorder sections — publications after Doctoral Researcher or after Education.

- **Issue:** cv-to-website notify step in CI is silently failing.
  **Severity:** Low (manual `gh workflow run` is a 1-line workaround).
  **Resolution:** Tracked as task #38; investigate after submission.

## Timeline

- **Spec started:** 2026-05-10
- **All OQs resolved:** 2026-06-06
- **Today:** 2026-06-24
- **Original cohort deadline:** July 20, 2026 (now rolling per the official page)
- **Target submission:** First week of July 2026 — ~10 days remaining

## What's NOT Done

- [ ] PR to fix PR #5 master failure (drop sde-long baseline)
- [ ] Refresh sde-long baseline from fresh artifact after fix lands
- [ ] Commit fresh `anthropic-fellow` baseline (still untracked at `tests/baselines/anthropic-fellow/`)
- [ ] Verify / fix "M.I.T. and B.S., Economics" education line
- [ ] Investigate + fix missing arXiv preprint in publications section
- [ ] Restructure projects section (deduplicate vs doctoral-research bullets)
- [ ] Reorder sections (move publications higher)
- [ ] A/B classic vs refined-serif theme (optional)
- [ ] User: identify R3, supply emails, voice-pass prose drafts, submit
