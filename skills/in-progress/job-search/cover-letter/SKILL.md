---
name: cover-letter
description: Write the user's cover letter ("lettre de motivation", LM, motivation letter) for a specific job offer, in French or English, as a one-page HTML and PDF in a clean house letter style, using only facts from the user's master CV and their own answers. Complements ats-cv, reusing its work folder (offer, master, keywords, answers) when a tailored CV already exists. Use this skill, rather than a generic document or docx skill, whenever the user wants a cover letter, lettre de motivation or LM for a job offer, posting or company, or asks to finish an application ("candidature") with a letter after the CV, even if they only paste the offer and say "the letter now".
---

# Cover letter from the master CV

A cover letter does what the CV cannot: it picks the two or three things in this offer that matter most, and shows with named, checkable work why the candidate fits them. It is read by a human, often after the CV, so a single invented or inflated claim costs the whole application, and the candidate has to defend every sentence in interview.

## The one rule

**Every claim about the candidate comes from the master CV, from `answers.md` (career facts the user confirmed for ats-cv) or from `letter_answers.md` (what the user told you for this letter).** Rewording, choosing and ordering are your job. Adding an employer, project, tool, number, outcome, level, motivation, mobility or availability is not.

- Keep the master's hedges: "Rust (side projects)", "Terraform (as a student)", "Kubernetes (familiar, occasional use)". A letter tempts you to smooth them away; don't.
- Keep the master's verbs: "participated in" does not become "led", "contributed to" does not become "designed".
- Facts about the company come only from the offer text. Do not add what you "know" about the company: it may be wrong or outdated, and the reader will know.
- Claiming an offer requirement the candidate lacks is never allowed. Mentioning one is optional, and how is covered in step 4.

The user's past letters (the profile's `past_letters`, if set) show the tone, but some of their claims may have come from conversations, not the master (a willingness to relocate, a company the candidate never worked for). Do not copy a sentence from a past letter unless the master or the answers back it.

## Profile

Read `~/.config/ats-cv/profile.md`, the file the ats-cv skill uses: `name`, `file_prefix`, `master_en`, `master_fr`, `drive_folder`, `past_letters`. If it is missing, ask the user for these values once and write it there, never into this skill's folder (it may be a public repository).

## Inputs and work folder

Work in `~/cv-builds/<Company>_<Role>/`, the same folder ats-cv uses. Look there first:

- `offer.md`: the offer text. If missing, save the pasted text, the file, or the fetched URL there.
- `master.md`: the master CV. If missing, fetch it as ats-cv does: the profile's `master_en` for English or `master_fr` for French; for a `drive:<id>` entry, Google Drive `read_file_content` on that id, writing its `fileContent` there unchanged; for a path, copy the file. If the EN and FR files disagree on a fact, the EN file wins; tell the user.
- `keywords.json` and `answers.md`: from ats-cv, if it ran. Reuse them: the keyword map already says which offer terms are backed (`matched`, `confirmed`) and which are `gap`. If they are absent, do not run the full ats-cv workflow: list the offer's 5 to 8 main requirements yourself and find, for each, the master line that backs it (or none).

The letter is in the offer's language (one letter). Write the other language only if the user asks.

Name the outputs like the user's past letters:
- English: `<file_prefix>_CoverLetter_<Company>_<Role>_EN.{html,pdf}`
- French: `<file_prefix>_Lettre_<Company>_<Role>_FR.{html,pdf}`

## Workflow

### 1. Read the offer for what it really asks

Find the 2 or 3 requirement blocks that carry the role (for example: "Java tooling", "technical leadership", "quality in a regulated domain"), plus the hook: one specific thing in this offer (a responsibility, the product, the team's approach) that connects to the candidate's actual work. A specific hook is what separates a letter written for this offer from a generic one.

Note the addressee (company, team, site, a named recruiter if given), the exact job title and any reference number: they go in the header and subject line.

### 2. Pick the evidence

For each requirement block, choose **one** master story, two at most: a named employer and project, what the candidate did (master's verb), the tools, and the outcome if the master states one. Prefer the story with the strongest outcome that also contains the offer's keywords. Leave the other projects to the CV: the letter is not the CV in sentences, and a paragraph that lists four projects reads as an enumeration, which the user dislikes. Write down, for yourself, which master line backs each sentence you plan to write.

### 3. Ask the user, once, in one batch

The master does not hold what a letter needs about the person. Ask, in one message:
- why this company or role, if they have a reason of their own (beyond what the offer says)
- location and mobility for this job: on site, relocation, remote
- availability or start date, if the offer asks
- anything the offer requires that the master lacks and `answers.md` does not settle (the gaps)

Append the answers verbatim to `letter_answers.md`. Keep career facts the user confirms in `answers.md` too (ats-cv reads that file as facts), but keep motivation and mobility in `letter_answers.md` only, so they never leak into a CV.

If the user cannot answer now (they said so, or you run unattended), write the questions to `questions.md` in the work folder, treat every answer as no, and write the letter without any personal claim: no relocation, no availability date, no personal motivation beyond what follows from the offer and the master. It still works as a letter, and the answers can be added in a second pass.

### 4. Write the letter

Start from `assets/letter_template.html` and keep its CSS and class names; read its top comment. Fill in:

- **Header**: name; `.role` line with the offer's job title (what the candidate applies as); contact block from the master (city, phone as written in the master, email, LinkedIn).
- **Addressee and date**: `.to` with the company and team or site from the offer; `.place` with the master's city and today's date (run `date`, do not guess it). French: "Lyon, le 11 novembre 2026".
- **Subject**: "Subject: application for the <exact title> position (ref. <ref>)" / "Objet : candidature au poste de <intitulé exact> (réf. <réf>)". Leave out the reference if the offer has none.
- **Salutation**: a named person if the offer gives one; otherwise "Dear Hiring Team," or "Madame, Monsieur,".
- **Body, 3 to 5 paragraphs, 250 to 450 words**:
  1. The hook: open on what *they* are looking for, in their own terms, then answer at once with the candidate's matching fact. "You are looking for an engineer who can ...", "Vous recherchez ...", or "Your search for a Tech Lead within the payments team caught my attention, particularly because the test strategy appears there as a responsibility of the role ...". Avoid administrative openings that recite the offer ("Your offer asks for X, Y and Z", "Votre offre demande ...") and flattery ("your offer describes almost word for word what I love", "votre entreprise prestigieuse"): the user called that "lèche-bottes". Say why this role and the candidate's work meet; do not praise.
  2. and 3. One paragraph per requirement block, each built on its one story from step 2: the context, what the candidate did, the outcome, then one sentence connecting it to what the offer needs. Use the offer's vocabulary. Show the role played (specifications, architecture, review, mentoring) when the offer asks for seniority.
  4. Optional: how the candidate's way of working fits the domain or team described in the offer.
  5. The close: location or availability from `letter_answers.md` if the user gave them, then the request for an interview. End on what the candidate brings, never on what they lack.
- **Gaps** (offer requirements the master lacks): you may leave them out; the CV and the interview will show them. If one is central to the role, mention it once, briefly, inside a body paragraph, as the next step from what the candidate already does: "running these services on Kubernetes in production is a natural next step from my Docker work, and one I would like to take". It must read as a direction, not as experience: no "I have worked with", no hint of use. Never list several gaps in a row ("I have not used X, Y or Z"): the user found such a paragraph "a killer".
- **Closing formula**: EN "Thank you for your time and consideration." FR "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées." (match the salutation if a person is named).

Style: plain declarative sentences, first person, concrete nouns, no superlatives. Every claim of fit carries a fact. Avoid stock phrases ("passionate", "dynamic", "perfect fit", "passionné", "motivé"): the checker flags them. Write numbers as the master writes them; if you spell one out ("dix ans"), it still has to be in the master.

### 5. Render and check

```bash
L=<this skill's folder>/scripts; S=$L/../../ats-cv/scripts   # the ats-cv skill, installed beside this one
NO_DOCX=1 $S/render.sh LETTER.html
python3 $L/letter_check.py LETTER.html --master master.md --offer offer.md \
  [--answers answers.md] [--letter-answers letter_answers.md] [--keywords keywords.json]
```

It FAILs on: more than one page, header or paragraph text lost in the PDF text layer, the master's email or phone missing, fewer than 4 paragraphs, and any number (digits or number words, EN or FR) in the body that is not in the master or answers. Offer numbers (reference, dates) are allowed in the header only, so "5 years of experience" copied from the requirements FAILs in the body.

The WARNs need a decision from you:
- *gap keyword in the letter*: fine when restating the offer, or once as a direction the candidate wants to grow in (step 4, Gaps); never as a claim, never in a list of what the candidate lacks.
- *term not in the master/answers*: a proper noun or tech term with no fact behind it. From the offer, it may describe the company ("your Kotlin stack"); otherwise it is an invented claim, so remove it.
- *personal claim not in letter_answers.md*: relocation, remote, availability, salary. Remove unless the user said it.
- *cliché* and *word count*: rewrite.

Fix and re-run until it passes. If the letter is over one page, cut words; do not shrink the font or margins. Stop after 5 rounds and report what still fails.

### 6. Deliver

Report briefly:
- the check result (PASS or the remaining FAILs) and the WARNs you kept, with why
- the 2 or 3 requirement blocks you answered and the master stories you used for each
- the offer requirements you did not claim (gaps), and the questions left in `questions.md` if any
- the paths of the HTML and PDF

Then offer to upload both files to the user's Drive (ask which folder; the profile's `drive_folder` is where past applications sit). Do not upload without a yes. If there is no tailored CV for this offer yet, offer one; on a yes, call the Skill tool with "ats-cv".
