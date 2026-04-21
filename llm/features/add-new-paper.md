# Feature: Add Paper Skill + Stricter Bib Lint

**Status:** IMPLEMENTED
**Date:** 2026-04-20
**Author:** Feature Architect (AI-assisted)

## Problem

Adding a new publication to `own-bib.bib` today requires hand-writing bibtex with exact field names, remembering which fields are required per entry type, formatting authors correctly, and remembering to add the custom `github` field that the website's papers page surfaces. Mistakes are caught only when CI runs `tools/lint_bib.py`, after a push.

Worse, the current lint is weak: it validates required fields and 4-digit years but does **not** catch malformed author strings, invalid URLs, implausible years, broken DOI formats, or empty titles. So even when a paper is added cleanly, a garbage fetch result (or a typo) can reach `master` because the lint didn't notice.

This feature solves both problems together: a Claude Code skill that fetches paper metadata from a URL and writes a well-formed entry, backed by a stricter lint that actually catches the failure modes fetch+parse can produce.

## Goals

- **G1**: A Claude Code skill `/add-paper <url>` that takes a paper URL, fetches metadata, appends a validated bibtex entry to `own-bib.bib`, and offers to commit.
- **G2**: arXiv URLs auto-populate title, authors, year, abstract, and URL via arXiv's bibtex endpoint and abs page.
- **G3**: DOI URLs auto-populate metadata via Crossref's public API.
- **G4**: Unknown URLs fall back to WebFetch-based extraction, then to fully-prompted mode if extraction fails.
- **G5**: The skill always prompts for the optional GitHub repo URL (no paper source provides it).
- **G6**: **Stricter `tools/lint_bib.py`** validates author format, URL well-formedness, year sanity, DOI format, and non-empty title — applied to all entries (existing and new).
- **G7**: The stricter lint is the programmatic verification gate. The skill trusts it; there is no "does this look right?" step that puts correctness burden on the user.
- **G8**: User sees a diff before commit and explicitly confirms. Push is never automatic.

## Non-Goals

- **NG1**: Web UI or form-based add. CLI/skill only.
- **NG2**: A Python CLI tool (`tools/add_paper.py`). The skill uses Claude's existing WebFetch / Read / Edit / Bash tools — no new Python code beyond the lint enhancement.
- **NG3**: Auto-fetch from paywalled sources (IEEE Xplore, ACM DL, Springer). Those URLs fall through to prompt mode.
- **NG4**: Automated coauthor notification, sharing, or external integration.
- **NG5**: Editing or deleting existing entries. Only adding new ones. Duplicate detection asks how to proceed.
- **NG6**: Auto-push to remote. Commit happens on confirmation; push is always separate.

## User Stories

- As Jason, I want to paste an arXiv URL and have a well-formed bibtex entry created automatically, so I don't have to remember field names or risk typos.
- As Jason, I want the skill to ask me for the GitHub repo URL, so my website's papers page surfaces the code for the paper.
- As Jason, I want to trust the lint — not eyeball the output — so I'm not the verification gate.
- As Jason, I want lint failures to block the commit so malformed entries never reach `master`.
- As Jason, I want to add a paper from any URL, with the system falling back to prompting me for fields it couldn't extract.
- As Jason, I want my `git log` to be readable — commit subjects short and searchable, full details in the body.

## Design Approach

### Skill Location and Invocation

- File: `.claude/skills/add-paper/SKILL.md`
- Primary invocation: `/add-paper <url>` (the user supplies the URL as the skill argument)
- Fully-prompted mode: `/add-paper` with no argument → skip fetch, prompt for all fields

### Source Detection

The skill recognizes these URL patterns:

| URL pattern | Source | Fetch strategy |
|---|---|---|
| `arxiv.org/abs/<id>` | arXiv | WebFetch `https://arxiv.org/bibtex/<id>` (ready-made bibtex) + WebFetch abs page for abstract |
| `arxiv.org/pdf/<id>` | arXiv | Strip `/pdf/` → use abs form |
| `doi.org/<doi>` or `dx.doi.org/<doi>` | DOI | WebFetch `https://api.crossref.org/works/<doi>` (JSON metadata) |
| Anything else | Unknown | WebFetch the URL; ask to extract title / authors / year / venue from page meta tags |
| Empty (no arg) | None | Skip fetch, prompt mode |

Version suffixes on arXiv IDs (`v2`, `v3`) are stripped for the bibtex endpoint but preserved in the entry's `note` field if present.

### Fetch + Parse

**arXiv:**
- `WebFetch("https://arxiv.org/bibtex/<id>")` → returns bibtex-formatted metadata (author, title, year, eprint, url, archivePrefix, primaryClass)
- `WebFetch("https://arxiv.org/abs/<id>", prompt="Extract the abstract...")` → abstract text
- Combine both into the final entry.

**DOI/Crossref:**
- `WebFetch("https://api.crossref.org/works/<doi>")` → JSON
- Map fields: `title`, `author[].given`+`family`, `issued.date-parts[0][0]` (year), `container-title` (journal/booktitle), `DOI`, `type` (maps to entry type — "journal-article" → `article`, "proceedings-article" → `inproceedings`, etc.)

**Unknown URL:**
- `WebFetch(url, prompt="Extract paper metadata...")` — ask the model to find title, authors, year, venue from `<meta name="citation_*">` tags (Highwire Press convention on academic sites), OpenGraph tags, or visible page content.
- If extraction is empty/uncertain, fall through to prompt mode.

### Prompts

After fetch (or in prompt mode), the skill asks **only for fields no source can provide**:

1. **Entry type** — but only if the source doesn't provide it clearly:
   - arXiv → defaults to `misc` (preprint) unless user says otherwise
   - Crossref → use `type` field mapping directly
   - Unknown → always ask
2. **GitHub URL** — always asked (optional, blank to skip)
3. **Anything else?** — single open-ended prompt for edge cases (additional note, translator, editor, etc.)

The skill does NOT ask the user to confirm fetched fields field-by-field. The lint is the verification gate.

### Author Formatting

Standard bibtex: `author = {First Last and First Last and ...}`. No `\bibnamedelima` needed for the current `\mynames{Cusati/Jason}` config (no-space given name). If a coauthor has a multi-word given name (e.g., "Lian Tze"), the skill emits them as `Lim, Lian Tze` (comma-form) which biblatex handles correctly. If the user wants `\mynames` to match a multi-word given name, that's a separate configuration concern — out of scope.

### Citation Key Generation

Format: `{firstAuthorLastname}{year}{firstTitleWord}`, lowercase, alphanumeric only.

- **Stop words stripped** from first-title-word extraction: "the", "a", "an", "of", "on", "in". If stripping leaves the title empty, fall back to the first non-stop word.
- **Max length**: 32 chars. Truncate and note in logs.
- Example: "A Study of LLMs" by Brown, 2025 → `brown2025study` (not `brown2025a`).
- Example: "Exploring the Evidence-Based SE Beliefs..." by Brown, 2025 → `brown2025exploring`.

### Citation Key Collision

Before writing, the skill `grep`s `own-bib.bib` for the proposed key. If found:
- Show the existing entry side-by-side with the new draft
- Offer: **skip** (default) / **rename** (append `-2`, then `-3`, etc. until free) / **replace** (explicit confirm required; warn about potential `\cite{}` references)

### Write → Lint → Diff → Commit

1. Append the new entry to the end of `own-bib.bib` with a blank line separator.
2. Run `python -m tools.lint_bib own-bib.bib` (now with the **stricter rules** below).
3. If lint fails:
   - Show the error messages.
   - Revert via `git checkout -- own-bib.bib`.
   - Prompt user to fix the problem field (re-enter at Step 2 of the main flow).
4. If lint passes:
   - Show `git diff own-bib.bib` so user sees exactly what's added.
5. Ask "Commit this? (y/n)". If yes, commit with:
   - **Subject**: `add paper: <citation-key>` (always short, searchable)
   - **Body**: full title, authors, year, venue, url, github (if set)
   - **Footer**: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`
6. Never push. Tell the user "Push when ready."

### Stricter Bib Lint (`tools/lint_bib.py` enhancement)

The lint gains these checks, applied to **every entry** (not just new ones):

| Check | Rule | Error message |
|---|---|---|
| **Author format** | `author` field non-empty, doesn't end with `and`, each `and`-separated name has a plausible shape (no empty parts, allows `Last, First` or `First Last`, supports unicode) | `author malformed: <specific issue>` |
| **URL well-formedness** | If `url` field present, it parses as a URL with scheme (`http`/`https`) and host | `url malformed: <value>` |
| **Year sanity** | Year is 4-digit integer in `[1900, current_year + 2]` (allows "in press" up to 2 years out) | `year out of range: <value>` |
| **DOI format** | If `doi` field present, matches regex `10\.\d+/.+` | `doi malformed: <value>` |
| **Non-empty title** | `title` field present and non-empty after whitespace-stripping | `title missing or empty` |
| **GitHub URL (if present)** | If `github` custom field is set, must be a well-formed URL starting with `https://github.com/` | `github field malformed: <value>` |

All checks accumulate errors into a single `BibLintError` as today — one failing entry shows every problem with it, not just the first.

### Existing Entry Compliance

As part of this feature, **the existing `own-bib.bib` must pass the new lint rules.** Any existing entry that fails must be fixed before the feature is considered complete. If `brown2025exploringevidencebasedsebeliefs` passes — good. If not, fix it.

## Sample Implementation

`.claude/skills/add-paper/SKILL.md` (illustrative excerpt):

```markdown
---
name: add-paper
description: Fetch a paper's metadata from a URL (arXiv, DOI, or arbitrary), generate a validated bibtex entry, append to own-bib.bib, and offer to commit. Uses the stricter lint as the verification gate — no "does this look right?" questions.
---

# Add Paper

Argument: `<url>` (optional — invoke without URL for fully prompted mode).

## Flow

### Step 1: Detect source from URL

Match against regex:
- `arxiv.org/(?:abs|pdf)/(?P<id>[0-9]+\.[0-9]+)(?P<ver>v[0-9]+)?`
- `(?:dx\.)?doi\.org/(?P<doi>10\..+)`
- Otherwise → unknown source
- Empty → prompt-only mode

### Step 2: Fetch metadata

**arXiv:**
- WebFetch `https://arxiv.org/bibtex/<id>` → bibtex text
- Parse: author, title, year, eprint, url
- WebFetch `https://arxiv.org/abs/<id>` with prompt "Extract the abstract text only" → abstract

**Crossref:**
- WebFetch `https://api.crossref.org/works/<doi>` → JSON
- Map: title[0], author (join given+family), issued.date-parts[0][0],
       container-title[0], DOI, type → entry type

**Unknown:**
- WebFetch url with prompt for citation_* tags / OpenGraph / visible text
- If result is empty, fall through to prompt mode

### Step 3: Auto-generate citation key

`{firstAuthorLastname}{year}{firstNonStopWordOfTitle}`, lowercase alphanumeric,
max 32 chars. Stop words: the, a, an, of, on, in.

### Step 4: Ask only for fields no source provides

- Entry type (only if Crossref didn't determine it)
- GitHub URL (always — no source has it)
- Anything else to add (optional)

### Step 5: Duplicate detection

Grep own-bib.bib for the citation key.
If found: show both entries, offer skip (default) / rename (-2, -3, ...) / replace.

### Step 6: Append to own-bib.bib

Append with one blank line before the new entry.

### Step 7: Run stricter lint

`python -m tools.lint_bib own-bib.bib`
If fail:
  - Show error.
  - `git checkout -- own-bib.bib` to revert.
  - Prompt user to fix the failing field; loop back to Step 6.

### Step 8: Show diff

`git diff own-bib.bib`

### Step 9: Offer commit

Ask: "Commit this? (y/n)"
If yes:
  git add own-bib.bib
  git commit -m "add paper: {citation-key}" -m "<body with full metadata>" \
    -m "Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
Never push.
```

Illustrative lint extension (pseudo-code for `tools/lint_bib.py`):

```python
import re
from urllib.parse import urlparse

_CURRENT_YEAR = datetime.now().year
_YEAR_MIN = 1900
_YEAR_MAX = _CURRENT_YEAR + 2
_DOI_RE = re.compile(r"^10\.\d+/.+")
_GITHUB_PREFIX = "https://github.com/"

def _check_authors(authors: str) -> list[str]:
    problems = []
    s = authors.strip()
    if not s:
        return ["author missing or empty"]
    if s.lower().endswith(" and"):
        problems.append("author field ends with 'and' (trailing separator)")
    parts = [p.strip() for p in re.split(r"\s+and\s+", s)]
    for part in parts:
        if not part:
            problems.append("empty author in list")
        elif "," in part:
            # "Last, First" form
            last, _, first = part.partition(",")
            if not last.strip() or not first.strip():
                problems.append(f"malformed author '{part}' (comma form requires both sides)")
    return problems

def _check_url(url: str) -> list[str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return [f"url malformed (bad scheme): {url!r}"]
    if not parsed.netloc:
        return [f"url malformed (no host): {url!r}"]
    return []

def _check_year(year: str) -> list[str]:
    try:
        y = int(year)
    except ValueError:
        return [f"year not numeric: {year!r}"]
    if not (_YEAR_MIN <= y <= _YEAR_MAX):
        return [f"year out of range [{_YEAR_MIN}, {_YEAR_MAX}]: {y}"]
    return []

def _check_doi(doi: str) -> list[str]:
    return [] if _DOI_RE.match(doi) else [f"doi malformed: {doi!r}"]

def _check_github(gh: str) -> list[str]:
    if not gh.startswith(_GITHUB_PREFIX):
        return [f"github field must start with '{_GITHUB_PREFIX}': {gh!r}"]
    return _check_url(gh)
```

**Key decisions illustrated:**
- **arXiv bibtex endpoint** is the primary fetch — structured, reliable, no HTML parsing.
- **Abstract fetched separately** from abs page (arXiv bibtex omits it).
- **Crossref `type` field** maps directly to entry type, avoiding a prompt when possible.
- **Stop-word-aware citation keys** prevent `brown2025a` for titles starting with "A".
- **Lint-as-gate**: no user eyeballing; the stricter lint is the verification.
- **Commit subject = citation key**, body has full metadata — readable `git log`.

## Edge Cases & Error Handling

### EC-1: arXiv URL with version suffix
- **Scenario**: User supplies `arxiv.org/abs/2407.13900v2`.
- **Behavior**: Strip `v2` when calling the bibtex endpoint. Add `note = {arXiv version v2}` to the entry if user cares about version tracking.
- **Test**: Invoke on `arxiv.org/abs/2407.13900v2`; assert bib uses `2407.13900` as eprint.

### EC-2: arXiv bibtex endpoint fails (404 or garbage)
- **Scenario**: arXiv serves a broken response.
- **Behavior**: Fall back to WebFetching the abs page directly and extracting metadata via prompt.
- **Test**: Mock 404; assert fallback runs without aborting.

### EC-3: Crossref returns sparse metadata
- **Scenario**: DOI lookup returns only title + authors, missing year or venue.
- **Behavior**: Use what's available, prompt for the rest.
- **Test**: Use a DOI with known sparse metadata; assert prompts fill the gaps.

### EC-4: User aborts during prompts
- **Scenario**: User cancels before commit.
- **Behavior**: If `own-bib.bib` was appended, revert via `git checkout`. No git operations run. Clean exit message.
- **Test**: Manual — invoke, abort at each step, verify file unchanged after.

### EC-5: Duplicate citation key
- **Scenario**: Generated key matches existing entry.
- **Behavior**: Show both, offer skip (default) / rename / replace. Replace warns about `\cite{}` breakage if the key is literally changed.
- **Test**: Add existing arXiv URL; assert collision flow.

### EC-6: Lint failure after append (existing rules)
- **Scenario**: Generated entry has missing required field or bad year.
- **Behavior**: Revert append, show lint error, prompt user to fix.
- **Test**: Force bad year; assert revert + prompt.

### EC-7: Lint failure from stricter rules
- **Scenario**: Author field has trailing "and" from bad arXiv parse; URL has no scheme; DOI malformed.
- **Behavior**: Stricter lint catches it, same revert-and-prompt flow as EC-6.
- **Test**: One fixture per new rule (author trailing-and, bad URL, bad DOI, bad year, empty title); each triggers lint failure.

### EC-8: Network failure during fetch
- **Scenario**: WebFetch times out.
- **Behavior**: Fall through to fully-prompted mode. Do not abort.
- **Test**: Manual — disconnect, invoke, confirm fallback.

### EC-9: Non-ASCII author names
- **Scenario**: Coauthor "François Dupont" or "李明".
- **Behavior**: Preserve UTF-8 in the bibtex entry. Biblatex + xelatex handle it natively.
- **Test**: Add a paper with non-ASCII coauthor; assert lint passes and compiled PDF renders correctly.

### EC-10: Citation key too long / starts with stop words
- **Scenario**: Title "A Study of LLMs in Modern Software Engineering Practice" by Brown 2025.
- **Behavior**: Strip "A", use "study". Result: `brown2025study`. Max length truncation: 32 chars.
- **Test**: Fixtures for stop-word stripping and 32-char truncation.

### EC-11: Existing `own-bib.bib` entry fails new lint rules
- **Scenario**: `brown2025exploringevidencebasedsebeliefs` or a future entry doesn't match the stricter rules.
- **Behavior**: CI lint step fails. Must be fixed as part of this feature's implementation before it can ship.
- **Test**: Run new lint against current bib in CI; must pass.

### EC-12: Replace mode with active `\cite{}` references
- **Scenario**: User replaces an entry whose key is referenced via `\cite{key}`.
- **Behavior**: If the key stays the same, no breakage. If the user renames during replace, warn explicitly.
- **Test**: Manual — replace + rename, check for broken references.

### EC-13: Abstract contains LaTeX-unsafe characters
- **Scenario**: Abstract from arXiv has `%`, `&`, `_`, `#`, `$`.
- **Behavior**: bibtex abstract fields are typically read by biblatex without LaTeX-escape, but when rendered via `\printbibliography` with an abstract-enabled style, the specials could cause compile errors. Either (a) store raw and let biblatex/render-time handle it, or (b) escape on write. Recommendation: (a), because the current publications template doesn't render abstracts in LaTeX (only on the website, which HTML-escapes).
- **Test**: Add a paper whose abstract has LaTeX specials; assert PDF compile succeeds and website renders the abstract with specials intact.

## Acceptance Criteria

### AC-1: arXiv URL produces a valid entry end-to-end
- **Given** the user invokes `/add-paper https://arxiv.org/abs/2407.13900`
- **When** the skill runs and the user confirms commit
- **Then** `own-bib.bib` contains a new entry with title, authors, year, url, and abstract populated from arXiv; the stricter lint passes; `git log` shows a commit with subject `add paper: <key>` and body containing full metadata.

### AC-2: DOI URL produces a valid entry via Crossref
- **Given** the user invokes `/add-paper https://doi.org/10.1145/3597503.3608123`
- **When** the skill runs
- **Then** metadata is pulled from Crossref JSON, entry type is auto-detected from the `type` field, and the final entry passes stricter lint.

### AC-3: Unknown URL triggers extraction + fallback
- **Given** the user invokes `/add-paper https://some-journal.com/article/abc`
- **When** the skill runs
- **Then** it WebFetches the page, attempts to extract metadata, and either writes a complete entry or falls back to prompting for every field. Neither path crashes.

### AC-4: GitHub URL is always prompted
- **Given** any successful fetch
- **When** the skill reaches Step 4
- **Then** it asks for the GitHub URL (with "blank to skip" option). The field is included in the written entry only if provided.

### AC-5: Citation key generated correctly
- **Given** fetched author "Brown, Chris", year 2025, title "A Study of LLMs"
- **When** the skill generates the citation key
- **Then** the key is `brown2025study` (stop word "A" stripped), lowercase alphanumeric, ≤32 chars.

### AC-6: Duplicate detection prevents silent overwrite
- **Given** the generated citation key already exists in `own-bib.bib`
- **When** duplicate detection fires
- **Then** the user sees both entries, is offered skip (default) / rename / replace, and the file is only changed if the user picks an option explicitly.

### AC-7: Stricter lint catches bad author format
- **Given** an entry with `author = {Chris Brown and }` (trailing "and")
- **When** `python -m tools.lint_bib own-bib.bib` runs
- **Then** lint exits non-zero with a clear message naming the entry and the author problem.

### AC-8: Stricter lint catches bad URL
- **Given** an entry with `url = {not a url}`
- **When** lint runs
- **Then** lint exits non-zero naming the entry and the URL problem.

### AC-9: Stricter lint catches bad year
- **Given** an entry with `year = {9999}` or `year = {1024}`
- **When** lint runs
- **Then** lint exits non-zero with year out-of-range message.

### AC-10: Stricter lint catches bad DOI
- **Given** an entry with `doi = {not-a-doi}`
- **When** lint runs
- **Then** lint exits non-zero with DOI format message.

### AC-11: Stricter lint catches bad GitHub URL
- **Given** an entry with `github = {ftp://github.com/foo}`
- **When** lint runs
- **Then** lint exits non-zero with github field malformed message.

### AC-12: Stricter lint passes on current bib
- **Given** the current `own-bib.bib` at `master`
- **When** the enhanced `tools/lint_bib.py` runs against it
- **Then** it exits 0. Any existing entry that doesn't meet the new rules is fixed as part of this feature's implementation (otherwise CI fails).

### AC-13: Lint failure aborts cleanly without git changes
- **Given** a newly-appended entry fails lint
- **When** the skill detects the failure
- **Then** `own-bib.bib` is reverted via `git checkout --` and no commit is made. The user sees the specific lint error.

### AC-14: Diff shown before commit
- **Given** lint passes
- **When** the skill is ready to commit
- **Then** `git diff own-bib.bib` is shown and the user explicitly confirms before `git add` / `git commit` run.

### AC-15: Commit format is subject + body + footer
- **Given** user confirms commit
- **When** the commit runs
- **Then** the subject is `add paper: <citation-key>` (≤72 chars), the body contains title/authors/year/venue/url/github (if set), and the footer includes the `Co-Authored-By` tag.

### AC-16: Push is never automatic
- **Given** a successful commit
- **When** the skill exits
- **Then** no `git push` runs. User is told they can push when ready.

### AC-17: Round-trip with existing paper
- **Given** user invokes `/add-paper https://arxiv.org/abs/2407.13900` (already in bib)
- **When** the skill runs
- **Then** duplicate detection fires, offers skip (default), and no file change happens if user picks skip.

## Technical Notes

### Affected components
- **New**: `.claude/skills/add-paper/SKILL.md` — the skill flow.
- **Modified**: `tools/lint_bib.py` — extended with author/URL/year/DOI/title/github checks.
- **Modified tests**: `tools/tests/test_lint_bib.py` — covers new rules (one test per new check) + regression on existing rules.
- **Possibly modified**: `own-bib.bib` — if any existing entry fails the new rules, it must be fixed.
- **Unchanged**: all other Python tooling, all templates, the website repo.

### Patterns to follow
- Skill structure mirrors existing skills under `.claude/skills/` (frontmatter + flow).
- Uses existing tools: `WebFetch`, `Read`, `Edit`, `Bash` (for `lint_bib.py` and `git`).
- Lint enhancement extends the existing `_check_entry()` function in `tools/lint_bib.py` — no new public API.
- Commit format matches this repo's convention (subject short, body detailed, `Co-Authored-By` footer).

### Data model changes
- None. `own-bib.bib` already supports `github` and `abstract` custom fields — the website's `bib.ts` already reads them.

## Dependencies

- No new Python packages. Uses stdlib `urllib.parse` for URL parsing and `re` for DOI/year regex.
- External services at skill runtime: arXiv (`arxiv.org/bibtex/<id>` + `arxiv.org/abs/<id>`), Crossref (`api.crossref.org/works/<doi>`), and arbitrary URLs for unknown sources.

## Open Questions

- **OQ-1**: Stop-word list — is `the, a, an, of, on, in` enough, or should we add `for, with, and, or`? Recommendation: ship with the minimal list; add more if real titles produce bad keys.
- **OQ-2**: Rename collision suffix — `-2`, `-3`, ... vs. `-v2`, `-v3`, ...? Recommendation: `-2` (simpler).
- **OQ-3**: Should the new lint rules be gated behind a config flag for a transition period (e.g., warn-only mode)? Recommendation: no — this feature explicitly requires all entries to pass.
- **OQ-4**: Should `WebFetch` responses be cached during a single skill invocation to avoid re-fetching the same URL multiple times? Recommendation: yes — trivial to implement.
- **OQ-5**: When replacing with a key change, should the skill grep the repo for `\cite{<oldkey>}` usage and warn with file+line? Recommendation: yes — one-line `grep -rn "\\\\cite{<oldkey>}" .` in the skill.
- **OQ-6**: Year upper bound — fixed `current_year + 2` or make it configurable? Recommendation: hardcode; revisit if someone has a 2030 preprint.
