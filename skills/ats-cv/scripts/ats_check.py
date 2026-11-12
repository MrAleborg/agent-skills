#!/usr/bin/env python3
"""ATS check for a CV built from assets/cv_template.html.

Usage:
  ats_check.py CV.html --master MASTER.md --keywords KEYWORDS.json --offer OFFER.md [--answers ANSWERS.md] [--lang en|fr]

Reads CV.pdf and CV.docx next to CV.html (run render.sh first). The HTML is the
source of what the parsers *should* recover; the PDF is what they *do* recover,
via two independent extractors: pdftotext (plain text layer, like most ATS) and
open-resume (layout-aware section/field parser). The DOCX is checked as plain text.

Exit 0 when there are no FAIL lines. WARN lines need judgement, not a fix.
Writes CV.ats-report.json next to the HTML.
"""
import argparse, html, json, os, re, subprocess, sys, zipfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("ATS_CV_CACHE", os.path.expanduser("~/.cache/ats-cv"))


# ---------- normalisation ----------
def norm(s: str) -> str:
    s = html.unescape(s)
    s = re.sub(r"\\([\\#*_&\-\[\]()>+.!`])", r"\1", s)  # markdown escapes as exported by Drive
    s = s.replace("**", "")
    s = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", s)
    s = re.sub(r"[‘’]", "'", s).replace(" ", " ").replace("­", "")
    s = re.sub(r"-\s*\n\s*", "-", s)  # hyphen broken across lines
    return re.sub(r"\s+", " ", s).strip().lower()


def has_term(text_n: str, term: str) -> bool:
    t = norm(term)
    return re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", text_n) is not None


def digits(s: str) -> str:
    return re.sub(r"\D", "", s)


# ---------- read the HTML: what the CV claims ----------
class CVHtml(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.text = [], []
        self.name, self.contact, self.headings = "", [], []
        self.jobs, self.edus = [], []
        self._cur = None  # (kind, dict) for the block being read
        self._rowtexts = None

    def _classes(self):
        out = []
        for _, c in self.stack:
            out += c
        return out

    def handle_starttag(self, tag, attrs):
        cls = (dict(attrs).get("class") or "").split()
        if tag in ("meta", "link", "br", "img", "hr", "input", "wbr"):  # void: never closed
            if tag == "br":
                self.text.append("\n")
            return
        self.stack.append((tag, cls))
        if tag in ("p", "div", "h1", "h2", "br", "li"):
            self.text.append("\n")
        elif tag == "span":
            self.text.append(" ")
        if "emp" in cls:
            self._cur = {"title": "", "date": "", "company": "", "location": ""}
            self.jobs.append(self._cur)
        elif "edu" in cls:
            self._cur = {"title": "", "date": "", "company": "", "location": ""}
            self.edus.append(self._cur)
        if "row" in cls:
            self._rowtexts = []
        if tag == "span" and self._rowtexts is not None:
            self._rowtexts.append("")

    def handle_endtag(self, tag):
        if tag not in [t for t, _ in self.stack]:
            return
        while True:
            t, cls = self.stack.pop()
            if t == tag:
                break
        if "row" in cls and self._rowtexts is not None and self._cur is not None:
            parts = [p.strip() for p in self._rowtexts if p.strip()]
            a, b = (parts + ["", ""])[:2]
            if "role" in cls and not self._cur["title"]:
                self._cur["title"], self._cur["date"] = a, b
            elif "org" in cls and not self._cur["company"]:
                self._cur["company"], self._cur["location"] = a, b
            self._rowtexts = None

    def handle_data(self, data):
        if any(t in ("style", "script", "title", "head") for t, _ in self.stack):
            return
        self.text.append(data)
        tags = [t for t, _ in self.stack]
        cls = self._classes()
        if tags and tags[-1] == "h1":
            self.name += data
        if "h2" in tags:
            if tags[-1] == "h2":
                self.headings.append(data.strip())
        if "contact" in cls and data.strip() not in ("", "|"):
            self.contact.append(data.strip())
        if self._rowtexts is not None and self._rowtexts:
            self._rowtexts[-1] += data

    def handle_entityref(self, name):
        self.handle_data(html.unescape(f"&{name};"))


# ---------- extractors ----------
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def pdftotext(pdf):
    return run(["pdftotext", "-layout", pdf, "-"]).stdout


def open_resume(pdf):
    cli = os.path.join(CACHE, "or-cli.js")
    if not os.path.exists(cli):
        r = run([os.path.join(HERE, "setup_open_resume.sh")])
        if r.returncode:
            return None, "open-resume setup failed: " + r.stderr[-500:]
    env = dict(os.environ, NODE_PATH=os.path.join(CACHE, "deps", "node_modules"))
    r = run(["node", cli, pdf], env=env)
    if r.returncode:
        return None, "open-resume crashed: " + r.stderr[-500:]
    return json.loads(r.stdout), None


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf8")
    structural = {"tables": xml.count("<w:tbl>") + xml.count("<w:tbl "), "textboxes": xml.count("<w:txbxContent")}
    xml = re.sub(r"</w:p>|<w:br/>|<w:tab/>", "\n", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml)), structural


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


# ---------- checks ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--master", required=True)
    ap.add_argument("--keywords", required=True)
    ap.add_argument("--answers", help="user-confirmed facts gathered during the session")
    ap.add_argument("--offer", help="the job offer text; enables the smuggled-offer-term check")
    ap.add_argument("--lang", default="en", choices=["en", "fr"])
    a = ap.parse_args()

    base = os.path.splitext(a.html)[0]
    pdf, docx = base + ".pdf", base + ".docx"
    fails, warns, oks = [], [], []
    F, W, O = fails.append, warns.append, oks.append

    cv = CVHtml()
    cv.feed(open(a.html, encoding="utf8").read())
    cv_text_n = norm("".join(cv.text))
    master_raw = open(a.master, encoding="utf8").read()
    answers_raw = open(a.answers, encoding="utf8").read() if a.answers else ""
    facts_n = norm(master_raw + "\n" + answers_raw)
    master_n, answers_n = norm(master_raw), norm(answers_raw)
    email = next((c for c in cv.contact if "@" in c), "")
    phone = next((c for c in cv.contact if len(digits(c)) >= 9 and "@" not in c and "/" not in c), "")
    name = cv.name.strip()

    if not os.path.exists(pdf):
        print(f"FAIL: {pdf} missing, run render.sh first"); sys.exit(1)

    # --- 1. pdftotext: the plain text layer most ATS read ---
    pt = pdftotext(pdf)
    pt_n = norm(pt)
    if len(pt_n) < 300:
        F("pdftotext: almost no text extracted (image-only or broken PDF)")
    for label, val in (("name", name), ("email", email)):
        (O if val and has_term(pt_n, val) else F)(f"pdftotext: {label} {'found' if val and has_term(pt_n, val) else 'NOT found'}: {val!r}")
    if phone:
        (O if digits(phone) in digits(pt) else F)(f"pdftotext: phone {phone!r}")
    else:
        F("html: no phone number in the .contact line")
    for c in cv.contact:  # city, LinkedIn, website: a contact line too long for the page splits them mid-item
        if c not in (email, phone) and norm(c) not in pt_n:
            F(f"pdftotext: contact item {c!r} split or lost in the text layer (contact line too long?)")
    for h in cv.headings:
        (O if has_term(pt_n, h) else F)(f"pdftotext: heading {h!r}")
    for j in cv.jobs + cv.edus:
        for k in ("title", "company", "date"):
            if j[k] and not has_term(pt_n, j[k]):
                F(f"pdftotext: {k} {j[k]!r} not found in text layer")
    # A job whose title/company opens a page gets merged into the previous job by layout parsers.
    # Checked on the text layer so it also covers French, where open-resume parses no jobs.
    for i, page in enumerate(pt.split("\f")[1:], start=2):
        head = norm(" ".join([l for l in page.splitlines() if l.strip()][:2]))
        for j in cv.jobs:
            if any(j[k] and has_term(head, j[k]) for k in ("title", "company")):
                F(f"page {i} starts with job {j['title']!r}: layout parsers merge it into the previous job. "
                  "Move the break inside a job (class=\"pb\" on an earlier bullet or project); if the previous job is short, "
                  "cut a line or two on page 1 so the break moves")
    pages = run(["pdfinfo", pdf]).stdout
    m = re.search(r"Pages:\s+(\d+)", pages)
    if m and int(m.group(1)) > 2:
        W(f"pdf has {m.group(1)} pages; 1-2 is the norm")
    fonts = run(["pdffonts", pdf]).stdout.splitlines()[2:]
    if any(re.search(r"\sno\s", l) for l in fonts):
        F("pdf: some fonts are not embedded")
    imgs = run(["pdfimages", "-list", pdf]).stdout.splitlines()[2:]
    if imgs:
        W(f"pdf contains {len(imgs)} image(s); ATS ignore them, make sure no text lives in an image")

    # --- 2. open-resume: does a layout parser recover the structure? ---
    orj, err = open_resume(pdf)
    or_n = ""
    if err:
        F(err)
    else:
        r = orj["resume"]
        or_n = norm(" ".join(strings(r)))
        prof = r["profile"]
        if norm(prof.get("name", "")) != norm(name):
            F(f"open-resume: name parsed as {prof.get('name')!r}, expected {name!r}")
        else:
            O("open-resume: name")
        (O if norm(prof.get("email", "")) == norm(email) else F)(f"open-resume: email parsed as {prof.get('email')!r}")
        got_phone = digits(prof.get("phone", ""))
        # open-resume's regex grabs 10 digits, so "+33600000000" parses as its last 10: accept a suffix match.
        if phone and not (len(got_phone) >= 9 and digits(phone).endswith(got_phone)):
            F(f"open-resume: phone parsed as {prof.get('phone')!r}, expected {phone!r}. "
              "Write it as the 10-digit national number, e.g. 0600000000 (open-resume reads the first 10 digits)")
        else:
            O("open-resume: phone")
        wx = r.get("workExperiences", [])
        # French headings are detected but open-resume parses 0 jobs under them, so this cannot gate FR.
        (O if len(wx) == len(cv.jobs) else (F if a.lang == "en" else W))(
            f"open-resume: {len(wx)} jobs parsed, CV has {len(cv.jobs)}"
            + ("" if len(wx) >= len(cv.jobs) or a.lang != "en" else ". A job starting at the top of a page merges into the previous one: move the .pb page break"))
        if a.lang == "en":
            secs = [norm(s) for s in orj["sections"]]
            for h in cv.headings:
                if norm(h) not in secs:
                    F(f"open-resume: section {h!r} not detected as a heading (got {orj['sections']})")
            for exp, got in zip(cv.jobs, wx):
                for k, gk in (("company", "company"), ("title", "jobTitle"), ("date", "date")):
                    if norm(exp[k]) != norm(got.get(gk, "")):
                        F(f"open-resume: job {exp['title']!r}: {gk} parsed as {got.get(gk)!r}, expected {exp[k]!r}")
            ed = r.get("educations", [])
            (O if len(ed) == len(cv.edus) else W)(f"open-resume: {len(ed)} education entries parsed, CV has {len(cv.edus)}")
            for exp, got in zip(cv.edus, ed):
                if norm(exp["company"]) != norm(got.get("school", "")):
                    W(f"open-resume: school parsed as {got.get('school')!r}, expected {exp['company']!r} "
                      "(it only knows English school words; harmless unless the degree is lost too)")
        else:
            W("open-resume: French CV, only contact fields and job count are checked (parser is English-only)")

    # --- 3. DOCX ---
    docx_n = ""
    if os.path.exists(docx):
        dt, st = docx_text(docx)
        docx_n = norm(dt)
        if st["textboxes"]:
            F(f"docx: {st['textboxes']} text box(es); ATS often skip text boxes")
        if st["tables"]:
            W(f"docx: {st['tables']} table(s); some ATS scramble table cells")
        for label, val in (("name", name), ("email", email)):
            if val and not has_term(docx_n, val):
                F(f"docx: {label} {val!r} not found")
        if phone and digits(phone) not in digits(dt):
            F(f"docx: phone {phone!r} not found")
        for h in cv.headings:
            if not has_term(docx_n, h):
                F(f"docx: heading {h!r} not found")
        for j in cv.jobs + cv.edus:
            for k in ("title", "company", "date"):
                if j[k] and not has_term(docx_n, j[k]):
                    F(f"docx: {k} {j[k]!r} not found (glued to a neighbour?)")
    else:
        W("docx missing")

    # --- 4. keywords: coverage, evidence, and no gap smuggled in ---
    kws = json.load(open(a.keywords, encoding="utf8"))
    placed, total = 0, 0
    kw_rows = []
    for k in kws:
        term, variants = k["term"], k.get("variants", [])
        forms = [term] + variants
        status, ev = k.get("status", "matched"), (k.get("evidence") or "").strip()
        total += 1
        in_html = [f for f in forms if has_term(cv_text_n, f)]
        row = {"term": term, "status": status, "in_cv": bool(in_html)}
        if status in ("matched", "confirmed"):
            src_n = master_n if status == "matched" else answers_n
            if not ev:
                F(f"keyword {term!r}: status {status} but no evidence quote")
            elif norm(ev) not in src_n:
                F(f"keyword {term!r}: evidence quote not found verbatim in {'master CV' if status == 'matched' else 'answers'}: {ev[:80]!r}")
            else:
                # every spelling that reached the CV must exist in the source, whatever `variants` says
                unsourced = [f for f in in_html if not has_term(src_n, f)]
                if unsourced:
                    W(f"keyword {term!r}: inferred match, the CV says {unsourced} but the source does not "
                      f"(evidence: {ev[:70]!r}). List it for the user at delivery")
            if not in_html:
                F(f"keyword {term!r}: backed by evidence but missing from the CV")
            else:
                placed += 1
                # open-resume drops text under headings it cannot parse (all French ones), so skip it for fr
                for label, txt in (("pdftotext", pt_n), ("open-resume", or_n if a.lang == "en" else ""), ("docx", docx_n)):
                    if txt and not any(has_term(txt, f) for f in in_html):
                        # glued text still holds the term as a raw substring ("buildinghigh-trafficapis");
                        # a term in a section open-resume ignores is absent altogether
                        if label == "open-resume" and not any(norm(f) in txt for f in in_html):
                            W(f"keyword {term!r}: lost by open-resume. Expected if it only sits in a section open-resume "
                              "ignores (Languages, Certifications, Publications); otherwise text is glued, see template comment")
                        else:
                            F(f"keyword {term!r}: in the HTML but lost by {label} (glued or split text?)")
        elif status == "gap":
            if in_html and not any(has_term(master_n, f) for f in in_html):
                F(f"keyword {term!r}: marked gap (no evidence) but appears in the CV")
        kw_rows.append(row)
    backed = sum(1 for k in kws if k.get("status") in ("matched", "confirmed"))
    gaps = [k["term"] for k in kws if k.get("status") == "gap"]
    coverage = f"coverage: {placed}/{total} offer keywords placed ({backed} evidence-backed); gaps left out: {', '.join(gaps) or 'none'}"

    # --- 5. fabrication heuristics: numbers and term-like tokens not in the facts ---
    cv_plain = "".join(cv.text)
    nums = set(re.findall(r"(?<![\w.])\d+(?:[.,]\d+)?%?", html.unescape(cv_plain)))
    facts_digits = set(re.findall(r"(?<![\w.])\d+(?:[.,]\d+)?%?", html.unescape(master_raw + answers_raw)))
    contact_digits = digits(phone)
    for n in sorted(nums - facts_digits):
        if digits(n) and digits(n) in contact_digits:
            continue
        F(f"number {n!r} appears in the CV but nowhere in the master CV or answers")
    tokens = set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*(?:[+#.][A-Za-z0-9+#]*)*\b", cv_plain))
    suspicious = sorted(t for t in tokens
                        if re.search(r"[A-Z]|\d|[+#]", t[1:])  # tech-like: FastAPI, K8s, C++, AWS
                        and not has_term(facts_n, t) and not has_term(norm(name), t))
    if a.offer:
        # Offer words that reached the CV without being in the facts: the classic way a gap leaks in.
        stop = set("""a an and are as at be by for from in into is it of on or our the to we will with you your
            this that their they who what our us all any can has have more than other plus team work years year""".split())
        words = lambda t: {w.strip(".-") for w in re.findall(r"[a-zà-ÿ][a-zà-ÿ0-9+#.\-]{2,}", t)} - stop - {""}
        offer_words = words(norm(open(a.offer, encoding="utf8").read()))
        leaked = sorted(w for w in offer_words & words(cv_text_n) if not has_term(facts_n, w))
        if leaked:
            W("offer words in the CV but not in master/answers (each must be a harmless rewording, else remove): " + ", ".join(leaked))
    if suspicious:
        W("terms in the CV not found in master/answers (check each is a rewording, not a new claim): " + ", ".join(suspicious))

    report = {"coverage": coverage, "fails": fails, "warns": warns, "oks": oks, "keywords": kw_rows,
              "open_resume": orj, "pdftotext": pt}
    json.dump(report, open(base + ".ats-report.json", "w", encoding="utf8"), indent=2, ensure_ascii=False)
    for l in fails:
        print("FAIL:", l)
    for l in warns:
        print("WARN:", l)
    for l in oks:
        print("ok:  ", l)
    print("\n" + coverage)
    print(f"{'PASS' if not fails else 'NOT PASSING'}: {len(fails)} fail(s), {len(warns)} warning(s). Report: {base}.ats-report.json")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
