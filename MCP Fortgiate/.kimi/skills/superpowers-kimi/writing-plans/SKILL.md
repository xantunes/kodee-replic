# Writing Plans

## When to Use
When you have specs, requirements, or an approved approach and need to create an implementation plan.

## Purpose
Produce a clear, actionable, bite-sized implementation plan.

## Instructions

1. **Break down the work:** Divide into small, verifiable steps.
2. **Identify key files:** Which files need to be read, created, or modified?
3. **Define verification:** How will each step be validated? (tests, manual check, etc.)
4. **Write the plan:**
   - Use a plan file if the project uses them (e.g., `docs/plans/YYYY-MM-DD-<feature>.md`)
   - Or present the plan inline if the task is small
5. **Get approval:** Present the plan to the user before execution.

## Plan Structure
```
## Goal
## Steps
1. Step name - verification method
2. Step name - verification method
## Risks / Open Questions
```

## Critical Rules
- Plans should be bite-sized — no step should take more than ~15 minutes.
- Always include a verification method for each step.
- If the user rejects the plan, revise and present again.
