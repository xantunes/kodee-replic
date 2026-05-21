# Subagent-Driven Development

## When to Use
When executing complex plans that benefit from parallelization or delegation (e.g., multi-file changes, research + implementation, complex refactoring).

## Purpose
Use subagents to execute work in parallel, keeping the main session focused on coordination.

## Instructions

1. **Break the plan into sub-tasks** that can run independently.
2. **Delegate to subagents:**
   - Use `Agent` tool with appropriate `subagent_type`:
     - `coder` — for software engineering tasks
     - `explore` — for read-only codebase investigation
     - `plan` — for architecture/planning tasks
3. **Provide complete context:** Each subagent needs full context in its prompt — they do not automatically see the parent context.
4. **Run in parallel** when tasks are independent.
5. **Review results:** Inspect subagent outputs before accepting.
6. **Integrate changes:** Apply approved subagent changes to the codebase.
7. **Proceed to verification:** Load `verification-before-completion`.

## Critical Rules
- Always provide complete prompts to subagents — do not assume shared context.
- Prefer resuming existing subagent instances if they have relevant context.
- Use foreground subagents by default; background only when beneficial.
- Do NOT delegate trivial tasks (<3 tool calls) to subagents — overhead is not worth it.
