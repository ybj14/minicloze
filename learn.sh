#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${MINICLOZE_TIBETAN_VENV:-"$ROOT_DIR/.venv-tibetan"}"

usage() {
    cat >&2 <<'EOF'
Usage: ./learn.sh <language-or-corpus> [inverse]

Examples:
  ./learn.sh mongolian
  ./learn.sh tibetan
  ./learn.sh tibetan-a1
  ./learn.sh tibetan-a1 inverse
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ "$#" -lt 1 ]; then
    usage
    exit 1
fi

if ! command -v cargo >/dev/null 2>&1; then
    echo "cargo is required to run minicloze. Install Rust from https://rustup.rs/." >&2
    exit 1
fi

TARGET="$1"

needs_tibetan_python() {
    case "$1" in
        tibetan|bod|tibetan-*|bod-*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

ensure_tibetan_python() {
    if [ ! -x "$VENV_DIR/bin/python" ]; then
        if ! command -v python3 >/dev/null 2>&1; then
            echo "python3 is required to create the Tibetan tokenizer environment." >&2
            exit 1
        fi

        echo "Creating Python environment at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    fi

    local python="$VENV_DIR/bin/python"

    if ! "$python" -c "import botok, pyewts" >/dev/null 2>&1; then
        echo "Installing Tibetan tokenizer dependencies: botok and pyewts..."
        "$python" -m pip install --upgrade pip "setuptools<81" wheel
        "$python" -m pip install botok
        "$python" -m pip install --no-build-isolation pyewts
    fi

    export MINICLOZE_PYTHON="$python"
}

cd "$ROOT_DIR"

if needs_tibetan_python "$TARGET"; then
    ensure_tibetan_python
fi

echo "Starting minicloze for $TARGET..."
cargo run --quiet -- "$@"
