# Feature: Publishing to the research hub

**Status:** IMPLEMENTED
**Date:** 2026-09-15
**Author:** Satellite Implementation Engineer (AI-assisted)

## What changed

A push to `master` now publishes the CV to the research hub at
<https://jason.cusati.us> through the hub's published contract. cv is the hub's
first satellite.

Before, the hub reached into cv: its build downloaded cv's `latest` GitHub
release and unzipped `cv-data.zip`. Now cv pushes a finished folder to a Google
Cloud Storage bucket and the hub polls that bucket. The hub no longer knows
anything about cv's releases, its build or its LaTeX.

Nothing about the CV itself changed: same variants, same PDFs, same visual
regression gate, same `latest` release with the same assets.

## The interface, in one sentence

The `publish` job stages a `dist/` folder, writes a `manifest.json` at its root
describing what is in it, and hands both to the hub's composite action
`djjay0131/website/contract/publish@main`, which validates the manifest and
uploads `dist/` to `gs://<content-bucket>/sources/cv/`.

```
dist/
├── manifest.json          the whole interface
├── academic.pdf
├── anthropic-fellow.pdf
├── research-professional.pdf
├── sde-long.pdf
└── cv-data/
    ├── data/content/*.yaml
    ├── data/variants/*.yaml
    ├── own-bib.bib
    └── photo_jason_1.jpeg
```

`cv-data/` is exactly the contents of `cv-data.zip`, unzipped. Both are packed
from the same staged directory, so they cannot drift.

## The manifest

`dist/manifest.json` is generated, never hand-maintained, by
`tools/manifest.py` (`python -m tools.manifest --dist dist`). It describes five
items:

| slug | format | path | comes from |
|---|---|---|---|
| `academic` | `pdf` | `academic.pdf` | `data/variants/academic.yaml` |
| `anthropic-fellow` | `pdf` | `anthropic-fellow.pdf` | `data/variants/anthropic-fellow.yaml` |
| `research-professional` | `pdf` | `research-professional.pdf` | `data/variants/research-professional.yaml` |
| `sde-long` | `pdf` | `sde-long.pdf` | `data/variants/sde-long.yaml` |
| `cv-data` | `data` | `cv-data/` | the staged payload above |

The variant items are **discovered**, exactly as the workflow's `configure` job
discovers its build matrix: every `data/variants/*.yaml` becomes an item. Add a
variant and it publishes itself. Each item's `title` is that variant's `label`
and its `summary` is that variant's `description`; a variant with no `label`
fails the build rather than being given a title the tool made up. Every item's
`date` is the committer date of the commit being published, so re-running a
build does not move it.

The authority on the manifest's shape is `contract/manifest.schema.json` in the
website repository. `tools/manifest.py` mirrors the few rules it needs so that a
bad manifest fails in cv's own build, with cv's file names in the error, rather
than in the hub's action afterwards.

## `schema_version`

The `cv-data` item carries `schema_version`, currently `"1"`. It versions the
**shape** of the payload, not its contents, and the hub fails its build on a
value it does not recognise.

Bump it when the payload's structure changes in a way hub code must be taught:
a renamed, removed or re-typed YAML key, a moved or renamed file, a changed
directory layout, a new required field. Do **not** bump it for ordinary CV
edits — new employment bullets, a new publication, a reworded summary, or a new
variant file. A shape change published without a bump produces a subtly wrong
CV page on the hub instead of a loud failure, which is the failure mode the
version exists to prevent. A bump needs a matching change in the hub's
`site/src/lib/cv-data.ts`, so raise it with the hub before publishing.

## No website credential is involved

cv holds **no GitHub credential for the website repository** and no
service-account key.

- Authentication is Workload Identity Federation. The `publish` job grants
  `id-token: write`; the hub's action exchanges that OIDC token for a
  short-lived GCP credential that exists only for the length of the run.
- That credential can create, replace and read objects under `sources/cv/` and
  nothing else. It deliberately cannot even list the bucket, so cv cannot see
  what other sources have published — and cannot verify its own upload by
  listing it either.
- The hub is **not notified**. It polls the bucket on a schedule, so a publish
  appears at the next poll rather than immediately.

The old "Notify website repo" step, which would have fired a
`repository_dispatch` at the website repository using a PAT with `repo` scope,
has been deleted along with every reference to `WEBSITE_DISPATCH_PAT` and
`vars.WEBSITE_REPO`. Any credential able to dispatch at `website` could also
write to it, which is precisely what the hub's ADR-0007 forbids. If anyone
proposes re-adding a website PAT here, the answer is no.

## Repository settings the owner must set

Four GitHub Actions **variables** (Settings → Secrets and variables → Actions →
Variables), not secrets — none of them is secret, and making them secrets only
makes failures harder to read:

| Variable | What it is |
|---|---|
| `GCP_PROJECT_ID` | The hub's Google Cloud project id |
| `GCP_WIF_PROVIDER` | cv's Workload Identity provider, in the hub's `satellites` pool |
| `GCP_PUBLISH_SA` | cv's publishing service account |
| `GCP_CONTENT_BUCKET` | The hub's content bucket name |

The hub owner issues all four. Until they are set, the publish step fails at the
WIF exchange; everything before it — tests, the PDF matrix, the visual
regression gate, the `latest` release — is unaffected.

## The GitHub release is unchanged

`latest` still carries the four PDFs and `cv-data.zip`, and still has consumers
outside the hub. It is not part of the hub contract and was not touched beyond
moving where the zip is staged.

## Cross-references

- `docs/satellites.md` in the website repository — the satellite how-to
- `contract/README.md`, `contract/manifest.schema.json` in the website
  repository — the reference and the schema
- website `llm/governance/adr/0007-…` — no satellite holds a GitHub credential
- website `llm/governance/adr/0008-…` — the `data` format and `schema_version`
- `tools/manifest.py`, `tools/tests/test_manifest.py`
- `.github/workflows/build-cv.yml` — the `publish` job
