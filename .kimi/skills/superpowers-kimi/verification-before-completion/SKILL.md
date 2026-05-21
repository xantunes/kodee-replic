---
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs. Requires running verification commands and confirming output before making any success claims.
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command with Shell tool (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting subagent success reports without checking
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over

## The Process

When you're about to say something is done:

1. **Identify the verification command**
   - What specifically proves this works?
   - Not "tests should pass" — which tests? Which command?

2. **Run it fresh with Shell tool**
   - Run the full command, not a partial one
   - Don't assume you know the output

3. **Read the output with ReadFile or check Shell result**
   - Read every line if needed
   - Check exit code
   - Count failures/errors explicitly

4. **Verify against the claim**
   - Does output match what you claimed?
   - Are there hidden failures in the middle of output?
   - Did something else break?

5. **State claim WITH evidence**
   - "Tests pass: pytest output shows 42 passed, 0 failed"
   - "Build succeeds: npm run build exited 0"
   - NOT "tests pass" without evidence

## Examples

**BAD:**
> I've fixed the bug. The tests should pass now.

**GOOD:**
> I've fixed the bug. Verification:
> ```
> $ python -m pytest tests/test_bug.py -v
> test_bug.py::test_regression PASSED
> test_bug.py::test_edge_case PASSED
> 2 passed in 0.3s
> ```

**BAD:**
> The feature is complete.

**GOOD:**
> The feature is complete. Verification:
> ```
> $ python -m pytest tests/test_feature.py -v
> test_feature.py::test_basic PASSED
> test_feature.py::test_advanced PASSED
> test_feature.py::test_edge_case PASSED
> 3 passed in 0.5s
>
> $ python -m mypy src/feature.py
> Success: no issues found
> ```

## Completion Checklist

Before claiming complete:
- [ ] I ran the exact verification command fresh with Shell
- [ ] I read the full output
- [ ] I verified the output matches my claim
- [ ] I cited the evidence when making the claim
