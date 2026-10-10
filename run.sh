#!/usr/bin/env bash
# Start the chat UI on http://127.0.0.1:8800. Settings come from .env at the repo root (see .env.example).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi
if [[ -z "${LLM_API_KEY:-}${ZAI_API_KEY:-}" ]]; then
  echo "LLM_API_KEY is not set. Copy .env.example to .env and fill it in." >&2
  exit 1
fi

# Chainlit's history sidebar needs auth, and auth needs a token-signing secret: generated once, kept in artifacts/
SECRET_FILE=artifacts/.chainlit_auth_secret
if [[ -z "${CHAINLIT_AUTH_SECRET:-}" ]]; then
  mkdir -p artifacts
  [[ -s $SECRET_FILE ]] || uv run python -c 'import secrets;print(secrets.token_urlsafe(48))' > "$SECRET_FILE"
  CHAINLIT_AUTH_SECRET=$(cat "$SECRET_FILE")
  export CHAINLIT_AUTH_SECRET
fi

# Chainlit reads .chainlit/ and chainlit.md from the working directory, so run from chat/
cd chat
exec uv run chainlit run app.py --host 127.0.0.1 --port "${PORT:-8800}" --headless "$@"
