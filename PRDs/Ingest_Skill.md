# **Skill: ddo-ingest**

## **Description**

Extracts and structures raw information from source materials into a deterministic YAML schema.

Operates under a strict zero-hallucination constraint.

## **Inputs**

1. source\_paths: Paths to raw documents, URLs, or notes.  
2. schema: The target domain schema (e.g., ddo/schemas/prd.yaml).  
3. output\_dir: The target output directory (e.g., Documents/YYYY.MM.DD\_DocType\_Title/).

## **Execution Logic**

1. **Read & Parse:** Ingest all provided source\_paths.  
2. **Schema Mapping:** Apply the target schema. Extract facts from the sources and map them to the corresponding YAML nodes.  
3. **Zero Hallucination Enforcement:** \- If a schema field cannot be verifiably filled from the source material, populate the node with the exact string: \[REQUIRES USER INPUT: \<reason\>\].  
   * Never invent dates, metrics, or technical specifics.  
4. **Evidence Linkage:** For every extracted claim, create an entry in the evidence\_bank array and link its ID to the claim.  
5. **Output:** Write the resulting structure to \<output\_dir\>/document\_data.yaml.

## **Post-Condition**

Present a summary of fields populated vs. \[REQUIRES USER INPUT\] fields remaining to the user.

\[WAITING FOR USER REVIEW\]

Halt execution until the user has manually filled the missing fields in the YAML and provided explicit approval to proceed.