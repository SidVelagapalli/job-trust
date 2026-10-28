"""Evidence-gathering tools for the Job Trust agent.

Each tool is a plain Python function: it takes simple inputs, returns a JSON-friendly dict,
and NEVER raises. If something goes wrong it returns {"error": "..."} so the agent loop can
carry on and the model can explain what it couldn't check.
"""

import ipaddress
import re
import socket
from datetime import datetime, timezone

import httpx

TIMEOUT = 8.0  # seconds; a slow website shouldn't freeze the agent
HEADERS = {"User-Agent": "JobTrust/1.0 (student project; contact via GitHub)"}
# identity = "don't compress": a tiny gzip reply can unpack to gigabytes, which would dodge the 1 MB cap.
PAGE_HEADERS = {**HEADERS, "Accept-Encoding": "identity"}
MAX_PAGE_BYTES = 1_000_000  # read at most 1 MB of a careers page: a huge page shouldn't eat memory
MAX_REDIRECTS = 5           # follow at most this many same-site redirects

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


def resolve_ips(host: str) -> list[str]:
    """DNS lookup: 'acme.com' -> ['93.184.216.34', ...]. Raises OSError if the name doesn't resolve."""
    return [info[4][0] for info in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)]


def is_public_host(host: str) -> bool:
    """True only if EVERY address the host resolves to is on the public internet.

    The domain comes from an untrusted posting, so a scammer could point it at 127.0.0.1 (this machine),
    10.x.x.x (a home/office network) or 169.254.169.254 (cloud secrets). is_global is False for all of
    those (private, loopback, link-local, reserved), so we refuse them before sending any request.
    """
    ips = resolve_ips(host)
    return bool(ips) and all(ipaddress.ip_address(ip.split("%")[0]).is_global for ip in ips)


def make_client() -> httpx.Client:
    """One place that builds the HTTP client, so tests can swap in a fake network.
    follow_redirects=False: fetch_page follows redirects itself, only within the same site."""
    return httpx.Client(timeout=TIMEOUT, headers=PAGE_HEADERS, follow_redirects=False)


class Refused(Exception):
    """A redirect tried to send us to another site or to a private address."""


def fetch_page(client: httpx.Client, url: str, domain: str) -> tuple[int, str]:
    """GET a page, following redirects only while they stay on `domain`, reading at most 1 MB.

    acme.com/careers -> www.acme.com/careers is fine (same site); -> evil.com raises Refused.
    Every hop is checked with is_public_host, because www.acme.com could resolve somewhere else.
    """
    for _ in range(MAX_REDIRECTS + 1):
        parsed = httpx.URL(url)
        host = parsed.host
        if parsed.scheme != "https" or parsed.port not in (None, 443):
            raise Refused("redirect away from https on the normal port")
        if normalize_domain(host) != domain:
            raise Refused("redirect to another site")
        if not is_public_host(host):
            raise Refused("private or local address")
        with client.stream("GET", url) as reply:
            if reply.is_redirect and "location" in reply.headers:
                url = str(reply.url.join(reply.headers["location"]))
                continue
            body = b""
            for chunk in reply.iter_bytes():   # stream: stop reading once we have 1 MB
                body += chunk
                if len(body) >= MAX_PAGE_BYTES:
                    break
            body = body[:MAX_PAGE_BYTES]
            try:
                text = body.decode(reply.encoding or "utf-8", errors="replace")
            except LookupError:  # the site named a charset Python doesn't know: fall back to utf-8
                text = body.decode("utf-8", errors="replace")
            return reply.status_code, text
    raise Refused("too many redirects")


def check_careers_page(company_domain: str, job_title: str) -> dict:
    """Fetch the company's careers page and look for the job title's words on it.

    Weak evidence only: many careers pages load jobs with JavaScript (Greenhouse, Lever, Workday),
    so 'not found' often just means we couldn't see them.
    """
    domain = normalize_domain(company_domain)
    words = title_words(job_title)
    if not domain or not words:
        return {"error": "need a valid company domain and a job title"}
    try:
        if not is_public_host(domain):
            return {"error": "refused: domain resolves to a private or local address"}
    except Exception:  # DNS lookup failed: we can't reach anything on this domain
        return {"error": "network failure"}

    paths = ("/careers", "/jobs", "/careers/", "/about/careers")
    network_errors = 0
    with make_client() as client:
        for path in paths:
            url = f"https://{domain}{path}"
            try:
                status, text = fetch_page(client, url, domain)
            except (httpx.TransportError, OSError):  # timeout, connection refused, DNS, ...
                network_errors += 1
                continue
            except Exception:  # Refused, bad encoding, ...: this path is a dead end, try the next
                continue
            if status == 200:
                page = text.lower()
                hits = [w for w in words if w in page]
                return {
                    "reachable": True,
                    "checked_url": url,
                    "title_words_found": f"{len(hits)}/{len(words)}",
                    "found": len(hits) >= max(1, round(len(words) * 0.66)),
                }
    if network_errors == len(paths):
        # Every request failed to connect: that says nothing about the careers page, so don't pretend it does.
        return {"error": "network failure"}
    return {"reachable": False, "found": None, "note": "no careers page reachable at common paths"}
