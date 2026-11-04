---
"mattpocock-skills": minor
---

`implement` now runs in rounds that only the user ends. It writes the plan in the todo list and waits for approval. It builds every unblocked top-level step in a parallel implementer subagent, each in its own worktree. Merger subagents bring the worktrees back one at a time, and a reviewer subagent reviews each round's range. The main agent proposes fixes, and each round of picked fixes gets its own review.
