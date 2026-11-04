## What it does

`implement` builds work that has already been decided. You point it at a [ticket](https://www.aihero.dev/ai-coding-dictionary/ticket), a [spec](https://www.aihero.dev/ai-coding-dictionary/spec), or the plan you just agreed in the conversation. It turns that into a numbered plan, waits for you to approve it, builds the independent steps in parallel, reviews what landed, and proposes fixes. The cycle repeats until you say you're done.

It never reopens the design. The plan it shows you is the settled work broken into steps and waves, not a new proposal, and your approval is about how the work is split, not what the work is. That is what separates it from typing "build this" at a fresh [agent](https://www.aihero.dev/ai-coding-dictionary/agent), which often redesigns the work while it builds it.

## When to reach for it

You invoke this by typing `/implement` yourself, and the agent won't reach for it on its own. It ships with `disable-model-invocation: true`, so no other skill can call it either. Wherever [ask-matt](https://aihero.dev/skills-ask-matt) or [to-tickets](https://aihero.dev/skills-to-tickets) says "then `/implement` per ticket", that is an instruction to you, not something the agent will do unprompted.

Where the work currently lives decides whether this is the right skill:

| The work is… | Reach for |
| --- | --- |
| A ticket on the tracker | `/implement #42`, one ticket per [session](https://www.aihero.dev/ai-coding-dictionary/session), [clearing](https://www.aihero.dev/ai-coding-dictionary/clearing) context between tickets |
| A spec, not yet split up, and the build spans sessions | [to-tickets](https://aihero.dev/skills-to-tickets) first, then `/implement` per ticket, or [implement-spec](https://aihero.dev/skills-implement-spec) for all of them in one run |
| A spec, and the build is small | `/implement` directly against the spec |
| Only in the conversation you just had, and it's still small | `/implement` right there, in the same window |
| Not written down anywhere yet | [grill-with-docs](https://aihero.dev/skills-grill-with-docs), or [grill-me](https://aihero.dev/skills-grill-me) if there's no codebase |
| One concrete behaviour you want test-first, with no spec | [tdd](https://aihero.dev/skills-tdd) directly |
| Already built, and you want it checked | [code-review](https://aihero.dev/skills-code-review) directly |

If the plan lives only in the thread, say so when you invoke it, so the [model](https://www.aihero.dev/ai-coding-dictionary/model) doesn't go looking for a spec file that doesn't exist.

## Prerequisites

`implement` commits to the branch you are on. It does not create one, and it does not ask. Check you are on the branch you want the work on before you start.

If the tickets came from [to-tickets](https://aihero.dev/skills-to-tickets), [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills) configured the tracker they live on. `code-review` reads the same configuration to find the originating spec.

## Rounds

A run is a loop of **rounds**, and only you end it:

1. **Plan.** The main agent writes the ticket as numbered steps in the todo list (`1.`, `1.1`), each top-level step marking what it is `blocked by`. It shows you the plan grouped into **waves** of steps that can run together, and builds nothing until you approve.
2. **Build.** Every unblocked step goes to its own implementer [subagent](https://www.aihero.dev/ai-coding-dictionary/subagent) in its own git worktree, all at once. As steps land, the ones they were blocking start.
3. **Merge.** A merger subagent brings each finished worktree into your current branch, one at a time. It fixes mechanical conflicts itself. A conflict where two steps changed the same behaviour stops the run and comes to you.
4. **Review.** A fresh reviewer subagent reviews only what this round added, and the findings come back to you as numbered proposed fixes.
5. **Decide.** Pick the fixes you want and they become the next round's plan, with its own review. Or say you're done.

Because the plan lives in the todo list, a plan pane such as the agent-monitor mod shows it as it moves, with each step's owner.

## Who does what

On Claude Code, the main agent only plans, dispatches, and relays. The heavy work runs in subagents, so merge output and build logs stay out of the main [context window](https://www.aihero.dev/ai-coding-dictionary/context-window):

| Role | Model | Effort | Calls |
| --- | --- | --- | --- |
| Implementer, one per unblocked step | Sonnet 5.5 | high | `ponytail`, or [tdd](https://aihero.dev/skills-tdd) when it isn't installed |
| Merger, one per finished implementer | Sonnet 5.5 | medium | git |
| Reviewer, one per round | Opus 5.5 | high | `ponytail-review`, or [code-review](https://aihero.dev/skills-code-review) when it isn't installed |

Without the Agent tool, the main agent runs the same rounds itself: it builds the steps one at a time with `tdd`, commits after each, and runs `code-review` on the round. The plan approval and the fix loop stay.

## Pre-agreed seams

The `tdd` path rests on the **seam**, the public boundary you observe behaviour at without reaching inside. Tests live at seams. When the seam is agreed before any code exists, the tests last, and you can rewrite the implementation underneath without changing them.

Nothing inside `implement` agrees the seams. `tdd` is the skill that asks, and it refuses to write a test at an unconfirmed seam. So the agreement happens either upstream in the spec, or at the plan approval. Naming the seams in the spec is what stops the run becoming "just write the code".

## Common questions

**It finished, but my ticket is still open and the acceptance criteria are still unchecked.**

Correct, and expected. `implement` has no completion step. It ends at the commits on your branch and never touches the work item, on any tracker. Close the ticket and reconcile the `- [ ]` boxes yourself. This matters most on a dependency chain, because `to-tickets` defines the frontier as tickets whose blockers are all closed. If nothing gets closed, nothing ever becomes visibly unblocked.

**Can I point it at all my tickets at once?**

Not with `/implement`: one invocation, one ticket, spec, or plan. It runs the steps *inside* that unit in parallel. For a whole spec of tickets in one run, use [implement-spec](https://aihero.dev/skills-implement-spec), which works the tickets as a task graph on one integration branch. Running several `/implement` sessions side by side in one checkout is worse than unsupported: one field report describes an amend landing on another session's commit, a vanished stash, and commits on the wrong branch, all in one afternoon. Each implementer inside a single run gets its own worktree for exactly this reason.

**Why does it stop and ask me to approve the plan?**

Parallel subagents can't be steered once they start, so the split has to be right before they do. The gate is where you catch a step that should be two, a missing `blocked by`, or a seam nobody agreed. A plain "go" in chat approves it.

**Can it open a pull request instead of committing?**

Not built in. It commits straight to the current branch, round by round. People override it in the invocation ("work on a new branch and open a PR at the end") or by editing their local copy of the skill. When the agent does write the PR, [pr](https://aihero.dev/skills-pr) shapes its body.

**Doesn't an agent reviewing its own code go easy on it?**

That bias is why the review runs in a fresh reviewer subagent that never saw the build, and only on the range the round added. Every round is merged and committed before the review, so the reviewer always has a real diff to read.

**One ticket burned a lot of tokens. Am I using it wrong?**

Probably not. The ticket is more likely too big. Each implementer explores, builds, and tests, and every round adds a review, so a non-trivial ticket running past 100k [tokens](https://www.aihero.dev/ai-coding-dictionary/token) across all agents is normal. The fix is upstream: right-size the tickets in [to-tickets](https://aihero.dev/skills-to-tickets). If a single ticket keeps going over, split it rather than raising the [effort](https://www.aihero.dev/ai-coding-dictionary/effort) level.

**`/implement #2` in a fresh session worked on something completely unrelated.**

The agent resolved `#2` against another numbered list in context, such as a todo file or checklist, rather than the configured tracker. `implement` now fetches a passed reference from the issue tracker and states its title before starting, and asks when the reference is ambiguous. Check that title matches the ticket you meant; passing the issue URL or `owner/repo#2` removes the ambiguity entirely.

## It's working if

- The session opens by reading the ticket or spec and showing you a numbered plan grouped into waves, rather than asking you what to build.
- No code is written and no subagent starts until you approve the plan.
- Independent steps start at the same time, each in its own worktree, and the plan pane shows who owns each step.
- The main conversation shows short merger reports, not raw merge output.
- After each round you get numbered proposed fixes, and nothing is fixed until you pick.
- The run ends when you say so, with every round's work committed on your current branch.

## Where it fits

`implement` is the build step of the main chain:

```txt
grill-with-docs → to-spec → to-tickets → implement → code-review → retro
```

Its neighbours are [to-tickets](https://aihero.dev/skills-to-tickets), which produces the tickets it consumes; [implement-spec](https://aihero.dev/skills-implement-spec), which runs a whole spec of tickets instead of one; and [code-review](https://aihero.dev/skills-code-review), which closes every round when `ponytail-review` isn't installed. It sits downstream of the planning skills and trusts them, so a horizontally-layered ticket gets built as written.

That trust is why [wayfinder](https://aihero.dev/skills-wayfinder) merges onto the chain at [to-spec](https://aihero.dev/skills-to-spec) rather than looping its map straight into `implement`. Go straight to `implement` from a map only when the effort turned out small.

[ask-matt](https://aihero.dev/skills-ask-matt) is the router over the whole set when you are not sure which flow you are in.
