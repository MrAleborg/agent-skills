---
name: ats-cv
description: Build an ATS-compatible CV (HTML, PDF and DOCX) tailored to a job offer, using only facts from the user's master CV (in Google Drive or a local file). Extracts every keyword from the offer, maps each one to evidence in the master CV, asks about gaps instead of inventing, then renders and re-checks the CV against pdftotext and the open-resume parser until it parses cleanly. Use this whenever the user shares a job offer, job posting, LinkedIn/Welcome to the Jungle/Indeed link or job description and wants a CV, resume, "candidature", tailored or targeted CV, or asks to adapt/update their CV for a company or role, even if they don't say "ATS".
---

# ATS CV from the master CV

You turn a job offer into a CV that (1) contains every offer keyword the candidate can truthfully claim, (2) contains nothing the candidate cannot back up, and (3) is proven to parse in real ATS-style parsers. The three goals pull against each other, and this workflow exists to keep (2) winning: a recruiter who catches one invented claim discards the whole CV, and the candidate has to defend every line in interview.

## The one rule

**Every fact in the CV comes from the master CV or from an answer the user gave in this session.** Rewording, condensing, reordering and choosing what to omit are your job. Adding an employer, title, date, number, tool, skill, degree, responsibility or level of proficiency is not. When the offer wants something the master does not show, that is a *gap*: ask about it, and if the user cannot confirm it, leave it out.

Keep the master's hedges. "Rust (side projects)", "Terraform (as a student)", "Spark (online course)" and "Kubernetes (familiar, occasional use)" must keep their qualifier, or you have inflated the claim. The qualifier's punctuation may change ("Kubernetes, familiar" for "Kubernetes (familiar)"); its words may not. "Participated in" does not become "Led". "Contributed to" does not become "Designed".

## Profile

The candidate's personal settings live outside the skill, in `~/.config/ats-cv/profile.md` (the cover-letter skill reads the same file). Read it first. It holds:

```markdown
name: Jane Doe                      # as on the CV
file_prefix: Jane_Doe               # start of every output file name
master_en: drive:<file id>          # or a local path; the canonical fact base
master_fr: drive:<file id>          # optional, or a local path
drive_folder: Applications          # optional: where past applications live in Drive
past_letters: drive:<folder id>     # optional: past cover letters, for tone only
```

If the file is missing, ask the user for these values once, write the file, and carry on. Never copy its values into this skill's folder: it may be a public repository.

## Inputs

- **Job offer**: pasted text, a file, or a URL (fetch it). Note company, role title, language.
- **Master CV**: from the profile, `master_en` (the canonical fact base) or `master_fr`. For a `drive:<id>` entry, fetch it with the Drive `read_file_content` tool and write its `fileContent` to `master.md` in the work dir; for a path, copy the file. Copy the text exactly; whitespace differences do not matter, since the checker normalises them. It comes back with escaped markdown (`\#`, `\*\*`); leave that as is, because the checker normalises escapes on both sides. If an id fails, ask the user. If the user gives another master file in the session, use it instead.
- Pick the master in the offer's language. If the facts differ between the EN and FR files, the EN file wins; mention the discrepancy to the user.

Work in `~/cv-builds/<Company>_<Role>/` (create it) and save the offer text there as `offer.md`. Name outputs `<file_prefix>_CV_<Company>_<Role>_ATS.{html,pdf,docx}`.

## Workflow

### 1. Extract ALL keywords from the offer

Read the whole offer, including the boilerplate: requirements, "nice to have", responsibilities, the company blurb and benefits that mention a stack. ATS rank on literal term overlap, so be exhaustive and literal. Capture:

- the job title itself, plus any seniority term ("Senior", "Staff", "Lead")
- hard skills: languages, frameworks, libraries, tools, platforms, cloud services, protocols, standards
- methods and practices: Agile, Scrum, TDD, CI/CD, MBSE, code review, ...
- domain terms: automotive, embedded, fintech, LLM, MLOps, ...
- degrees, certifications, spoken languages, years of experience
- soft skills and responsibilities phrased as nouns: mentoring, stakeholder management, technical leadership

Record each one in its offer spelling, with `variants`: the acronym and its expansion, and the spellings an ATS might match ("CI/CD", "continuous integration"; "LLM", "Large Language Models"). One concept gets one entry. Variants are spellings of the *offer's* term. Do not add the master's different wording as a variant to make a match look direct: that hides an inferred match from the checker and from the user.

### 2. Map each keyword to evidence

Write `keywords.json`:

```json
[
  {"term": "Kafka", "variants": [], "status": "matched", "evidence": "Migrated batch jobs to a Kafka event pipeline"},
  {"term": "Kubernetes", "variants": ["K8s"], "status": "gap", "evidence": null},
  {"term": "Rust", "variants": [], "status": "confirmed", "evidence": "Rust: two years of side projects, no professional use"}
]
```

- `matched`: `evidence` is a verbatim quote from the master CV (copy it, do not paraphrase: the checker looks it up character for character, modulo case and whitespace).
- `gap`: the master has no evidence. A *related* skill is not evidence: Keras does not prove PyTorch production work, and Jenkins does not prove GitHub Actions. If the master states something equivalent under another name (offer "GitLab CI", master "GitLab CI/CD"), that is `matched`.
- `confirmed`: the user confirmed it in this session; `evidence` is a verbatim quote from `answers.md`.

### 3. Ask about gaps, once, in one batch

List the gaps to the user with a short reason each matters for this offer, and ask whether they have real experience with any of them, and in what form (job, project, course, level). Append the user's answers verbatim to `answers.md` in the work dir, then flip the confirmed ones to `confirmed` with a quote. Anything unconfirmed stays `gap` and stays out of the CV. If there are no gaps, skip this step.

If the user cannot answer now (they said so, or you run unattended), write the questions to `questions.md`, treat every answer as no, and keep `answers.md` free of gap terms. Then carry on: the CV is still useful, and the questions can be answered later for a second pass.

Also ask here about anything else you need and cannot find in the master: for example which of two contradictory dates is right, or whether the user wants a specific job omitted. Do not guess.

### 4. Write the CV HTML

Start from `assets/cv_template.html` and keep its CSS and structure: the checker reads the CV's expected fields from those class names (`h1`, `.contact`, `.emp`, `.edu`, `.row.role`, `.row.org`). Read the comment block at the top of the template; every rule there came from a real parse failure.

- **Contact line**: phone as the 10-digit national number (`0600000000`, reformatted from a master's `+33 6 00 00 00 00`; this is the same fact, and open-resume misses every other format), then email, city, LinkedIn and the candidate's personal website if the master gives one anywhere (it may sit inside a project or the links section, not the contact block).
- **Headline** (line under the name): the offer's job title if the master supports it, plus the degree. Do not claim a title the candidate never held as a past job title; the headline describes what they are applying as. A keyword placed only in the headline (the offer's job title, typically) has no evidence quote naming it: record it as `matched` with the closest master evidence, expect the checker's inferred-match WARN, and list it at delivery like any other inferred match.
- **Summary**: 3 to 5 sentences, densest in top keywords, every claim traceable to the master.
- **Skills**: grouped lines; list every `matched`/`confirmed` keyword here in the offer's spelling, with qualifiers kept.
- **Experience**: all jobs from the master, reverse chronological, dates exactly as in the master. Choose and reword bullets so the keywords appear *in context*: a keyword that is only in the skills list is weaker for both ATS ranking and the human reader. Drop bullets that serve nothing for this offer, but never drop a job (it would leave a gap in the timeline) unless the user asks.
- **Projects**: the master groups work into named projects. Any project that uses one of the offer's keywords keeps its own `Project:` heading and at least one bullet naming that keyword, however old it is: the reader is looking for *every* place the candidate used that tool, and folding an old project into its job's summary makes the experience look smaller than it is. Projects with no offer keyword may be shortened to one line or dropped, to stay within 2 pages. Personal or side projects outside any job get their own `<h2>` section marked up as in the template (`.proj`, never `.emp`, which the checker counts as a job).
- **Education, certifications, languages**: from the master. Publications and associative work only if relevant to the offer.
- Length: 2 pages at most.
- French offer: `<html lang="fr">`, French headings (Profil, Compétences, Expérience professionnelle, Formation, Certifications, Langues) and the French master.

### 5. Render, check, refine (loop)

```bash
S=<this skill's folder>/scripts
$S/render.sh CV.html          # writes CV.pdf (headless Chromium) and CV.docx (LibreOffice)
python3 $S/ats_check.py CV.html --master master.md --keywords keywords.json --offer offer.md [--answers answers.md] [--lang fr]
```

The first `ats_check.py` run builds the open-resume parser into `~/.cache/ats-cv` (about 10 s, needs network once).

The checker runs two independent parsers on the PDF. **pdftotext** reads the plain text layer, as most ATS do. **open-resume** is the parser behind open-resume.com's resume checker: it detects sections and fields the way a layout-aware ATS does. The DOCX is checked as text too. It FAILs on: contact fields or headings not recovered, jobs mis-parsed, a keyword lost to glued or split text, an evidence quote that does not exist in the master, a `gap` keyword that slipped into the CV, and any number in the CV that appears nowhere in the master or answers. Three WARNs are about truthfulness, and each one needs a decision from you:
- *inferred match*: a `matched` keyword whose evidence quote does not name it (offer "continuous integration", master "CI/CD pipelines"). Keep it only if it really is the same thing, and list it for the user at delivery. Translations count too (FR "revues de code" for EN "code review").
- *offer words not in master/answers*: an offer word reached the CV without a fact behind it. Generic verbs are fine; a tool, skill or domain term is a gap that leaked in, so remove it. If the word belongs to a `matched` keyword (removing it would FAIL "keyword missing from CV"), the match is really inferred: keep the offer term only if it truly names the master's fact, and list it at delivery.
- *terms not found*: tech-like tokens (inner capitals, digits, `+`/`#`) with no source. Each must be a rewording or go.

The last lines of the output are the `coverage:` line and the PASS verdict; read them even if you filter the rest.

While it FAILs, fix and re-run. Fix by changing **layout and wording only**, never facts. Typical fixes are in the template comment (spans around words, phone format, exotic dashes, a job starting at the top of page 2). If a fix would need a fact change (a date the parser chokes on, say), ask the user. Stop after 5 rounds; if it still fails, report what fails and why rather than looping.

French CVs: open-resume is English-only. It finds French headings but parses no jobs under them, so `--lang fr` reduces it to name, email and phone (the job count becomes a WARN). The "page N starts with job" check runs on the text layer, so the page-break merge is still caught in French. pdftotext and DOCX checks, which carry the fields, keywords and fact checks, apply in full.

### 6. Deliver

Report, briefly:

- the result of the last check run (PASS, or the remaining FAILs)
- keyword coverage: `placed / total offer keywords`, then the list of gaps left out, so the user sees what the offer wants that the CV does not claim
- every inferred match you kept, as "offer term ← master wording", so the user can veto a stretch
- the master projects you shortened or dropped, so the user can ask for one back
- the paths of the HTML, PDF and DOCX

Then offer to upload the three files to the user's Drive (ask which folder; the profile's `drive_folder` is where past applications sit). Do not upload without a yes. Also offer the matching cover letter; on a yes, call the Skill tool with "cover-letter", which reuses this work folder.
