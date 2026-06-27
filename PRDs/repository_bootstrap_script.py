import os

# DDO Repository Initialization Script
# Run: python3 bootstrap_ddo.py

FILES = {
    ".gitignore": r'''
# DDO Output Directories
Documents/

# Hypergraph Coding Agent Framework (HACF)
HACF/
Hypergraph-Coding-Agent-Framework/
hypergraph/

# Python & Environment
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.env

# OS specific
.DS_Store
Thumbs.db
''',

    "ddo/writing_style.md": r'''
# DDO Enforced Writing Style

**CRITICAL INSTRUCTION FOR ALL SKILLS:**
These rules are not suggestions. They are machine-readable constraints. All generated text must conform strictly to these parameters. Failure to adhere to these rules is a critical system failure.

## 1. Typography & Punctuation
* **No em-dashes:** Never use an em-dash (`—`) or en-dash (`–`). Replace them with a comma and a space.

## 2. Voice & Tone
* **Active Voice Only:** The subject of the sentence must perform the action.
* **No Hedging Language:** Do not use words that weaken claims (e.g., "may potentially," "could possibly").
* **Professional & Direct:** Be confident without being boastful. Avoid corporate jargon.

## 3. Epistemic Rigor
* **Evidence-Linked Claims:** Every assertion of fact must trace directly to a verifiable entry in the `evidence_bank`.
* **Precise Language:** Technical terms must be used correctly and consistently.

## 4. Domain Register
* Adjust formality based on the document domain while maintaining all rules above.
''',

    "ddo/build.py": r'''
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typst>=0.11",
#   "jinja2>=3.1",
#   "pyyaml>=6.0",
# ]
# ///

import yaml
import subprocess
import jinja2
import argparse
from pathlib import Path
import sys

def build(data_file: Path, template: str, doc_format: str, output: Path):
    if not data_file.exists():
        print(f"Error: Data file {data_file} not found.")
        sys.exit(1)

    try:
        data = yaml.safe_load(data_file.read_text(encoding='utf-8'))
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
        
    if doc_format == "pdf":
        template_path = Path("ddo/templates/typst") / f"{template}.typ"
        subprocess.run([
            "typst", "compile", str(template_path), str(output),
            "--root", ".", "--input", f"data_file={data_file}"
        ], check=True)
        
    elif doc_format in ("html", "md"):
        template_dir = Path("ddo/templates/jinja") if doc_format == "html" else Path("ddo/templates/markdown")
        template_filename = f"{template}.{doc_format}.j2"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_dir)))
        tmpl = env.get_template(template_filename)
        output.write_text(tmpl.render(**data), encoding='utf-8')
        
    elif doc_format == "docx":
        md_output = output.with_suffix(".md")
        build(data_file, template, "md", md_output)
        subprocess.run(["pandoc", str(md_output), "-o", str(output)], check=True)
            
    else:
        print(f"Error: Unsupported format '{doc_format}'")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--template", type=str, required=True)
    parser.add_argument("--format", type=str, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.data, args.template, args.format, args.output)
''',

    "ddo/skills/ddo-ingest.md": r'''
# Skill: ddo-ingest
## Description
Extracts and structures raw information from source materials into a deterministic YAML schema.
## Inputs
1. `source_paths`: Paths to raw documents.
2. `schema`: The target domain schema.
3. `output_dir`: The target output directory.
## Execution Logic
1. Parse sources and apply `schema`.
2. Zero Hallucination: If a field cannot be filled, write `[REQUIRES USER INPUT: <reason>]`.
3. Create entries in `evidence_bank` and link to claims.
4. Write to `<output_dir>/document_data.yaml`.
[WAITING FOR USER REVIEW]
Halt execution until user fills missing fields.
''',

    "ddo/skills/ddo-render.md": r'''
# Skill: ddo-render
## Description
Transforms structured YAML into the final document formats via hermetic Python build orchestrator.
## Inputs
1. `data_file`: Path to `document_data.yaml`.
2. `template_name`: Name of the template.
3. `format`: Target output format.
## Execution Logic
1. Pre-Condition: Scan `data_file` for `[REQUIRES USER INPUT]`. Abort if found.
2. Invoke: `uv run ddo/build.py --data <data_file> --template <template_name> --format <format> --output <generated_file_path>`
[WAITING FOR USER REVIEW]
Prompt user to review compiled document.
''',

    "ddo/skills/ddo-red-team.md": r'''
# Skill: ddo-red-team
## Description
Adversarial critique using a domain Persona.
## Inputs
1. `document_path`: Rendered document (.md or .html preferred).
2. `persona_name`: Persona to load.
3. `output_dir`: Target directory.
## Execution Logic
1. Load `ddo/personas/<persona_name>.md`.
2. Critique document against persona attack vectors and ensure claims map to `evidence_bank`.
3. Output `red_team_report.yaml` and read-only `red_team_view.md`.
[WAITING FOR USER REVIEW]
Prompt user to review view and begin interview.
''',

    "ddo/skills/ddo-interview.md": r'''
# Skill: ddo-interview
## Description
Paced Q&A dialogue to resolve Red Team issues.
## Execution Logic
1. Load `red_team_report.yaml`.
2. Iterative Loop: Present batch of issues, wait for response, map to revise/acknowledge/dispute/defer.
3. Write `interview_log.yaml`. Update `red_team_report.yaml`.
''',

    "ddo/skills/ddo-refine.md": r'''
# Skill: ddo-refine
## Description
Applies resolutions to source YAML and triggers rebuild.
## Execution Logic
1. Load `interview_log.yaml` and `document_data.yaml`.
2. Generate Before/After patch diffs for YAML modification.
[WAITING FOR USER APPROVAL]
3. Apply patches to `document_data.yaml`.
4. Trigger `ddo-render`.
''',

    "ddo/skills/ddo-run.md": r'''
# Skill: ddo-run
## Description
Composite HACF macro node chaining the 5-phase loop.
Executes: ingest -> render -> red-team -> interview -> refine.
''',

    "ddo/schemas/prd.yaml": r'''
meta:
  doc_type: "prd"
  title: "[REQUIRES USER INPUT]"
  version: "0.1.0"
  date: "[REQUIRES USER INPUT: ISO-8601]"
  authors: []
  status: "draft"
  persona: "product_critic"
  output_formats: ["pdf", "html", "md"]
  template: "prd"
  review_log: []
content:
  sections:
    - id: "problem_statement"
      title: "1. Problem Statement"
      body: "[REQUIRES USER INPUT]"
      claims: []
      evidence: []
    - id: "acceptance_criteria"
      title: "2. Acceptance Criteria"
      body: "[REQUIRES USER INPUT]"
      claims: []
      evidence: []
evidence_bank: []
''',

    "ddo/schemas/scientific_report.yaml": r'''
meta:
  doc_type: "scientific_report"
  title: "[REQUIRES USER INPUT: Full Title]"
  version: "1.0.0"
  date: "[REQUIRES USER INPUT: ISO-8601]"
  authors: []
  corresponding_author: "[REQUIRES USER INPUT]"
  abstract: "[REQUIRES USER INPUT]"
  keywords: []
  status: "draft"
  persona: "scientific_reviewer"
  output_formats: ["pdf", "html", "md"]
  template: "scientific_report"
  review_log: []
content:
  sections:
    - id: "introduction"
      title: "1. Introduction"
      body: "[REQUIRES USER INPUT]"
      claims: []
      evidence: []
evidence_bank: []
''',

    "ddo/personas/product_critic.md": r'''
# Persona: product_critic
## Domain
Product Requirements Documents (PRDs).
## Attack Vectors
1. **Missing Acceptance Criteria**: Are functional requirements strictly testable?
2. **Unsupported Value Claims**: Is every user need backed by `evidence_bank` data?
3. **Scope Creep**: Are edge cases explicitly fenced in "Out of Scope"?
## Severity
* Critical: Prevents engineering start.
* Major: Mid-sprint blocker.
* Minor: Format/tone.
''',

    "ddo/personas/scientific_reviewer.md": r'''
# Persona: scientific_reviewer
## Domain
Scientific publications.
## Attack Vectors
1. **Methodological Vagueness**: Enough detail to reproduce?
2. **Unsupported Assertions**: Missing citations?
3. **Statistical Ambiguity**: Missing p-values or significance tests?
## Severity
* Critical: Fatal flaws, rejection.
* Major: Requires major revision.
* Minor: Terminology.
''',

    "ddo/templates/typst/prd.typ": r'''
#let data_file = sys.inputs.at("data_file", default: "document_data.yaml")
#let data = yaml(data_file)
#set document(title: data.meta.title, author: data.meta.authors)
#set page(paper: "us-letter", margin: 1in)
#set text(font: "Helvetica Neue", size: 10pt)
#align(center)[#block(text(weight: 700, 18pt, data.meta.title))]
#v(1em)
#for section in data.content.sections [
  #heading(level: 1, section.title)
  #section.body
  #v(1em)
]
''',

    "ddo/templates/typst/scientific_report.typ": r'''
#let data_file = sys.inputs.at("data_file", default: "document_data.yaml")
#let data = yaml(data_file)
#set document(title: data.meta.title)
#set page(paper: "us-letter", margin: 1in)
#set text(font: "New Computer Modern", size: 11pt)
#set par(justify: true, leading: 0.65em)
#align(center)[#block(text(weight: "bold", 18pt, data.meta.title))]
#v(1em)
#show: columns.with(2, gutter: 0.25in)
#for section in data.content.sections [
  #heading(level: 1, section.title)
  #section.body
  #v(1em)
]
''',

    "ddo/templates/markdown/prd.md.j2": r'''
# {{ meta.title }}
**Product Requirements Document**

{% for section in content.sections %}
## {{ section.title }}
{{ section.body }}
{% endfor %}

{% if evidence_bank %}
## Appendix: Evidence Bank
{% for item in evidence_bank %}
**ID:** `{{ item.id }}` - {{ item.content }}
{% endfor %}
{% endif %}
''',

    "ddo/templates/markdown/scientific_report.md.j2": r'''
# {{ meta.title }}
**Authors:** {{ meta.authors | join(', ') }}

**Abstract:** {{ meta.abstract }}

{% for section in content.sections %}
## {{ section.title }}
{{ section.body }}
{% endfor %}
''',

    "ddo/templates/jinja/prd.html.j2": r'''
<!DOCTYPE html>
<html><body>
<h1>{{ meta.title }}</h1>
{% for section in content.sections %}
<h2>{{ section.title }}</h2>
<p>{{ section.body }}</p>
{% endfor %}
</body></html>
''',

    "ddo/templates/jinja/scientific_report.html.j2": r'''
<!DOCTYPE html>
<html><body>
<h1>{{ meta.title }}</h1>
<p><strong>Abstract:</strong> {{ meta.abstract }}</p>
{% for section in content.sections %}
<h2>{{ section.title }}</h2>
<p>{{ section.body }}</p>
{% endfor %}
</body></html>
'''
}

def bootstrap():
    print("Initializing Deterministic Document Orchestrator (DDO)...")
    for filepath, content in FILES.items():
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Created: {filepath}")

    # Create empty directories
    os.makedirs("Documents", exist_ok=True)
    os.makedirs("examples", exist_ok=True)

    print("\nSuccess! DDO environment is fully configured.")

if __name__ == "__main__":
    bootstrap()
