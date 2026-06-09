#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT_DIR/scripts/tibetan-python-env.sh"

usage() {
    cat >&2 <<'EOF'
Usage: ./web.sh

Starts the local minicloze web app with Tibetan Botok/pyewts support enabled.

Optional environment variables:
  MINICLOZE_WEB_ADDR=127.0.0.1:4000
  MINICLOZE_TIBETAN_VENV=/path/to/venv
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if ! command -v cargo >/dev/null 2>&1; then
    echo "cargo is required to run minicloze-web. Install Rust from https://rustup.rs/." >&2
    exit 1
fi

cd "$ROOT_DIR"
ensure_tibetan_python

echo "Starting minicloze-web with Tibetan Wylie support..."
exec cargo run --quiet -p minicloze-web -- "$@"
