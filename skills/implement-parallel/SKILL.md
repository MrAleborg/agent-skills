---
name: implement-parallel
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec, the tickets, or the plan agreed in this conversation. The work runs in **rounds**: plan, build, merge, review, and then the user decides what comes next. The cycle ends only when the user says they are done.

## 1. Plan

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Before writing any code or spawning any subagent, write or refine the plan in this context as numbered steps (`1.`, `1.1`, ...) with TodoWrite or TaskCreate, so it also shows in any plan pane the harness offers. Break every top-level step into subtasks (`1.1`, `1.2`, ...) and write each subtask as its own entry, so the work inside a step shows too. Each top-level step is one unit of parallel work, and its subtasks stay with it. Whenever the plan is updated, write the subtasks of every new or changed step the same way. Mark a dependency in the step's title as `blocked by <n>`. Keep each step's status current as the work moves.

Show the plan to the user in chat, grouped into **waves**: the steps that can run together first, then each wave that waits on an earlier one. Fold the user's edits into the plan and show it again. This step is done when the user approves the plan; a plain "go" in chat counts as approval.

## 2. Build the round

Note the current branch name and its HEAD SHA: the SHA is this round's starting point.

The **frontier** is every pending top-level step whose blockers are complete. Spawn one **implementer subagent** per frontier step, all in the same response with no cap on their number, each with `subagent_type: "mraleborg-skills:implementer"` and `isolation: "worktree"`. Give it context pointers (the ticket, spec, or agreed plan), not copies, the current branch name, and each step it owns (`Step 2`, `Step 2.1`). The agent already knows to reset onto that branch, build with `ponytail` or `tdd`, typecheck and test, commit in its worktree, and report.

If `mraleborg-skills:implementer` is not in the available agent types, spawn `general-purpose` with model Sonnet 5.5 and effort high, and tell it to do those same things.

When an implementer reports, merge its branch into the current branch yourself, one implementer at a time:

- resolve mechanical conflicts (imports, neighbouring edits that don't overlap in meaning), then run the typecheck;
- abort the merge when both sides change the same behaviour, leaving the current branch clean, then relay the conflict to the user and wait for direction;
- remove the worktree and its branch after a clean merge.

After each clean merge, recompute the frontier and spawn implementers for the newly unblocked steps.

This step is done when every step in the plan is merged. Then run the full test suite once.

## 3. Review the round

Spawn a **reviewer subagent** with `subagent_type: "mraleborg-skills:reviewer"` on `<round start SHA>..HEAD`, pointed at the same ticket or spec. If that agent type is not available, spawn `general-purpose` with model Opus 5.5 and effort high, and tell it to call the Skill tool with "ponytail-review" if that skill is installed, otherwise "code-review", on that range, and fix nothing.

Relay the reviewer's findings to the user as numbered proposed fixes. Fix nothing unprompted.

## 4. Next round or done

- The user picks fixes: add each as a new plan step with its subtasks. The pick is the approval, so go straight back to step 2 for a new round, and its own review.
- The user says they are done: report the commits now on the current branch and stop.

## Without the Agent tool

Run the same rounds in this context. Build the frontier steps yourself one at a time, calling the Skill tool with "tdd" at pre-agreed seams, running typechecking and single test files regularly, and committing to the current branch after each step. In step 3, call the Skill tool with "code-review" on the round's range yourself. The plan approval and the review loop stay the same.
