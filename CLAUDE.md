Every skill lives in `skills/<name>/`, with the folder name matching the `name:` in its `SKILL.md`.

Every skill must have an entry in the `README.md` (with its name linked to its `SKILL.md`, under **User-invoked** or **Model-invoked**) and in `.claude-plugin/plugin.json`'s `skills` array. Run `claude plugin validate . --strict` after touching either manifest.

A user-invoked skill has `disable-model-invocation: true` in its `SKILL.md` plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.

Don't give a skill the same name as one of Matt Pocock's skills: both plugins get installed side by side.

Re-run `scripts/link-skills.sh` after adding, removing, or renaming a skill.

No em-dashes anywhere in this repo's prose. Where a sentence reaches for one, rewrite it with a comma, colon, period, parentheses, or a conjunction.
