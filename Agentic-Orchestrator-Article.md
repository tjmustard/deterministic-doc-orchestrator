# The Agent Orchestrator: Scaling Innovation at SandboxAQ

## The Innovation Bottleneck: Why Great Ideas Get Stuck in Paperwork

At deep-tech companies like SandboxAQ, invention disclosures are the lifeblood of intellectual property. But the manual process of creating them is often a slow, repetitive grind. For our scientists, writing a comprehensive disclosure required days of dedicated "deep work" spread out over weeks.

While essential for the legal and review teams, this administrative burden was a massive time sink for the inventors. Every hour spent wrestling with documentation was an hour taken away from actual innovation. Even worse, the sheer time commitment meant some brilliant ideas were never articulated simply because the scientists didn't have the bandwidth to write them down.

**The "Aha" Moment** The turning point came when a colleague voiced their frustration about how long these documents took to generate. As a Product Manager, I had previously built workflows to automatically generate PRDs based on user interviews. Listening to my colleague, it clicked: *If I can synthesize a PRD from a user interview, I can synthesize an invention disclosure by interviewing a scientist.* I realized that manual document creation, at its core, is just a series of repeatable, highly contextual tasks. But I also knew that applying AI to this problem required more than just typing a prompt into a chat window.

**The Shift to "Agent Orchestrator"** To solve this, I had to shift from being a solo writer to an **Agent Orchestrator**.

Being an Orchestrator means designing the comprehensive system and processes that AI agents must follow to successfully achieve a goal. It requires an intimate understanding of every step of the workflow so you can engineer precise instructions and parameters.

To build this, I "dogfooded" the system on an invention of my own. My initial attempts were clunky, filled with manual bottlenecks, and required constant tweaking. But through repeated failures and iterations, I transformed a poor workflow into an automated, highly structured, and inventor-friendly system that unblocked our scientists and scaled our IP generation.

---

## Breaking the Monolith: Markdown and Modularity

Building an automated system required standardizing our inputs and outputs. Previously, invention disclosures were generated manually, resulting in a chaotic mix of formatting and styles depending on who was writing. To fix this, I converted our existing disclosure formats into a structured **Markdown** template.

Why Markdown? LLMs are exceptionally good at following formatting and style guidelines when provided with Markdown examples. More importantly, this format allowed me to embed specific clues and instructions directly into the template—guiding the AI on exactly what each paragraph, bulleted list, and table should contain.

**Solving for Accuracy: The Context Window Trap** When working with AI, it is tempting to feed all your data into a massive prompt and ask the LLM to write the entire document at once. But through manual testing and dogfooding my own inventions, I quickly learned that this approach fails for highly technical tasks.

Invention disclosures require incredibly specific details to be accurate. When forced to process long, monolithic documents, the LLM's accuracy degraded. It would stray from the original scope, lose track of nuanced meaning, or skip vital details. To maintain high fidelity, I had to keep the context window small.

**The Strategy: Slicing the Monolith** Instead of one massive prompt, I broke the document generation into a series of distinct sub-sections. I got lucky in this regard: our internal IP process required inventors to copy and paste specific sections of their disclosure into an online form. Those individual text boxes naturally became my roadmap.

By treating each text box as a separate module, I could assign an agent to focus entirely on one narrow, high-fidelity task at a time without losing the thread of the larger narrative. This modular approach drastically improved the quality of the output—a realization that has since become a foundational strategy for all of my complex document generation projects.

---

## The SOP: Engineering the Context

An agentic system is only as effective as the data it consumes. If you feed an LLM garbage, it will eloquently summarize that garbage. To ensure high-quality outputs, I had to engineer the context *before* the agents ever touched the data.

Through trial and error, I discovered that my detailed Markdown template could do more than just format the output—it could dictate the input. I used the required structure of the template to reverse-engineer an **interview script**.

**Standardizing the Input** Rather than staring at a blank page, inventors use this script to interview themselves or their co-inventors. By simply talking through their invention and answering the script's targeted questions, they generate a rich, highly detailed transcript. This transcript becomes the perfect raw material, giving the agents exactly the context they need to populate the Markdown sections accurately.

To scale this across the team, I developed a comprehensive **Standard Operating Procedure (SOP)**. This document serves as the central hub for the entire process. It provides:

* **The Workflow:** Step-by-step instructions and links to the interview scripts and internal disclosure forms.  
* **Guardrails:** Clear guidelines on which AI tools are approved for use.  
* **Security Protocols:** Strict data handling rules to protect our highly sensitive intellectual property.

**Human-in-the-Loop: Protecting the Insight** One of the biggest risks of using LLMs for technical writing is the tendency for the AI to "flatten" complex ideas into sanitized, generic corporate speak.

To prevent this, the SOP enforces a strict human-in-the-loop requirement. The system does not automatically submit the final document. Instead, inventors are required to manually read, edit, copy, and paste the generated sections into the final disclosure form themselves. This intentional "productive friction" ensures the inventor takes final ownership of the text, guaranteeing their unique technical insight remains the undeniable core of the document.

---

## The "Secret Sauce": The Adversarial Agent

Generative AI is great at drafting text, but to create a truly robust invention disclosure, you need friction. You need to stress-test the idea.

The inspiration for this step came after I was peppered with questions while submitting my own manual invention disclosure. A colleague suggested we formalize that rigorous questioning process. I took their idea and integrated it into my agentic system, creating what became the "Secret Sauce" of our workflow: **The Adversarial Agent**.

**The Interrogator Persona** I designed this agent to act as a highly skeptical **Patent Examiner**. Its sole job is to review the initial disclosure drafts and play Devil’s Advocate, questioning every assumption, technical leap, and methodology. (Looking ahead, I see immense potential in combining multiple personas—like a peer scientist and a patent attorney—either as a single skill or an ensemble of agents, to interrogate the document from multiple angles).

**The Deep Dive: 50 Questions, 3 at a Time** A rigorous patent examiner persona can easily generate over 50 challenging questions about a single disclosure. Handing an inventor a list of 50 complex questions is daunting and risks stalling the process entirely.

To solve this, I built a secondary "Interview Agent." Instead of dropping a massive questionnaire on the inventor, this agent conducts a conversational interview, feeding the inventor just three questions at a time. To keep the friction low, inventors are encouraged to use Speech-to-Text (STT) or simply record and transcribe a meeting where they talk through their answers.

**Refining Logic and Uncovering Novelty** This adversarial step is transformative. It forces inventors to articulate edge cases, consider alternative materials, and explain workarounds they might have intuitively known but failed to document.

I experienced this firsthand. When I ran my own invention through the Adversarial Agent, it forced me to clarify my arguments and uncover hidden novelty. Not only did this make the patent highly defensible, but it made the claims significantly stronger—ultimately clearing the high bar required by our legal team to move forward.

---

## The Final Synthesis

After the inventor has survived the Adversarial Agent's gauntlet, the system enters its final phase. The raw data has been gathered, structured, and rigorously stress-tested. Now, it all needs to come together.

**The Integration Agent** To build the final document, I designed an Integration Agent. This agent takes both the original, baseline invention disclosure and the rich transcripts generated from the adversarial Q\&A sessions. It then intelligently updates each Markdown section with the newly discovered edge cases, clarifications, and stronger claims.

*(Note: Building this system is an iterative process. I've already realized that this integration phase could benefit from the same modular, "one-sub-section-at-a-time" approach I used in the initial drafting phase, and that is my next optimization target.)*

**The Result: Standardizing Excellence** The impact of this workflow has been deeply rewarding. Our internal IP team found the agentic system so useful that we have now rolled it out company-wide. I've personally helped multiple departments convert standard inventor interviews into highly technical, defensible disclosures.

The feedback from the scientists has been overwhelmingly positive. While manual review and editing are always required—the system is an assistant, not an autopilot—the inventors are consistently impressed by the results. Most importantly, they highlight the massive reduction in the time it takes to get an idea out of their heads and onto paper. By standardizing the quality to a high minimum baseline, we ensure every idea that moves forward is primed for success.

**Success at SandboxAQ: Faster Time-to-File** Ultimately, this "innovation factory" drastically reduces the time needed to generate documentation, which directly accelerates our time-to-file.

While there are other parts of the patent pipeline ripe for AI optimization, this process also highlighted a crucial boundary: the final legal review. AI is incredible for generating, structuring, and stress-testing ideas, but you cannot hold an AI agent liable for a mistake. The human lawyer remains an irreplaceable part of the process. By automating the grueling administrative drafting, we simply allow our legal team to do what they do best—practicing law, rather than chasing down technical details.

---

## Closing Thoughts: The Role of the Orchestrator

If there is one lesson to take away from building this "innovation factory," it is this: for complex workflows, "prompting" is not enough. You have to design the *system* the agents reside in to get the output you want.

**Beyond Prompting: The "Recent Grad" Rule** When building agentic workflows, I treat AI agents like recent graduates who have only had five minutes of training. If you hand them a massive, multi-tiered project all at once, they will fail. But if you act as the Orchestrator and break that complex workflow down into **atomic functions**—giving each agent one highly specific, well-defined job—you create a solution that is robust, high-quality, and infinitely repeatable.

**The Future of IP and Autonomous Agents** Looking ahead, what is truly exciting is the evolution toward more autonomous agents that can learn from their mistakes. We are moving toward a future where a system could take a known input and a desired output, and automatically break the problem down into those atomic issues itself.

Of course, a human-in-the-loop will always be a strict requirement for legal documents. But the administrative heavy lifting of IP generation is shifting. Agentic systems allow technical teams to spend less time wrestling with documentation and more time doing what they do best: focusing on the next major breakthrough.

As we transition from solo contributors to Agent Orchestrators, our bottleneck is no longer our capacity to write, but our capacity to design better systems.

**So, I leave you with this question:** What is the complex, manual workflow in your organization that could—and should—be orchestrated next?  
