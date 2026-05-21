---
description: Use when implementing any feature or bugfix, before writing implementation code. Enforces red-green-refactor cycle.
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Violating the letter of the rules is violating the spirit of the rules.**

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask your human partner):**
- Throwaway prototypes
- Generated code
- Configuration files

Thinking "skip TDD just this once"? Stop. That's rationalization.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

## Red-Green-Refactor

### RED: Write the failing test
- Write a test that describes the desired behavior
- Run it with `Shell` tool
- Verify it fails for the RIGHT reason (use `ReadFile` to check output)
- If it fails for the wrong reason: fix the test, not the code

### GREEN: Write minimal code to pass
- Write the simplest code that makes the test pass
- Cheating is allowed: hardcode returns, copy-paste, whatever passes
- The only goal: make the test green
- Run the test with `Shell` tool to confirm green

### REFACTOR: Clean up
- Now that tests pass, improve the code
- Keep all tests green during refactoring
- Run the full test suite with `Shell` tool after each change
- Commit after refactoring

### Next
- Move to the next behavior
- Repeat the cycle

## The Process

1. **Identify next behavior** — smallest increment of value
2. **Write test** — assert the behavior
3. **Run test** — `Shell` with test command, expect RED
4. **Verify RED** — check failure is expected (use `ReadFile` on output if needed)
5. **Write minimal code** — just enough to pass
6. **Run test** — expect GREEN
7. **Refactor** — clean while green
8. **Run all tests** — nothing broke
9. **Commit** — `Shell` with `git commit`
10. **Repeat**

## Test Quality Rules

- One concept per test
- Test name describes behavior, not method: `test_user_cannot_access_admin_panel` not `test_access_control`
- Arrange-Act-Assert structure
- No logic in tests (no if/for/while)
- Use factory methods/fixtures for setup
- Test edge cases: empty, null, max, boundary

## Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|----------------|-----|
| Writing code before test | You don't know if test tests the right thing | Delete code, write test first |
| Testing implementation details | Brittle tests, false confidence | Test behavior, not structure |
| One giant test | Hard to diagnose failures | One concept per test |
| No assert | Test always passes, worthless | Assert something meaningful |
| Mocking everything | Test doesn't verify integration | Mock at boundaries only |
| Skipping "watch it fail" | Test might test wrong thing | Always verify RED first |

## Verification

Before claiming TDD was followed:
- `Shell` tool output showing test FAILED before code was written
- `Shell` tool output showing test PASSED after code was written
- `Shell` tool output showing full suite still passes
