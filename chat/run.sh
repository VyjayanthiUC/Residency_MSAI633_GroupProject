#!/usr/bin/env bash
# Start the chat UI on http://127.0.0.1:8800
# Reads ZAI_API_KEY (and optional GLM_BASE_URL / GLM_MODEL) from chat/.env — copy .env.example first.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi
if [[ -z "${ZAI_API_KEY:-}" ]]; then
  echo "ZAI_API_KEY is not set. Copy .env.example to .env and fill it in." >&2
  exit 1
fi

# Auth (required for the history sidebar) needs a token-signing secret: generated on first run, kept in git-ignored data/
SECRET_FILE=data/.chainlit_auth_secret
if [[ -z "${CHAINLIT_AUTH_SECRET:-}" ]]; then
  mkdir -p data
  [[ -s $SECRET_FILE ]] || python3 -c 'import secrets;print(secrets.token_urlsafe(48))' > "$SECRET_FILE"
  CHAINLIT_AUTH_SECRET=$(cat "$SECRET_FILE")
  export CHAINLIT_AUTH_SECRET
fi

exec uv run chainlit run app.py --host 127.0.0.1 --port "${PORT:-8800}" --headless "$@"
