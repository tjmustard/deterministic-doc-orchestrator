# **Deterministic Document Orchestrator (DDO)**

An intelligence-augmented document engine that transforms structured YAML data into reproducible documents via deterministic templates and adversarial AI review loops.

## **Overview**

DDO is a domain-agnostic orchestrator built to generate Product Requirements Documents (PRDs), Scientific Reports, Patent Disclosures, and more. It utilizes a strict 5-phase pipeline governed by the Hypergraph Coding Agent Framework (HACF) to ensure **zero hallucination**. Every generated word traces back to a version-controlled YAML source of truth.

## **The 5-Phase Loop**

1. **Ingest:** Parses raw notes/sources into structured, domain-specific YAML.  
2. **Render:** Compiles YAML deterministically into PDF (Typst), HTML, or Markdown (Jinja2).  
3. **Red Team:** Adversarially critiques the document using domain expert Personas.  
4. **Interview:** Conducts a structured CLI interview with you to resolve Red Team findings.  
5. **Refine:** Safely patches your YAML based on the interview and rebuilds the document.

## **Prerequisites**

* [uv](https://github.com/astral-sh/uv) (for isolated Python execution)  
* [Typst](https://typst.app/) (for PDF generation)  
* [Pandoc](https://pandoc.org/) (optional, for DOCX generation)

## **Quick Start**

1. Ensure your HACF orchestrator is active.  
2. Provide raw materials and prompt the system to run:  
   Execute the \`ddo-run\` skill using my notes to generate a PRD.

## **Architecture**

* **ddo/schemas/**: Minimal contract YAML definitions (meta \+ evidence\_bank).  
* **ddo/personas/**: Adversarial review lenses (e.g., product\_critic, scientific\_reviewer).  
* **ddo/templates/**: Deterministic visual layouts (Typst and Jinja2).  
* **ddo/skills/**: The HACF cognitive nodes defining the state machine.