# Executing Plans

## When to Use
When executing a written plan manually in the current session. Use for simple plans (≤2-3 files, straightforward changes).

## Purpose
Execute the plan step-by-step with minimal overhead.

## Instructions

1. **Load the plan:** Read the plan file or recall the agreed steps.
2. **Update todo list:** Mark the current step as `in_progress` using `SetTodoList`.
3. **Execute one step at a time:**
   - Read necessary files
   - Make changes using `WriteFile`, `StrReplaceFile`, or `Shell`
   - Run tests or verification commands
4. **Mark done:** After verification, mark the step as `done`.
5. **Handle failures:** If a step fails, debug, fix, and re-verify before moving on.
6. **Proceed to verification:** When all steps are done, load `verification-before-completion`.

## Critical Rules
- Do NOT skip verification steps.
- If the plan turns out to be wrong, pause and re-plan if needed.
- Use `executing-plans` for simple work; for complex parallel work use `subagent-driven-development`.
