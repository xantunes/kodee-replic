---
description: Use before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.

## HARD GATE

Do NOT write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

Use `SetTodoList` to track these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to their complexity, get user approval after each section
5. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md` and commit
6. **Spec self-review** — quick inline check for placeholders, contradictions, ambiguity, scope
7. **User reviews written spec** — ask user to review the spec file before proceeding
8. **Transition to implementation** — proceed to `writing-plans` phase

## Process Flow

1. Explore project context
2. Ask clarifying questions (one at a time)
3. Propose 2-3 approaches with trade-offs
4. Present design sections → get user approval
5. Write design doc to `docs/specs/`
6. Spec self-review
7. User reviews spec → approved?
8. Proceed to writing-plans

**The terminal state is writing-plans.** Do NOT jump to implementation. The ONLY next phase after brainstorming is writing-plans.

## The Process

**Understanding the idea:**

- Check out the current project state first (use `ReadFile`, `Grep`, `Glob`, `Shell` with `git log`, etc.)
- Before asking detailed questions, assess scope: if the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.
- If the project is too large for a single spec, help the user decompose into sub-projects: what are the independent pieces, how do they relate, what order should they be built? Then brainstorm the first sub-project through the normal design flow. Each sub-project gets its own spec → plan → implementation cycle.
- For appropriately-scoped projects, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Once you understand the goal, propose 2-3 approaches with clear trade-offs
- State your recommendation and why
- Let the user choose or suggest modifications

**Presenting the design:**

- Present in sections: overview, data model, API/interface, UI/UX (if applicable), edge cases
- Scale detail to complexity — a simple script gets a paragraph, a complex system gets sections
- Get explicit approval on each section before moving to the next

**Writing the spec:**

- Save to `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Include: goal, approach, data model, interfaces, edge cases, open questions
- Self-review for: placeholders, contradictions, ambiguity, scope creep
- Ask user to review the written spec before proceeding

**Transition:**
- Once spec is approved, say: "Design approved. Moving to writing-plans phase."
- The `writing-plans` skill will load automatically or you should proceed following its methodology.
