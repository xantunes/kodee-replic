---
description: Use when executing implementation plans with independent tasks. Dispatches fresh Kimi subagent per task, with two-stage review after each - spec compliance first, then code quality.
---

# Subagent-Driven Development

## Overview

Execute plans by dispatching fresh subagents per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions, you ensure they stay focused and succeed. They don't inherit your session's context or history — you construct exactly what they need. This preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete.

## When to Use

Use this skill when:
- You have an implementation plan
- Tasks are mostly independent
- You want quality through review

**vs. Executing Plans (manual):**
- This skill uses subagents for each task
- Two-stage review after each task
- Faster iteration (no human-in-loop between tasks)
- Higher quality through isolated focus

## The Process

### Step 1: Read Plan and Extract Tasks

1. Read the plan file with `ReadFile`
2. Extract all tasks with full text
3. Note context and dependencies
4. Create `SetTodoList` with all tasks

### Step 2: Per-Task Execution Loop

For each task:

#### A. Dispatch Implementer Subagent

Use `Agent` tool with `subagent_type="coder"`:
- **description:** "Implement Task N: [task name]"
- **prompt:** Use template from `implementer-prompt.md`, filling in:
  - Task number and name
  - FULL TEXT of the task from the plan
  - Context (where this fits, dependencies)
  - Working directory

**Model selection:**
- Simple tasks (1-2 files, clear spec): use default model
- Complex tasks (multi-file, integration): use `model` override if needed
- Architecture/design tasks: use most capable model

#### B. Handle Implementer Response

Implementer reports one of four statuses:

| Status | Meaning | Action |
|--------|---------|--------|
| **DONE** | Completed successfully | Proceed to spec review |
| **DONE_WITH_CONCERNS** | Completed but flagged doubts | Read concerns. If about correctness/scope, address before review. If observations, note and proceed. |
| **NEEDS_CONTEXT** | Needs missing information | Provide context and re-dispatch |
| **BLOCKED** | Cannot complete | Assess: provide context, re-dispatch with different model, break into smaller tasks, or escalate to human |

**Never** ignore BLOCKED or force retry without changes.

#### C. Dispatch Spec Compliance Reviewer

Use `Agent` tool with `subagent_type="coder"` or `subagent_type="explore"`:
- **description:** "Review spec compliance for Task N"
- **prompt:** Use template from `spec-reviewer-prompt.md`, filling in:
  - Full task requirements
  - Implementer's report
  - Files to review

Reviewer checks:
- Missing requirements
- Extra/unneeded work
- Misunderstandings

If issues found: fix them (re-dispatch implementer or fix yourself), then re-review.

#### D. Dispatch Code Quality Reviewer

Only after spec review passes.

Use `Agent` tool with `subagent_type="coder"`:
- **description:** "Review code quality for Task N"
- **prompt:** Use template from `code-quality-reviewer-prompt.md`, filling in:
  - Task description
  - Files changed
  - Commit range (if applicable)

Reviewer checks:
- Clean code, maintainability
- Test quality
- File organization
- Adherence to plan structure

If issues found: fix them, then re-review.

#### E. Mark Complete

Use `SetTodoList` to mark task complete.

### Step 3: Final Review

After all tasks:
1. Dispatch final code reviewer for entire implementation
2. Use `finishing-a-development-branch` methodology

## Prompt Templates

- `./implementer-prompt.md` - Prompt for implementer subagent
- `./spec-reviewer-prompt.md` - Prompt for spec compliance reviewer
- `./code-quality-reviewer-prompt.md` - Prompt for code quality reviewer

## Example Workflow

```
You: I'm using Subagent-Driven Development to execute this plan.

[Read plan file]
[Extract all 5 tasks with full text and context]
[SetTodoList with all tasks]

Task 1: Hook installation script

[Dispatch implementer subagent via Agent tool]

Implementer: "Before I begin - should the hook be installed at user or system level?"

You: "User level (~/.config/superpowers/hooks/)"

Implementer: "Got it. Implementing now..."
[Later] Implementer returns DONE with report.

[Dispatch spec compliance reviewer via Agent tool]
Spec reviewer: ✅ Spec compliant

[Dispatch code quality reviewer via Agent tool]
Code reviewer: Strengths: Good test coverage. Issues: None. Approved.

[SetTodoList - mark Task 1 complete]

Task 2: Recovery modes
[Continue loop...]
```

## Integration

**Required workflow skills:**
- `writing-plans` — Creates the plan this skill executes
- `finishing-a-development-branch` — Complete development after all tasks
- `test-driven-development` — Implementers should follow TDD when specified
- `verification-before-completion` — Verify before marking complete
