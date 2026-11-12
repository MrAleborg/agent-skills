# agent-skills

My own agent skills. They are meant to sit next to [Matt Pocock's skills](https://github.com/mattpocock/skills), which some of them call (`tdd`, `code-review`, `setup-matt-pocock-skills`).

## Skills

### User-invoked

- [implement-parallel](./skills/implement-parallel/SKILL.md): my take on Matt's `implement`. Plan first, approve with "go", parallel implementer rounds, the main agent merges, then a review loop.
- [implement-spec-parallel](./skills/implement-spec-parallel/SKILL.md): my take on Matt's `implement-spec`. The main agent merges the ticket branches itself, following explicit merge rules.

Both spawn this plugin's subagents from [`agents/`](./agents): `implementer` (Sonnet, writes code in a worktree), `reviewer` (Opus, read-only) and `explorer` (Sonnet, writes notes outside the repo). Without the plugin installed, they fall back to `general-purpose` subagents.

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

### Dependencies

`implement-parallel` and `implement-spec-parallel` call skills from two other plugins. Install both next to this one.

[Matt Pocock's skills](https://github.com/mattpocock/skills) provide `tdd`, `code-review` and `setup-matt-pocock-skills`:

```sh
claude plugin install mattpocock-skills@claude-plugins-official
```

Then run `/setup-matt-pocock-skills` once in each repo where you use these skills, so they know your issue tracker.

[Ponytail](https://github.com/DietrichGebert/ponytail) is optional. When it is installed, the implement skills use `ponytail` to build and `ponytail-review` to review, instead of `tdd` and `code-review`:

```sh
claude plugin marketplace add DietrichGebert/ponytail
claude plugin install ponytail@ponytail
```

Local dev (symlinks every skill into `~/.claude/skills` and `~/.agents/skills`):

```sh
scripts/link-skills.sh
```

## History

These skills were first written in my fork of `mattpocock/skills`. That history is kept on this repo's [`alex-archive`](https://github.com/MrAleborg/agent-skills/tree/alex-archive) branch.
