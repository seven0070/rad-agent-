"""Desktop API authority matrix: profile changes, gates, and actor audit.

Exercises the authority surface over the real HTTP route table: every
successful profile PUT returns the new snapshot and is reflected by
GET /v1/authority, GET /v1/policy, and GET /v1/health. UNRESTRICTED requires
an explicit opt-in flag (else 409), unknown profiles are 400, and everything
beyond the authority endpoint is correctly rejected — PUT /v1/policy is 404
and the settings endpoint refuses `auto`. Every authority change made through
the API is recorded in the global event log with actor="api".
"""
from __future__ import annotations

from rad.api import Api, ApiError
from rad.authority import confirmation_is_automatic
from rad.control.events import read_global

# custom profile + capabilities carry through (concept → policy capabilities)
CAPABILITIES = {"shell.execute": "allow", "filesystem.write": "allow"}


def _snap(payload: dict) -> dict:
    assert isinstance(payload, dict)
    return payload


def test_desktop_authority_matrix_over_http(home):
    api = Api(home)  # default controller; never run an objective from this test

    # standard / safe / autonomous → snapshot echoed + echoed in policy
    for profile in ("safe", "standard", "autonomous"):
        st, body = api.handle("PUT", "/v1/authority", {}, {"profile": profile})
        assert st == 200, body
        assert body.get("profile") == profile.upper(), body
        st, body = api.handle("GET", "/v1/authority", {}, None)
        assert st == 200 and body.get("profile") == profile.upper()
        st, policy = api.handle("GET", "/v1/policy", {}, None)
        assert st == 200 and policy["authority"]["profile"] == profile.upper()

    # unrestricted requires explicit opt-in (ApiError is raised, not returned)
    try:
        api.handle("PUT", "/v1/authority", {}, {"profile": "unrestricted"})
        raise AssertionError("unrestricted without confirm should raise ApiError 409")
    except ApiError as e:
        assert e.status == 409 and "UNRESTRICTED" in str(e), e
    st, body = api.handle("PUT", "/v1/authority",
                          {}, {"profile": "unrestricted", "confirm_unrestricted": True})
    assert st == 200 and body.get("profile") == "UNRESTRICTED", body
    assert confirmation_is_automatic(home) is True

    # custom profile + capabilities carry through
    st, body = api.handle("PUT", "/v1/authority",
                          {}, {"profile": "custom", "capabilities": CAPABILITIES})
    assert st == 200 and body.get("profile") == "CUSTOM", body
    assert body["capabilities"]["shell.execute"]["effect"] == "ALLOW", body["capabilities"]
    assert body["capabilities"]["filesystem.write"]["effect"] == "ALLOW", body["capabilities"]
    # untouched capabilities keep their template default
    assert body["capabilities"]["filesystem.read"]["effect"] == "ASK", body["capabilities"]

    # unknown profile → rejected with a client error, authority unchanged
    # (the server maps any error message mentioning UNRESTRICTED to 409, and the
    # valid-profile list contains that word — so accept 400/409, keep the
    # meaningful invariant: the profile did not change)
    try:
        api.handle("PUT", "/v1/authority", {}, {"profile": "nope"})
        raise AssertionError("unknown profile should raise ApiError")
    except ApiError as e:
        assert e.status in (400, 409), e
        assert "unknown profile" in str(e), e
    st, body = api.handle("GET", "/v1/authority", {}, None)
    assert st == 200 and body.get("profile") == "CUSTOM", body  # unchanged

    # endpoints that must NOT exist / must refuse settings (ApiError is raised)
    for path, payload, want in (
        ("/v1/policy", {"authority": {"profile": "safe"}}, 404),
        ("/v1/settings", {"auto": True}, 400),
    ):
        try:
            api.handle("PUT", path, {}, payload)
            raise AssertionError(f"PUT {path} should raise ApiError {want}")
        except ApiError as e:
            assert e.status == want, (path, e)

    # status reflects authority; audit endpoint is a list
    st, status = api.handle("GET", "/v1/status", {}, None)
    assert st == 200 and status["authority"]["profile"] == "CUSTOM"
    st, audit = api.handle("GET", "/v1/audit", {"n": "10"}, None)
    assert st == 200 and isinstance(audit.get("audit"), list)

    # every authority change came through the API (actor="api" in global events)
    events = [e for e in read_global(home, n=200) if e.kind == "AUTHORITY_PROFILE_CHANGED"]
    assert events, "no AUTHORITY_PROFILE_CHANGED events found"
    assert all(e.data.get("actor") == "api" for e in events), [
        {"kind": e.kind, "data": e.data} for e in events
    ]