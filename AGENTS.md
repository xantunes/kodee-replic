# Superpowers-Kimi Activation

This project uses the **Superpowers methodology** adapted for Kimi Code CLI.

## How It Works

Kimi loads skills automatically from `.kimi/skills/superpowers-kimi/` when they are relevant to your task. You don't need to invoke skills manually — the system presents them when appropriate.

## Workflow

```
Brainstorm → Write Plan → Execute → Verify → Finish
```

1. **Brainstorming** — Before any implementation, explore requirements and get design approval
2. **Writing Plans** — Create bite-sized implementation plans
3. **Execution** — Choose:
   - `subagent-driven-development` — Delegate tasks to subagents (complex plans)
   - `executing-plans` — Execute manually in current session (simple plans)
4. **Verification** — Evidence before claims, always
5. **Finish** — Final review, cleanup, present options

## Critical Rules

- **Follow loaded skills BEFORE any response or action.** Even a 1% chance a skill might apply means you should read and follow it.
- **User instructions always override skills.** If the user says "skip TDD," skip TDD.
- **Use `SetTodoList` to track progress.** Update it as you move through phases.
- **Use `Agent` tool with `subagent_type` for subagent work** when skills instruct you to.

## Tool Mapping (Claude Code → Kimi)

| Claude Code | Kimi |
|-------------|------|
| `Skill` tool | Automatic loading — read and follow loaded skills |
| `TodoWrite` | `SetTodoList` |
| `Bash` | `Shell` |
| `Read` | `ReadFile`, `Grep`, `Glob` |
| `Subagent` / dispatch | `Agent` tool with `subagent_type` |
| `Write` | `WriteFile`, `StrReplaceFile` |

## Available Skills

| Skill | When It Loads |
|-------|---------------|
| `superpowers-bootstrap` | At start of any dev conversation |
| `brainstorming` | Before creative/building work |
| `writing-plans` | When you have specs/requirements |
| `executing-plans` | When executing a written plan manually |
| `subagent-driven-development` | When executing plans with subagents |
| `test-driven-development` | Before writing implementation code |
| `verification-before-completion` | Before claiming work is done |
| `finishing-a-development-branch` | When all tasks are complete |

## Docs Location

- Specs: `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Plans: `docs/plans/YYYY-MM-DD-<feature>.md`
