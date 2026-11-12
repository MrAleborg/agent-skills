---
name: implement-spec-parallel
description: "Implement the result of /to-spec and /to-tickets in code."
disable-model-invocation: true
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency.

## Steps

1. Read the spec and tickets to understand the task graph.

2. (optional) Use an **exploration subagent** (`subagent_type: "mraleborg-skills:explorer"`) to conduct any exploration required by the tickets - relevant codebase files or external documentation. Give it a directory outside the repo, accessible by all future subagents, for its markdown notes. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use **implementer subagents** (`subagent_type: "mraleborg-skills:implementer"`) to implement each ticket, each in its own worktree on its own branch. Give each one the integration branch name and its ticket. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - calls the Skill tool with `tdd` to build the ticket (`ponytail` instead when that skill is installed);
   - merges the integration branch tip into its own branch before reporting done

5. Once an **implementer subagent** completes, merge its branch into the integration branch yourself, one at a time.
   - resolve mechanical conflicts (imports, neighbouring edits that don't overlap in meaning), then run the typecheck;
   - abort the merge when both sides change the same behaviour, leaving the integration branch clean, then relay the conflict to the user and wait for direction;
   - remove the worktree and its branch after a clean merge.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, call the Skill tool with `code-review` on the integration branch. Fix all issues raised by the code review in a single **implementer subagent**.

   On Claude Code, replace the `code-review` call with a **reviewer subagent** (`subagent_type: "mraleborg-skills:reviewer"`) on the integration branch, pointed at the spec. It uses `ponytail-review` when installed, otherwise `code-review`. The fix step is unchanged.

   Where a `mraleborg-skills:*` agent type is not in the available agent types, spawn `general-purpose` instead: Haiku 5.5, effort medium for the explorer, Sonnet 5.5, effort high for the implementers, Opus 5.5, effort high for the reviewer, with the same instructions.

8. If a draft PR exists, mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up all **implementer subagent** worktrees.
