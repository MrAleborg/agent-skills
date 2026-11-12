# agent-skills

My own agent skills. They are meant to sit next to [Matt Pocock's skills](https://github.com/mattpocock/skills), which some of them call (`tdd`, `code-review`, `setup-matt-pocock-skills`).

## Skills

### User-invoked

- [implement-parallel](./skills/implement-parallel/SKILL.md): my take on Matt's `implement`. Plan first, approve with "go", parallel implementer rounds, the main agent merges, then a review loop.
- [implement-spec-parallel](./skills/implement-spec-parallel/SKILL.md): my take on Matt's `implement-spec`. The main agent merges the ticket branches itself, following explicit merge rules.

### Model-invoked

- [version-control](./skills/version-control/SKILL.md): git workflow and hygiene, from commits and branches to PRs and recovering from mistakes.
- [ats-cv](./skills/ats-cv/SKILL.md) (beta): an ATS-friendly CV tailored to a job offer, built only from facts in the master CV.
- [cover-letter](./skills/cover-letter/SKILL.md) (beta): a one-page cover letter for a job offer, reusing the `ats-cv` work folder.

## Install

Claude Code:

```sh
claude plugin marketplace add MrAleborg/agent-skills
claude plugin install mraleborg-skills@mraleborg
```

Local dev (symlinks every skill into `~/.claude/skills` and `~/.agents/skills`):

```sh
scripts/link-skills.sh
```

## History

These skills were first written in my fork of `mattpocock/skills`. That history is kept on this repo's [`alex-archive`](https://github.com/MrAleborg/agent-skills/tree/alex-archive) branch.
