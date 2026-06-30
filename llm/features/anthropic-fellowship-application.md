---
name: anthropic-fellowship-application
description: Tailored answers + fellowship-targeted CV variant for Jason's Anthropic Fellows Program application
type: project
---

# Feature: Anthropic Fellowship Application Package

**Status:** SPECIFIED
**Date:** 2026-05-10
**Author:** Feature Architect (AI-assisted)

## Problem

Jason is applying to the Anthropic Fellows Program (4-month full-time empirical-research fellowship; ~$3,850/wk + ~$15k/mo compute; ~25-50% convert to full-time). The application is administered by Constellation via a multi-section Airtable form. Existing artifacts are wrong-target: the `academic.yaml` CV variant opens with *"Results-oriented technical executive and principal engineer..."* — a framing tuned for an academic hiring committee evaluating an industry-veteran-turned-PhD-candidate, not for an alignment fellowship reviewing him for fast empirical research execution. The form's prose questions also need first drafts: *Why Fellows / research areas / accept-FT % / continue-safety %* each need answers that link Jason's published research (ICSE 2026 + arXiv 2024) to the alignment team's actual methodology.

Concretely:
- The `academic` summary leads with industry-architect framing; reviewers will skim it as "wrong applicant" before reaching the publications.
- All bullets from non-research roles are currently included in full; for a fellowship resume, most should be aggressively collapsed.
- No fellowship-specific prose answers exist anywhere; without first drafts the cohort deadline (July 20, 2026) becomes a forcing function for shallow writing.
- The personal website (https://djjay0131.github.io/website/) is the natural backup-context anchor for the application but isn't currently linked from anywhere reviewers will look.

## Goals

- **G1**: A complete, edit-and-submit-ready set of answers for every required form field, with each prose answer grounded in a specific artifact (paper, project, role, or cert) Jason can defend in interview.
- **G2**: A new `data/variants/anthropic-fellow.yaml` that compiles to PDF via existing `make <variant>` flow and renders at `/cv/anthropic-fellow` on the website without code changes.
- **G3**: A new `summaries.yaml` entry (`fellowship`) that opens with PhD-candidate framing and explicitly names the alignment-methodology angle (claims, evidence, behavioral evals).
- **G4**: Website-link strategy — the "Other links" form field points to the personal website, which acts as a deeper-context backup for everything in the uploaded PDF.
- **G5**: Three form-answer questions (acceptance %, continue-safety %, other commitments) framed honestly without inflated numbers, since reviewers read across the cohort.
- **G6**: The fellowship resume PDF is structurally correct (publications visible, page count ≤2) and free of stale facts (GRA dates corrected from "Present").

## Non-Goals

- **NG1**: Iterating with reviewer feedback — the spec covers first-submission drafts only. Post-feedback revision is a follow-up.
- **NG2**: Interview prep, take-home assessments, or research-discussion preparation — separate concerns triggered if the application advances.
- **NG3**: Designing a generic "fellowship" variant for future programs (MATS, Astra, etc.). This variant is Anthropic-specific; reuse is incidental.
- **NG4**: Modifying the `academic` variant or any other existing artifact beyond the GRA-date correction (which is a standalone fact fix that benefits all variants).
- **NG5**: Rewriting any published paper, abstract, or bib entry to better match alignment-fellowship framing — those facts stand as-is.
- **NG6**: Submitting the application. The user submits manually after final review.
- **NG7**: Setting up a Google Scholar profile if one doesn't exist — note as open question; don't block on it.

## User Stories

- As Jason, I want each form prose question pre-drafted with the right voice and length, so I can edit not write from scratch under deadline.
- As Jason, I want a fellowship-targeted PDF that I can upload directly to the form without further editing.
- As Jason, I want my personal website linked from "Other links" so reviewers can verify the PDF facts and see fuller project context.
- As Jason, I want every multi-select form field (cohort, workspace, work auth) pre-decided and recorded in one place, so I don't second-guess them on submission day.
- As Jason, I want my references section fully drafted with R1 + R2 background and relationship paragraphs, so I only need to fill R3 and verify emails.
- As Jason, I want the fellowship answer drafts to read as a single coherent voice (claims-and-evidence empiricism + mid-career deliberateness + hands-on mech-interp curiosity), not as five disconnected essays.

## Design Approach

### Form-answer matrix

Every field from the Airtable form, with delivery plan:

| Section | Field | Required | Source |
|---|---|---|---|
| General | First/Last Name | Y | Known: Jason Cusati |
| General | Email | Y | Known: djjay@vt.edu |
| General | Pronunciation / Pronouns | N | User to fill |
| General | Resume upload | Y | **NEW: anthropic-fellow.pdf from this variant** |
| General | Applied to Anthropic/MATS/Astra/Fellows in past year? | Y | **OQ-1** — assume No |
| General | AI policy understanding | Y | Yes |
| Links | Google Scholar | N | **OQ-2** — does Jason have a profile? |
| Links | LinkedIn | N | jason-cusati (from meta.yaml) |
| Links | GitHub | N | djjay0131 (from meta.yaml) |
| Links | Other | N | **https://djjay0131.github.io/website/** (G4) |
| Motivation | Top team | Y | AI Safety & Alignment |
| Motivation | Other teams | N | Mech Interp; Frontier Red Team |
| Motivation | Why Fellows? | Y | **DRAFT below** (1-2 paragraphs) |
| Motivation | Research areas excited about | Y | **DRAFT below** (1 paragraph) |
| Motivation | Relevant background | N | **DRAFT below** (1 paragraph; high-leverage even though optional) |
| Motivation | Accept FT % | Y | **DRAFT below** — 100% with framing |
| Motivation | Continue safety % | Y | **DRAFT below** — 100% with framing |
| References | R1: Dr. Chris Brown | Y | **DRAFT below** |
| References | R2: Dr. Kereshmeh Afsari (keresh@vt.edu) | Y | **DRAFT below** |
| References | R3: Dave Hollander (davidhollander@gmail.com) | Y | **DRAFT below** |
| References | Additional refs | N | Skip unless an obvious 4th surfaces |
| Logistics | Cohort | Y | July 20, 2026 |
| Logistics | Other timelines/deadlines | N | Skip unless something arises |
| Logistics | Earliest FT start | Y | **DRAFT below** |
| Logistics | Country of residence | Y | USA |
| Logistics | Work authorization | Y | USA |
| Logistics | Other work-auth details | N | Skip |
| Logistics | Workspace preference | Y | Berkeley: 25%+ (with explanation in field below) |
| Logistics | Previously applied to Anthropic | Y | **OQ-1** — assume No |
| Logistics | Other commitments during program | Y | **DRAFT below** |
| Misc | How heard about program | N | **OQ-4** — Jason to fill |
| Misc | Anything else? | N | **DRAFT below** (optional but useful) |
| Misc | Marketing opt-in | N | **OQ-5** — defer to Jason |
| Misc | Refer to other orgs | N | **OQ-5** — defer to Jason |

### CV variant: `anthropic-fellow.yaml`

Selector lives at `data/variants/anthropic-fellow.yaml`. Uses the existing variant-selector DSL (bullet filtering + collapse + skills item subsetting). No code changes to the resolver, templates, or website.

Builds via `make anthropic-fellow` (assuming Makefile auto-discovery from feature `variant-selector-dsl`); renders on the website at `/cv/anthropic-fellow` automatically (Astro `[variant].astro` dynamic route from feature `cv-website`).

Page target: 2 pages. The fellowship application takes a resume upload and reviewers skim — but a researcher CV with publications + projects justifies 2 pages. 1 page would force cutting publications, which is the wrong tradeoff for an alignment application.

### New summary entry

Add to `data/content/summaries.yaml`:

```yaml
- id: fellowship
  text: >-
    PhD candidate in Computer Science (SE with AI/ML/MI) at Virginia Tech, focused on
    the empirical methodology of evaluating LLM behavior and accumulating verifiable
    safety claims. Two papers on evidence-based reasoning in GenAI tools and knowledge
    accumulation in software engineering research (**ICSE 2026**; arXiv preprint).
    Background combines hands-on ML/LLM application work — LLM-assisted code generation,
    ML-driven incident prediction, behavioral evals — with **20+ years of secure-software
    delivery** (CSSLP-certified, recent mesh-VPN/2FA platform hardening at Virginia
    Tech's ARCADE Lab). Currently studying mechanistic interpretability via Neel Nanda's
    curriculum and TransformerLens. Seeking to bring an empirical-claims-and-evidence
    methodology to alignment research at Anthropic.
```

### CV restructuring decisions

- **Employment** — emphasize research-recent and research/security-relevant work:
  - `vt-gra-mrs`: full, all 4 bullets. **Dates corrected** to "April 2026 -- May 2026" (G6).
  - `yoh-adf-architect`: only `yoh-llm` + `yoh-api` bullets (LLM application work).
  - `duck-creek-architect`: only `dc-sev1` (ML for incident prediction) + `dc-pen-testing` (security).
  - `blackbaud-principal`, `blackbaud-solutions`, `djjaynet-consultant`: collapsed to "Earlier roles..." one-liner via the variant DSL `collapse: true` flag.
  - LimeLeap, NCMEC, Force, A.T. Kearney: **excluded entirely** (already collapsed in academic; further reduction here).
- **Education** — keep all three.
- **Projects** — reorder ML/LLM-relevant first: `llm-coding-assistant`, `security-classifier`, `sentiment-yelp`, `nfl-ml`.
- **Publications** — keep (load-bearing). Both bib entries already exist and pass lint.
- **Skills** — reorder to lead with **AI/ML**, then Languages (Python first), then Tools (subset), then Platforms. Drop legacy items (VB.NET, ASP.NET, PHP, Objective C, Access, AngularJS, jQuery) via the skills DSL `items: [...]` subset.
- **Misc** — keep all certifications (CSSLP especially relevant), keep awards.
- **Referee** — "Available on Request" (same as academic).

### Website link strategy

- **"Other links" field** → `https://djjay0131.github.io/website/`
- The website's `/papers` page surfaces both papers with abstracts and (for the ICSE paper) the ICSE 2026 acceptance note.
- The website's CV page (`/cv/academic`) provides the academic-variant view as a deeper-context backup.
- After this spec is implemented, `/cv/anthropic-fellow` will also exist — but the spec deliberately sends reviewers to the site root, not directly to the fellowship variant URL, because the academic+papers view is the more credible "verify the PDF facts" experience.

### Cohort + logistics

| Field | Value | Why |
|---|---|---|
| Cohort | July 20, 2026 | User confirmed; ~10 weeks lead time. |
| Workspace | Berkeley: 25%+ | User confirmed ~50% on-site. Maps to the "25%+" form bucket; will explain "~50%" in the workspace-explanation field. |
| Work auth | USA | User confirmed. |
| Country | USA | Blacksburg, VA. |
| Previously applied | No | **OQ-1** — assume but verify. |

### References

- **R1: Dr. Chris Brown** (Virginia Tech) — coauthor on both papers (ICSE 2026 + arXiv 2024). Email: TBD by user. **Background**: VT CS faculty; has Google Scholar; co-PI'd both publications. **Relationship**: ~2 years collaboration on empirical SE research, including paper drafting and review. Closest research collaborator.
- **R2: Dr. Kereshmeh Afsari** (Virginia Tech, keresh@vt.edu) — PI of ARCADE Lab; supervised the just-completed (April–May 2026) GRA work on the MRS robotics platform. **Background**: VT faculty; PI of ARCADE Lab focused on construction robotics and remote sensing systems. **Relationship**: 2-month direct supervision on platform deployment, security hardening, and reliability work. Can speak to shipping-velocity and engineering judgment.
- **R3: Dave Hollander** (davidhollander@gmail.com) — senior collaborator from the Yoh / Core Specialty Insurance engagement. Adds an industry-ML execution voice that R1 (Chris Brown, academic-research) and R2 (Kereshmeh Afsari, academic-engineering) don't provide. Two-academic + one-industry reads stronger for an industry-research fellowship than three academic refs.

User should email-warn all three the day of submission (Anthropic reaches out without notice; warning references is professional courtesy and avoids surprise non-responses).

## Sample Implementation

### Variant YAML

```yaml
# data/variants/anthropic-fellow.yaml
variant: anthropic-fellow

sections:
  - type: summary
    content_id: fellowship

  - type: employment
    include:
      - vt-gra-mrs
      - id: yoh-adf-architect
        bullets: [yoh-llm, yoh-api]
      - id: duck-creek-architect
        bullets: [dc-sev1, dc-pen-testing]
      - id: blackbaud-principal
        collapse: true
      - id: blackbaud-solutions
        collapse: true
      - id: djjaynet-consultant
        collapse: true

  - type: education
    include: [phd-cs-vt, meng-cs-vt, bs-econ-vt]

  - type: projects
    include:
      - llm-coding-assistant
      - security-classifier
      - sentiment-yelp
      - nfl-ml

  - type: publications

  - type: skills
    include:
      - id: ai-ml
      - id: languages
        items: [Python, C#, Java, JavaScript, Bash, PowerShell, T-SQL, C++, Node.js]
      - id: tools
        items: [Azure, AWS, Docker, FastAPI, Streamlit, scikit-learn, TensorFlow, PostgreSQL, SQL Server, VS Code, PyCharm, Wireshark]
      - platforms

  - type: misc

  - type: referee
    content_id: available
```

Key decisions:
- **`bullets: [...]` per role** — uses existing variant-selector DSL bullet-filtering (feature `variant-selector-dsl`).
- **`collapse: true`** — uses existing collapse flag; produces the "Earlier roles include..." paragraph.
- **`items: [...]` on skills** — uses existing skills item subsetting; drops legacy languages/tools without modifying the pool.
- **Section order matches `academic.yaml`** — only emphasis differs.

### Sample summary YAML

(Already shown above — repeating here for self-containment.)

```yaml
# Append to data/content/summaries.yaml
- id: fellowship
  text: >-
    PhD candidate in Computer Science (SE with AI/ML/MI) at Virginia Tech, focused on
    the empirical methodology of evaluating LLM behavior and accumulating verifiable
    safety claims. ...
```

### GRA date correction (separate small fix)

```yaml
# data/content/employment.yaml — change vt-gra-mrs.dates
- id: vt-gra-mrs
  dates: "April 2026 -- May 2026"   # was: "April 2026--Present"
```

This benefits the academic variant too (the "Present" claim becomes false May 2026 onward).

## Form Answers — Drafts (Ready for User Revision)

### "Why are you interested in participating in the Fellows program?" *(1-2 paragraphs, REQUIRED)*

> I'm a mid-career software engineer turned PhD candidate at Virginia Tech (SE with AI/ML/MI), and my published research is converging on a question Anthropic's alignment team is already living inside: how does a community of researchers reliably accumulate verifiable claims about an LLM's behavior under conflicting incentives? My ICSE 2026 paper analyzes this for software engineering research; my prior arXiv work empirically probes what GenAI tools "believe" relative to evidence. The Fellows program is the most direct route I can see to apply that empirical-claims-and-evidence methodology to alignment proper — to building behavioral evals, auditing frameworks, and the kind of reproducible safety infrastructure that lets the field's claims compound rather than churn.
>
> Equally important: I want the next four months of my career to be spent inside Anthropic's research culture, mentored by people doing this work full-time. I'm not exploring whether to take AI safety seriously — I'm trying to find the highest-leverage way to contribute to it, and a Fellow project shipped under direct mentorship dominates anything I could do solo. I bring twenty years of secure-software delivery (CSSLP, recent robotics-platform hardening) and active hands-on study of mechanistic interpretability via Neel Nanda's curriculum and TransformerLens, which I expect to deepen materially in the lead-up to the July cohort.

*~220 words. Voice: claims-and-evidence empiricism + mid-career deliberateness.*

### "With your selected team(s) in mind, tell us briefly about one or more research areas you're excited about right now, and why." *(1 paragraph, REQUIRED)*

> Three threads I'd want to push on in an alignment context. First, **automated behavioral eval infrastructure** in the lineage of Petri / AuditBench — specifically, applying the claims-and-evidence framework from my ICSE 2026 work to make eval results compose across studies rather than being repeated ad-hoc per paper. Second, **alignment faking and stated-vs-revealed beliefs** — my arXiv work on evidence-based SE beliefs is empirically the same shape as the question of when models say one thing in training and act differently at inference; I'd want to push the methodology onto richer model traces. Third, on the mech-interp side, I've been reading Neel Nanda's papers and built a small transformer + TransformerLens setup to understand induction heads and attribution patching first-hand; the question I keep coming back to is whether sparse-autoencoder features trained on safety-relevant task data surface stable circuits for evidence-evaluation behaviors, or whether those collapse into general reasoning circuits that resist isolation.

*~180 words. Names actual artifacts (Petri, AuditBench, TransformerLens, induction heads, SAEs) so it survives an interview probe.*

### "Please share any relevant background and provide links where possible (e.g., research experience, coursework, self-directed study, past roles, relevant projects)." *(1 paragraph, OPTIONAL)*

> Research: two papers with Dr. Chris Brown at Virginia Tech — *From Papers to Progress: Rethinking Knowledge Accumulation in Software Engineering* (ICSE 2026, accepted) and *Exploring the Evidence-Based SE Beliefs of Generative AI Tools* (arXiv:2407.13900). Both are linked from my site at https://djjay0131.github.io/website/papers. Coursework toward a PhD in CS (SE with AI/ML/MI) and an M.S. in Engineering at Virginia Tech, on top of a B.S. in Economics. Self-directed: Neel Nanda's mech-interp curriculum, transformer-from-scratch + TransformerLens experimentation. Past technical work most relevant to alignment: a Sev-1-incident prediction model from production logs (Duck Creek), an LLM-assisted code-generation prototype for data-pipeline mapping (Yoh), a Security Vulnerability Classifier project mapping code to CVE labels, and an LLM Coding Assistant built on FastAPI/Streamlit with an agentmon design (all linked at /projects). Twenty years of secure-software delivery experience (CSSLP-certified) including very recent mesh-VPN/2FA/audit-logging hardening of an autonomous robotics platform at VT's ARCADE Lab.

*~180 words. Heavy on links and concrete artifacts. Treats the optional field as the "make me concrete" backup.*

### "How likely are you to accept a full-time offer at Anthropic if you receive one after the Fellows program?" *(% + brief, REQUIRED)*

> **100%.** I made a deliberate mid-career pivot from twenty years of industry software delivery into a PhD specifically to work on AI/ML and the methodology of empirical research on LLMs. Joining Anthropic full-time is the obvious continuation of that pivot — better mentorship, better compute, better problem density than anything I could pursue independently. I would arrange the PhD around the offer (flexible timeline / dissertation while at Anthropic) rather than the reverse.

*~75 words. Frames 100% as deliberate not naive — the PhD is means, not end.*

### "How likely are you to be interested in continuing to work on AI safety/security after the Fellows program?" *(% + brief, REQUIRED)*

> **100%.** The reason I'm applying is that I've already concluded AI safety is where I want to spend the next decade of my technical work. If the fellowship doesn't lead to a full-time offer at Anthropic, I'd pursue similar work elsewhere — academic safety labs, Constellation, MATS, or open-source eval / interpretability infrastructure — and continue publishing in the space. The fellowship is the highest-leverage entry point I can see; it isn't the only path.

*~80 words. Demonstrates the commitment isn't Anthropic-conditional, which is what they actually want to know.*

### References (drafts)

#### Reference 1: Dr. Chris Brown

- **Name:** Chris Brown
- **Email:** dcbrown@vt.edu
- **Background:** *Assistant Professor of Computer Science, Virginia Tech. Researches empirical software engineering, developer experience, and human factors in software development. Google Scholar: [link TBD]. VT faculty page: [link TBD].*
- **Relationship:** *Coauthor on two papers (Cusati & Brown, "Exploring the Evidence-Based SE Beliefs of Generative AI Tools," arXiv:2407.13900, 2024; and Cusati & Brown, "From Papers to Progress: Rethinking Knowledge Accumulation in Software Engineering," ICSE 2026). Approximately two years of close collaboration including study design, data analysis, paper drafting, and revision. He can speak to my research-execution velocity, methodological rigor, and ability to push empirical SE work to publication.*

#### Reference 2: Dr. Kereshmeh Afsari

- **Name:** Kereshmeh Afsari
- **Email:** keresh@vt.edu
- **Background:** *Faculty at Virginia Tech; PI of the ARCADE Lab focused on construction robotics, remote sensing, and autonomous systems for built-environment monitoring. VT faculty page: [link TBD].*
- **Relationship:** *Direct supervisor on a Graduate Research Assistantship from April 2026 to May 2026 (Spring semester) on the Multi Robot System (MRS) for Remote Construction Progress Monitoring project. I led cloud deployment, network architecture (mesh VPN), Terraform IaC, REST API + Web UI development, 2FA / video-streaming hardening, and audit logging across services. She can speak to shipping velocity on a real autonomous-systems platform, security judgment under production constraints, and ability to deliver an end-to-end deployment in a compressed timeframe.*

#### Reference 3: Dave Hollander

- **Name:** Dave Hollander
- **Email:** davidhollander@gmail.com
- **Background:** *Senior collaborator from the Yoh / Core Specialty Insurance engagement.*
- **Relationship:** *Direct collaborator during the 2024--2025 ADF Solution Architect engagement. Witnessed the LLM-prototyping work, the Streamlit + Data Ingestion API delivery, and Jason's day-to-day execution on a real production data platform. Chosen over a second VT faculty member because it adds an industry-ML execution voice to a references slate otherwise weighted toward academic-research (Chris Brown) and academic-engineering (Kereshmeh Afsari).*

### Logistics — short answers

- **Cohort:** July 20, 2026
- **Other timelines/deadlines:** *(skip — no commitments to disclose)*
- **Earliest FT start:** *"Immediately after the Fellows program ends (approximately mid-November 2026), or earlier if relocation/onboarding logistics permit."*
- **Country of residence:** USA
- **Work authorization:** USA
- **Workspace preference:** "Berkeley: for 25%+ of the program" *(confirmed)*
  - **Optional explanation field:** *"I plan to be on-site at the Berkeley workspace approximately 25--50% of the program, with the remainder remote from Blacksburg, VA. I have no constraint preventing full on-site if mentor matching makes that the better option --- happy to discuss."*
- **Previously applied to Anthropic:** No *(confirmed — never applied, never interviewed)*
- **Other commitments during the Fellows program:** *"None blocking. I am a PhD student at Virginia Tech and will be in a research-only term (no coursework) during the fellowship window. My GRA at the ARCADE Lab concluded at the end of Spring 2026 semester. I will spend the full 40 hours/week on the Fellows program."*

### Optional fields

- **Pronunciation:** *(user to fill if desired)*
- **Pronouns:** *(user to fill if desired)*
- **How heard about program:** Recommended by my PhD advisor, Dr. Chris Brown (Virginia Tech).
- **Anything else?** *(optional draft — use only if user wants to add a final note)*
  > *"My published research, my recent ARCADE Lab security work, and my self-directed mech-interp study all converge on the same question: how do we accumulate trustworthy claims about what an opaque system actually does? I see the Fellows program as the highest-leverage place to spend the next four months working on that question alongside the people doing it best."*
- **Marketing opt-in:** Yes
- **Refer to other orgs:** Yes

### Links

- **Google Scholar:** https://scholar.google.com/citations?user=TPwNZK4AAAAJ&hl=en
- **LinkedIn:** https://www.linkedin.com/in/jason-cusati
- **GitHub:** https://github.com/djjay0131
- **Other:** https://djjay0131.github.io/website/

## Edge Cases & Risks

### EC-1: ICSE 2026 paper acceptance status changes
- **Scenario**: The "Accepted; to appear" status changes (withdrawal, venue change, etc.) between now and submission.
- **Behavior**: Update bib entry first (`note` field), then re-build CV variant, then update prose answers that reference "ICSE 2026" by name.
- **Mitigation**: Re-verify acceptance ≤24h before submission.

### EC-2: Resume PDF compile fails locally before submission
- **Scenario**: User's local LaTeX install lacks a font (cochineal known-missing per session history).
- **Behavior**: Fall back to CI-built PDF — push the variant, wait for the cv repo's CI to publish a release, download via `gh release download`. Same flow used in the prior session.
- **Mitigation**: Build CV ≥48h before submission deadline, not the day of.

### EC-3: Variant fails Pydantic validation or bullet-ID lookup
- **Scenario**: A typo in `bullets: [...]` references a non-existent ID.
- **Behavior**: `make anthropic-fellow` fails loudly with file + ID per existing resolver behavior.
- **Mitigation**: Test build immediately after creating the variant file.

### EC-4: Reference R3 unresolved by submission deadline
- **Scenario**: User can't identify a third reference they're confident in.
- **Behavior**: Submit with two strong references and a note explaining the third is forthcoming, OR delay submission to next cohort. **Do not submit a weak third reference.**
- **Mitigation**: Treat R3 identification as a Day-1 task, not a Day-of task.

### EC-5: Prose answer exceeds visible character limit when pasted
- **Scenario**: Airtable shows "1 paragraph" but enforces a hidden character cap.
- **Behavior**: Drafts above are sized conservatively (180–220 words / ~1.2k chars per question). If a hidden cap is hit, trim adverbial clauses first, then sentence-merge, then drop the third example in research-areas.
- **Mitigation**: Paste each answer into a test field early to detect truncation.

### EC-6: GRA dates not corrected before submission
- **Scenario**: PDF still shows "April 2026 -- Present" when reviewers read it after May 2026.
- **Behavior**: Reviewer notes a stale claim; small but avoidable credibility hit.
- **Mitigation**: GRA-date correction is part of this spec's acceptance criteria (AC-7) — must land before resume PDF is uploaded.

### EC-7: Website link points to outdated CV PDF
- **Scenario**: `/pdfs/academic.pdf` on the live site is older than the new variant's content.
- **Behavior**: Reviewer compares uploaded fellowship PDF to website's academic PDF and sees inconsistencies.
- **Mitigation**: After landing the GRA-date fix in cv repo, push and trigger website rebuild so `/pdfs/academic.pdf` reflects the corrected GRA dates. The fellowship PDF is uploaded directly to the form, not hosted on the site, so no separate website upload is needed for it.

### EC-8: Interview probe on mech-interp claim
- **Scenario**: Reviewer in research interview asks Jason to walk through what he implemented with TransformerLens.
- **Behavior**: User must be able to answer concretely (which paper(s), what model, what hook ran, what was observed). The "research areas" prose names induction heads, attribution patching, and SAEs — interviewer will probe at least one.
- **Mitigation**: Pre-interview: re-read the Nanda paper(s) cited and re-run the local TransformerLens setup ≥24h before the call.

### EC-9: References auto-contacted before user warns them
- **Scenario**: Anthropic reaches out to R1/R2/R3 before user emails them.
- **Behavior**: References may be confused or non-responsive.
- **Mitigation**: User emails all three references the day of submission with a brief heads-up + the fellowship one-liner. Do not delay submission for ack.

### EC-10: Form field structure changes between draft and submission
- **Scenario**: Airtable form is updated by Constellation; new required field appears.
- **Behavior**: Draft is missing an answer.
- **Mitigation**: Re-verify form structure on submission day, not via the cached draft from May 2026.

## Acceptance Criteria

### AC-1: All required form fields have draft answers
- **Given** the form-answer matrix in this spec
- **When** the user reviews the spec before drafting
- **Then** every field marked "Y" (required) has either a fixed value or a draft prose answer in this document. Optional fields are noted with "user to fill" or have draft prose where high-leverage.

### AC-2: New variant compiles to PDF
- **Given** `data/variants/anthropic-fellow.yaml` and the new `fellowship` summary entry exist
- **When** `make anthropic-fellow` runs locally or in CI
- **Then** `build/anthropic-fellow/anthropic-fellow.pdf` is produced, ≤2 pages, with the new summary, restructured employment, and publications visible.

### AC-3: New variant renders on the website
- **Given** the variant ships in the cv repo's data artifact
- **When** the website CI rebuilds
- **Then** `https://djjay0131.github.io/website/cv/anthropic-fellow` renders without 404 and displays the new summary + restructured sections.

### AC-4: GRA dates corrected
- **Given** today's date is post-May 2026
- **When** any variant (academic OR anthropic-fellow) compiles
- **Then** the `vt-gra-mrs` role shows `"April 2026 -- May 2026"` (not "Present"), and the change is committed to cv repo master.

### AC-5: Website link is the chosen "Other" URL
- **Given** the form's "Other links" field
- **When** the user fills it
- **Then** the value is `https://djjay0131.github.io/website/` (not a deeper URL like `/cv/anthropic-fellow`).

### AC-6: References R1 + R2 fully drafted, R3 resolved before submission
- **Given** the references section of this spec
- **When** the user prepares to submit
- **Then** R1 (Brown) and R2 (Afsari) have name + email + background + relationship paragraphs filled, and R3 has been identified by name with at least an email + relationship sentence.

### AC-7: Resume PDF uploaded to form is the new variant, not academic
- **Given** the form's resume upload field
- **When** the user uploads
- **Then** the file is `anthropic-fellow.pdf` (not `academic.pdf`), built from `data/variants/anthropic-fellow.yaml` after AC-4 lands.

### AC-8: Multi-select choices match this spec
- **Given** every multi-select field in the form
- **When** the user fills the form
- **Then** values match the table in *Form-answer matrix*: top team = AI Safety & Alignment; secondaries = Mech Interp + Frontier Red Team; cohort = July 20; workspace = Berkeley 25%+; work auth = USA; country = USA; previously applied = No (verify); applied to Anthropic/MATS/Astra/Fellows in past year = No (verify); AI policy = Yes.

### AC-9: Acceptance and continue-safety percentages are 100%
- **Given** the two % questions
- **When** the user answers
- **Then** both are 100% with the framing in this spec (deliberate mid-career pivot for accept-FT; safety commitment is not Anthropic-conditional for continue-safety).

### AC-10: Spec ready ≥48h before submission deadline
- **Given** the user's chosen submission deadline (ideally ≥1 week before July 20 to allow Constellation/reference outreach)
- **When** the spec is reviewed final-pass
- **Then** every "OQ-" item is resolved, every prose answer has been edited to user voice, and a test resume PDF has been built and reviewed.

## Technical Notes

### Affected files

**New:**
- `data/variants/anthropic-fellow.yaml`

**Modified:**
- `data/content/summaries.yaml` — append `fellowship` entry
- `data/content/employment.yaml` — fix `vt-gra-mrs` dates ("Present" → "May 2026")

**Unchanged:**
- All Python tooling, all templates, the website repo, `own-bib.bib`, all other content files, all other variants.

### Patterns to follow

- The variant uses the existing variant-selector DSL only (no resolver / template / website code changes).
- Bullet filtering, role collapse, and skills item subsetting follow the patterns documented in feature `variant-selector-dsl`.
- New summary entry follows the same shape as the existing `academic` summary — `id` + `text` (Markdown-formatted, double-stars for bold).

### Build + verify

```bash
cd /Users/djjay0131/code/cv
.venv/bin/python -m tools.lint_bib own-bib.bib    # sanity (should already pass)
make anthropic-fellow                              # builds PDF
open build/anthropic-fellow/anthropic-fellow.pdf   # human review
```

If `make` doesn't auto-discover the new variant: add to the `VARIANTS` list in the Makefile or invoke `python -m tools.render anthropic-fellow && latexmk ...` manually.

### Cross-repo flow

Once the variant is committed and pushed:
1. `cv` repo CI builds the academic + new variant PDFs, attaches both to the `latest` release.
2. `website` repo CI fetches the new release, renders `/cv/anthropic-fellow`.
3. The fellowship resume PDF is uploaded directly to the Airtable form (NOT served from the website by default — the website's published PDF stays as `academic.pdf` to match the website's positioning).

## Dependencies

- Existing variant-selector DSL (feature `variant-selector-dsl`, status IMPLEMENTED) — required for `bullets`, `collapse`, `items` selectors.
- Existing CV pipeline (feature `cv-website`, status VERIFIED) — required for `make <variant>` build.
- Existing `own-bib.bib` containing both papers (verified in current session: `brown2025exploringevidencebasedsebeliefs` and `cusati2026papers`).
- User actions external to the codebase: identifying R3, supplying R1/R2 emails, confirming/declining marketing/refer-to-others, supplying pronunciation/pronouns/how-heard if desired, deciding whether to set up a Google Scholar profile.

## Open Questions

All OQs resolved 2026-06-06. Remaining user actions tracked under **Outstanding User Actions** below.

- **OQ-1** *(resolved)*: Never applied to Anthropic/MATS/Astra/Fellows; never interviewed.
- **OQ-2** *(resolved)*: Google Scholar profile exists: https://scholar.google.com/citations?user=TPwNZK4AAAAJ&hl=en
- **OQ-3** *(resolved)*: R3 = **Dave Hollander** (davidhollander@gmail.com), senior collaborator from the Yoh / Core Specialty Insurance engagement. Adds an industry-ML execution voice that R1+R2 (both academic faculty) don't provide.
- **OQ-4** *(resolved)*: How heard = recommended by PhD advisor Dr. Chris Brown (Virginia Tech).
- **OQ-5** *(resolved)*: Marketing opt-in = Yes; Refer-to-other-orgs = Yes.
- **OQ-6** *(resolved)*: Workspace preference stays "Berkeley: 25%+", with explanation noting 25--50% expected and full-on-site acceptable if mentor matching requires.
- **OQ-7** *(resolved)*: Do **not** replace `/pdfs/academic.pdf` on the website. The new `anthropic-fellow` variant will be published on the website but on an unlinked page (no nav entry, no homepage link) so reviewers reaching `/cv/anthropic-fellow` from a direct URL see the targeted view; general visitors continue to see the academic CV.
- **OQ-8** *(resolved)*: Target submission = on or before July 20, 2026 (cohort start). Rolling review accepted given the late start (today: 2026-06-06). Earlier-is-better still applies — aim for the first week of July if drafts firm up.

## Outstanding User Actions

These are the only items still blocking submission:

- ~~Identify R3 (Yoh senior collaborator) — name + email.~~ ✅ **Dave Hollander, davidhollander@gmail.com** (2026-06-30)
- ~~Supply R1 (Chris Brown) email.~~ ✅ **dcbrown@vt.edu** (2026-06-30)
- ~~Supply R2 (Burcin Afsari) email; verify spelling.~~ ✅ **Kereshmeh Afsari, keresh@vt.edu** — name was Kereshmeh, not Burcin (2026-06-30)
- Email-warn all three references the day of submission (Anthropic contacts them without notice).
- Decide pronunciation / pronouns optional fields (skip is fine).
- Final eyeball pass on prose answers (Why Fellows, research areas, background, acceptance%, continue-safety%, references R1/R2/R3, anything-else) to convert from draft voice to user voice.
- Build + review the `anthropic-fellow.pdf` (2-page target) before upload.
