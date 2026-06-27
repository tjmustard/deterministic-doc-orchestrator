# **Skill: ddo-interview**

## **Description**

Conducts a structured, paced Q\&A dialogue with the user to resolve issues identified by the Red Team. Captures decisions as data.

## **Inputs**

1. report\_path: Path to red\_team\_report.yaml.  
2. batch\_size: Number of issues to present per prompt (Default: 2).

## **Execution Logic**

1. **Initialize:** Read red\_team\_report.yaml. Filter for resolved: false. Sort by severity (Critical \-\> Major \-\> Minor).  
2. **Iterative Dialogue Loop:**  
   * Present the next batch\_size issues to the user in the terminal.  
   * For each issue, ask targeted questions based on the Persona's interview templates.  
   * \[WAITING FOR USER RESPONSE\]: Halt until the user dictates resolutions for the batch.  
   * Map user responses to a decision matrix: revise, acknowledge, dispute, or defer.  
   * Append resolutions to an interview\_log.yaml object in memory.  
   * Mark the issue as resolved: true in the in-memory report.  
3. **Commit:** Once all issues are addressed or user says "done for now", write the in-memory interview\_log.yaml to disk. Update red\_team\_report.yaml with resolved statuses.

## **Post-Condition**

Confirm interview\_log.yaml has been written successfully. Transition to ddo-refine.