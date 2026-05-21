# Superpowers Bootstrap

## When to Use
At the start of any development conversation or task.

## Purpose
Initialize the Superpowers-Kimi workflow and ensure all subsequent skills are followed in the correct order.

## Instructions

1. **Check for AGENTS.md** in the current and parent directories. Read and follow all instructions found there.
2. **Identify the task type:**
   - Creative/building work → Load `brainstorming`
   - Plan execution → Load `executing-plans` or `subagent-driven-development`
   - Writing specs → Load `writing-plans`
   - Before coding → Load `test-driven-development`
   - Wrapping up → Load `verification-before-completion` then `finishing-a-development-branch`
3. **Initialize tracking:** Use `SetTodoList` to track progress through the workflow phases.
4. **User overrides:** If the user explicitly contradicts any skill instruction, follow the user's instruction.

## Critical Rules
- Always follow loaded skills BEFORE any response or action.
- Even a 1% chance a skill might apply means you should read and follow it.
- User instructions always override skills.
