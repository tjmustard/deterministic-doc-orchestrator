# **Skill: ddo-run**

## **Description**

A composite HACF macro node that executes the full 5-phase deterministic orchestration pipeline in sequence.

## **Inputs**

1. source\_paths: Paths to raw material.  
2. schema: Target domain schema.  
3. template\_name: Template to apply.  
4. format: Output format.  
5. persona\_name: Persona for Red Team.

## **Execution Logic (Pipeline)**

1. **Phase 1:** Call ddo-ingest with source\_paths and schema. Wait for user completion of \[REQUIRES USER INPUT\] fields.  
2. **Phase 2:** Call ddo-render with format and template\_name.  
3. **Phase 3:** Call ddo-red-team using the generated markdown render and persona\_name.  
4. **Phase 4:** Call ddo-interview on the resulting report.  
5. **Phase 5:** Call ddo-refine to update the YAML and trigger a re-render.  
6. **Evaluation Gate:** Ask the user if the document is final or if another loop (Phase 3-\>5) is required.

## **Post-Condition**

If finalized, mark status: final in the YAML meta block.