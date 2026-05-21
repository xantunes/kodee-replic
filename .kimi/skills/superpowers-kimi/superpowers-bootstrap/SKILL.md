---
description: Use when starting any software development conversation. Establishes Superpowers methodology for Kimi - how to use skills, subagents, and the development workflow.
---

# Superpowers for Kimi

## If You Are a Subagent

Stop. If you were dispatched as a subagent to execute a specific task, skip this skill and focus on your assigned task.

## Core Principle

Before writing code, understand what you're building. After understanding, plan. After planning, execute with verification. After executing, verify before claiming completion.

This is not negotiable. This is not optional.

## How Superpowers Works on Kimi

Unlike Claude Code (which has a `Skill` tool), **Kimi loads skills automatically** when they are relevant to your task. You don't need to invoke skills manually - the system presents them to you when appropriate.

However, you MUST:
1. **Read and follow** any loaded skill completely before acting
2. **Use `SetTodoList`** to track tasks across the workflow
3. **Use `Agent` tool** with `subagent_type` for parallel/subagent work when skills instruct you to

## Instruction Priority

1. **User's explicit instructions** (AGENTS.md, direct requests) — highest priority
2. **Superpowers skills** (loaded automatically by Kimi) — override default behavior
3. **Default system prompt** — lowest priority

## The Superpowers Workflow

```
Brainstorm → Write Plan → Execute → Verify → Finish
```

### Phase 1: Brainstorming
**When:** User asks to build/create/implement anything.
**Skill:** `brainstorming` loads automatically.
**Goal:** Understand requirements, explore approaches, get user approval on design.
**Hard gate:** Do NOT write code before design is approved.

### Phase 2: Writing Plans
**When:** Design is approved.
**Skill:** `writing-plans` loads automatically.
**Goal:** Create bite-sized implementation plan.
**Save to:** `docs/plans/YYYY-MM-DD-<feature>.md`

### Phase 3: Execution
**When:** Plan exists and user says "go".
**Choose ONE:**
- **`subagent-driven-development`** — Use `Agent` tool (coder/explore/plan) per task, with review. Best for complex multi-task plans.
- **`executing-plans`** — Execute manually in current session. Best for simple/single-task plans.

### Phase 4: Verification
**When:** Before claiming work is complete.
**Skill:** `verification-before-completion` loads automatically.
**Rule:** Evidence before claims. Always.

### Phase 5: Finish
**When:** All tasks verified complete.
**Skill:** `finishing-a-development-branch` loads automatically.
**Goal:** Final review, present options, clean completion.

## Tool Adaptations from Claude Code to Kimi

| Claude Code | Kimi Equivalent |
|-------------|-----------------|
| `Skill` tool | Automatic loading - just read and follow loaded skills |
| `TodoWrite` | `SetTodoList` |
| `Bash` | `Shell` |
| `Read` | `ReadFile`, `Grep`, `Glob` |
| `Subagent` / dispatch | `Agent` tool with `subagent_type` (coder/explore/plan) |
| `Write` | `WriteFile`, `StrReplaceFile` |

## Critical Rules

- **Invoke/follow relevant skills BEFORE any response or action.** Even a 1% chance a skill might apply means you should read and follow it.
- **If a skill applies, you don't have a choice.** You MUST follow it.
- **User instructions always override skills.** If the user says "skip TDD," skip TDD.
- **Use `SetTodoList` to track progress.** Update it as you move through phases.
