#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT_DIR/scripts/tibetan-python-env.sh"

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

cd "$ROOT_DIR"

if needs_tibetan_python "$TARGET"; then
    ensure_tibetan_python
fi

echo "Starting minicloze for $TARGET..."
cargo run --quiet -- "$@"
