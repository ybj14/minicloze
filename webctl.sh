#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$ROOT_DIR/scripts/tibetan-python-env.sh"

PID_FILE="${MINICLOZE_WEB_PID_FILE:-"$ROOT_DIR/.minicloze-web.pid"}"
LOG_FILE="${MINICLOZE_WEB_LOG:-"$ROOT_DIR/.minicloze-web.log"}"

usage() {
    cat >&2 <<EOF
Usage: ./webctl.sh <start|stop|restart|status|logs|run>

Commands:
  start    Start minicloze-web in the background.
  stop     Stop the background minicloze-web process.
  restart  Stop, then start minicloze-web.
  status   Show whether the background process is running.
  logs     Follow the web server log.
  run      Run minicloze-web in the foreground.

Optional environment variables:
  MINICLOZE_WEB_ADDR=127.0.0.1:4000
  MINICLOZE_TIBETAN_VENV=/path/to/venv
  MINICLOZE_WEB_PID_FILE=/path/to/minicloze-web.pid
  MINICLOZE_WEB_LOG=/path/to/minicloze-web.log
EOF
}

require_cargo() {
    if ! command -v cargo >/dev/null 2>&1; then
        echo "cargo is required to run minicloze-web. Install Rust from https://rustup.rs/." >&2
        exit 1
    fi
}

pid_is_running() {
    local pid="${1:-}"
    [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1
}

current_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

run_server() {
    require_cargo
    cd "$ROOT_DIR"
    ensure_tibetan_python
    exec cargo run --quiet -p minicloze-web
}

start_server() {
    require_cargo

    local pid
    pid="$(current_pid || true)"
    if pid_is_running "$pid"; then
        echo "minicloze-web is already running with PID $pid."
        return 0
    fi

    if [ -n "$pid" ]; then
        rm -f "$PID_FILE"
    fi

    cd "$ROOT_DIR"
    ensure_tibetan_python

    echo "Starting minicloze-web in the background..."
    nohup cargo run --quiet -p minicloze-web >"$LOG_FILE" 2>&1 &
    pid="$!"
    echo "$pid" >"$PID_FILE"

    for _ in {1..40}; do
        if ! pid_is_running "$pid"; then
            rm -f "$PID_FILE"
            echo "minicloze-web failed to start. Log:" >&2
            tail -40 "$LOG_FILE" >&2 || true
            exit 1
        fi

        if grep -q "minicloze web is running at" "$LOG_FILE" 2>/dev/null; then
            local url
            url="$(
                grep -m1 "minicloze web is running at" "$LOG_FILE" \
                    | sed 's/^.*minicloze web is running at //'
            )"
            echo "minicloze-web started with PID $pid."
            echo "URL: $url"
            echo "Log: $LOG_FILE"
            return 0
        fi

        sleep 0.25
    done

    echo "minicloze-web is still starting with PID $pid."
    echo "Log: $LOG_FILE"
}

stop_server() {
    local pid
    pid="$(current_pid || true)"

    if ! pid_is_running "$pid"; then
        rm -f "$PID_FILE"
        echo "minicloze-web is not running."
        return 0
    fi

    echo "Stopping minicloze-web with PID $pid..."
    kill "$pid"

    for _ in {1..30}; do
        if ! pid_is_running "$pid"; then
            rm -f "$PID_FILE"
            echo "minicloze-web stopped."
            return 0
        fi
        sleep 0.2
    done

    echo "Process $pid did not stop after SIGTERM; sending SIGKILL..."
    kill -9 "$pid" >/dev/null 2>&1 || true
    rm -f "$PID_FILE"
    echo "minicloze-web stopped."
}

status_server() {
    local pid
    pid="$(current_pid || true)"

    if pid_is_running "$pid"; then
        echo "minicloze-web is running with PID $pid."
        echo "Log: $LOG_FILE"
    else
        rm -f "$PID_FILE"
        echo "minicloze-web is not running."
    fi
}

case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        start_server
        ;;
    status)
        status_server
        ;;
    logs)
        touch "$LOG_FILE"
        tail -f "$LOG_FILE"
        ;;
    run)
        run_server
        ;;
    -h|--help|help)
        usage
        ;;
    "")
        usage
        exit 1
        ;;
    *)
        echo "Unknown command: $1" >&2
        usage
        exit 1
        ;;
esac
