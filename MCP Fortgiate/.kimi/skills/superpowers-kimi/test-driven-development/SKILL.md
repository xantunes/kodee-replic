# Test-Driven Development

## When to Use
Before writing implementation code for new features, bug fixes, or refactors — especially when the project already has tests.

## Purpose
Ensure code is testable and verified from the start.

## Instructions

1. **Assess the testing setup:**
   - What test framework is used? (pytest, jest, vitest, etc.)
   - Where are tests located?
   - How are tests run?
2. **Write failing tests first** (if TDD is appropriate and the user has not said to skip it).
3. **Run tests** to confirm they fail for the expected reason.
4. **Write the minimum implementation** to make tests pass.
5. **Run tests again** to confirm they pass.
6. **Refactor** if needed, keeping tests green.

## When to Skip
- The user explicitly says "skip TDD" or "just implement it"
- The project has no testing infrastructure and setting it up is out of scope
- The change is purely cosmetic (formatting, comments, etc.)

## Critical Rules
- User instructions override this skill — if the user says skip TDD, skip it.
- Do NOT write tests for trivial one-liner fixes unless the project requires it.
- Always run the test suite after implementation changes.
