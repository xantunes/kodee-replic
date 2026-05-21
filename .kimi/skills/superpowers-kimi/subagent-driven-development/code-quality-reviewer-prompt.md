# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent via the `Agent` tool.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

## Agent Tool Parameters

```
subagent_type: "coder"
description: "Review code quality for Task N"
prompt: |
  You are reviewing code quality for a completed implementation.

  ## Task Description

  [Task description from plan]

  ## Files to Review

  [List of files changed/created by implementer]

  ## What to Check

  Read all changed files using ReadFile and evaluate:

  **Architecture & Organization:**
  - Does each file have one clear responsibility with a well-defined interface?
  - Are units decomposed so they can be understood and tested independently?
  - Is the implementation following the file structure from the plan?
  - Did this implementation create new files that are already large, or significantly grow existing files?
    (Don't flag pre-existing file sizes — focus on what this change contributed.)

  **Code Quality:**
  - Are names clear and descriptive?
  - Is the code clean and maintainable?
  - Are there obvious bugs or edge cases missed?
  - Is error handling appropriate?

  **Testing:**
  - Do tests verify actual behavior (not just mock behavior)?
  - Is test coverage adequate?
  - Are tests readable and maintainable?

  **Discipline:**
  - Did the implementer avoid overbuilding (YAGNI)?
  - Did they follow existing codebase patterns?
  - Are there debug statements or temporary code left behind?

  ## Report Format

  Provide a structured review:

  **Strengths:**
  - [What's well done]

  **Issues:**
  - 🔴 Critical: [must fix before approval]
  - 🟡 Important: [should fix, discuss if disagree]
  - 🟢 Minor: [nice to have, optional]

  **Assessment:** APPROVED | NEEDS_WORK

  If NEEDS_WORK, list exactly what needs to change with file:line references.
```
