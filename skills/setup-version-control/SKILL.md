---
name: setup-version-control
description: "Make every agent in this repo use the version-control skill for git work, through CLAUDE.md and AGENTS.md."
disable-model-invocation: true
---

Write a **version-control rule** into this repo's agent instruction files, so every agent working here, subagents included, loads the `version-control` skill before any git work.

## 1. Find the instruction files

At the repo root, look for `CLAUDE.md` and `AGENTS.md`. The rule goes in one place, the file every harness ends up reading:

- Both exist and `CLAUDE.md` imports `AGENTS.md` (an `@AGENTS.md` line): the rule goes in `AGENTS.md`.
- Both exist and stand alone: the rule goes in both.
- Only one exists: the rule goes in it. If it is `AGENTS.md`, add an `@AGENTS.md` line to a new `CLAUDE.md` only if the user confirms they use Claude Code.
- Neither exists: create `AGENTS.md` with the rule and a `CLAUDE.md` holding just `@AGENTS.md`.

This step is done when you can name every file you will edit or create.

## 2. Write the rule

In each target file, search for an existing version-control or git section. If there is one, put the rule's paragraph at its top and keep the repo-specific conventions it already holds (branch names, commit format, protected branches), so the skill and the house rules both apply. Otherwise append this section:

```markdown
## Version control

Load the `version-control` skill before any git work: committing, branching, pushing, rebasing, merging, opening a PR, stashing, or fixing history. Follow it for the whole operation. When you hand git work to a subagent, tell it to load `version-control` too.
```

Keep the rest of each file untouched. If the file has its own house style for headings, match it.

## 3. Report

Show the user the diff of every file you changed. Point out any existing git guidance that contradicts the `version-control` skill, so they can decide which wins. Leave the changes uncommitted.
