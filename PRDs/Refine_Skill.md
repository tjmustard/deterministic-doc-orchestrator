# **Skill: ddo-refine**

## **Description**

Applies user-approved resolutions from the interview log directly to the source YAML, then triggers a document rebuild.

## **Inputs**

1. log\_path: Path to interview\_log.yaml.  
2. data\_path: Path to document\_data.yaml.

## **Execution Logic**

1. **Read Logs:** Load both YAML files into memory.  
2. **Patch Generation:** Iterate through interview\_log.yaml:  
   * If decision \== revise: Construct the necessary YAML modification for document\_data.yaml at the appropriate node.  
   * If decision \== add evidence: Append new nodes to the evidence\_bank array and link to the relevant section.  
   * If decision \== acknowledge or dispute: Append to the review\_log meta array for traceability.  
3. **Dry Run:** Present a numbered list of "Before/After" YAML block diffs to the user.

\[WAITING FOR USER APPROVAL\]

Ask the user to approve the diffs (e.g., "approve all", "skip 2").

4. **Apply & Rebuild:** \- Apply approved patches to document\_data.yaml.  
   * Execute the ddo-render skill using the previously used template and format parameters to immediately regenerate the output.

## **Post-Condition**

Present the rebuilt document. Ask the user: "Would you like to run another Red Team pass, or are we finished?"