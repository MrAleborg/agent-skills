---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Before writing any code or spawning any subagent, write the plan in this context: the ticket broken into numbered steps (`1.`, `1.1`, ...) with TodoWrite or TaskCreate. Keep each step's status current as the work moves.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, call the Skill tool with "code-review" to review the work.

Commit your work to the current branch.

## On Claude Code

If the Agent tool is available and the `ponytail` and `ponytail-review` skills are installed, split the work across two subagents instead of building and reviewing in this context. Otherwise follow the steps above.

1. Write the plan first, as above. Then spawn an **implementer subagent** (model Sonnet 5.5, effort high) and tell it to call the Skill tool with "ponytail" to build the work, then commit to the current branch. Give it context pointers (the ticket, spec, or agreed plan), not copies, and name each plan step it owns in its prompt, one by one (`Step 1`, `Step 2`). Skip the `tdd` and `code-review` steps above: the implementer owns the build, and the reviewer owns the review.
2. The subagent reports back the context you need and its implementation result: what it built, the commits, and anything it skipped or is unsure about. Keep that report in this context.
3. Once it reports done, spawn a **reviewer subagent** (model Opus 5.5, effort high) and tell it to call the Skill tool with "ponytail-review" on the commits the implementer made, pointing it at the same ticket or spec.
4. Relay the reviewer's findings to the user. Don't fix them unprompted.
