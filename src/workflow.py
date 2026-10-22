"""Fixed-workflow version of the Job Trust agent, for comparison. No LLM decides anything:
regexes pull out the email/website/title, every check runs, the same rules decide."""

import re
import sys
from pathlib import Path

from src.decide import decide
from src.predict import score_posting
from src.tools import check_careers_page, check_domain_age, check_email_domain

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SITE_RE = re.compile(r"(?:website|site|www)\s*[:=]?\s*((?:https?://)?(?:www\.)?[\w-]+(?:\.[\w-]+)+)", re.I)


def run(text: str) -> dict:
    evidence = {"ml": score_posting(description=text)}
    email = EMAIL_RE.search(text)
    site = SITE_RE.search(text)
    title = text.strip().splitlines()[0]          # guess: the first line is the job title
    domain = site.group(1) if site else ""
    if email:
        evidence["check_email_domain"] = check_email_domain(email.group(0), domain)
    if domain:
        evidence["check_domain_age"] = check_domain_age(domain)
        evidence["check_careers_page"] = check_careers_page(domain, title)
    return {**decide(evidence), "evidence": evidence}


if __name__ == "__main__":
    out = run(Path(sys.argv[1]).read_text())
    print(out["verdict"], *out["rules_fired"], sep="\n  ")
