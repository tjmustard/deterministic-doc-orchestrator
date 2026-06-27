# **Skill: ddo-red-team**

## **Description**

Executes a systematic, adversarial critique of a generated document using a domain-specific Persona. Output is stored programmatically in YAML, with an ephemeral Markdown view for human review.

## **Inputs**

1. document\_path: Path to the rendered document (prefer .md or .html over .pdf for text extraction reliability).  
2. persona\_name: Name of the persona to load (e.g., product\_critic).  
3. output\_dir: The target document directory.

## **Execution Logic**

1. **Load Persona:** Read ddo/personas/\<persona\_name\>.md. Internalize its attack vectors, severity taxonomy, and format rules.  
2. **Read Document:** Parse the full text of document\_path.  
3. **Adversarial Critique:** Cross-reference the document's claims against the domain-specific attack vectors. Ensure all factual claims map to the evidence\_bank.  
4. **Data Generation:** Write red\_team\_report.yaml to output\_dir. Structure must include an array of issues containing: id, severity, category, location, description, suggestion, resolved (default false), and resolution (default null).  
5. **View Generation:** Write red\_team\_view.md to output\_dir. This is a read-only, human-friendly translation of the YAML report.

## **Post-Condition**

Present a summary (N Critical, N Major, N Minor) to the user in the terminal.

\[WAITING FOR USER REVIEW\]

Prompt the user to review red\_team\_view.md and confirm readiness to begin ddo-interview.