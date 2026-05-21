# Verification Before Completion

## When to Use
Before claiming any work is done. Always run this skill before finishing.

## Purpose
Provide evidence that the work is correct and complete.

## Instructions

1. **Run the full test suite** (or relevant subset) and confirm all tests pass.
2. **Manual verification:**
   - For UI changes: verify visually or describe what was checked
   - For API changes: test endpoints or show curl/output
   - For configs: validate syntax and semantics
3. **Check for regressions:** Did you break anything else?
4. **Review your changes:**
   - Are they minimal and focused?
   - Do they follow the project's coding style?
   - Is there any debug code or prints left behind?
5. **Update todos:** Mark all items as `done` in `SetTodoList`.

## Evidence Checklist
- [ ] Tests pass (or testing was appropriately skipped)
- [ ] Manual verification performed
- [ ] No obvious regressions
- [ ] Changes are minimal and focused
- [ ] No leftover debug code

## Critical Rules
- Never claim work is done without evidence.
- If tests fail, fix them before finishing.
- If you cannot verify something, state that clearly — do not claim it is verified.
