# **Product Requirements Document: Deterministic Document Orchestrator (DDO)**

**Version:** v0.0.2 (HACF Integration)

**Date:** June 2026

## **1\. Executive Summary**

The Deterministic Document Orchestrator (DDO) is an intelligence-augmented document engine designed to transform structured YAML data into reproducible documents via deterministic templates and adversarial AI review loops.

## **2\. Core Tenets**

1. **YAML as the Source of Truth:** Documents are data routing problems.  
2. **Deterministic Output:** Same YAML \+ Same Template \= Identical Output.  
3. **Mandatory Human-in-the-Loop:** Strict state-machine phase gates prevent runaway generation.  
4. **Adversarial by Default:** Documents are actively attacked by domain-specific Personas.

## **3\. Technical Constraints & Decisions**

* **Cognitive Orchestrator:** Hypergraph Coding Agent Framework (HACF). DDO operates as a pure domain engine (schemas, templates, personas), while HACF drives the state machine and cognitive loops. The HACF framework directory is strictly .gitignore'd to maintain separation of concerns.  
* **Schema Architecture:** "Fully Dynamic with Minimal Contract." Dynamic YAML requires a meta block and an evidence\_bank array. Claim linkage is enforced at the section level.  
* **Review UI/Data Separation:** To avoid bidirectional parsing errors, Red Team and Interview phases rely on machine-readable YAML (red\_team\_report.yaml, interview\_log.yaml) for programmatic data mutation. A Read-Only ephemeral Markdown file is generated strictly for human visual review.  
* **Text Parsing Workaround:** To guarantee 100% accurate AI reading, the Red Team critiques the Jinja2 Markdown/HTML render rather than the PDF. Since both formats derive deterministically from the same YAML, the critique remains mathematically valid for the PDF.  
* **Output Formats:** Typst (PDF) and Jinja2 (HTML, MD).

## **4\. The 5-Phase HACF Skill Pipeline**

1. **ddo-ingest:** Transforms raw sources into document\_data.yaml. Flags missing data.  
2. **ddo-render:** Hermetic Python orchestrator converting YAML to target format via Typst/Jinja2.  
3. **ddo-red-team:** Adversarial review using a Persona file. Outputs red\_team\_report.yaml.  
4. **ddo-interview:** Paced, batched terminal Q\&A to resolve findings. Outputs interview\_log.yaml.  
5. **ddo-refine:** Safely patches document\_data.yaml based on interview logs (with Before/After diff approval) and auto-triggers ddo-render.  
* **ddo-run:** A composite HACF macro chaining phases 1 through 5\.

## **5\. System Architecture**

deterministic-doc-orchestrator/  
├── ddo/  
│   ├── schemas/           \# Curated minimal contracts (PRD, Scientific Report)  
│   ├── templates/         \# Typst and Jinja2 templates  
│   ├── personas/          \# Red Team Personas (product\_critic, scientific\_reviewer)  
│   ├── skills/            \# HACF skill definitions (ddo-\*.md)  
│   ├── build.py           \# PEP 723 Python orchestrator   
│   └── writing\_style.md   \# Domain-agnostic style enforcement  
├── PRD/                   \# Project documentation  
├── Documents/             \# Output directory (gitignored)  
└── .gitignore             \# Explicitly ignores HACF framework

## **6\. Success Criteria**

1. Successfully ingest a raw text brief into YAML (ddo-ingest).  
2. Successfully render YAML into PDF, Markdown, and HTML (ddo-render).  
3. Execute a complete HACF Red Team \-\> Interview \-\> Refine loop patching a logical gap in a test document without corrupting the YAML structure.