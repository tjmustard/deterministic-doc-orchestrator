# Deterministic Document Orchestrator (DDO)
## From Project Aegis to a General-Purpose Intelligence-Augmented Document Engine

---

> **Purpose of this document:** This is a project brief intended to seed a co-researcher AI session for the purpose of generating a Product Requirements Document (PRD) for a new software project: **deterministic-doc-orchestrator**. It is written in the voice of the system's designer and is meant to be verbose, technically precise, and complete enough that an AI research collaborator can ask intelligent follow-up questions, challenge assumptions, and co-author a rigorous PRD without needing additional context.

---

## Table of Contents

1. [Origin Story — Project Aegis](#1-origin-story--project-aegis)
2. [How Aegis Works — Technical Deep-Dive](#2-how-aegis-works--technical-deep-dive)
3. [Where Aegis Falls Short](#3-where-aegis-falls-short)
4. [The DDO Vision](#4-the-ddo-vision)
5. [The DDO Workflow — Five-Phase Pipeline](#5-the-ddo-workflow--five-phase-pipeline)
6. [The Persona System](#6-the-persona-system)
7. [Template Generation from Existing Documents](#7-template-generation-from-existing-documents)
8. [DDO Technical Architecture](#8-ddo-technical-architecture)
9. [Homage to Aegis — What We Inherit and What We Add](#9-homage-to-aegis--what-we-inherit-and-what-we-add)
10. [Gap Analysis — Aegis vs. DDO](#10-gap-analysis--aegis-vs-ddo)
11. [Open Questions for the PRD Session](#11-open-questions-for-the-prd-session)

---

## 1. Origin Story — Project Aegis

### 1.1 What Aegis Is

Project Aegis is a Claude Code-based toolkit, built in early 2026, for generating tailored resumes and cover letters from a structured YAML career database. It was motivated by a simple observation: most people treat resume generation as a creative writing problem, and that framing produces hallucinated metrics, generic phrasing, and inconsistent presentation. Aegis reframes it:

> **"Resume tailoring is a data routing problem, not a creative writing exercise."**

That reframe is the intellectual seed of everything that follows.

Aegis v0.4.1 is a mature, production-grade system that the designer has used to generate 40+ real job applications. It works. It eliminates hallucination. It produces ATS-optimized PDFs in a single Claude Code session. It is the proof of concept that the architecture described in this document is sound.

### 1.2 The Core Insight That Transfers

The central design principle of Aegis — which transfers in full to DDO — is this:

> **"Every generated word traces back to a source of truth you control."**

In Aegis, that source of truth is `master_career_db.yaml`: a structured, version-controlled YAML file containing every professional achievement, skill, and metric the designer has ever produced. Nothing in a generated resume is invented by the LLM. The LLM routes, filters, and reorders existing data. That is it.

DDO extends this principle to any document type. The source of truth is still a structured YAML file. The LLM still does not invent. The document is still deterministic in the sense that two runs with the same YAML and the same template produce the same document. The only thing that changes between domains is the schema of the YAML and the shape of the templates.

### 1.3 Why a New Project

Aegis is domain-specific. Its skills reference career databases, job descriptions, cover letters, and resumes. Its templates are Typst files designed for single-page resume layouts. Its phase gates ask questions like "should I include a cover letter?" that make no sense outside of a hiring context.

DDO generalizes Aegis to be document-type agnostic. The same architecture — YAML source of truth, state machine workflow, template rendering, human-in-the-loop phase gates — works equally well for a scientific publication, a patent disclosure, a product requirements document, a grant proposal, or a legal brief. The only thing that changes is the schema and the personas.

DDO also adds capabilities that Aegis does not have and cannot reasonably be retrofitted with: an adversarial red team review loop, a structured interview for human resolution of red team findings, a persona system for domain-specific critique, and template generation with interview-driven validation. These are new enough that they deserve a new project rather than a major version bump.

---

## 2. How Aegis Works — Technical Deep-Dive

This section documents Aegis as it exists today. It is detailed enough to be used as a reference spec when building DDO.

### 2.1 Three-Layer Architecture

Aegis is organized around three explicit layers:

#### Layer 1 — Data (YAML)

The canonical source of truth is `aegis/master_career_db.yaml`. This file contains the designer's complete professional history, decomposed into atomic, reusable units called `atomic_achievements`. Each achievement is a single sentence describing one thing the person did, with explicit metadata:

```yaml
atomic_achievements:
  - id: sandboxaq-ecosystem-arch
    bullet: "Leads product definition and ecosystem architecture for core scientific assets, transforming proprietary Large Quantitative Models (LQMs) and datasets into standardized, revenue-generating API products."
    skills_applied: [LQMs, API-First Microservices, Cloud Marketplaces, GCP, AWS, Azure]
    impact_metrics: []
    tags: [ecosystem, cloud, platform, api]
```

The full schema is:

```yaml
personal_info:
  name: string
  credentials: string
  contact:
    email: string
    phone: string
    location: string
    linkedin: url
    github: url (optional)
    orcid: string (optional)

professional_summary: string

skills_taxonomy:
  <category_label>: [string]

professional_experience:
  - company: string
    roles:
      - title: string
        start_date: string
        end_date: string
        display_title: string (optional)
        display_title_variants: [string] (optional)
    context: string
    atomic_achievements:
      - id: string
        bullet: string
        skills_applied: [string]
        impact_metrics: [string]
        tags: [string]

education:
  - degree: string
    field: string
    institution: string
    year: string
    notes: string

publications:
  - id: int
    citation: string
    year: int
    tags: [string]

patents: (optional)
  - title: string
    year: int
    status: string
```

The `master_career_db.yaml` file for the current user is 1,311 lines and represents a decade of career history with atomic decomposition throughout.

**Why atomic decomposition?** Because the LLM is not generating achievements; it is selecting and routing existing ones. Each atomic node is a stable, versioned unit of career truth. When the LLM proposes to include an achievement in a tailored resume, it references it by ID. When an achievement needs updating, it is updated once in the master DB and every subsequent document derived from it automatically picks up the change.

#### Layer 2 — Cognition (State Machine)

The cognitive layer is implemented as a series of slash commands and skill files. The most important is `/aegis-tailor`, which drives a strict six-phase state machine:

- **Phase 0:** Ask user whether a cover letter is needed. Hard stop for response.
- **Phase 1:** Deconstruct the job description. Extract core requirements, keywords, domain signals, seniority indicators. Output a "Target Profile." Hard stop for user approval.
- **Phase 2:** Propose specific atomic achievements from the master DB that match the Target Profile. For roles with `display_title_variants`, select the variant that best matches the job description's language. Include ORCID in the tailored resume if the job description is scientific. Hard stop for user approval.
- **Phase 3 (if cover letter):** Draft cover letter content anchored to 1-2 selected achievements. Show full text inline. Hard stop for user approval.
- **Phase 3.5 (if cover letter):** Fit-check. Build the cover letter PDF. If it overflows one page, run a Python paragraph analysis script using `pypdf` to extract text layout, score each paragraph by word count divided by last-line fill percentage, identify the best trim target, propose cuts, get user approval, apply, rebuild, and repeat until the letter fits on one page.
- **Phase 5 (cover letter edits sync):** Review all wording changes made during Phases 3 and 3.5. Identify which changes represent standing preferences (not just page-fit trims). Propose syncing those changes back to `master_career_db.yaml`. Approve/edit/skip per change.
- **Phase 4:** Final compilation. Write `tailored_resume.yaml` and `cover_letter.yaml` to the application folder. Run the build script. Generate PDFs.

The hard stops are not optional. The skill file includes explicit `[WAITING FOR USER APPROVAL]` directives at each gate. The LLM is not permitted to proceed past a gate without a user response. This is the mechanism that prevents the LLM from generating the full output in one autoregressive burst, which is both the major failure mode of LLM-assisted document generation and the thing Aegis is most explicitly designed to prevent.

#### Layer 3 — Presentation (Typst Templates)

Typst is a modern, Rust-based typesetting engine that compiles `.typ` files to PDF. It natively parses YAML, which means templates consume structured data directly with no intermediate transformation step:

```typst
#let data_file = sys.inputs.at("data_file", default: "tailored_resume.yaml")
#let data = yaml(data_file)

// Render experience section by iterating over YAML array
#for job in data.professional_experience {
  let primary_role = job.roles.first()
  let display = if "display_title" in primary_role { 
    primary_role.display_title 
  } else { 
    primary_role.title 
  }
  resume-entry(
    title: display,
    date: job.roles.last().start_date + " -- " + primary_role.end_date,
    description: job.company,
  )
  resume-item[
    #for ach in job.atomic_achievements [
      - #ach.bullet
    ]
  ]
}
```

Templates are pure functions: the same YAML in always produces the same PDF out. There is no state, no runtime mutation, no LLM-generated layout decisions. This is what "deterministic" means in the project name.

The build pipeline:

```
tailored_resume.yaml
    ↓
build.py (Python, PEP 723 inline deps, uv)
    ↓
typst compile resume.typ --input data_file=<yaml_path>
    ↓
Thomas_J_L_Mustard-Resume.pdf
```

The Python build script (`aegis/build.py`) handles one task: extracting the name from the YAML file, constructing the output filename, and calling the Typst CLI with the correct arguments. The Typst template handles everything else. The build is hermetic: `uv run build.py` creates an ephemeral virtual environment with inline-declared dependencies, runs the build, and exits. No persistent virtualenvs, no global package state.

### 2.2 All Slash Commands

Aegis exposes eight domain-specific slash commands:

| Command | What It Does |
|---|---|
| `/aegis-tailor <jd-path>` | Full 6-phase interactive workflow from JD to compiled PDFs |
| `/aegis-score <jd-path>` | 4-dimension match scoring, gap analysis, ATS keyword check, optional achievement enrichment |
| `/aegis-db-edit <instruction>` | Propose/review/approve changes to master DB with before/after blocks |
| `/aegis-generate` | Compile PDFs from existing YAMLs without re-running tailoring |
| `/aegis-ingest` | Parse master_resume.md into master_career_db.yaml; zero hallucination tolerance |
| `/aegis-render <pdf>` | Analyze a resume PDF and generate a Typst template that replicates its visual design |
| `/cover-letter <jd-path>` | Quick single-pass cover letter without the full interactive workflow |
| `/tailor-resume <jd-path>` | Quick single-pass tailored resume without the full interactive workflow |

Each slash command is a thin wrapper that reads the corresponding skill file from `aegis/skills/` and follows its instructions. The separation between command dispatch (`.claude/commands/`) and skill implementation (`aegis/skills/`) is deliberate: commands are one-liners, skills are the detailed instruction sets.

### 2.3 Skill Architecture

Six skill files implement the core logic:

**`skill_tailor_interactive.md`** (~11,260 characters) — The heart of Aegis. Implements the 6-phase state machine described above. Includes the Phase 3.5 paragraph analysis Python script inline, the cover letter YAML schema, the tailored resume YAML schema, and all phase gate directives. The skill is explicit about what the LLM is and is not permitted to do at each phase.

**`skill_score_jd.md`** (~4,634 characters) — Career Strategy Engine. Scores match across four dimensions (Technical Skills Match 30pts, Experience Depth 30pts, Domain Alignment 20pts, Leadership/Soft Skills 20pts). Classifies gaps as Fillable/Partial/True Gap. Drafts new atomic achievements for Fillable gaps following exact schema and style constraints.

**`skill_db_edit.md`** (~3,454 characters) — Career DB Editor. Accepts natural language or explicit change instructions. Presents numbered before/after blocks for each proposed change. Supports approve/edit/skip per change and "approve all"/"skip all" shortcuts. Never writes before all approvals are collected.

**`skill_ingest_master.md`** (~980 characters) — Strict data-extraction agent. Parses flat Markdown resume into structured YAML. Zero hallucination tolerance: no invented dates, metrics, skills, or responsibilities. Extracts hard numbers into `impact_metrics` arrays. Flags missing context with `[REQUIRES USER INPUT]`.

**`skill_replicate_template.md`** (~352 characters) — Analyzes a resume PDF or image and constructs a Typst template that natively parses `tailored_resume.yaml`. Initial output is a draft; the user compiles, observes visual discrepancies, and reports them for iterative debugging.

**`skill_document.md`** (~4,401 characters) — Documentation agent. Updates README.md and CHANGELOG.md after code changes. Runs a PII scan replacing real company names, product names, personal contact info, and conference names with generic placeholders before committing docs to version control.

### 2.4 Writing Style as Enforced Specification

`aegis/writing_style.md` is not a suggestion. It is read by every skill that generates written content. The rules:

- **No em-dashes.** Replace with comma and space. Wrong: `I know your platform — not just as an admirer.` Right: `I know your platform, not just as an admirer.`
- **Professional but direct.** Confident without boastful.
- **First-person, active voice.**
- **No filler phrases, no corporate jargon, no hedging language.**

These rules are machine-readable constraints, not style advice. The skills check their output against them.

### 2.5 The Cover Letter Fit-Check Algorithm

This is worth documenting in detail because it is one of the most sophisticated sub-components of Aegis and should be preserved in DDO.

When a cover letter overflows one page, the system does not randomly cut text. It runs a paragraph efficiency analysis:

1. Build the PDF using Typst.
2. Extract the text layout using `pypdf` (a Python library for PDF parsing).
3. For each paragraph, measure:
   - Total word count
   - Last-line fill percentage (how full is the last line of the paragraph, as a fraction of page width)
4. Score each paragraph: `score = word_count / last_line_fill`
5. The highest-scoring paragraph with a last-line fill below 50% is the best trim target (cutting its last partial line will save the most vertical space for the fewest lost words).
6. Propose specific sentence cuts from that paragraph with word count deltas.
7. Get user approval for each proposed cut.
8. Apply cuts, rebuild PDF, re-run analysis.
9. Repeat until page count = 1.

This algorithm is heuristic but principled. It minimizes word loss while maximizing space recovered. It preserves user control by requiring approval for every cut.

### 2.6 Data Flow Summary

```
master_career_db.yaml          (1,311 lines, decade of career history)
         ↓
/aegis-tailor <jd-path>
         ├─ [Phase 1] JD → Target Profile          → USER APPROVAL
         ├─ [Phase 2] Achievements selected         → USER APPROVAL
         ├─ [Phase 3] Cover letter drafted          → USER APPROVAL
         ├─ [Phase 3.5] Fit-check loop              → USER APPROVAL per cut
         ├─ [Phase 5] DB sync loop                  → USER APPROVE/SKIP per change
         └─ [Phase 4] Final compile
         ↓
tailored_resume.yaml   +   cover_letter.yaml
         ↓
build-all.py → typst compile (resume.typ, coverletter2.typ)
         ↓
[Name]-Resume.pdf   +   [Name]-Cover_Letter.pdf
         ↓
Applications/YYYY.MM.DD_Company_Role/
```

---

## 3. Where Aegis Falls Short

Aegis is production-ready for its intended use case. But it has hard limitations that are worth documenting honestly, because DDO is designed to address each of them.

### 3.1 Document-Type Lock-In

Every skill, schema field, template, and phase gate in Aegis assumes the output is a resume or cover letter. The vocabulary is career vocabulary: "job description," "atomic achievements," "cover letter," "ATS keywords." There is no mechanism to point Aegis at a scientific report draft and ask it to review the methodology section.

**DDO fix:** Fully agnostic document-type system. The YAML schema is extensible per domain. Skills are parameterized by persona rather than hardcoded to career context.

### 3.2 Output Format Lock-In

Aegis generates PDFs only, via Typst. There is no path to HTML, DOCX, Markdown, or any other format. For resumes and cover letters this is fine. For scientific reports, PRDs, or patent disclosures, PDF is often not the right output format.

**DDO fix:** Multi-format output. Same YAML, same templates in different formats: Typst for PDF, Jinja2 for HTML/DOCX/MD, Pandoc as a conversion layer. Same pipeline handles all formats.

### 3.3 No Adversarial Review Loop

Aegis generates a document and then the user either accepts it or manually edits it. There is no mechanism to systematically stress-test the generated document. No agent reads it and asks: "Is this claim supported? Does this section contradict that one? Is the logic of this paragraph internally consistent? Would a skeptical reader find holes in this?"

This is arguably the most significant missing capability. A document that has never been adversarially reviewed is a document whose weaknesses are unknown.

**DDO fix:** The red team phase (Phase 3 in the DDO pipeline) is a dedicated adversarial agent that reads the rendered document and systematically attacks it. The output is a structured `red_team_report.yaml` with issues ranked by severity, categorized by type, and paired with suggested resolutions.

### 3.4 No Structured Refinement Dialogue

When Aegis users want to improve a document, they do so by manually editing YAML files or providing ad-hoc instructions. There is no structured process for systematically working through a list of issues one at a time, capturing the user's responses, and using those responses to update the source data.

**DDO fix:** The interview phase (Phase 4) presents red team findings to the user in batches of 1-3 issues at a time. The agent asks targeted questions, captures answers, and compiles everything into an `interview_log.yaml`. The refine phase (Phase 5) merges the interview log back into the source YAML and triggers a rebuild.

### 3.5 Template Generation Is One-Shot and Unvalidated

`/aegis-render` generates a Typst template from a PDF image of a resume. The initial output is frequently inaccurate because current vision models lack pixel-perfect spatial reasoning. The iteration loop is entirely freeform: the user compiles the template, observes problems, reports them in natural language, and the agent attempts to fix them. There is no structured validation interview, no schema extraction, and no guarantee that the final template is correct.

**DDO fix:** Template generation (`/ddo-template-gen`) adds a structured interview validation step. After generating the initial template, the agent renders it with synthetic data, presents the output, and walks the user through a structured review: "Does section X match the reference? Is the heading hierarchy correct? Are these fields in the right order?" The output includes not just the template file but a `template_schema.yaml` describing what YAML fields the template expects.

### 3.6 No Persona System

Every Aegis skill assumes the same reviewing perspective: a career coach/ATS optimizer. There is no way to tell Aegis to review a document as a hiring manager would, or as an executive sponsor would, or as a skeptical peer reviewer would. The system has one lens.

**DDO fix:** The persona system (described in Section 6) defines domain-specific reviewing lenses as reusable skill files. A persona specifies what the reviewer cares about, what attack vectors to probe, what severity taxonomy to use, and what domain-specific format rules apply. Personas are composable: a scientific report can be reviewed first by a `scientific_reviewer` persona and then by a `technical_writer` persona.

### 3.7 Context Bloat from Unstructured Examples

`aegis/examples/` holds reference job descriptions, resumes, and cover letters as few-shot grounding material for the LLM. The white paper explicitly notes that this directory must be "strictly curated" because too many examples degrade performance through token bloat. There is no built-in mechanism for prioritizing, pruning, or relevance-scoring which examples to include in a given context.

**DDO fix:** The evidence bank schema (described in Section 8) structures reference materials as tagged, typed YAML nodes rather than raw files. This makes them filterable by relevance to the current document domain, preventing context bloat.

### 3.8 Cover Letter Fit-Check Limitations

The paragraph efficiency heuristic is effective but not perfect. Very long paragraphs composed of short sentences may not trim cleanly. Paragraphs with tight semantic coupling between sentences (where every sentence is necessary) may show up as trim targets but have no safe cut points. The user must intervene manually in these cases.

**DDO fix:** The red team phase provides a cleaner approach to document length management for general documents. Rather than heuristic space analysis, the red team identifies over-explained, redundant, or low-value sections as part of its structural critique.

### 3.9 No Iterative Quality Loop

Aegis is a one-pass system. The cover letter fit-check loop is an exception, but it only iterates on page count, not on content quality. There is no mechanism for running the full generation → review → edit → regenerate cycle multiple times to progressively improve document quality.

**DDO fix:** The Phase 3 → Phase 4 → Phase 5 loop can run N times. After each rebuild, the user can choose to run another red team pass. This creates a convergent quality loop where each cycle produces a demonstrably better document.

---

## 4. The DDO Vision

### 4.1 What DDO Is

**Deterministic Document Orchestrator (DDO)** is a generalized, document-type-agnostic orchestration engine that transforms structured YAML data through configurable templates into any document format, then iteratively refines those documents through an adversarial review → structured interview → rebuild loop.

It is built on top of Claude Code, using the same slash command + skill file architecture as Aegis. It is not a standalone application, a SaaS product, or a web service. It is a Claude Code toolkit: a set of prompts, skills, schemas, templates, and build scripts that live in a git repository and run inside a Claude Code session.

### 4.2 Core Principles

**1. The source of truth is always a YAML file you control.**
No generated word exists outside of a YAML node that you have reviewed and approved. The LLM routes and refines; it does not invent.

**2. Document generation is deterministic.**
The same YAML in, the same template applied, produces the same document out. Reproducibility is a first-class property.

**3. Human judgment is mandatory at every phase gate.**
The LLM never proceeds from one phase to the next without explicit human approval. The state machine is not advisory; it is enforced by skill file directives.

**4. Adversarial review is not optional; it is a phase.**
Every document passes through a red team review before being considered complete. The red team's job is to find problems before the document's audience does.

**5. Refinement is iterative, not one-shot.**
The Phase 3 → 4 → 5 loop can run as many times as the user chooses. Each cycle produces a measurably better document.

**6. Personas define the reviewing lens.**
There is no universal document critic. Domain expertise determines what makes a document good or bad. Personas encode that domain expertise in a reusable, swappable form.

### 4.3 What DDO Can Generate

DDO is not limited to any specific document type. Examples:

- **Scientific reports** — Introduction, Methods, Results, Discussion, Conclusions with figures, tables, and citations
- **Patent / invention disclosures** — Background, Summary of Invention, Claims, Drawings, Detailed Description
- **Product Requirements Documents (PRDs)** — Problem statement, user stories, requirements, acceptance criteria, success metrics
- **Business proposals** — Executive summary, problem statement, proposed solution, timeline, budget, risk analysis
- **Legal briefs** — Statement of facts, argument sections, citations to authority
- **Grant proposals** — Specific aims, background and significance, innovation, approach, bibliography
- **Technical white papers** — Abstract, introduction, technical architecture, performance data, comparison to alternatives
- **HTML websites** — Single-page or multi-page sites generated from structured content YAML via Jinja2 templates
- **Clinical study summaries** — Study design, population, endpoints, results, safety summary
- **Invention disclosures** — Inventors, field of invention, problem solved, solution description, embodiments
- **Meeting reports / lab notebooks** — Structured notes, observations, decisions, action items
- **Any document with a known schema and repeatable format**

### 4.4 The Naming Logic

The name "deterministic-doc-orchestrator" is chosen carefully:

- **Deterministic:** Same input produces same output. The system is reproducible, testable, and version-controlled.
- **Doc:** Short for document — intentionally ambiguous across formats (PDF, HTML, DOCX, MD, etc.).
- **Orchestrator:** The system coordinates data, templates, LLM cognition, and human judgment. It does not do any of these things in isolation; it orchestrates them.

---

## 5. The DDO Workflow — Five-Phase Pipeline

### Overview

```
Phase 1: INGEST
  Sources (PDFs, docs, research, interviews, APIs)
    → Structured document_data.yaml
    → Human review of [REQUIRES USER INPUT] fields

Phase 2: RENDER
  document_data.yaml + template
    → Document (PDF, HTML, DOCX, MD)
    → Human review of output

Phase 3: RED TEAM
  Document + persona
    → red_team_report.yaml (structured critique)
    → Human reviews findings

Phase 4: INTERVIEW
  red_team_report.yaml
    → Structured Q&A (1-3 issues per batch)
    → interview_log.yaml (findings → resolutions)

Phase 5: REFINE & REBUILD
  interview_log.yaml + document_data.yaml
    → Updated document_data.yaml
    → Trigger Phase 2 (re-render)
    → Optional: loop back to Phase 3

TERMINATION: User signals completion via /ddo-finalize
```

### 5.1 Phase 1 — Ingest (Sources → Structured YAML)

**Purpose:** Transform raw information sources into a structured, version-controlled YAML file that serves as the document's single source of truth.

**Analogous to:** `/aegis-ingest` in Aegis, but generalized.

**Inputs (any combination):**
- Raw documents: PDFs, DOCX files, Markdown files, plain text
- Research papers or citations
- Interview transcripts or conversation logs
- Database exports or API responses
- Web pages (scraped content)
- User-provided notes or outlines
- Existing drafts in any format

**Command:**
```
/ddo-ingest <source-paths> --schema <domain-schema> --output <document-folder>
```

**What the skill does:**
1. Read all source materials.
2. Apply the specified domain schema (e.g., `schemas/scientific_report.yaml`) as a structural target.
3. Extract content from sources and map it to schema fields. Only extract; never invent.
4. For each schema field that cannot be filled from sources, insert `[REQUIRES USER INPUT: <explanation of what's needed>]`.
5. For each extracted claim that should have evidence, populate the `evidence_bank` with a citation or reference and link it to the claim via evidence ID.
6. Output `document_data.yaml` in the document folder.
7. Present a summary: fields populated vs. `[REQUIRES USER INPUT]` fields remaining.
8. Hard stop: `[WAITING FOR USER REVIEW]`.

**Zero hallucination rule:** The ingest skill operates under the same constraint as `/aegis-ingest`: it is permitted to extract, organize, and restructure information from sources, but it is not permitted to generate content that is not present in the sources. Missing information is flagged, not invented.

**Output:** `Documents/<slug>/document_data.yaml`

**Phase gate:** User reviews the YAML output, fills in `[REQUIRES USER INPUT]` fields directly in the YAML file, approves the result, and proceeds.

### 5.2 Phase 2 — Render (YAML → Document)

**Purpose:** Transform the structured YAML into a formatted document via a template engine.

**Analogous to:** `/aegis-generate` in Aegis, but multi-format.

**Command:**
```
/ddo-render --data Documents/<slug>/document_data.yaml --template <name> --format <pdf|html|docx|md>
```

**Supported formats and template engines:**

| Format | Engine | Template Type |
|---|---|---|
| PDF | Typst | `.typ` files; Typst natively parses YAML |
| HTML | Jinja2 | `.html.j2` files; renders to static HTML |
| DOCX | Pandoc + Jinja2 | `.md.j2` → Markdown → Pandoc → DOCX |
| Markdown | Jinja2 | `.md.j2` files; renders to `.md` |

**What the skill does:**
1. Verify `document_data.yaml` is present and has no unfilled `[REQUIRES USER INPUT]` fields.
2. Identify the template file for the requested format.
3. Invoke the build script: `python3 ddo/build.py --data <yaml> --template <name> --format <format> --output <output-path>`
4. The build script calls the appropriate template engine (Typst CLI, Jinja2 renderer, Pandoc) with the YAML file injected as input.
5. Report success or compilation errors.

**Output:** Document file(s) in `Documents/<slug>/`

**Multiple format rendering:** The same YAML can feed multiple templates simultaneously. Running the command twice with different `--format` flags produces both a PDF and an HTML version of the same document with no content duplication.

**Phase gate:** User reviews the rendered document. If satisfied, proceeds to Phase 3. If not, may return to Phase 1 to update the YAML.

### 5.3 Phase 3 — Red Team (Adversarial Review)

**Purpose:** Subject the rendered document to systematic adversarial critique, surface its weaknesses before its intended audience does, and produce a structured report of findings.

**This is the core new capability of DDO. It has no equivalent in Aegis.**

**Command:**
```
/ddo-red-team --document Documents/<slug>/<output-file> --persona <persona-name>
```

**What the skill does:**
1. Load the specified persona file from `ddo/personas/<persona-name>.md`. The persona defines: what this reviewer cares about, what attack vectors to probe, what severity taxonomy to use, and what format compliance rules to check.
2. Read the full rendered document.
3. Conduct a systematic adversarial review across attack vectors defined by the persona.
4. For each issue found, record:
   - `id`: unique issue slug
   - `severity`: critical / major / minor (persona-defined taxonomy)
   - `category`: logic / evidence / structure / style / compliance / completeness
   - `location`: section title or document excerpt where the issue appears
   - `description`: what the problem is, stated precisely
   - `suggestion`: one possible resolution (not prescriptive; just a starting point)
5. Rank issues by severity.
6. Output `red_team_report.yaml` in the document folder.
7. Present a summary to the user: N critical issues, N major issues, N minor issues.
8. Hard stop: `[WAITING FOR USER REVIEW]`.

**Red team attack vectors (by default):**
- **Unsupported claims:** Assertions without evidence in the evidence bank.
- **Internal contradictions:** Statements in one section that conflict with statements in another.
- **Logic gaps:** Reasoning that skips steps or relies on unstated assumptions.
- **Hedging language:** Weak language that undermines claims ("may potentially," "could possibly," "it seems like").
- **Missing context:** Information the reader would need to evaluate a claim that is not present.
- **Structural issues:** Sections in wrong order, missing standard sections, poor transitions.
- **Format compliance:** Domain-specific format rules (defined by persona) that are violated.
- **Scope creep:** Content that is outside the document's stated scope.
- **Completeness:** Standard fields or sections that are expected but absent.

**`red_team_report.yaml` schema:**
```yaml
meta:
  document: string
  persona: string
  date: string
  total_issues: int
  critical: int
  major: int
  minor: int

issues:
  - id: string
    severity: string          # critical | major | minor
    category: string          # logic | evidence | structure | style | compliance | completeness
    location: string          # Section title or quoted excerpt
    description: string       # What the problem is
    suggestion: string        # One possible resolution
    resolved: false           # Updated to true after interview
    resolution: null          # Updated with user's answer after interview
```

**Phase gate:** User reviews the red team report. May choose to skip to Phase 5 for minor issues only. Proceeds to Phase 4 (interview) for critical and major issues.

### 5.4 Phase 4 — Interview (Structured Human Resolution)

**Purpose:** Present red team findings to the user in a structured, paced dialogue, capture the user's answers and decisions, and compile an interview log that drives document updates.

**This is the second core new capability of DDO. It has no equivalent in Aegis.**

**Command:**
```
/ddo-interview --red-team-report Documents/<slug>/red_team_report.yaml --batch-size 2
```

**What the skill does:**
1. Read `red_team_report.yaml`. Filter to unresolved issues. Sort by severity (critical first, then major, then minor).
2. Present the first batch of `--batch-size` issues to the user:
   - For each issue: display the severity badge, the location in the document, the full description, and the suggestion.
   - Ask targeted questions: "Is this claim supported by evidence we didn't capture in the ingest phase?", "Would you like to revise this section, acknowledge the limitation, or dispute the finding?", "Do you have data or references that address this gap?"
3. Hard stop: `[WAITING FOR USER RESPONSE]`.
4. Capture the user's answers for each issue. Record:
   - Decision: revise / acknowledge / dispute / defer
   - New content (if revising): what to add or change in the document
   - Evidence (if supporting): new evidence to add to the evidence bank
   - Counter-argument (if disputing): why the red team finding is not valid
5. Mark each issue as resolved in the report.
6. When the user says "next," present the next batch.
7. Continue until all issues are addressed or the user signals "done for now."
8. Output `interview_log.yaml` in the document folder.

**Interview pacing and Claude Code best practices:**
- Batches of 1-3 issues at a time. Never dump all issues at once.
- The user controls pacing: they type "next" to proceed, "back" to revisit the previous batch, "skip" to defer an issue.
- The agent never suggests that the user is wrong or that their counter-argument is invalid. It records all responses faithfully.
- The agent may ask clarifying follow-up questions within a batch, but does not initiate a new batch until the user signals readiness.

**`interview_log.yaml` schema:**
```yaml
meta:
  document: string
  red_team_report: string
  date: string
  interviewer_persona: string

resolutions:
  - issue_id: string          # Links to red_team_report.yaml issue
    decision: string          # revise | acknowledge | dispute | defer
    new_content: string       # If revising: what to add/change
    evidence: string          # If adding evidence: citation or data
    counter_argument: string  # If disputing: why the finding is wrong
    yaml_path: string         # Where in document_data.yaml this maps to
    notes: string             # Any additional context
```

**Phase gate:** After all batches are complete, the user reviews the full `interview_log.yaml` and approves it before Phase 5 begins.

### 5.5 Phase 5 — Refine and Rebuild

**Purpose:** Apply interview log resolutions to the source YAML, update the evidence bank, and trigger a document rebuild.

**Analogous to:** Phase 5 (DB sync) in `/aegis-tailor`, but generalized and more sophisticated.

**Command:**
```
/ddo-refine --interview-log Documents/<slug>/interview_log.yaml --data Documents/<slug>/document_data.yaml
```

**What the skill does:**
1. Read `interview_log.yaml` and `document_data.yaml`.
2. For each resolution with decision = "revise":
   - Locate the relevant field in `document_data.yaml` using the `yaml_path`.
   - Apply the `new_content` change.
   - Present a numbered before/after block to the user.
3. For each resolution with new evidence:
   - Add an entry to the `evidence_bank` section of `document_data.yaml`.
   - Link it to the relevant claim via the claim's evidence array.
4. For each resolution with decision = "dispute" or "acknowledge":
   - No YAML change required, but record the decision in a `review_log` field in the document's `meta` section for traceability.
5. Collect all proposed changes. Present as numbered list with before/after for each. Ask for final approval.
6. Hard stop: `[WAITING FOR USER APPROVAL]`.
7. Apply all approved changes to `document_data.yaml`.
8. Trigger Phase 2 (re-render): call `/ddo-render` with the same template and format as before.
9. Present the rebuilt document to the user.
10. Ask: "Would you like to run another red team pass? (yes/no)"

**Loop termination:**
- User says "no" → document is considered complete. Proceed to `/ddo-finalize`.
- User says "yes" → loop back to Phase 3. Specify same or different persona.
- User says "different persona" → run Phase 3 with a new persona, then Phase 4, then Phase 5 again.

**The full loop:**

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 2
                        ↑                              ↓
                        └──────────────────────────────┘
                              (N iterations)
```

Each iteration produces a measurably better document with a complete audit trail in YAML.

### 5.6 Full Pipeline Command

For experienced users who trust the process, a single command runs the full pipeline:

```
/ddo-run <source-paths> --schema <domain-schema> --template <name> --format <format> --persona <persona-name>
```

This executes Phases 1-5 in sequence, pausing at each phase gate for human approval. It is the `/aegis-tailor` equivalent for DDO.

### 5.7 Finalization

```
/ddo-finalize --document-folder Documents/<slug>
```

Marks the document as final in `document_data.yaml` (`status: final`). Generates a final render of all requested output formats. Creates a summary report:
- Total iterations
- Issues raised by red team (by severity)
- Issues resolved vs. deferred vs. disputed
- Evidence bank size
- Final document word count

---

## 6. The Persona System

### 6.1 Why Personas

A patent examiner and a product manager and a scientific peer reviewer would read the same document and find completely different problems. The patent examiner looks for prior art that anticipates the claims, for claim language that is too broad or too narrow, for specification enablement. The product manager looks for user value proposition, for missing acceptance criteria, for scope creep. The peer reviewer looks for statistical power, for methodology gaps, for novelty relative to the literature.

A single "document reviewer" persona cannot do justice to any of these domains. Personas encode domain expertise in a reusable, swappable form. You choose the persona that matches the document's intended audience, and the red team adopts that lens.

### 6.2 Persona Structure

Each persona is a Markdown skill file in `ddo/personas/`:

```markdown
# Persona: [Name]
## Domain
[One paragraph describing the domain, the typical reader, and what this reader cares about most]

## Reviewing Mission
[One paragraph describing the reviewing lens: what does a good document look like in this domain?]

## Attack Vectors
[Ordered list of specific issues to probe, most important first]
- [Attack vector 1]: [Description of what to look for and why it matters]
- [Attack vector 2]: ...
...

## Severity Taxonomy
- **Critical:** [What rises to critical severity in this domain]
- **Major:** [What rises to major severity]
- **Minor:** [What is minor]

## Domain-Specific Format Rules
[List of format requirements that this domain expects: standard sections, citation format, claim structure, etc.]

## Interview Question Templates
[Suggested questions to ask the user when resolving findings in this domain]
- For unsupported claims: "..."
- For logic gaps: "..."
- For format violations: "..."
```

### 6.3 Built-In Personas

**`scientific_reviewer`**
- Domain: Peer-reviewed scientific publications (journals, conference proceedings)
- Attack vectors: statistical validity, reproducibility, novelty vs. prior art, methodology rigor, figure/table accuracy, claim-to-evidence traceability
- Format rules: standard IMRaD structure (Introduction, Methods, Results, Discussion), citation format compliance, figure captions

**`patent_examiner`**
- Domain: Patent applications (utility, design, provisional)
- Attack vectors: prior art anticipation, claim breadth (too broad or too narrow), enablement (can a skilled practitioner reproduce the invention from the specification?), written description (does the spec support all claims?), novelty and non-obviousness
- Format rules: claim hierarchy (independent claims → dependent claims), 35 U.S.C. compliance, abstract word count

**`product_critic`**
- Domain: Product requirements documents, feature specifications
- Attack vectors: user value proposition (who benefits and how?), missing acceptance criteria, scope creep, technical feasibility, success metric clarity, stakeholder alignment, missing edge cases
- Format rules: user story format, testable acceptance criteria, definition of done

**`investor_skeptic`**
- Domain: Business proposals, pitch decks, investment memoranda
- Attack vectors: market size validation, competitive moat, unit economics, team credibility, go-to-market clarity, risk acknowledgment
- Format rules: executive summary, financial projections, risk section

**`legal_analyst`**
- Domain: Legal briefs, contracts, compliance documents
- Attack vectors: ambiguous language, undefined terms, missing jurisdiction, compliance gaps, liability exposure, contradictory provisions
- Format rules: case citation format, defined terms section, governing law clause

**`technical_writer`**
- Domain: Technical documentation, user guides, API references
- Attack vectors: terminology consistency, missing prerequisites, incomplete examples, unclear instructions, broken cross-references, audience mismatch
- Format rules: consistent heading hierarchy, code block formatting, glossary

**`grant_reviewer`**
- Domain: Research grant proposals (NSF, NIH, DARPA, etc.)
- Attack vectors: specific aims clarity, significance and innovation, approach feasibility, team qualifications, budget justification, timeline realism
- Format rules: page limit compliance, required sections by agency, biosketch format

### 6.4 Creating New Personas

```
/ddo-create-persona <domain> <description>
```

The skill interviews the user about the domain:
1. "Who is the intended audience for documents in this domain?"
2. "What does a high-quality document look like in this domain? What are the clearest signals of quality?"
3. "What are the most common failure modes or weaknesses you see in documents in this domain?"
4. "Are there standard format requirements (section names, citation styles, length limits) that documents in this domain must follow?"
5. "How would you rank severity? What is critical vs. major vs. minor?"

Based on answers, generates `ddo/personas/<domain>.md` following the persona structure template. Presents the draft persona to the user for review and approval. The persona is immediately available for use in `/ddo-red-team`.

### 6.5 Persona Composition

Multiple personas can be applied to the same document sequentially:

```
/ddo-red-team --document <path> --persona scientific_reviewer
→ red_team_report_round1.yaml

/ddo-interview --red-team-report red_team_report_round1.yaml
→ interview_log_round1.yaml

/ddo-refine --interview-log interview_log_round1.yaml
→ Updated document_data.yaml → Rebuild

/ddo-red-team --document <rebuilt-path> --persona technical_writer
→ red_team_report_round2.yaml
...
```

This allows a scientific paper to be reviewed first for scientific rigor (scientific_reviewer) and then for clarity and documentation quality (technical_writer), with each pass building on the improvements from the previous one.

---

## 7. Template Generation from Existing Documents

### 7.1 The Problem

Users frequently have an existing document that they want to replicate: a company-standard PRD template, a journal submission format, a specific patent filing style. Asking the user to manually describe the structure of that document in enough detail to build a template is impractical. It is faster and more accurate to show the system an example.

### 7.2 The Workflow

**Command:**
```
/ddo-template-gen <reference-doc> --output-format <typst|jinja|md> --schema-output <schema-name>
```

**Phase 1 — Analysis:**
The skill reads or analyzes the reference document and extracts:
- Section structure: heading hierarchy, section names, ordering
- Field patterns: what types of content appear in each section (prose, tables, bullet lists, code blocks, citations)
- Visual layout (for PDF/HTML): margins, font hierarchy, column layout, header/footer patterns
- Writing conventions: tense, voice, terminology patterns
- Conditional sections: sections that may be present or absent depending on content

**Phase 2 — Template Generation:**
Based on the analysis, the skill generates:
- A template file in the requested format (`.typ`, `.html.j2`, `.md.j2`)
- A `template_schema.yaml` describing what YAML fields the template expects, including field types, required vs. optional, and example values

The template is generated with placeholders — no hardcoded content from the reference document. Everything that would vary between instances of the document is a YAML field reference.

**Phase 3 — Synthetic Render:**
The skill generates synthetic YAML data that satisfies the `template_schema.yaml`. It renders the template with this synthetic data and presents the output to the user alongside the original reference document.

**Phase 4 — Structured Interview Validation:**

This is the key improvement over Aegis's `/aegis-render`. Instead of free-form "report visual discrepancies," the skill conducts a structured interview:

For each major section of the template:
1. "Does the [Section Name] section match the reference document's structure?"
2. "Is the heading level correct? (H1, H2, H3?)"
3. "Are the fields in this section in the correct order?"
4. "Is there a field present in the reference that is missing from the template?"
5. "Is there a field in the template that does not appear in the reference?"

For visual/layout issues (PDF/HTML only):
6. "Does the page margin match? (too wide, too narrow, correct?)"
7. "Is the font size hierarchy correct? (headers, body, captions)"
8. "Is the column layout correct?"

The user answers each question. The skill iterates on the template based on answers. After each iteration, the skill re-renders with synthetic data and presents the updated output for comparison.

**Phase 5 — Validation and Storage:**
When the user approves the template, the skill:
1. Saves the template to `ddo/templates/<format>/<schema-name>.<ext>`
2. Saves the schema to `ddo/schemas/<schema-name>.yaml`
3. Reports: "Template `<name>` is ready. Use it with `/ddo-render --template <name> --format <format>`"

### 7.3 Differences from Aegis `/aegis-render`

| Feature | `/aegis-render` (Aegis) | `/ddo-template-gen` (DDO) |
|---|---|---|
| Input formats | PDF/image only | PDF, DOCX, HTML, MD, image |
| Output formats | Typst only | Typst, Jinja2, Markdown |
| Validation | Free-form iteration | Structured section-by-section interview |
| Schema output | None | `template_schema.yaml` generated alongside template |
| Synthetic test render | Not done | Yes, with auto-generated synthetic YAML |
| Iterative approval | Free-form | Structured per-section interview per iteration |

---

## 8. DDO Technical Architecture

### 8.1 Repository Structure

```
deterministic-doc-orchestrator/
│
├── CLAUDE.md                         # Claude Code guidance for this repo
├── DDO_PROJECT_BRIEF.md              # This document (origin and vision)
├── README.md                         # User-facing documentation
├── CHANGELOG.md                      # Version history
├── LICENSE                           # MIT (matching Aegis)
│
├── ddo/                              # Core framework
│   │
│   ├── schemas/                      # Domain YAML schemas
│   │   ├── base_schema.yaml          # Minimal shared fields all doc types have
│   │   ├── scientific_report.yaml    # Schema for scientific publications
│   │   ├── patent_disclosure.yaml    # Schema for patent applications
│   │   ├── prd.yaml                  # Schema for product requirements documents
│   │   ├── grant_proposal.yaml       # Schema for research grant proposals
│   │   ├── business_proposal.yaml    # Schema for business proposals
│   │   ├── technical_whitepaper.yaml # Schema for white papers
│   │   └── career.yaml               # Schema for Aegis compatibility (resumes, cover letters)
│   │
│   ├── templates/                    # Document templates by format
│   │   ├── typst/                    # Typst → PDF templates
│   │   │   ├── scientific_report.typ
│   │   │   ├── patent.typ
│   │   │   ├── prd.typ
│   │   │   └── resume.typ            # Carried over from Aegis
│   │   ├── jinja/                    # Jinja2 → HTML/DOCX/MD templates
│   │   │   ├── scientific_report.html.j2
│   │   │   ├── prd.md.j2
│   │   │   └── website.html.j2
│   │   └── markdown/                 # Pure Markdown templates
│   │       └── lab_notebook.md.j2
│   │
│   ├── personas/                     # Domain-specific red team + interview personas
│   │   ├── scientific_reviewer.md
│   │   ├── patent_examiner.md
│   │   ├── product_critic.md
│   │   ├── investor_skeptic.md
│   │   ├── legal_analyst.md
│   │   ├── technical_writer.md
│   │   └── grant_reviewer.md
│   │
│   ├── skills/                       # Skill prompt files
│   │   ├── skill_ingest.md           # Phase 1: Sources → YAML
│   │   ├── skill_render.md           # Phase 2: YAML → Document
│   │   ├── skill_red_team.md         # Phase 3: Adversarial review
│   │   ├── skill_interview.md        # Phase 4: Structured Q&A
│   │   ├── skill_refine.md           # Phase 5: YAML update + rebuild
│   │   ├── skill_template_gen.md     # Template generation + validation
│   │   ├── skill_create_persona.md   # New persona creation interview
│   │   └── skill_document.md         # README/CHANGELOG updates (carried from Aegis)
│   │
│   ├── build.py                      # Multi-format build orchestrator (PEP 723)
│   └── writing_style.md              # Domain-agnostic writing conventions
│
├── .claude/
│   └── commands/                     # Slash command definitions
│       ├── ddo-ingest.md             # → skill_ingest.md
│       ├── ddo-render.md             # → skill_render.md
│       ├── ddo-red-team.md           # → skill_red_team.md
│       ├── ddo-interview.md          # → skill_interview.md
│       ├── ddo-refine.md             # → skill_refine.md
│       ├── ddo-run.md                # Full pipeline composite
│       ├── ddo-finalize.md           # Finalization + summary report
│       ├── ddo-template-gen.md       # → skill_template_gen.md
│       ├── ddo-create-persona.md     # → skill_create_persona.md
│       └── document.md               # Carried from Aegis
│
├── Documents/                        # Generated documents (gitignored, personal)
│   └── YYYY.MM.DD_<DocType>_<Title>/
│       ├── document_data.yaml        # Source of truth YAML
│       ├── red_team_report.yaml      # Red team findings (per iteration)
│       ├── interview_log.yaml        # User resolutions (per iteration)
│       ├── review_history/           # Versioned snapshots per iteration
│       │   ├── v1_document_data.yaml
│       │   ├── v1_red_team_report.yaml
│       │   └── v1_interview_log.yaml
│       └── <outputs>/
│           ├── <title>.pdf
│           ├── <title>.html
│           └── <title>.docx
│
└── examples/                         # Reference examples per domain (curated, tracked)
    ├── scientific_report/
    │   ├── example_JD.md            # Reference job or task description
    │   └── example_data.yaml        # Sanitized example YAML
    ├── patent/
    └── prd/
```

### 8.2 Base YAML Schema

Every document in DDO shares a base schema. Domain schemas extend this base:

```yaml
# base_schema.yaml — core fields shared by all document types

meta:
  doc_type: string             # "scientific_report" | "patent" | "prd" | etc.
  title: string
  version: string              # Semantic version: "1.0.0", "2.1.0"
  date: string                 # ISO 8601: "2026-06-26"
  authors: [string]
  status: string               # "draft" | "red_teamed" | "final"
  persona: string              # Default persona for red team reviews
  output_formats: [string]     # ["pdf", "html", "docx"]
  template: string             # Default template name

content:
  sections:
    - id: string               # Unique slug: "introduction", "methods", etc.
      title: string            # Display heading
      body: string             # Prose content (block literal)
      claims: [string]         # Specific assertions (linked to evidence)
      evidence: [string]       # Evidence bank IDs supporting this section
      subsections: []          # Recursive: same structure as sections
      tags: [string]           # Thematic tags for filtering

evidence_bank:
  - id: string                 # Unique slug: "smith2024-ml-potentials"
    type: string               # "citation" | "data" | "experiment" | "testimony" | "calculation"
    content: string            # The evidence itself (citation text, data summary, etc.)
    source: string             # URL, DOI, filename, or description of origin
    tags: [string]

review_log:                    # Populated by red team + interview cycles
  - iteration: int
    persona: string
    date: string
    issues_raised: int
    issues_resolved: int
    issues_disputed: int
    issues_deferred: int
```

Domain schemas extend this by adding domain-specific fields. For example, `patent_disclosure.yaml` adds:

```yaml
# extends base_schema.yaml
patent_specific:
  inventors: [string]
  filing_date: string
  priority_date: string
  assignee: string
  field_of_invention: string
  claims:
    independent: [string]
    dependent:
      - claim_num: int
        depends_on: int
        text: string
```

### 8.3 Build System

`ddo/build.py` is the multi-format orchestrator. Like Aegis's `build.py`, it uses PEP 723 inline metadata for hermetic, ephemeral builds.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typst>=0.11",
#   "jinja2>=3.1",
#   "pyyaml>=6.0",
# ]
# ///

import yaml, subprocess, jinja2
from pathlib import Path

def build(data_file: Path, template: str, format: str, output: Path):
    data = yaml.safe_load(data_file.read_text())
    
    if format == "pdf":
        template_path = Path("ddo/templates/typst") / f"{template}.typ"
        subprocess.run([
            "typst", "compile", str(template_path), str(output),
            "--root", "/",
            "--input", f"data_file={data_file}"
        ], check=True)
    
    elif format in ("html", "md"):
        template_path = Path("ddo/templates/jinja") / f"{template}.{format}.j2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader("ddo/templates/jinja"))
        tmpl = env.get_template(f"{template}.{format}.j2")
        output.write_text(tmpl.render(**data))
    
    elif format == "docx":
        # Jinja → MD → Pandoc → DOCX
        md_path = output.with_suffix(".md")
        build(data_file, template, "md", md_path)
        subprocess.run([
            "pandoc", str(md_path), "-o", str(output)
        ], check=True)
```

Run with: `uv run ddo/build.py --data <yaml> --template <name> --format <format> --output <path>`

### 8.4 Slash Command — Skill File Separation

As in Aegis, slash commands are thin dispatchers and skill files hold the logic:

```markdown
<!-- .claude/commands/ddo-red-team.md -->
Read the skill file at `ddo/skills/skill_red_team.md` and follow its instructions exactly.
The document to review is: $ARGUMENTS
```

```markdown
<!-- ddo/skills/skill_red_team.md -->
# DDO Red Team Skill

## MISSION
You are an adversarial reviewer. Your job is to find every weakness in the provided document 
before its intended audience does. You adopt the specified persona. You are not trying to be 
helpful to the document's authors; you are trying to find problems that would cause the 
document to fail its purpose.

## PHASE 1 — Load Persona
Read the persona file at `ddo/personas/<persona>.md`. Internalize its domain context, 
attack vectors, severity taxonomy, and format rules.

## PHASE 2 — Read Document
Read the full document. For PDF/HTML, extract and read all text content. Do not skip sections.

## PHASE 3 — Systematic Review
For each attack vector defined by the persona, conduct a thorough review. Document every issue.

## PHASE 4 — Output Report
Write `red_team_report.yaml` to the document folder following the schema below.
Present a summary: N critical, N major, N minor issues found.

[WAITING FOR USER REVIEW]

## red_team_report.yaml schema
...
```

### 8.5 Writing Style

`ddo/writing_style.md` generalizes Aegis's style guide:

- **No em-dashes.** Replace with comma and space.
- **Active voice.** "The system validates input" not "Input is validated by the system."
- **No hedging.** "The approach works" not "The approach may potentially work in some cases."
- **Precise language.** Technical terms should be used correctly and consistently.
- **Evidence-linked claims.** Every assertion of fact should have a corresponding entry in the evidence bank.
- **Domain-appropriate register.** Formal for scientific and legal documents. Direct for PRDs and proposals. Accessible for user documentation.

The last two points are new relative to Aegis and reflect the generalized domain scope of DDO.

---

## 9. Homage to Aegis — What We Inherit and What We Add

### 9.1 What DDO Inherits from Aegis

**The Three-Layer Architecture**
Data (YAML) / Cognition (state machine) / Presentation (templates). This is the core architectural insight of Aegis and it transfers completely. DDO is built on this foundation.

**Atomic Decomposition**
Content is broken into discrete, reusable, tagged nodes (atomic achievements in Aegis; `content.sections[].claims` and `evidence_bank` entries in DDO). The LLM selects and routes; it does not generate from scratch.

**Phase Gate State Machine**
Every workflow phase ends with a hard stop requiring explicit user approval. `[WAITING FOR USER APPROVAL]` and `[WAITING FOR USER INPUT]` directives are inherited verbatim. The user has absolute veto power over every output.

**YAML as Universal Source of Truth**
All document content lives in a version-controlled YAML file. Nothing exists in the final document that does not exist first in the YAML. Generated documents are reproducible from their YAML source.

**Machine-Readable Style Guide**
`writing_style.md` is enforced by all skills, not advisory. DDO's writing style guide is a direct extension of Aegis's.

**Hermetic Build Pipeline**
PEP 723 inline dependencies via `uv`. No persistent virtualenvs. No global package state. The build is reproducible on any machine with `uv` and the relevant template engines.

**Bidirectional Sync**
Updates flow back into the source data. In Aegis, cover letter edits sync back to `master_career_db.yaml`. In DDO, interview resolutions sync back to `document_data.yaml`. The YAML is always kept current with the best-known version of the content.

**Slash Command / Skill File Separation**
Commands dispatch; skills implement. This separation keeps command files tiny and skill files focused on one concern.

**Phase Naming Convention**
Phase gates use the same naming convention: `[WAITING FOR USER APPROVAL]` at decision points, `[WAITING FOR USER INPUT]` at input collection points.

**Ephemeral Application Folders**
Aegis creates `Applications/YYYY.MM.DD_Company_Role/` folders. DDO creates `Documents/YYYY.MM.DD_<DocType>_<Title>/` folders. Same pattern, generalized naming.

**Example-Driven Grounding**
`examples/` holds sanitized reference documents per domain. Same role as Aegis's `aegis/examples/`, but organized by domain rather than document type.

### 9.2 What DDO Adds

**Adversarial Red Team Phase**
No equivalent in Aegis. A dedicated phase where an adversarial agent reads the rendered document and systematically attacks it, producing a structured `red_team_report.yaml`. This is the most significant new capability.

**Structured Interview Phase**
No equivalent in Aegis (the cover letter approval flow is closest, but it is not structured Q&A). A dedicated phase for working through red team findings with the user in paced batches, capturing decisions and new content in `interview_log.yaml`.

**Iterative Quality Loop**
No equivalent in Aegis. Phase 3 → 4 → 5 can repeat N times. Each cycle is versioned and produces demonstrably improved output.

**Persona System**
No equivalent in Aegis. Domain-specific reviewing lenses encoded as reusable, swappable persona files. Composable: multiple personas can be applied sequentially.

**Template Generation with Interview Validation**
Aegis's `/aegis-render` generates without structured validation. DDO's `/ddo-template-gen` adds a section-by-section structured interview, schema extraction, and synthetic data rendering for validation.

**Multi-Format Output**
Aegis: PDF only. DDO: Typst PDF, Jinja2 HTML, Pandoc DOCX, Jinja2 Markdown. Same YAML drives all formats.

**Domain-Agnostic Schema System**
Aegis has one schema (career DB). DDO has a base schema plus domain extensions. The base schema provides shared fields; domain schemas add domain-specific structure.

**Evidence Bank**
No equivalent in Aegis. A structured, typed, tagged collection of evidence entries linked to claims throughout the document. Enables the red team to attack unsupported claims precisely rather than generally.

**Review History**
DDO versions each red team and interview cycle in `review_history/`. The YAML evolution is traceable. Aegis has no equivalent.

**`/ddo-run` Composite Command**
No equivalent in Aegis (closest is the full `/aegis-tailor` workflow). A single command that runs the full 5-phase pipeline with phase gates, parameterized by schema, template, format, and persona.

### 9.3 Migration Path from Aegis

For Aegis users who want DDO to handle their career documents alongside other document types:

1. Copy `master_career_db.yaml` to `Documents/Career/document_data.yaml`. Add `meta.doc_type: career` and `meta.persona: product_critic` (as the closest analogue for interview/hiring context).
2. Copy Typst templates from `aegis/templates/` to `ddo/templates/typst/`. They work without modification — DDO's Typst invocation uses the same `sys.inputs.at("data_file")` pattern.
3. The `career.yaml` domain schema in DDO mirrors the Aegis YAML structure. Existing tailored YAML files are compatible.
4. Existing Aegis slash commands can coexist in `.claude/commands/`. DDO commands use the `ddo-` prefix; Aegis commands use the `aegis-` prefix. No collision.

The designer's intent is for DDO to eventually subsume Aegis entirely, with career documents being one domain among many rather than the only domain. But the migration is gradual, not a forced cutover.

---

## 10. Gap Analysis — Aegis vs. DDO

| Limitation in Aegis | Root Cause | DDO Solution |
|---|---|---|
| PDF-only output | Typst hardcoded as sole build target | Multi-format build system: Typst PDF, Jinja HTML, Pandoc DOCX, Jinja MD |
| Career/hiring domain locked | Schema, skills, templates all career-specific | Domain-agnostic base schema + extensible domain schemas |
| No adversarial review | Not a design goal of Aegis | Phase 3 Red Team: dedicated adversarial agent with persona-driven attack vectors |
| No structured refinement dialogue | Cover letter approval is closest; not systematic | Phase 4 Interview: paced Q&A in batches of 1-3, structured per finding |
| No iterative quality loop | One-pass workflow | Phase 3→4→5 repeatable N times; each cycle versioned |
| Template gen is one-shot and unvalidated | `/aegis-render` has no validation step | Template gen + structured interview validation + synthetic data render |
| No persona system | One reviewer lens for all documents | Domain-specific persona files; composable; user-created |
| Context bloat from unstructured examples | Raw files in `examples/` directory | Evidence bank in YAML: structured, typed, tagged, filterable |
| Supporting materials cause context bloat | Raw files in `Supporting_Information/` | All reference material ingested and structured in `evidence_bank` |
| No ATS compliance validation | Not built | Can be implemented as a `recruiter_filter` persona in DDO |
| Vision model limitations in template replication | Free-form iteration only | Structured section-by-section validation interview |
| No claim-to-evidence linkage | Atomic achievements are isolated | `evidence_bank` + `claims` array in sections; explicit linkage |
| No review history or audit trail | No versioning per iteration | `review_history/` folder with versioned YAML snapshots per cycle |
| Hard-coded English/US assumptions | Not parameterized | Writing style file supports domain-appropriate register; locale is a schema field |
| Fit-check is heuristic (paragraph efficiency) | Works but has edge cases | Red team structural critique replaces heuristic for general documents |
| Phase 5 DB sync is manual and per-session | Not persisted between sessions | `interview_log.yaml` is a durable record; sync can run asynchronously |

---

## 11. Open Questions for the PRD Session

These are the questions that a co-researcher AI agent should explore, challenge, and help answer in the process of generating the DDO PRD.

### 11.1 Schema Architecture

**Q1: Fixed base schema with domain extensions, or fully dynamic schema per doc type?**

Option A (fixed base + extensions): Every document has the same `meta`, `content.sections`, and `evidence_bank` top-level fields. Domain schemas add additional top-level blocks. The advantage is that shared tooling (the build system, the red team skill, the interview skill) can always rely on the base fields being present.

Option B (fully dynamic): Each domain schema is entirely self-defining. Nothing is guaranteed at the top level. The advantage is maximum flexibility. The disadvantage is that shared tooling must be more defensive.

Leaning toward Option A, but the PRD should specify the exact base schema fields and what extensibility looks like.

**Q2: How should schema versions be managed?**

If a domain schema changes (a new required field is added), existing `document_data.yaml` files may be invalid against the new schema. How should migration be handled? Explicit schema version in `meta`? A `/ddo-migrate` command? Forward-compatible schemas only?

### 11.2 Red Team Report Format

**Q3: YAML or Markdown for `red_team_report.yaml`?**

YAML enables programmatic processing (the refine phase can read it and apply resolutions automatically). Markdown is more human-readable and easier for the user to review and annotate. A hybrid is possible: Markdown file with YAML frontmatter. But the PRD should make a definitive choice.

**Q4: How granular should the red team findings be?**

Document-level: "This document lacks an introduction." Section-level: "The Methods section lacks a sample size justification." Sentence-level: "This sentence makes a claim without evidence." Sentence-level is most actionable but produces a very large report for long documents. The PRD should specify the granularity expectation.

### 11.3 Interview UX

**Q5: What is the exact UX pattern for the interview phase?**

In Aegis, the cover letter approval flow presents draft text and asks for a thumbs-up or specific edit instructions. The DDO interview is more complex: it presents a finding and asks open-ended questions. What is the exact format?

- Does the agent present questions as numbered items for the user to answer in sequence?
- Does the user type free text, or are some questions multiple-choice?
- How does the agent handle ambiguous or incomplete answers?

The PRD should specify the exact dialogue format and how the agent handles edge cases.

**Q6: What happens when the user disputes a finding?**

If the user says "this finding is wrong, the evidence is in section 3," the interview log records the dispute. But does the refine phase do anything with a disputed finding? Does the red team acknowledge the counter-argument in the next iteration? The PRD should specify.

### 11.4 Template Format Priority

**Q7: Which output formats should be built first?**

Three candidates for v1: Typst PDF (carries over from Aegis with minimal work), Jinja2 HTML (high utility for websites and reports), Pandoc DOCX (required for many enterprise contexts). The PRD should specify the v1 scope and defer the rest.

**Q8: Should DDO generate multi-file HTML websites, or single-page HTML documents only?**

Single-page HTML is straightforward: one Jinja2 template renders one YAML file. Multi-page websites require a different build model: a directory of Jinja2 templates, a navigation structure, and multiple YAML files or a YAML file with nested page content. This is a significant scope decision.

### 11.5 Persona Storage and Privacy

**Q9: Should personas live in the repo (tracked by git) or be user-local (like `master_career_db.yaml`)?**

For the built-in personas, tracking in git makes sense. But user-created personas may contain sensitive domain knowledge (company-specific PRD format, proprietary legal analysis framework). The PRD should specify whether custom personas are gitignored by default and whether there is a "shared personas" vs. "private personas" directory distinction.

### 11.6 Loop Termination and Quality Signaling

**Q10: How does the user signal that the document is "good enough"?**

Options:
- User explicitly runs `/ddo-finalize` after any rebuild.
- Red team report reaches a threshold: no critical or major issues remain.
- User sets a maximum iteration count in the document's `meta`.
- No explicit termination: the document stays in "draft" until the user finalizes.

The PRD should specify the termination mechanism and what "finalized" means in terms of file state.

**Q11: Should DDO track a quality score across iterations?**

If each red team report includes a score (e.g., total issues weighted by severity), the user could see whether quality is improving across cycles. But this creates a risk: users optimize for the score rather than the document. The PRD should decide whether to include scoring.

### 11.7 Version Control and Review History

**Q12: Should each refinement cycle snapshot the YAML?**

Currently proposed: `review_history/v<N>_document_data.yaml`, `v<N>_red_team_report.yaml`, `v<N>_interview_log.yaml`. The advantage is full audit trail. The disadvantage is directory clutter for long refinement cycles.

Alternative: Rely entirely on git history for versioning. The PRD should specify.

### 11.8 Multi-Author and Collaborative Documents

**Q13: Can DDO support multiple humans in the interview loop?**

Many real documents (scientific papers, legal briefs, grant proposals) are authored by multiple people. The current design assumes a single user in the interview phase. What would multi-author support look like? Multiple sequential interview sessions? Parallel interview logs that are merged? The PRD should address this even if v1 defers it.

### 11.9 LLM Provider and Platform Assumptions

**Q14: How tightly coupled to Claude Code should DDO be?**

Aegis is explicitly Claude Code-only. The slash command system, the skill file format, and the state machine protocol are all Claude Code idioms. DDO could:
- Stay Claude Code-only (simplest; leverage Claude's strengths)
- Be designed to be portable to other LLM platforms (higher engineering cost; broader addressable use)

The PRD should make a definitive choice. The recommendation is Claude Code-only for v1, with portability as a stretch goal.

### 11.10 Evidence Bank Linkage Granularity

**Q15: How granular should claim-to-evidence linking be?**

The current schema links evidence IDs to sections (`content.sections[].evidence: [string]`). Should links be at section level, paragraph level, or sentence/claim level?

- Section level: simple but imprecise. A section may have 10 claims; only 3 are supported.
- Claim level (`content.sections[].claims: [string]` each linked to evidence): more precise, requires the ingest phase to decompose sections into discrete claims.
- Sentence level: maximum precision, maximum complexity in the schema.

The red team phase benefits from fine-grained linkage (it can identify exactly which claims are unsupported), but the ingest phase burden increases significantly. The PRD should specify the level.

---

## Closing Note

This document is the founding artifact of the deterministic-doc-orchestrator project. It was written in one session by Thomas J. L. Mustard, with full technical support from Claude Code, building on two months of production experience with Project Aegis.

The document is intentionally verbose and open-ended. It is not a PRD. It is a briefing for the co-researcher who will help turn it into one. Every open question in Section 11 is a decision that the PRD must make. Every design element in Sections 5-8 is a starting point, not a final specification.

The designer's core conviction, carried from Aegis into DDO, is this: **AI-assisted document generation works best when the AI routes and refines existing human knowledge, not when it generates from nothing.** The YAML file is the mind. The template is the voice. The red team is the conscience. The interview is the refinement. The loop is the learning.

Build the right loop, and you build a document that earns its conclusions.

---

*Project Aegis v0.4.1 was developed by Thomas J. L. Mustard. Repository: https://github.com/tjmustard/Aegis. This document describes the design vision for its successor project, deterministic-doc-orchestrator.*
