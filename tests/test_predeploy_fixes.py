"""Offline tests for the 3 pre-deploy fixes: total time limit, compressed replies, paid-call cap."""

import httpx
import pytest

from src import mcp_server, tools

PUBLIC_IP = "93.184.216.34"


def fake_network(monkeypatch, handler):
    requested = []

    def recording_handler(request):
        requested.append(str(request.url))
        return handler(request)

    monkeypatch.setattr(tools, "resolve_ips", lambda host: [PUBLIC_IP])
    monkeypatch.setattr(tools, "make_client", lambda: httpx.Client(
        transport=httpx.MockTransport(recording_handler), follow_redirects=False))
    return requested


def test_compressed_reply_is_refused_unread(monkeypatch):
    # The server ignores our "identity" request and gzips anyway: we must not unpack it.
    fake_network(monkeypatch, lambda r: httpx.Response(
        200, headers={"content-encoding": "gzip"}, content=iter([b"not really gzip"])))  # streamed, like a real server
    out = tools.check_careers_page("acme.com", "Software Engineer")
    # The site answered, so it IS reachable; we just didn't read it. Never "no careers page".
    assert out["reachable"] is True and out["found"] is None
    assert "compressed" in out["note"]


def test_identity_encoding_header_is_still_read(monkeypatch):
    fake_network(monkeypatch, lambda r: httpx.Response(
        200, headers={"content-encoding": "identity"}, text="software engineer"))
    assert tools.check_careers_page("acme.com", "Software Engineer")["found"] is True


def test_slow_drip_page_stops_at_the_total_time_limit(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(tools.time, "monotonic", lambda: clock["now"])

    def drip():  # each piece "takes" 5 s; the title would only arrive after 100 pieces
        for _ in range(100):
            clock["now"] += 5
            yield b"x" * 10
        yield b"software engineer"

    requested = fake_network(monkeypatch, lambda r: httpx.Response(200, content=drip()))
    out = tools.check_careers_page("acme.com", "Software Engineer")
    assert "timed out" in out["error"]  # gave up: we learned nothing about the careers page
    assert len(requested) == 1          # the shared budget was spent, so no other paths tried
    assert clock["now"] <= tools.TOTAL_SECONDS + 5


def test_404_then_timeout_is_not_reported_as_no_careers_page(monkeypatch):
    # Path 1 is a clean 404, path 2 drips past the budget: paths 3-4 were never checked.
    clock = {"now": 0.0}
    monkeypatch.setattr(tools.time, "monotonic", lambda: clock["now"])

    def drip():
        for _ in range(100):
            clock["now"] += 5
            yield b"x"

    def handler(request):
        if request.url.path == "/careers":
            return httpx.Response(404)
        return httpx.Response(200, content=drip())

    fake_network(monkeypatch, handler)
    out = tools.check_careers_page("acme.com", "Software Engineer")
    assert "error" in out and "reachable" not in out


def test_fast_pages_are_unaffected_by_the_time_limit(monkeypatch):
    fake_network(monkeypatch, lambda r: httpx.Response(200, text="software engineer"))
    assert tools.check_careers_page("acme.com", "Software Engineer")["found"] is True


@pytest.fixture
def empty_call_log(monkeypatch):
    monkeypatch.setattr(mcp_server, "_recent_calls", mcp_server.deque())


def test_paid_calls_are_capped_per_hour(empty_call_log):
    limit = mcp_server.MAX_CALLS_PER_HOUR
    assert not any(mcp_server.over_call_limit(now=i) for i in range(limit))  # first `limit` calls pass
    assert mcp_server.over_call_limit(now=limit + 1)                         # the next one is refused


def test_cap_frees_up_after_an_hour(empty_call_log):
    for i in range(mcp_server.MAX_CALLS_PER_HOUR):
        mcp_server.over_call_limit(now=i)
    assert not mcp_server.over_call_limit(now=3600 + mcp_server.MAX_CALLS_PER_HOUR)


def test_over_limit_check_posting_never_calls_llm(empty_call_log, monkeypatch):
    monkeypatch.setattr(mcp_server, "over_call_limit", lambda: True)
    monkeypatch.setattr(mcp_server, "run_agent", lambda *a, **k: pytest.fail("paid call made over the limit"))
    assert "limit reached" in mcp_server.check_posting("any posting")["error"]
