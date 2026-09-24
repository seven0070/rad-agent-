from unittest import mock

import pytest

import rad.providers as P
from rad.home import RadHome
from rad.router import RouterState


def _spec(name="testp"):
    return P.ProviderSpec(name=name, kind="openai", base_url="http://x/v1")


def test_key_from_env(home, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_1234567890")
    key = P.find_key(home, P.ProviderSpec("groq", "openai", key_names=("GROQ_API_KEY",)))
    assert key == "gsk_1234567890"


def test_key_from_vault_by_provider_name(home):
    home.vault_set("nvidia", "nvapi_test12345")
    spec = P.ProviderSpec("nvidia", "openai", key_names=("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"))
    assert P.find_key(home, spec) == "nvapi_test12345"


def test_key_from_env_file(home, monkeypatch, tmp_path):
    (tmp_path / ".env").write_text('CEREBRAS_API_KEY="csk_abc123"\n# comment\n')
    monkeypatch.chdir(tmp_path)
    key = P.find_key(home, P.ProviderSpec("cerebras", "openai", key_names=("CEREBRAS_API_KEY",)))
    assert key == "csk_abc123"


def test_vault_roundtrip(home):
    home.vault_set("mistral", "msk_secret")
    assert home.vault_get_all()["mistral"] == "msk_secret"
    home.vault_remove("mistral")
    assert "mistral" not in home.vault_get_all()


def test_chain_order_local_first(home):
    monkeypatch_env = {"OPENAI_API_KEY": "sk_test", "GROQ_API_KEY": "gsk_test"}
    with mock.patch.dict(__import__("os").environ, monkeypatch_env):
        with mock.patch.object(P, "probe_local", side_effect=lambda s: (True, ["m1"]) if s.local else (False, [])):
            r = RouterState(home)
            chain = r.build_chain()
            names = [e.spec.name for e in chain]
            # local tiers before free before paid
            tiers = [e.spec.tier for e in chain]
            assert tiers == sorted(tiers, key=lambda t: {"local": 0, "free": 1, "paid": 2}[t])
            assert "openai" in names and "groq" in names


def test_free_lock_drops_paid(home):
    with mock.patch.dict(__import__("os").environ, {"OPENAI_API_KEY": "sk_test", "GROQ_API_KEY": "gsk_test"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            r = RouterState(home)
            chain = r.build_chain(free_lock=True)
            assert all(e.spec.tier != "paid" for e in chain)
            assert any(e.spec.tier == "free" for e in chain)


def test_chat_fallback_across_providers(home):
    calls = {"n": 0}

    def fake_chat(spec, key, messages, **kw):
        calls["n"] += 1
        if spec.name == "groq":
            raise P.ProviderError("groq: HTTP 429 rate limited", status=429, retryable=True)
        return P.ChatResult(text=f"hi from {spec.name}", provider=spec.name, model="m", usage={"in": 1, "out": 1})

    with mock.patch.dict(__import__("os").environ, {"GROQ_API_KEY": "gsk", "CEREBRAS_API_KEY": "csk"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch.object(P, "chat", side_effect=fake_chat):
                r = RouterState(home)
                r.preferred["free"] = "groq"  # force groq first so it gets the 429
                res = r.chat([{"role": "user", "content": "hi"}], stream_cb=None)
                assert res.provider != "groq"
                assert calls["n"] == 2


def test_chat_no_brain_clear_error(home):
    with mock.patch.object(P, "probe_local", return_value=(False, [])):
        r = RouterState(home)
        with pytest.raises(P.ProviderError) as ei:
            r.chat([{"role": "user", "content": "hi"}])
        assert "no brain available" in str(ei.value)


def test_model_pin_scoped_to_force_provider_on_fallback(home):
    """Regression: cfg.model is a pin *for the pinned provider* (home.DEFAULTS),
    but router chat sent it to every chain entry. After nvidia timed out and
    Class C rotated to ollama, ollama got 'z-ai/glm-5.3-flash' → HTTP 404,
    killing the fallback that was supposed to save the run. health.py already
    scoped the same pin (`not force or force == spec.name`) — the router must too."""
    home.update(force_provider="nvidia", model="z-ai/glm-5.3-flash")
    home.vault_set("nvidia", "nvapi_test")
    seen = []

    def fake_chat(spec, key, messages, **kw):
        seen.append((spec.name, kw.get("model")))
        if spec.name == "nvidia":
            raise P.ProviderError("network: The read operation timed out", retryable=True)
        return P.ChatResult(text="ok", provider=spec.name, model=kw.get("model") or "",
                            usage={"in": 1, "out": 1})

    def fake_probe(s):
        return (True, ["qwen3:4b"]) if s.name == "ollama" else (False, [])

    with mock.patch.object(P, "probe_local", side_effect=fake_probe):
        with mock.patch.object(P, "chat", side_effect=fake_chat):
            r = RouterState(home)
            res = r.chat([{"role": "user", "content": "hi"}])
            assert res.provider == "ollama"
            assert dict(seen).get("nvidia") == "z-ai/glm-5.3-flash"   # pin reaches its own brain
            assert all(m != "z-ai/glm-5.3-flash" for n, m in seen if n != "nvidia")


def test_free_rotation(home):
    with mock.patch.dict(__import__("os").environ,
                         {"GROQ_API_KEY": "a", "CEREBRAS_API_KEY": "b", "GEMINI_API_KEY": "c"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            r = RouterState(home)
            c1 = [e.spec.name for e in r.build_chain() if e.spec.tier == "free"]
            assert len(c1) == 3
            # after a success on the first free provider, rotation starts there
            r.preferred["free"] = c1[0]
            c2 = [e.spec.name for e in r.build_chain() if e.spec.tier == "free"]
            assert c2[0] == c1[0]
