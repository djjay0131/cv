---
name: add-paper
description: Fetch paper metadata from a URL (arXiv, DOI, or arbitrary), generate a validated bibtex entry, append to own-bib.bib, and offer to commit. Uses the stricter tools/lint_bib.py as the verification gate — does NOT ask the user to eyeball field values. Always prompts for the optional GitHub repo URL.
---

# Add Paper

You are running the `add-paper` skill. Your job: fetch a paper's metadata from a URL, generate a well-formed bibtex entry, validate it via the linter, and offer to commit.

**Argument:** `<url>` — the paper URL. Optional. If omitted, enter fully-prompted mode (no fetch).

## Hard Rules

- NEVER push without explicit user request.
- NEVER overwrite an existing entry without showing the existing one and getting explicit "replace" confirmation.
- NEVER skip the lint step — it's the gate that prevents broken bib from reaching git.
- ALWAYS ask for the GitHub URL — no source provides it automatically.
- DO NOT ask the user to eyeball each parsed field. Trust the source; trust the lint. Only prompt for fields no source can provide (entry type when ambiguous, GitHub URL, optional notes).
- If a fetch fails or returns garbage, fall through to prompt mode without crashing.

## Flow

### Step 1: Detect source from URL

Match the user-supplied URL (case-insensitive) against:

| Pattern | Source |
|---|---|
| `arxiv.org/(?:abs\|pdf)/(?P<id>[0-9]+\.[0-9]+)(?P<ver>v[0-9]+)?` | arXiv |
| `(?:dx\.)?doi\.org/(?P<doi>10\.\S+)` | DOI / Crossref |
| `https?://...` (anything else) | Unknown |
| (empty / not provided) | Prompt-only |

For arXiv `/pdf/` URLs, strip `/pdf/` to get the abs form. Strip any `vN` suffix from the ID for the bibtex endpoint, but remember it for the optional `note` field.

### Step 2: Fetch metadata

**arXiv** — two fetches:

1. `WebFetch("https://arxiv.org/bibtex/<id>", prompt="Return the bibtex entry from this page verbatim.")` → ready-made bibtex with author, title, year, eprint, url, archivePrefix.
2. `WebFetch("https://arxiv.org/abs/<id>", prompt="Extract the abstract text only — no other commentary.")` → abstract.

If a `vN` suffix was present, add `note = {arXiv version vN}` to the entry.

**DOI / Crossref:**

1. `WebFetch("https://api.crossref.org/works/<doi>", prompt="Extract: title, authors (with given+family separately), year (from issued.date-parts), container-title, type, DOI, URL, abstract if present. Return as JSON.")` → structured metadata.
2. Map `type` to entry type:
   - `journal-article` → `article`
   - `proceedings-article` → `inproceedings`
   - `book`, `book-chapter` → `book` / `incollection`
   - anything else → `misc` (and prompt user to confirm)

**Unknown URL:**

1. `WebFetch(url, prompt="Extract from this page: paper title, author names (in 'First Last' format, separated by 'and'), publication year, venue (journal or conference name), DOI if present, abstract if present. Look for <meta name='citation_*'> tags first (Highwire Press convention used by academic publishers), then OpenGraph tags, then visible page content. Return JSON with keys: title, authors, year, venue, doi, abstract. Use null for fields you can't find.")` → best-effort extraction.
2. If the result is empty/uncertain, fall through to prompt mode for any missing fields.

### Step 3: Auto-generate citation key

Format: `{firstAuthorLastname}{year}{firstNonStopWordOfTitle}`, lowercase, alphanumeric only, max 32 chars.

- Stop words to strip from title-first-word: `the`, `a`, `an`, `of`, `on`, `in`. If stripping leaves the title empty, use the second word.
- Strip non-alphanumerics from each piece.
- Truncate the final key at 32 chars.

Examples:
- "Brown, Chris" + 2025 + "Exploring the Evidence-Based..." → `brown2025exploring`
- "Doe, Jane" + 2024 + "A Study of LLMs" → `doe2024study`

### Step 4: Ask only for fields no source provides

Always ask:

1. **GitHub URL**: "GitHub repo URL for this paper (optional, press enter to skip):"

Conditionally ask:

2. **Entry type**: only if Crossref didn't determine it OR source was arXiv (default `misc`) OR source was unknown. Options: `article`, `inproceedings`, `misc`, `book`, `incollection`, `techreport`, `unpublished`. Show the default; user can accept it.
3. **Anything else**: a single open-ended prompt if you suspect missing fields. Skip if not needed.

DO NOT ask the user to confirm fetched fields one-by-one. Trust the source.

### Step 5: Detect duplicate citation key

Use the Bash tool to grep `own-bib.bib` for the proposed key:

```
grep -n "^@.*{<citation-key>," own-bib.bib
```

If found:
- Read the existing entry from the file (the lines from the matched `@type{` to the closing `}`).
- Show the user both the existing and the new draft entry side-by-side.
- Offer three options:
  - **skip** (default): abort the operation, no changes.
  - **rename**: append `-2`, `-3`, etc. to the new key until it's unique. Use the renamed key for the new entry.
  - **replace**: overwrite the existing entry. Require explicit "replace" confirmation. Warn that any `\cite{<key>}` references in the LaTeX will continue to work since the key stays the same; if the user is renaming AND replacing (different new key), warn that `\cite{}` references would break.

### Step 6: Append the new entry to own-bib.bib

Build the bibtex entry:

```
@<type>{<citation-key>,
  author = {<authors>},
  title = {<title>},
  <journal/booktitle/publisher per type> = {<venue>},
  year = {<year>},
  url = {<url>},
  <doi = {<doi>}> if present,
  <github = {<gh-url>}> if user provided,
  <abstract = {<abstract>}> if fetched,
  <note = {<note>}> if vN suffix preserved,
}
```

Append it to `own-bib.bib` with a single blank line separator before it. Use the Edit tool (read first, append at end).

### Step 7: Run the stricter lint

Run via Bash:

```
cd <repo root> && .venv/bin/python -m tools.lint_bib own-bib.bib
```

If exit code is non-zero:
1. Show the lint output to the user.
2. Revert the file via Bash: `git checkout -- own-bib.bib`.
3. Identify which check failed (author, url, year, doi, github, title, missing-required).
4. Prompt the user to provide a corrected value for the failing field.
5. Loop back to Step 6 with the corrected entry.

If exit code is 0, proceed to Step 8.

### Step 8: Show the diff

Run `git diff own-bib.bib` and show the user exactly what was added.

### Step 9: Offer to commit

Ask: "Commit this change? (y/n)"

If yes, commit using a heredoc to handle special characters in the title:

```bash
git add own-bib.bib && git commit -m "$(cat <<'EOF'
add paper: <citation-key>

<title>
<authors-comma-separated>
<venue> (<year>)
<url-if-present>
<github-if-present>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

The subject is `add paper: <citation-key>` (always short and searchable). The body has the full title, authors, venue, year, and any optional fields for readable `git log` context.

### Step 10: Tell the user about push

After a successful commit (or if the user declined to commit), tell them:

- "Committed. Push when you're ready: `git push`."
- Or: "No commit made. The file changes were reverted."

NEVER run `git push` automatically.

## Edge Cases

- **arXiv version suffix** (`v2`, `v3`): strip for the bibtex endpoint, preserve in `note` field.
- **arXiv bibtex endpoint fails**: fall back to fetching the abs page and extracting metadata via prompt.
- **Crossref sparse data**: use what's available, prompt for the rest.
- **User aborts mid-flow**: revert any file changes via `git checkout`, exit cleanly.
- **Network failure**: fall through to prompt mode; do not crash.
- **Non-ASCII names**: preserve UTF-8 in the bibtex entry. Lint accepts unicode.
- **LaTeX-special characters in abstract** (`%`, `&`, `_`, `#`, `$`): store raw. The current publications template doesn't render abstracts in LaTeX (only on the website, which HTML-escapes).
- **Title starting with stop word**: strip the stop word for citation key generation. Fall back to the second word.

## Verification

The lint is the verification gate. If lint passes, the entry is correct enough to commit. If lint fails, the user is prompted to fix the specific failing field — no eyeballing required.
