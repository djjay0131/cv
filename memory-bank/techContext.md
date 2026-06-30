# Technical Context

## Local Development Environment

- **OS:** macOS (Darwin 25.5.0)
- **Working dir:** `/Users/djjay0131/code/cv`
- **Companion website dir:** `/Users/djjay0131/code/website`
- **Python venv:** `/Users/djjay0131/code/cv/.venv` (Python 3.9)
- **Shell:** zsh
- **Default git branch:** `master` (cv); `main` (website)

## Python Tooling

- `tools/render.py` — entry: `python -m tools.render <variant>` (positional arg)
- `tools/resolver.py` — variant DSL resolver (Pydantic strict schema with Literal enums)
- `tools/schema.py` — type definitions
- `tools/lint_bib.py` — bib file linter (`@inproceedings` vs `@misc` enforcement)

**Important:** `tools.render` accepts the variant name **positionally**, NOT via `--variant` flag. `python -m tools.render --variant foo` fails with `data/variants/--variant.yaml not found`.

## Cochineal Font: Broken Locally

The `refined-serif` theme uses the Cochineal serif font. On macOS, font-cache resolution fails:

```
! Package fontspec Error: The font "Cochineal-Roman" cannot be found
```

**Workaround:** Compile in CI, download via `gh run download`:
```bash
gh run download <RUN_ID> --repo djjay0131/cv --dir /tmp/cv-artifacts
# PDFs land at /tmp/cv-artifacts/variant-<name>/<name>.pdf
```

User noted (per memory) they planned to update their system 2026-05-19; status unverified. **Do not attempt local make commands for variants using `refined-serif`** — fall back to CI.

`classic` theme variants (academic, sde-long) may compile locally. Untested in current session.

## CI: Two Repositories

### cv repo (`djjay0131/cv`)
- Workflow: `.github/workflows/build-cv.yml` (job name: `build-cv`)
- Stages: `Python tests & lint` → `Discover variants` → `Compile <variant>` (matrix) → `Publish release + cv-data` (master only)
- Visual regression runs inside each `Compile <variant>` job
- Artifacts: `variant-<name>` (one per variant, contains `<name>.pdf`)
- Release: `latest` tag on master, attached PDFs + `cv-data.zip`

### website repo (`djjay0131/website`)
- Workflow: `.github/workflows/build.yml` (workflow ID 262054596, name `build-and-deploy`)
- Triggers: `push` to main, `schedule` (every ~2hr), `workflow_dispatch`
- Stages: `build` (incl. `vitest run`) → `deploy` → `smoke-test`
- Tests: `src/lib/cv-data.test.ts` — asserts pool shape (e.g., projects.length ≥ 7)

## Cross-Repo Data Flow

`scripts/fetch-data.sh` in the website repo:
```bash
gh release download "latest" --repo djjay0131/cv --pattern "cv-data.zip"
gh release download "latest" --repo djjay0131/cv --pattern "*.pdf"
unzip cv-data.zip → data/
```

The website's local-dev variant: `scripts/sync-local-data.sh` symlinks from a local cv checkout instead of downloading.

## PDF Inspection

`pypdf` is installed in cv venv but NOT pre-installed (had to `pip install pypdf -q` mid-session). For page counts:
```bash
.venv/bin/python -c "from pypdf import PdfReader; print(len(PdfReader('path').pages))"
```

For visual review, just `open path/to.pdf` (macOS Preview).

`mdls -name kMDItemNumberOfPages -raw` is finicky with relative paths — prefer pypdf.

## Text Extraction Caveats

pypdf's text extraction from Cochineal-rendered PDFs introduces spurious spaces in capital-T sequences:
- `Virginia Tech` extracts as `Virginia T ech`
- `M.I.T.` extracts as `M.I. T.`

These are **extraction artifacts**, NOT rendering bugs. The visual PDF is correct.

## GitHub CLI Patterns

- Wait for a run: `gh run watch <ID> --repo <org/repo> --exit-status`
- List runs by branch: `gh run list --repo <r> --branch <b> --limit N --json ...`
- Download artifacts: `gh run download <ID> --repo <r> --dir <dest>`
- Merge PR (squash + delete branch): `gh pr merge <N> --repo <r> --squash --delete-branch`
- Auto-merge **not enabled** on the website repo (`enablePullRequestAutoMerge` returns GraphQL error).

## Race Hazard With Captured Run IDs

After merging a PR, the master CI run takes a few seconds to enqueue. Querying `gh run list --branch master --limit 1` immediately can return the **previous** master run, not the new one. Pattern that bit us:

```bash
gh pr merge 5 ... && CV_RUN=$(gh run list --branch master --limit 1 --json databaseId --jq '.[0].databaseId')
# CV_RUN here is often the PRIOR merge's run ID, not the new one
```

**Mitigation:** Match by commit SHA, or sleep a few seconds before querying, or check `displayTitle` matches the just-merged PR.

## Caches

- GitHub Pages CDN may serve stale PDF for several minutes after deploy. Cache-bust with: `curl "url?$(date +%s)"` or `-H "Cache-Control: no-cache"`.

## Spec Doc Location

Feature specs live at `llm/features/<feature-name>.md`. Current fellowship spec: `llm/features/anthropic-fellowship-application.md`.
