---
description: Use when all planned tasks are complete and verified. Finalizes work with review, cleanup, and presentation of next steps.
---

# Finishing a Development Branch

## Overview

The final phase: review what was built, clean up, present options, and hand back to your human partner with clarity.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Final Verification

Run the full verification suite with `Shell` tool:
- Full test suite
- Linters
- Type checkers
- Any manual verification steps from the plan

Do NOT skip this. Use `verification-before-completion` methodology.

### Step 2: Review Changes

Use `Shell` tool to review what changed:
```bash
git diff --stat
git diff
git status
```

Read the diff with `ReadFile` if needed. Check for:
- Debug code left behind (print, console.log, debugger)
- TODO comments that should be resolved
- Files that shouldn't be committed (logs, temp files)
- Sensitive data (API keys, passwords)

### Step 3: Clean Up

Remove any temporary files, debug code, or accidental changes.
Use `Shell` tool:
```bash
git checkout -- .  # be careful — only for files that shouldn't change
git clean -fd       # remove untracked files
```

### Step 4: Final Commit

If everything is clean:
```bash
git add .
git commit -m "feat: [description]"
```

Or if you prefer to let the user commit:
> All changes are staged. Review with `git diff --cached` and commit when ready.

### Step 5: Present Summary

Provide a concise summary:

```markdown
## Summary

**What was built:** [one sentence]

**Key changes:**
- `file.py`: [what changed]
- `test_file.py`: [tests added]

**Verification:**
- Tests: X passed, 0 failed
- Linter: clean
- Type check: clean

**Next steps (pick one):**
1. **Commit and continue** — I can commit these changes and move to the next feature
2. **Review first** — You review the diff, then I commit
3. **PR workflow** — Create a branch, commit, and prepare for PR
4. **Done for now** — Work is complete, no further action needed

What would you like to do?
```

## What NOT To Do

- Don't present options without verification evidence
- Don't say "done" and then keep working
- Don't dump a giant diff without summary
- Don't forget to mention any known issues or limitations
- Don't commit without user consent unless explicitly authorized

## Completion Gate

Before presenting as complete:
- [ ] Full verification passed (with evidence)
- [ ] Changes reviewed for quality
- [ ] No debug code left
- [ ] Summary written
- [ ] Options presented clearly
- [ ] User chooses next step
