"""Fixed rules that turn evidence into a verdict. Code decides; the LLM only explains."""

# Part 1: constants
HIGH = 0.79               # ML score at or above this = high zone (notebooks/04_zones.ipynb)
LOW = 0.12                # ML score below this = low zone
YOUNG_DOMAIN_DAYS = 180   # domain younger than this = red flag
OLD_DOMAIN_DAYS = 730     # domain at least this old = green check


# Part 2: def decide(evidence) + read evidence safely
def decide(evidence: dict) -> dict:
    prob = evidence["ml"]["probability"]                 # always present, so [] is fine
    email = evidence.get("check_email_domain") or {}     # may be missing -> {} instead of crash
    age = evidence.get("check_domain_age") or {}
    careers = evidence.get("check_careers_page") or {}

    reds = []
    greens = []

    # Part 3: red flags
    if email.get("free_webmail") is True:
        reds.append("RED: recruiter uses a free webmail address")
    elif email.get("company_domain") and email.get("matches_company") is False:
        reds.append("RED: recruiter email does not match the company domain")

    days = age.get("age_days")
    if days is not None and days < YOUNG_DOMAIN_DAYS:
        reds.append(f"RED: company domain is only {days} days old")

    # Part 4: green checks (separate ifs: several can be true)
    if email.get("matches_company") is True:
        greens.append("GREEN: recruiter email matches the company domain")
    if days is not None and days >= OLD_DOMAIN_DAYS:
        greens.append(f"GREEN: company domain is {days} days old")
    if careers.get("found") is True:
        greens.append("GREEN: careers page found on the company site")
    # careers found == False adds nothing: JavaScript job boards hide listings.

    # Part 5: ML zone line (explanation only, doesn't change the verdict)
    if prob >= HIGH:
        zone = f"ML: {prob:.2f} (high zone, >= {HIGH})"
    elif prob < LOW:
        zone = f"ML: {prob:.2f} (low zone, < {LOW})"
    else:
        zone = f"ML: {prob:.2f} (middle zone)"

    # Part 6: verdict
    if (prob >= HIGH and len(reds) >= 1) or len(reds) >= 2:
        verdict = "scam"
    elif len(reds) == 0 and ((prob < LOW and len(greens) >= 1) or (prob < HIGH and len(greens) >= 2)):
        verdict = "likely_real"
    else:
        verdict = "unsure"

    # Part 7: return
    return {"verdict": verdict, "rules_fired": [zone] + reds + greens}
