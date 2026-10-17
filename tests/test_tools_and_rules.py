"""Offline tests for the tools and the rules: no network, no API key needed."""

from datetime import datetime, timezone

from src.decide import HIGH, LOW, decide
from src.tools import age_from_rdap, check_email_domain, normalize_domain, registrable_domain


def test_normalize_domain():
    assert normalize_domain("https://www.Acme.com/careers") == "acme.com"
    assert normalize_domain("not a domain") == ""


def test_registrable_domain():
    assert registrable_domain("careers.acme.com") == "acme.com"
    assert registrable_domain("jobs.acme.co.uk") == "acme.co.uk"


def test_free_webmail_flagged():
    r = check_email_domain("hr.acme@gmail.com", "acme.com")
    assert r["free_webmail"] is True and r["matches_company"] is False


def test_subdomain_email_matches():
    assert check_email_domain("jane@careers.acme.com", "www.acme.com")["matches_company"] is True


def test_rdap_age_parsing():
    rdap = {"events": [{"eventAction": "registration", "eventDate": "2026-08-01T00:00:00Z"}]}
    out = age_from_rdap(rdap, today=datetime(2026, 10, 17, tzinfo=timezone.utc))
    assert out == {"registered": "2026-08-01", "age_days": 77}


def test_decide_scam_needs_two_kinds_of_evidence():
    high_ml_only = {"ml": {"probability": HIGH + 0.05}}
    assert decide(high_ml_only)["verdict"] == "unsure"           # ML alone is not enough
    plus_gmail = {**high_ml_only, "check_email_domain": {"free_webmail": True}}
    assert decide(plus_gmail)["verdict"] == "scam"


def test_decide_two_red_flags_is_scam_even_with_mid_score():
    ev = {"ml": {"probability": 0.5},
          "check_email_domain": {"free_webmail": True},
          "check_domain_age": {"age_days": 30}}
    assert decide(ev)["verdict"] == "scam"


def test_decide_likely_real():
    ev = {"ml": {"probability": LOW - 0.05},
          "check_email_domain": {"free_webmail": False, "company_domain": "stripe.com", "matches_company": True}}
    assert decide(ev)["verdict"] == "likely_real"


def test_careers_not_found_is_not_a_red_flag():
    ev = {"ml": {"probability": LOW - 0.05}, "check_careers_page": {"found": False}}
    assert decide(ev)["verdict"] == "unsure"


def test_two_green_checks_beat_a_middle_score():
    ev = {"ml": {"probability": 0.31},
          "check_email_domain": {"free_webmail": False, "company_domain": "stripe.com", "matches_company": True},
          "check_domain_age": {"age_days": 5800}}
    assert decide(ev)["verdict"] == "likely_real"
