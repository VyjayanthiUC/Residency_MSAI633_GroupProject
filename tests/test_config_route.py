"""LLM route selection (#92): the LLM_* and GLM_* settings are chosen as a whole, never mixed per field."""
import importlib

import pytest

KEYS = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "ZAI_API_KEY", "GLM_BASE_URL", "GLM_MODEL"]


@pytest.fixture
def load(monkeypatch):
    from rag import config
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)  # ignore a developer's local .env
    def _load(**env):
        for k in KEYS:
            monkeypatch.delenv(k, raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        return importlib.reload(config)
    yield _load
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    importlib.reload(config)


def test_no_key_defaults_to_openrouter_glm(load):
    c = load()
    assert (c.LLM_ROUTE, c.LLM_BASE_URL, c.LLM_MODEL, c.LLM_API_KEY) == \
        ("llm", "https://openrouter.ai/api/v1", "z-ai/glm-5.3-flash", "")


def test_zai_key_alone_uses_zai_defaults(load):
    # the #92 case: Z.ai key without GLM_MODEL used to send the OpenRouter ID to api.z.ai
    c = load(ZAI_API_KEY="z")
    assert (c.LLM_ROUTE, c.LLM_BASE_URL, c.LLM_MODEL, c.LLM_API_KEY) == \
        ("zai", "https://api.z.ai/api/coding/paas/v4", "glm-5.3-flash", "z")


def test_openrouter_key_ignores_leftover_glm_settings(load):
    # the other #92 case: a leftover GLM_MODEL used to reach OpenRouter, which rejects it
    c = load(LLM_API_KEY="o", ZAI_API_KEY="z", GLM_MODEL="glm-5.3-flash", GLM_BASE_URL="https://api.z.ai/x")
    assert (c.LLM_ROUTE, c.LLM_BASE_URL, c.LLM_MODEL, c.LLM_API_KEY) == \
        ("llm", "https://openrouter.ai/api/v1", "z-ai/glm-5.3-flash", "o")
