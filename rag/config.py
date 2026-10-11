"""Every path and tunable setting in one place. Each can be overridden by an environment variable or the root .env."""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _env(name: str, default):
    raw = os.environ.get(name)
    return default if raw in (None, "") else type(default)(raw)


# Committed corpus snapshot (input) and generated files (git-ignored output)
CORPUS_DIR = Path(_env("CORPUS_DIR", str(ROOT / "data" / "genshin")))
DOCS_PATH = CORPUS_DIR / "normalized" / "docs.jsonl"
MANIFEST_PATH = CORPUS_DIR / "manifest.jsonl"
RAW_DIR = CORPUS_DIR / "raw"
ARTIFACTS = Path(_env("ARTIFACTS_DIR", str(ROOT / "artifacts")))
CHROMA_DIR = Path(_env("CHROMA_DIR", str(ARTIFACTS / "chroma"))).resolve()
LLM_CACHE = ARTIFACTS / "llm_cache"
THREADS_DB = ARTIFACTS / "threads.sqlite"

# Embedding (stage 4). The tokenizer that sizes chunks is the embedding model's own.
EMBED_MODEL = _env("EMBED_MODEL", "BAAI/bge-m3")
COLLECTION = "chunks-" + re.sub(r"[^a-zA-Z0-9]+", "-", EMBED_MODEL).strip("-").lower()  # one collection per model

# Chunking (stage 3)
A_SIZE = _env("A_SIZE", 512)
A_OVERLAP = _env("A_OVERLAP", 64)
B_MAX = _env("B_MAX", 512)

# Retrieval and reranking (stages 7–8)
RETRIEVER = _env("RETRIEVER", "hybrid")          # bm25 | dense | hybrid
CHUNK_STRATEGY = _env("CHUNK_STRATEGY", "B")     # A | B
RERANK = _env("RERANK", "1") != "0"
RERANK_MODEL = _env("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
K_POOL = _env("K_POOL", 20)
K_FINAL = _env("K_FINAL", 5)
RRF_K = 60
# Tuned on dev: at 50, same-page chunks present in both lists out-scored chunks ranked first by dense alone
FUSION_DEPTH = _env("FUSION_DEPTH", 30)
# Top rerank score below which the system refuses without calling the LLM; tuned on dev for bge-reranker-v2-m3
# (evaluation/results/threshold_dev.json) — re-tune if RERANK_MODEL changes. 0 disables.
REFUSE_BELOW = _env("REFUSE_BELOW", 0.52)

# Generation (stage 9): any OpenAI-compatible API, reached by one of two routes. The route is chosen as a whole, so a
# .env that sets values from both never sends one route's model ID to the other (#92):
#   LLM_*  OpenRouter by default; used whenever LLM_API_KEY is set (or no key is set at all)
#   GLM_*  Z.ai directly; used when only ZAI_API_KEY is set
LLM_ROUTE = "zai" if os.environ.get("ZAI_API_KEY") and not os.environ.get("LLM_API_KEY") else "llm"
if LLM_ROUTE == "zai":
    LLM_BASE_URL = os.environ.get("GLM_BASE_URL") or "https://api.z.ai/api/coding/paas/v4"
    LLM_MODEL = os.environ.get("GLM_MODEL") or "glm-5.3-flash"
    LLM_API_KEY = os.environ["ZAI_API_KEY"]
else:
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or "https://openrouter.ai/api/v1"
    LLM_MODEL = os.environ.get("LLM_MODEL") or "z-ai/glm-5.3-flash"
    LLM_API_KEY = os.environ.get("LLM_API_KEY") or ""
