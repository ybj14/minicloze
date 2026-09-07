ensure_tibetan_python() {
    local venv_dir="${MINICLOZE_TIBETAN_VENV:-"$ROOT_DIR/.venv-tibetan"}"

    if [ ! -x "$venv_dir/bin/python" ]; then
        if ! command -v python3 >/dev/null 2>&1; then
            echo "python3 is required to create the Tibetan tokenizer environment." >&2
            exit 1
        fi

        echo "Creating Python environment at $venv_dir..."
        python3 -m venv "$venv_dir"
    fi

    local python="$venv_dir/bin/python"

    if ! "$python" -c "import botok, pyewts" >/dev/null 2>&1; then
        echo "Installing Tibetan tokenizer dependencies: botok and pyewts..."
        "$python" -m pip install --upgrade pip "setuptools<81" wheel
        "$python" -m pip install botok
        "$python" -m pip install --no-build-isolation pyewts
    fi

    export MINICLOZE_PYTHON="$python"
}
