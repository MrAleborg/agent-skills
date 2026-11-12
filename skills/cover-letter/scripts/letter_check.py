#!/usr/bin/env python3
"""Check a cover letter built from assets/letter_template.html.

Usage:
  letter_check.py LETTER.html --master MASTER.md --offer OFFER.md
                  [--answers ANSWERS.md] [--letter-answers LETTER_ANSWERS.md] [--keywords KEYWORDS.json]

Reads LETTER.pdf next to the HTML (render it first). Exit 0 when there is no FAIL.
FAIL: not one page, text lost in the PDF, a number with no source.
WARN (judgement): gap keywords, tech-like terms not in the facts, clichés, length.
"""
import argparse, datetime, json, os, re, subprocess, sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "ats-cv", "scripts"))  # sibling ats-cv skill
from ats_check import norm, has_term, digits  # shared normalisation, so both skills agree on matching

WORDS = {w: n for n, ws in {
    2: "two deux", 3: "three trois", 4: "four quatre", 5: "five cinq", 6: "six", 7: "seven sept",
    8: "eight huit", 9: "nine neuf", 10: "ten dix", 11: "eleven onze", 12: "twelve douze dozen douzaine",
    13: "thirteen treize", 14: "fourteen quatorze", 15: "fifteen quinze", 16: "sixteen seize",
    17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty vingt vingtaine", 30: "thirty trente trentaine",
    40: "forty quarante", 50: "fifty cinquante", 100: "hundred cent centaine"}.items() for w in ws.split()}
# shortcut: "one/un/une" are skipped (articles) and compounds ("vingt-cinq") are read word by word.
NUM_RX = r"(?<![\w.])\d+(?:[.,]\d+)?%?"
SALUTATION = {"Madame", "Monsieur", "Mesdames", "Messieurs", "Dear", "Hiring", "Team", "Sir", "Madam"}
HEADER = {"role", "contact", "to", "org", "place", "subject"}
CLICHES = ["passionate", "passionné", "passionnée", "highly motivated", "team player", "perfect fit", "dynamique",
           "motivé", "motivée", "je suis convaincu", "i am confident that i", "self-starter", "go-getter", "rigoureux et"]


class Letter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.body, self.header, self.cur = [], [], [], None

    def handle_starttag(self, tag, attrs):
        if self.cur is not None and tag in ("br", "div", "p"):
            self.cur.append("\n")  # block boundary: "Example Corp<br>Lyon" is two lines
        if tag in ("br", "meta"):
            return
        cls = set((dict(attrs).get("class") or "").split())
        self.stack.append(tag)
        if self.cur is None and tag == "p":
            self.cur, self.kind, self.depth = [], "body", len(self.stack)
        elif self.cur is None and cls & HEADER:
            self.cur, self.kind, self.depth = [], "header", len(self.stack)

    def handle_endtag(self, tag):
        if self.cur is not None and tag in ("div", "p"):
            self.cur.append("\n")
        if self.cur is not None and len(self.stack) == self.depth:
            (self.body if self.kind == "body" else self.header).append(re.sub(r"[ \t\r]+", " ", "".join(self.cur)).strip())
            self.cur = None
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.cur is not None and "style" not in self.stack and "title" not in self.stack:
            self.cur.append(data)


def numbers(text):
    """Digit numbers and spelled-out number words in text, as digit strings."""
    found = {digits(n) or n for n in re.findall(NUM_RX, text)}
    found |= {str(WORDS[w]) for w in re.findall(r"[a-zà-ÿ]+", norm(text)) if w in WORDS}
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--master", required=True)
    ap.add_argument("--offer", required=True)
    ap.add_argument("--answers", help="answers.md from ats-cv (career facts the user confirmed)")
    ap.add_argument("--letter-answers", help="letter_answers.md (motivation, mobility, availability)")
    ap.add_argument("--keywords", help="keywords.json; its gap terms are flagged if they reach the letter")
    a = ap.parse_args()
    read = lambda p: open(p, encoding="utf8").read() if p else ""
    master, offer = read(a.master), read(a.offer)
    facts = master + "\n" + read(a.answers) + "\n" + read(a.letter_answers)
    facts_n = norm(facts)
    fails, warns, oks = [], [], []

    lt = Letter()
    lt.feed(read(a.html))
    body = [re.sub(r"\s+", " ", p) for p in lt.body if p]
    pdf = os.path.splitext(a.html)[0] + ".pdf"
    if not os.path.exists(pdf):
        print(f"FAIL: {pdf} missing, run render.sh first"); sys.exit(1)

    # --- 1. one page, nothing lost in the text layer ---
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    (oks if pages == 1 else fails).append(f"{pages} page(s); a cover letter must fit on one" if pages != 1 else "one page")
    pt_n = norm(subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout)
    # pdftotext may interleave the two header columns line by line, so header text is compared per line.
    for chunk in [l for h in lt.header for l in h.split("\n")] + body:
        # pdftotext drops a hyphen at a line break ("Software-in-the-\nLoop" -> "theLoop"): compare without hyphens.
        if chunk.strip() and norm(chunk).replace("-", "") not in pt_n.replace("-", ""):
            fails.append(f"text missing or garbled in the PDF text layer: {chunk[:70]!r}")
    for what, rx in [("email", r"[\w.+-]+@[\w-]+\.[\w.]+"), ("phone", r"\+?\d[\d .]{8,}\d")]:
        m = re.search(rx, master)
        if m and (digits(m.group()) not in digits(pt_n) if what == "phone" else m.group().lower() not in pt_n):
            fails.append(f"{what} from the master CV ({m.group()}) not in the letter")
    if len(body) < 4:
        fails.append(f"only {len(body)} paragraphs: expected salutation, 2 to 4 body paragraphs and a closing formula")

    # --- 2. numbers: body numbers need a fact; offer numbers and dates belong in the header only ---
    fact_nums = numbers(facts)
    header_ok = fact_nums | numbers(offer)
    for n in sorted(numbers(" ".join(body)) - fact_nums):
        hint = " (it is in the offer: a requirement is not the candidate's fact)" if n in numbers(offer) else ""
        fails.append(f"number {n!r} in the letter body is in neither the master CV nor the answers{hint}")
    today = datetime.date.today()
    header_ok |= {str(today.day), str(today.year), f"{today.day:02d}", f"{today.month:02d}"}
    for n in sorted(numbers(" ".join(lt.header)) - header_ok):
        fails.append(f"number {n!r} in the header comes from neither the offer, the facts nor today's date")

    # --- 3. truth heuristics: need a decision, not a mechanical fix ---
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(body))
    def where(term):
        return next((s for s in sentences if has_term(norm(s), term)), "")[:140]
    if a.keywords:
        for k in json.load(open(a.keywords, encoding="utf8")):
            if k.get("status") == "gap":
                hit = next((t for t in [k["term"]] + k.get("variants", []) if has_term(norm(" ".join(body)), t)), None)
                if hit:
                    warns.append(f"gap keyword {hit!r} is in the letter; fine only if restating the offer or naming the gap honestly: {where(hit)!r}")
    tokens = set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*(?:[+#.][A-Za-z0-9+#]*)*\b", " ".join(body)))
    # Proper nouns mid-sentence (Kubernetes, Snowflake) and tech-like tokens (K8s, C++) need a source.
    starts = {m.group(1) for m in re.finditer(r"(?:^|[.!?:]\s+)([A-Za-zÀ-ÿ]+)", ". ".join(body))}
    proper = set(re.findall(r"\b[A-ZÀ-Ý][a-zà-ÿ]+\b", " ".join(body))) - starts - SALUTATION
    odd = sorted(t for t in tokens | proper
                 if (t in proper or re.search(r"[A-Z]|\d|[+#]", t[1:])) and not has_term(facts_n, t) and not (t.endswith("s") and has_term(facts_n, t[:-1])))  # DSLs -> DSL
    warned = {w.split("'")[1].lower() for w in warns}
    org_n = norm(" ".join(lt.header))
    odd = [t for t in odd if t.lower() not in warned and not any(t.lower() in w.lower().split() for w in warned)
           and not has_term(org_n, t)]  # the company/team name restated from the header is not a claim
    for t in odd:
        src = "from the offer" if has_term(norm(offer), t) else "in no source"
        warns.append(f"term {t!r} ({src}) is not in the master/answers; it must describe the company, not claim a skill: {where(t)!r}")
    body_n = norm(" ".join(body))
    personal_n = norm(read(a.letter_answers))
    for rx in [r"relocat\w*", r"d[ée]m[ée]nag\w*", r"rapprochement", r"mobilit[ée]", r"remote", r"t[ée]l[ée]travail",
               r"(?:i am|i'm|je suis) (?:immediately )?(?:available|disponible)|disponible imm[ée]diatement|start date|date de d[ée]but",r"notice period|pr[ée]avis", r"salary|salaire|r[ée]mun[ée]ration"]:
        m = re.search(r"(?<![a-z])(" + rx + ")", body_n)
        if m and not re.search(rx, personal_n):
            warns.append(f"personal claim {m.group(1)!r} is not in letter_answers.md: keep it only if the user said it: {where(m.group(1))!r}")
    for c in CLICHES:
        if has_term(body_n, c):
            warns.append(f"cliché {c!r}: replace with a fact")
    n_words = len(" ".join(body).split())
    (oks if 250 <= n_words <= 450 else warns).append(f"{n_words} words (aim 250 to 450)")

    for l in fails: print("FAIL:", l)
    for l in warns: print("WARN:", l)
    for l in oks: print("ok:  ", l)
    print(f"{'PASS' if not fails else 'NOT PASSING'}: {len(fails)} fail(s), {len(warns)} warning(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
