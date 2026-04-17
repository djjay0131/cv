# Feature: Variant Selector DSL + Expanded Content Pool

**Status:** IMPLEMENTED
**Date:** 2026-04-17
**Author:** Feature Architect (AI-assisted)

## Problem

The current variant selector can only include or exclude entire content items by ID (`include: [id1, id2]`). Real resume variants — evidenced by 20+ years of Jason's role-targeted resumes — require bullet-level selection within a role, skills subsetting, role collapsing (full entry vs. one-liner), and section toggling. Meanwhile, the content pool only covers 5 employment roles (2005–2025), missing LimeLeap (2002–2011 with 4+ sub-roles), NCMEC, Force Inc., A.T. Kearney, and dozens of bullet variants that appear across different resume versions.

Without this feature, creating a new resume variant means hand-authoring a new LaTeX document from scratch — exactly the workflow the data-driven pipeline was built to eliminate.

## Goals

- **G1**: Expand `data/content/employment.yaml` from 5 roles to all roles across Jason's career, including LimeLeap sub-roles (Chief Engineer, Director of Productivity Solutions, Team Leader, Senior SE, Software Developer), NCMEC, Force Inc., A.T. Kearney, and additional bullet variants from the 2020–2025 resume corpus. Key bullets that exist in meaningfully different lengths across resume versions are stored as separate IDs (e.g., `dc-upgrade-short`, `dc-upgrade-detailed`).
- **G2**: Expand `data/content/skills.yaml` to the superset of all tools, languages, platforms, and AI/ML items across all resume variants.
- **G3**: Extend the variant selector YAML schema to support: bullet-level filtering, role collapse flags, skills item subsetting, and implicit section toggling (sections not listed are not rendered).
- **G4**: Produce at least two working variant files from the expanded pool — the updated `academic.yaml` and one industry variant (e.g., `sde-long.yaml`) — proving the DSL works.
- **G5**: Both variants compile to PDF via `make <variant>` and render on the website with no code changes to the website repo.
- **G6**: No regression — `make academic` produces the same PDF content as today.

## Non-Goals

- **NG1**: Per-variant summary/title authoring DSL. Summaries are currently selected by `content_id` from the pool; per-variant custom prose is a follow-up.
- **NG2**: Per-variant bullet rewording (overriding a bullet's text in the selector). Bullets are selected or excluded, not rewritten. For different verbosity levels, store separate bullet IDs in the pool (e.g., `dc-upgrade-short`, `dc-upgrade-detailed`).
- **NG3**: Structured facts content model + LLM polish pipeline. Deferred to a follow-up feature (`content-facts-model`). The current text-based bullet approach continues — picking the best version of each bullet from the corpus.
- **NG4**: Template visual redesign. The `curve`-class layout stays as-is.
- **NG5**: Website repo changes. The website already consumes the resolved data shape; the DSL changes are internal to the `cv` repo's resolver.

## User Stories

- As Jason, I want to create a new resume variant by writing a short YAML selector that picks roles, bullets, and skills from the canonical pool, so I can target a job in minutes instead of hours.
- As Jason, I want to include only 3 of 8 Duck Creek bullets in my Cloud Architect resume, so the CV stays on 2 pages and emphasizes the right accomplishments.
- As Jason, I want my LimeLeap/NCMEC/Force Inc./A.T. Kearney roles collapsed into a one-liner "Earlier employment..." paragraph in most variants, but expandable to full entries when I need a long-form CV.
- As Jason, I want to omit the publications and projects sections from a short industry resume, so it focuses on employment and skills.
- As Jason, I want to select a subset of skills per variant (e.g., drop AngularJS and PHP from a Python-focused role), so the skills section is relevant to the target.
- As Jason, I want to choose between a short and detailed version of the same accomplishment bullet depending on whether I'm targeting a 1-page or 3-page resume.

## Design Approach

### Extended Selector Schema

The `include` list entries can be **strings** (backwards-compatible, include all) OR **objects** with filtering. Parsing is **context-aware**: the parent section's `type` determines which selector model is used (e.g., `type: employment` → `EmploymentSelector`, `type: skills` → `SkillSelector`).

```yaml
# data/variants/<variant>.yaml
variant: sde-long
sections:
  - type: summary
    content_id: academic

  - type: employment
    include:
      # Simple string: include all bullets, no collapse
      - yoh-adf-architect

      # Object: pick specific bullets by ID
      - id: duck-creek-architect
        bullets: [dc-launch, dc-integration, dc-adf, dc-deployment-detailed, dc-sev1]

      # Object: all bullets but collapsed to one-liner
      - id: limeleap-chief-engineer
        collapse: true
      - id: ncmec-web-consultant
        collapse: true
      - id: force-inc-writer
        collapse: true
      - id: at-kearney-designer
        collapse: true

  - type: education
    include: [phd-cs-vt, meng-cs-vt, bs-econ-vt]

  # Sections not listed (publications, projects) are not rendered

  - type: skills
    include:
      # Simple string: all items in the group
      - platforms
      # Object: pick specific items from the group
      - id: tools
        items: [SQL Server, PostgreSQL, Azure, Docker, Octopus, FastAPI, Streamlit]
      - id: languages
        items: [C#, Java, Python, PowerShell, Bash, JavaScript]
      - id: ai-ml

  - type: misc
  - type: referee
    content_id: available
```

### Schema Changes (`tools/schema.py`)

Context-aware parsing: `VariantSection` parses `include` entries based on its `type` field.

```python
class EmploymentSelector(_StrictModel):
    id: str = Field(min_length=1)
    bullets: Optional[list[str]] = None   # None = all bullets
    collapse: bool = False

class SkillSelector(_StrictModel):
    id: str = Field(min_length=1)
    items: Optional[list[str]] = None     # None = all items

# VariantSection gains a validator that parses include entries:
# - type == "employment": str | EmploymentSelector
# - type == "skills": str | SkillSelector
# - all other types: str only (no object selectors)
```

### Resolver Changes (`tools/resolver.py`)

1. **Bullet filtering**: when `bullets` is specified, filter `role.bullets` to only those IDs. Order follows the selector (variant author controls the narrative).
2. **Collapse flag**: passed through to resolved data as `ResolvedEmploymentEntry(role=..., collapse=True/False)`.
3. **Skills item subsetting**: when `items` is specified, replace the group's items list with the subset. Validates all items exist in the pool group.
4. **Duplicate bullet ID detection**: error on duplicate bullet IDs in a single selector (prevents typos).

Resolved employment shape changes:
```python
class ResolvedEmploymentEntry:
    role: EmploymentRole    # with bullets possibly filtered
    collapse: bool          # False for normal, True for one-liner
```

### Template Changes

`templates/tex/employment.tex.j2` gains collapse support:
- Non-collapsed roles render as before (full `\entry*[dates]` with `\begin{itemize}` bullets).
- Collapsed roles are collected via `namespace()` and rendered as a single `\entry*{Earlier employment history includes tenure as...}` paragraph at the end.
- Empty bullet lists (`bullets: []`) render the role header without an `\begin{itemize}` block.

### Content Pool Expansion

**New employment entries** added to `data/content/employment.yaml`:

| Role ID | Company | Dates | Source |
|---|---|---|---|
| `limeleap-chief-engineer` | LimeLeap Solutions | 2005–2011 | 2020 Principal Engineer resume |
| `limeleap-director-productivity` | LimeLeap Solutions | (sub-role) | 2025 SDE Long |
| `limeleap-team-leader` | LimeLeap Solutions | (sub-role) | 2025 SDE Long |
| `limeleap-senior-se` | LimeLeap Solutions | (sub-role) | 2025 SDE Long |
| `limeleap-developer` | LimeLeap Solutions | (sub-role) | 2025 SDE Long |
| `ncmec-web-consultant` | NCMEC | (pre-2005) | 2025 SDE Long |
| `force-inc-writer` | Force, Inc. | (pre-2005) | 2025 SDE Long |
| `at-kearney-designer` | A.T. Kearney | (pre-2005) | 2025 SDE Long |

**Additional bullets** added to existing roles (Duck Creek, Blackbaud) from the 2025 SDE Long resume. Key bullets with meaningfully different lengths stored as separate IDs:
- `dc-upgrade-short` ("Saved 100's of hours by developing automated upgrade scripts")
- `dc-upgrade-detailed` ("Saved hundreds of hours...written in PowerShell for a 3-year-old Octopus instance and overseeing multiple exception cases")
- Similar pattern for other bullets where short/detailed versions exist across the corpus.

**Skills expansion**: `data/content/skills.yaml` expanded to the superset across all variants. New items added to existing groups (e.g., `AngularJS`, `Entity Framework`, `jQuery`, `R Studio`, `PyCharm`, `Wireshark`, `Gradle`, `Vue.js`, etc.). New AI/ML items: `KNN`, `RNN`, `CNN`, `Naive Bayes`, `Linear Regression`.

### Backwards Compatibility

The current `academic.yaml` format (`include: [id1, id2]`) continues to work unchanged. String entries in `include` are treated as "include all, no collapse." The M1 academic variant requires zero changes to the variant file.

## Sample Implementation

```python
# tools/schema.py — context-aware include parsing

class EmploymentSelector(_StrictModel):
    id: str = Field(min_length=1)
    bullets: Optional[list[str]] = None
    collapse: bool = False

class SkillSelector(_StrictModel):
    id: str = Field(min_length=1)
    items: Optional[list[str]] = None

class VariantSection(_StrictModel):
    type: str = Field(min_length=1)
    include: Optional[list] = None        # raw; parsed in validator
    content_id: Optional[str] = None

    @field_validator("include", mode="before")
    @classmethod
    def _parse_include(cls, v, info):
        # Context-aware parsing happens in resolve, not here,
        # because we need the `type` field which isn't available
        # in a field validator on a sibling field reliably.
        # Store raw and parse in a model_validator or at resolution time.
        return v
```

```python
# tools/resolver.py — extended resolution

@dataclass
class ResolvedEmploymentEntry:
    role: EmploymentRole
    collapse: bool

def _parse_employment_include(raw_include):
    """Parse mixed string/object include list for employment."""
    entries = []
    for item in raw_include:
        if isinstance(item, str):
            entries.append(EmploymentSelector(id=item))
        else:
            entries.append(EmploymentSelector(**item))
    return entries

def _resolve_employment(pool, section):
    selectors = _parse_employment_include(section.include)
    entries = []
    for sel in selectors:
        role = _lookup_one(pool.employment, sel.id, "employment")
        if sel.bullets is not None:
            # Validate no duplicates
            if len(sel.bullets) != len(set(sel.bullets)):
                raise ValueError(f"duplicate bullet IDs in selector for '{sel.id}'")
            # Filter and reorder bullets per selector
            bullet_map = {b.id: b for b in role.bullets}
            filtered = []
            for bid in sel.bullets:
                if bid not in bullet_map:
                    raise MissingContentIdError(
                        f"employment role '{sel.id}': unknown bullet '{bid}'"
                    )
                filtered.append(bullet_map[bid])
            role = role.model_copy(update={"bullets": filtered})
        entries.append(ResolvedEmploymentEntry(role=role, collapse=sel.collapse))
    return entries

def _parse_skills_include(raw_include):
    """Parse mixed string/object include list for skills."""
    entries = []
    for item in raw_include:
        if isinstance(item, str):
            entries.append(SkillSelector(id=item))
        else:
            entries.append(SkillSelector(**item))
    return entries

def _resolve_skills(pool, section):
    selectors = _parse_skills_include(section.include)
    groups = []
    for sel in selectors:
        group = _lookup_one(pool.skills, sel.id, "skills")
        if sel.items is not None:
            pool_items = set(group.items)
            for requested in sel.items:
                if requested not in pool_items:
                    raise ValueError(
                        f"skill group '{sel.id}': unknown item '{requested}'"
                    )
            group = group.model_copy(update={"items": sel.items})
        groups.append(group)
    return groups
```

```jinja
{# templates/tex/employment.tex.j2 — with collapse support #}
\begin{rubric}{Professional Experience}
{% set ns = namespace(collapsed=[]) %}
{% for entry in employment %}
{% if not entry.collapse %}
\entry*[{{ entry.role.dates }}]
    \textbf{ {{- entry.role.company | md_to_latex }} --- {{ entry.role.location | md_to_latex -}} } \emph{ {{- entry.role.title | md_to_latex -}} }
{% if entry.role.bullets %}
 \begin{itemize}
{% for bullet in entry.role.bullets %}
        \item {{ bullet.text | md_to_latex }}
{% if not loop.last %}

{% endif %}
{% endfor %}
    \end{itemize}
{% endif %}

{% else %}
{% set _ = ns.collapsed.append(entry.role) %}
{% endif %}
{% endfor %}
{% if ns.collapsed %}
\entry*{Earlier employment history includes tenure as
{%- for r in ns.collapsed %} {{ r.title | md_to_latex }}, {{ r.company | md_to_latex -}}
{%- if not loop.last %}; {% else %}.{% endif %}
{%- endfor %}}
{% endif %}
\end{rubric}
```

## Edge Cases & Error Handling

### EC-1: Bullet ID not found in role
- **Scenario**: Variant requests `bullets: [nonexistent-bullet]` for a role.
- **Behavior**: `MissingContentIdError` raised with role ID and bullet ID in the message.
- **Test**: Fixture variant with bad bullet ID; assert error names both IDs.

### EC-2: Skill item not found in group
- **Scenario**: Variant requests `items: [NonexistentTool]` for a skill group.
- **Behavior**: `ValueError` raised naming the group and the unknown item.
- **Test**: Fixture variant with bad skill item; assert error is clear.

### EC-3: All roles collapsed (no expanded entries)
- **Scenario**: Variant has every employment entry set to `collapse: true`.
- **Behavior**: No full entries rendered; only the "Earlier employment..." paragraph. Template handles gracefully.
- **Test**: Variant with all-collapsed employment; assert output contains "Earlier employment" and no `\begin{itemize}`.

### EC-4: Empty bullets list (explicitly empty)
- **Scenario**: Variant specifies `bullets: []` for a role — meaning "include the role header but no bullets."
- **Behavior**: Role renders with company/title/dates but no `\begin{itemize}` block. Template checks for non-empty bullets.
- **Test**: Variant with `bullets: []`; assert role header appears without bullet list.

### EC-5: Mixed string and object entries in include
- **Scenario**: `include: [yoh-adf-architect, {id: duck-creek-architect, bullets: [dc-launch]}]`
- **Behavior**: First entry includes all bullets; second filters to one. Both resolve correctly.
- **Test**: Variant with mixed entry types; assert both render with correct bullet counts.

### EC-6: Section not listed in variant
- **Scenario**: Variant omits `publications` and `projects` from sections list.
- **Behavior**: Those sections produce empty `.tex` files (current behavior — already works in M1).
- **Test**: Existing `test_section_not_declared_produces_empty_file` covers this.

### EC-7: Backwards compatibility with M1 academic.yaml
- **Scenario**: The current `academic.yaml` with `include: [id1, id2]` string-only format.
- **Behavior**: Works unchanged — string entries parsed as simple IDs with all bullets and no collapse.
- **Test**: Existing academic variant tests continue to pass with zero changes to the variant file.

### EC-8: Duplicate bullet IDs in selector
- **Scenario**: `bullets: [dc-launch, dc-launch]` — same bullet requested twice.
- **Behavior**: Error raised naming the role and the duplicate bullet ID. Duplicates suggest a typo.
- **Test**: Fixture with duplicate bullet ID; assert error.

### EC-9: Employment selector fields on a skills section (or vice versa)
- **Scenario**: A skills section include entry has `{id: "platforms", collapse: true}`.
- **Behavior**: `SkillSelector` parsing rejects unknown field `collapse` via `extra="forbid"`. Clear Pydantic validation error.
- **Test**: Fixture with cross-type selector fields; assert Pydantic error.

### EC-10: Multiple length variants of same bullet
- **Scenario**: Pool has `dc-upgrade-short` and `dc-upgrade-detailed`. Variant picks one.
- **Behavior**: Normal bullet-level selection — the variant includes whichever ID it wants.
- **Test**: Variant picks `dc-upgrade-short`; assert the short version appears and the detailed one does not.

## Acceptance Criteria

### AC-1: Expanded employment pool
- **Given** the content pool at `data/content/employment.yaml`
- **When** inspected
- **Then** it contains all roles from Jason's career: Yoh, Duck Creek, Blackbaud (Principal + Solution Architect), DJJayNet, LimeLeap (Chief Engineer + sub-roles as separate collapse-able entries), NCMEC, Force Inc., A.T. Kearney. Each role has a stable ID. Key bullets with meaningfully different lengths have separate IDs (e.g., `dc-upgrade-short`, `dc-upgrade-detailed`).

### AC-2: Expanded skills pool
- **Given** the content pool at `data/content/skills.yaml`
- **When** inspected
- **Then** it contains the superset of tools, languages, platforms, and AI/ML items across all resume variants (including AngularJS, Entity Framework, R Studio, PyCharm, Wireshark, scikit-learn, TensorFlow, KNN, RNN, CNN, etc.).

### AC-3: Bullet-level filtering
- **Given** a variant selector with `{id: duck-creek-architect, bullets: [dc-launch, dc-adf]}`
- **When** `make <variant>` runs
- **Then** the Duck Creek role renders with only those 2 bullets, not all 5+. Bullet order matches the selector, not the pool.

### AC-4: Role collapse
- **Given** a variant selector with `{id: limeleap-chief-engineer, collapse: true}`
- **When** `make <variant>` runs
- **Then** LimeLeap appears in an "Earlier employment..." one-liner paragraph, not as a full entry with bullets.

### AC-5: Skills item subsetting
- **Given** a variant selector with `{id: languages, items: [Python, C#, Java]}`
- **When** `make <variant>` runs
- **Then** the Languages skill group shows only those 3 items, not the full list.

### AC-6: Section toggling by omission
- **Given** a variant selector that does not list `publications` or `projects` in `sections`
- **When** `make <variant>` runs
- **Then** those sections do not appear in the PDF.

### AC-7: Two working variants
- **Given** `data/variants/academic.yaml` (unchanged) and `data/variants/sde-long.yaml` (new)
- **When** `make academic` and `make sde-long` are run
- **Then** both produce valid PDFs. The academic PDF matches today's output (no regression). The sde-long PDF demonstrates bullet filtering, role collapse, and/or skills subsetting.

### AC-8: Backwards compatibility
- **Given** the current `academic.yaml` with string-only `include` lists
- **When** `make academic` runs
- **Then** the output is identical to today — no changes to the variant file are required.

### AC-9: Bad bullet/skill ID fails loudly
- **Given** a variant referencing a nonexistent bullet ID or skill item
- **When** `make <variant>` runs
- **Then** the build fails with a clear error naming the variant, the role/group, and the unknown ID/item.

### AC-10: Website renders both variants
- **Given** both `academic.yaml` and `sde-long.yaml` variants
- **When** the website is rebuilt
- **Then** `/cv/academic` and `/cv/sde-long` both render correctly with the appropriate content differences.

## Technical Notes

### Affected components
- **Modified**: `tools/schema.py` (new `EmploymentSelector`, `SkillSelector` models; context-aware `include` parsing per section type), `tools/resolver.py` (bullet filtering, collapse flag, skills subsetting, duplicate detection), `templates/tex/employment.tex.j2` (collapse rendering + empty-bullets guard), `templates/tex/skills.tex.j2` (no structural change — resolver handles subsetting).
- **Expanded**: `data/content/employment.yaml` (new roles + bullet variants), `data/content/skills.yaml` (superset items).
- **New**: `data/variants/sde-long.yaml`.
- **Unchanged**: `data/variants/academic.yaml`, `tools/render.py`, `tools/converters.py`, `tools/lint_bib.py`, `cv-llt.tex`, `settings.sty`, website repo.

### Patterns to follow
- Pydantic `model_copy(update={...})` for creating filtered copies of pool items (immutable originals).
- `MissingContentIdError` for ID lookup failures (existing pattern from `resolver.py`).
- Jinja `namespace()` for mutable state inside template loops (required for collecting collapsed roles).
- All new schema models extend `_StrictModel` with `extra="forbid"`.
- Context-aware parsing: `VariantSection` parsing dispatches on `type` field — employment sections parse objects as `EmploymentSelector`, skills sections as `SkillSelector`, all others reject object entries.

### Data model changes
- `VariantSection.include` stores raw data (list of str/dict); parsing into typed selectors happens at resolution time based on section type.
- Resolved employment shape changes from `list[EmploymentRole]` to `list[ResolvedEmploymentEntry]` (role + collapse flag).
- `ResolvedCV.employment` type updated accordingly; website `cv-data.ts` types may need a minor update to handle the `collapse` field (but the website can ignore it — collapsed roles are rendered normally in HTML).

### Template contract change
- `employment.tex.j2`: loop variable changes from `role` (an `EmploymentRole`) to `entry` (a `ResolvedEmploymentEntry` with `.role` and `.collapse`).
- Empty bullets guard: `{% if entry.role.bullets %}` wraps the `\begin{itemize}` block.

## Dependencies

- No new Python dependencies. Pydantic, Jinja2, PyYAML already in place.
- Content expansion requires reading the resume corpus at `~/Library/CloudStorage/GoogleDrive-djjay0131@gmail.com/My Drive/Professional Development/Resumes/` (already accessible).
- Website repo unchanged — it consumes the same resolved shape via the data artifact.

## Follow-up Items (not in this spec)

- **Content Facts Model + LLM Polish**: store structured facts (`action`, `tools`, `outcome`, `metric`) instead of pre-written text; generate audience-appropriate prose at build time with optional LLM polish and cached output. Eliminates the need for separate short/detailed bullet IDs. Deferred because it requires migrating every bullet and adds API dependency.
- **Per-variant summary/title authoring**: custom title line and summary paragraph per variant, authored directly in the selector YAML.
- **Per-variant competencies/keywords**: custom keyword list per variant (currently not supported).

## Open Questions

- **OQ-1**: Should `bullets` order in the selector override the pool order? Recommendation: selector order (variant author controls the narrative). Decide at implementation.
- **OQ-2**: Should collapsed roles render dates in the one-liner? e.g., "Chief Engineer, LimeLeap Solutions (2005–2011)". Recommendation: include dates — they're useful context. Decide at implementation.
- **OQ-3**: LimeLeap sub-roles — separate pool entries (recommended, more flexible) or sub-entries under one role? Decide at implementation.
- **OQ-4**: Duplicate bullet IDs in selector — error (recommended) or deduplicate silently? Decide at implementation.
- **OQ-5**: Should `Makefile` `VARIANTS` auto-discover all `.yaml` files in `data/variants/`? Recommendation: yes. Decide at implementation.
