# Product Context

## Why Per-Role Variants Instead of One CV

Jason is **mid-career pivoting** from 20+ years secure-software delivery into a CS PhD focused on AI/ML/mechanistic interpretability. His credible candidate-profile differs sharply by role:

- **Academic search committee** wants publications + research arc + teaching potential.
- **Industry R&D / research scientist** wants research credibility AND shipping ability.
- **SDE** wants execution depth across the 20-year delivery history.
- **Alignment fellowship reviewer** (Anthropic) wants empirical-methodology research + behavioral evals + secure-software depth, framed for a 4-month sprint.

One CV cannot serve all four well. The variant system lets each role get a CV that **leads with the right framing** while reusing the same underlying employment/projects/skills pool.

## What Reviewers Actually Read

Across all variants:
- **Summary** is the 5-second scan that decides "right or wrong applicant."
- **Publications** are the credibility anchor for any research-adjacent role.
- **Doctoral Researcher** (newest employment role, added in this initiative) signals current work; needs to lead in research-targeted variants.
- **Earlier industry roles** carry weight by *job title*, not bullets — Director / Chief / Principal / Architect titles signal seniority that mid-level titles don't. Collapsed-paragraph rendering preserves these without taking lines.

## The Anthropic-Fellow Specific Tension

Two pulls in tension:
1. **Page-count pressure:** Reviewers skim; spec target was 2 pages, current is 3 (was 4 before bullet trims).
2. **Substance pressure:** "Sell me more" — user feedback after first 4-page draft. The doctoral-research bullets + project highlights need to land, not vanish into compression.

**Current resolution:** Lead with vt-doctoral-research (3 strong in-flight project bullets: agentic-KG, construction-AI, VVUQ). Collapse 5 earlier roles into one paragraph. Refined-serif theme, no photo. Lands at 3 pages.

**Unresolved:** Publications are still buried on page 3; projects section duplicates 3 of 5 doctoral-research bullets. Section reorder + dedup likely improves the read but is downstream of bug fixes.

## Why an Unlinked /cv/anthropic-fellow Page (OQ-7)

The site's homepage and nav point to `/cv/academic` (the academic variant) — that's the default "verify the PDF facts" experience for any reviewer. The fellowship variant lives at `/cv/anthropic-fellow` but is not linked from nav. Reviewers reach it only via the direct URL (which the user may or may not include in the form's "Other links" field — current spec recommendation is to send the site root instead, leading with academic + papers).

## What Counts as Success

1. Application submitted on or before first week of July 2026.
2. Every required form field has a drafted answer in user voice.
3. Resume PDF compiles cleanly, reads researcher-first, includes publications visibly.
4. All three references warned before reviewers contact them.
5. PR history is clean and reversible (small commits, no force-pushes).
