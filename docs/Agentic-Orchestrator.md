# Agent Orchestrator: Universal Document Generation via Deterministic State Management

## 1\. Project Overview & First Principles

This repository implements a multi-agent, deterministic CLI workflow for generating complex, high-stakes documents (e.g., Patent Invention Disclosures, PRDs).

It is designed to solve the **Specification Alignment Problem**. Large Language Models (LLMs) suffer from context collapse and hallucination when forced to ingest monolithic requirements. To solve this, this architecture decouples probabilistic reasoning (LLM Agents drafting text) from deterministic state management (Python scripts routing files).

By serializing document state into a rigid YAML graph and breaking the generation process into modular, adversarial phases, we transform probabilistic text generators into reliable document engineering engines.

## 2\. The File System Firewall (Directory Structure)

Agents are strictly sandboxed. They read only from designated input folders and write only to designated output folders.

``` text  
*/orchestrator\_*workspace  
├── .agent/  
│   ├── schemas/  
│   │   ├── state*\_graph.yml               \# The deterministic tracker*  
*│   │   ├── template\_*novelty.md           \# Module extraction instructions  
│   │   └── personas/  
│   │       ├── patent*\_examiner\_*adversary.md \# Adversarial instructions  
│   │       └── commercial*\_lead\_*adversary.md   
│   └── scripts/  
│       ├── orchestrator.py               \# The automated state-machine pipeline  
│       ├── archive*\_manager.py            \# Flushes active directories*  
*│       └── audit\_*state.py                \# Reconciles state*\_graph.yml*  
*├── transcripts/*  
*│   ├── raw\_*audio*\_notes.md                \# Human dump or STT output*  
*│   └── module\_*novelty*\_answers.md         \# Answers to adversarial questions*  
*├── active/*  
*│   ├── draft\_*novelty.md                  \# Modules currently being generated  
│   └── module*\_novelty\_*questions.md       \# The generated adversarial questions  
├── compiled/  
│   └── final*\_novelty.md                  \# The synthesized, human-reviewed output*  
*└── archive/                              \# The Graveyard: ignored by agents*  
```

## **3\. The CLI Skills (The Manual Track)**

These are the atomic LLM skills (prompts/tools) that act upon the files. In a Claude Code environment, these are implemented as custom tools or aliases.

* **/extract \[module\_id\]**:  
  * **Persona:** Technical Scraper.  
  * **Action:** Reads transcripts/raw\_audio\_notes.md and .agent/schemas/template\_\[module\_id\].md. Outputs active/draft\_\[module\_id\].md. If data is missing, it must write \[NEEDS\_CLARIFICATION\].  
* **/forge\_persona \[document\_type\]**:  
  * **Persona:** Meta-Architect.  
  * **Action:** Synthesizes a specific adversarial persona (e.g., HR, Legal, Legal) and outputs .agent/schemas/personas/\[document\_type\]\_adversary.md.  
* **/redteam \[module\_id\] \[persona\_id\]**:  
  * **Persona:** Adversary (Loaded dynamically).  
  * **Action:** Reads active/draft\_\[module\_id\].md and .agent/schemas/personas/\[persona\_id\].md. Appends hostile questions to active/module\_\[module\_id\]\_questions.md. Does not throttle output.  
* **/interview \[module\_id\]**:  
  * **Persona:** Pacing Agent.  
  * **Action:** Reads active/module\_\[module\_id\]\_questions.md. Presents 3 questions at a time to the user via CLI. Appends user answers to transcripts/module\_\[module\_id\]\_answers.md.  
* **/integrate \[module\_id\]**:  
  * **Persona:** Resolution Agent.  
  * **Action:** Reads active/draft\_\[module\_id\].md and transcripts/module\_\[module\_id\]\_answers.md. Synthesizes answers and writes to compiled/final\_\[module\_id\].md.  
* **/audit\_state**:  
  * **Persona:** Deterministic Script.  
  * **Action:** Scans the file system and reconciles .agent/schemas/state\_graph.yml based on file timestamps/existence.

## **4\. Deterministic State Management (state\_graph.yml)**

This YAML file is the single source of truth for the Orchestrator script. LLMs are forbidden from attempting graph traversal.

``` YAML
\# Document Orchestration State Graph  
document\_meta:  
  title: "Quantum Magnetometer Invention Disclosure"  
  type: "invention\_disclosure"  
  global\_status: "in\_progress" 

personas:  
  \- id: "patent\_examiner\_adversary"  
    status: "clean"   
    associated\_file: ".agent/schemas/personas/patent\_examiner\_adversary.md"

inputs:  
  \- id: "raw\_transcript\_01"  
    status: "clean"   
    associated\_file: "transcripts/raw\_audio\_notes.md"

modules:  
  \- id: "module\_novelty"  
    status: "pending\_extraction" \# \[pending\_extraction | extracted | pending\_interview | pending\_integration | integrated\]  
    associated\_files:  
      template: ".agent/schemas/template\_novelty.md"  
      draft: "active/draft\_novelty.md"  
      compiled: "compiled/final\_novelty.md"  
    applied\_personas:  
      \- "patent\_examiner\_adversary"  
    adversarial\_state:  
      status: "idle" \# \[idle | interview\_in\_progress | ready\_for\_integration\]  
      master\_questionnaire: "active/module\_novelty\_questions.md"  
      answers\_transcript: "transcripts/module\_novelty\_answers.md"
```

## **5\. The Orchestrator (orchestrator.py)**

This script automates the pipeline by reading the YAML state and executing the atomic CLI skills as subprocesses. It halts gracefully if human input is needed.

``` Python

\#\!/usr/bin/env python3  
import yaml  
import sys  
import os  
import subprocess  
from pathlib import Path

BASE\_DIR \= Path(\_\_file\_\_).parent.parent.resolve()  
STATE\_GRAPH\_PATH \= BASE\_DIR / ".agent" / "schemas" / "state\_graph.yml"

def load\_state():  
    try:  
        with open(STATE\_GRAPH\_PATH, 'r') as f:  
            return yaml.safe\_load(f)  
    except FileNotFoundError:  
        print(f"CRITICAL ERROR: State graph not found.")  
        sys.exit(1)

def save\_state(state\_data):  
    with open(STATE\_GRAPH\_PATH, 'w') as f:  
        yaml.dump(state\_data, f, sort\_keys=False, default\_flow\_style=False)

def execute\_skill(command\_list):  
    print(f"Executing: {' '.join(command\_list)}")  
    try:  
        result \= subprocess.run(command\_list, check=True, text=True, capture\_output=True)  
        print(result.stdout)  
        return True  
    except subprocess.CalledProcessError as e:  
        print(f"ERROR: {e.stderr}")  
        return False

def orchestrate():  
    state \= load\_state()  
    modules \= state.get('modules', \[\])  
      
    for module in modules:  
        mod\_id \= module\['id'\]  
        current\_status \= module\['status'\]

        if current\_status \== 'pending\_extraction':  
            if execute\_skill(\['claude', 'run', '/extract', mod\_id\]):  
                module\['status'\] \= 'extracted'  
                save\_state(state)  
            else: sys.exit(1)

        elif current\_status \== 'extracted':  
            personas \= module.get('applied\_personas', \[\])  
            for p\_id in personas:  
                execute\_skill(\['claude', 'run', '/redteam', mod\_id, p\_id\])  
            module\['status'\] \= 'pending\_interview'  
            module\['adversarial\_state'\]\['status'\] \= 'interview\_in\_progress'  
            save\_state(state)

        elif current\_status \== 'pending\_interview':  
            print(f"ACTION REQUIRED: Human interview for {mod\_id}.")  
            if execute\_skill(\['claude', 'run', '/interview', mod\_id\]):  
                module\['status'\] \= 'pending\_integration'  
                module\['adversarial\_state'\]\['status'\] \= 'ready\_for\_integration'  
                save\_state(state)  
            else:  
                print("Halting for human input.")  
                sys.exit(0) 

        elif current\_status \== 'pending\_integration':  
            if execute\_skill(\['claude', 'run', '/integrate', mod\_id\]):  
                execute\_skill(\['python3', '.agent/scripts/archive\_manager.py', mod\_id\])  
                module\['status'\] \= 'integrated'  
                save\_state(state)  
            else: sys.exit(1)

if \_\_name\_\_ \== "\_\_main\_\_":  
    orchestrate()
```

## **6\. Template Archetypes (Epistemic Boundaries)**

These Markdown files force the LLMs to adhere to strict schemas.

### **Content Template (template\_novelty.md)**

``` Markdown

\# Module: The Core Novelty  
**\*\*Agent Instruction:\*\*** Map the raw transcript to this schema. DO NOT hallucinate. If data is missing, output \`\[NEEDS\_CLARIFICATION\]\`.

\#\# 1\. The Core Problem  
\- **\*\*The specific failure point:\*\*** \[Insert from transcript\]  
\- **\*\*Current workarounds used:\*\*** \[Insert from transcript\]

\#\# 2\. The Differentiating Mechanism  
\- **\*\*The novel component:\*\*** \[Insert from transcript\]  
\- **\*\*How it functions differently:\*\*** \[Insert from transcript\]
```

### **Persona Template (patent\_examiner\_adversary.md)**

``` Markdown

\# Adversarial Persona: The Patent Examiner  
**\*\*Agent Instruction:\*\*** Review the drafted module. Hunt for prior art collisions and obviousness. Output strictly a numbered Markdown list of adversarial questions. 

**\*\*Constraints:\*\***  
1\. Force the inventor to define edge cases.  
2\. Force the inventor to explain why competitors cannot use alternative methods.  
3\. DO NOT output conversational filler.
```

## **7\. Standard Operating Procedure (Execution)**

1. **Initialize:** Define state\_graph.yml for your desired document.  
2. **Ingest:** Drop transcript into /transcripts/raw\_audio\_notes.md.  
3. **Orchestrate:** Run python orchestrator.py.  
4. **Interact:** When the script halts at pending\_interview, complete the Q\&A loop. Re-run python orchestrator.py to finalize synthesis.

