#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${MINICLOZE_TIBETAN_VENV:-"$ROOT_DIR/.venv-tibetan"}"

if ! command -v cargo >/dev/null 2>&1; then
    echo "cargo is required to run minicloze. Install Rust from https://rustup.rs/." >&2
    exit 1
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        echo "python3 is required to create the Tibetan tokenizer environment." >&2
        exit 1
    fi

    echo "Creating Python environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"

if ! "$PYTHON" -c "import botok" >/dev/null 2>&1; then
    echo "Installing Tibetan tokenizer dependency: botok..."
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install botok
fi

echo "Starting minicloze Tibetan mode..."
cd "$ROOT_DIR"
MINICLOZE_PYTHON="$PYTHON" cargo run --quiet -- tibetan "$@"
