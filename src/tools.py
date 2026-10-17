"""Evidence-gathering tools for the Job Trust agent.

Each tool is a plain Python function: it takes simple inputs, returns a JSON-friendly dict,
and NEVER raises. If something goes wrong it returns {"error": "..."} so the agent loop can
carry on and the model can explain what it couldn't check.
"""

import re
from datetime import datetime, timezone

import httpx

TIMEOUT = 8.0  # seconds; a slow website shouldn't freeze the agent
HEADERS = {"User-Agent": "JobTrust/1.0 (student project; contact via GitHub)"}

FREE_WEBMAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "icloud.com", "aol.com", "proton.me", "protonmail.com", "gmx.com", "mail.com", "yandex.com",
}

# Two-part public suffixes where the "real" domain is the last THREE labels (company.co.uk).
TWO_PART_SUFFIXES = {"co.uk", "ac.uk", "org.uk", "com.sg", "edu.sg", "co.in", "com.au", "co.jp"}

DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")


def normalize_domain(value: str) -> str:
    """'https://www.Acme.com/careers' -> 'acme.com'. Returns '' if it isn't a valid domain."""
    value = (value or "").strip().lower()
    value = re.sub(r"^[a-z]+://", "", value)       # drop https://
    value = value.split("/")[0].split(":")[0]       # drop path and port
    value = value.removeprefix("www.")
    return value if DOMAIN_RE.match(value) else ""


def registrable_domain(domain: str) -> str:
    """'careers.acme.co.uk' -> 'acme.co.uk'. RDAP only knows registrable domains."""
    parts = domain.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_PART_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


# ---------- Tool 1: how old is the company's domain? ----------

def age_from_rdap(rdap: dict, today: datetime | None = None) -> dict:
    """Pull the registration date out of an RDAP JSON reply. Separate so it can be tested offline."""
    today = today or datetime.now(timezone.utc)
    for event in rdap.get("events", []):
        if event.get("eventAction") == "registration":
            registered = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
            return {"registered": registered.date().isoformat(), "age_days": (today - registered).days}
    return {"error": "no registration date in RDAP record"}


def check_domain_age(domain: str) -> dict:
    """Look up when a domain was registered, using the free public RDAP service (WHOIS's successor)."""
    domain = normalize_domain(domain)
    if not domain:
        return {"error": "not a valid domain"}
    domain = registrable_domain(domain)
    try:
        reply = httpx.get(f"https://rdap.org/domain/{domain}", timeout=TIMEOUT,
                          follow_redirects=True, headers=HEADERS)
        if reply.status_code == 404:
            return {"domain": domain, "error": "domain not found in RDAP (may not exist)"}
        reply.raise_for_status()
        return {"domain": domain, **age_from_rdap(reply.json())}
    except Exception as err:  # network down, bad JSON, ...: report, don't crash
        return {"domain": domain, "error": f"lookup failed: {type(err).__name__}"}


# ---------- Tool 2: does the recruiter's email match the company? ----------

def check_email_domain(email: str, company_domain: str) -> dict:
    """Compare the recruiter's email domain with the company's website domain."""
    email = (email or "").strip().lower()
    if "@" not in email:
        return {"error": "not an email address"}
    email_domain = normalize_domain(email.rsplit("@", 1)[1])
    company = normalize_domain(company_domain)
    if not email_domain:
        return {"error": "email has an invalid domain"}
    free = email_domain in FREE_WEBMAIL
    matches = bool(company) and (email_domain == company or email_domain.endswith("." + company))
    return {
        "email_domain": email_domain,
        "company_domain": company or None,
        "free_webmail": free,
        "matches_company": matches,
    }


# ---------- Tool 3: is the role on the company's own careers page? ----------

def title_words(title: str) -> list[str]:
    """Meaningful words from a job title: 'Software Engineer Intern' -> ['software', 'engineer', 'intern']."""
    return [w for w in re.findall(r"[a-z]+", (title or "").lower()) if len(w) >= 4]


def check_careers_page(company_domain: str, job_title: str) -> dict:
    """Fetch the company's careers page and look for the job title's words on it.

    Weak evidence only: many careers pages load jobs with JavaScript (Greenhouse, Lever, Workday),
    so 'not found' often just means we couldn't see them.
    """
    domain = normalize_domain(company_domain)
    words = title_words(job_title)
    if not domain or not words:
        return {"error": "need a valid company domain and a job title"}
    for path in ("/careers", "/jobs", "/careers/", "/about/careers"):
        url = f"https://{domain}{path}"
        try:
            reply = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
        except Exception:
            continue
        if reply.status_code == 200:
            page = reply.text.lower()
            hits = [w for w in words if w in page]
            return {
                "reachable": True,
                "checked_url": url,
                "title_words_found": f"{len(hits)}/{len(words)}",
                "found": len(hits) >= max(1, round(len(words) * 0.66)),
            }
    return {"reachable": False, "found": None, "note": "no careers page reachable at common paths"}
