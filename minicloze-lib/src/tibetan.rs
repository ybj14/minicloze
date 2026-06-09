use std::error::Error;
use std::io::{Error as IoError, ErrorKind, Write};
use std::process::{Command, Stdio};

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub(crate) struct TibetanToken {
    pub text: String,
    pub wylie: String,
}

const BOTOK_HELPER: &str = r#"
import json
import sys
from pathlib import Path

try:
    from botok import WordTokenizer
    from botok.config import Config
    import pyewts
except ModuleNotFoundError:
    sys.stderr.write(
        "Tibetan tokenization requires Python packages botok and pyewts. "
        "Install them with: pip install botok && pip install 'setuptools<81' wheel && pip install --no-build-isolation pyewts\n"
    )
    sys.exit(2)


def token_to_text(token):
    if isinstance(token, str):
        return token

    for attr in ("text", "chunk", "content", "word"):
        value = getattr(token, attr, None)
        if isinstance(value, str) and value:
            return value

    to_dict = getattr(token, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
        for key in ("text", "chunk", "content", "word"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value

    return str(token)


texts = json.load(sys.stdin)

json_stdout = sys.stdout
sys.stdout = sys.stderr
config = Config(dialect_name="general", base_path=Path.home())
tokenizer = WordTokenizer(config=config)
converter = pyewts.pyewts()

output = []
for text in texts:
    tokens = []
    for token in tokenizer.tokenize(text, split_affixes=False):
        token_text = token_to_text(token)
        if token_text.strip():
            tokens.append({
                "text": token_text,
                "wylie": converter.toWylie(token_text),
            })
    output.append(tokens)

sys.stdout = json_stdout
json.dump(output, sys.stdout, ensure_ascii=False)
"#;

const WYLIE_HELPER: &str = r#"
import json
import sys

try:
    import pyewts
except ModuleNotFoundError:
    sys.stderr.write(
        "Tibetan Wylie transliteration requires pyewts. "
        "Install it with: pip install 'setuptools<81' wheel && pip install --no-build-isolation pyewts\n"
    )
    sys.exit(2)

texts = json.load(sys.stdin)
converter = pyewts.pyewts()
json.dump([converter.toWylie(text) for text in texts], sys.stdout, ensure_ascii=False)
"#;

pub fn tokenize_batch_with_botok(
    texts: &[&str],
) -> Result<Vec<Vec<TibetanToken>>, Box<dyn Error + Send + Sync>> {
    let python = std::env::var("MINICLOZE_PYTHON").unwrap_or_else(|_| "python3".to_string());
    let input = serde_json::to_vec(texts)?;

    let mut child = Command::new(&python)
        .arg("-c")
        .arg(BOTOK_HELPER)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|err| {
            IoError::new(
                err.kind(),
                format!(
                    "failed to start {python} for Tibetan tokenization; install Python 3, botok, and pyewts, or set MINICLOZE_PYTHON: {err}"
                ),
            )
        })?;

    let mut stdin = child.stdin.take().ok_or_else(|| {
        IoError::new(
            ErrorKind::BrokenPipe,
            "failed to open stdin for Tibetan tokenizer",
        )
    })?;
    stdin.write_all(&input)?;
    drop(stdin);

    let output = child.wait_with_output()?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(IoError::new(
            ErrorKind::Other,
            format!("Botok Tibetan tokenization failed: {}", stderr.trim()),
        )
        .into());
    }

    let tokenized = parse_botok_output(&output.stdout)?;
    if tokenized.len() != texts.len() {
        return Err(IoError::new(
            ErrorKind::InvalidData,
            format!(
                "Botok returned {} tokenized texts for {} inputs",
                tokenized.len(),
                texts.len()
            ),
        )
        .into());
    }

    Ok(tokenized)
}

pub(crate) fn transliterate_batch_to_wylie(
    texts: &[&str],
) -> Result<Vec<String>, Box<dyn Error + Send + Sync>> {
    let python = std::env::var("MINICLOZE_PYTHON").unwrap_or_else(|_| "python3".to_string());
    let input = serde_json::to_vec(texts)?;

    let mut child = Command::new(&python)
        .arg("-c")
        .arg(WYLIE_HELPER)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|err| {
            IoError::new(
                err.kind(),
                format!(
                    "failed to start {python} for Tibetan Wylie transliteration; install Python 3 and pyewts, or set MINICLOZE_PYTHON: {err}"
                ),
            )
        })?;

    let mut stdin = child.stdin.take().ok_or_else(|| {
        IoError::new(
            ErrorKind::BrokenPipe,
            "failed to open stdin for Tibetan Wylie transliteration",
        )
    })?;
    stdin.write_all(&input)?;
    drop(stdin);

    let output = child.wait_with_output()?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(IoError::new(
            ErrorKind::Other,
            format!("Tibetan Wylie transliteration failed: {}", stderr.trim()),
        )
        .into());
    }

    let transliterated = serde_json::from_slice::<Vec<String>>(&output.stdout)?;
    if transliterated.len() != texts.len() {
        return Err(IoError::new(
            ErrorKind::InvalidData,
            format!(
                "pyewts returned {} transliterations for {} inputs",
                transliterated.len(),
                texts.len()
            ),
        )
        .into());
    }

    Ok(transliterated)
}

pub fn tokenize_syllables(text: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();

    for ch in text.trim().chars() {
        current.push(ch);

        if is_tibetan_break(ch) || ch.is_whitespace() {
            push_token(&mut tokens, &mut current);
        }
    }

    push_token(&mut tokens, &mut current);
    tokens
}

fn parse_botok_output(output: &[u8]) -> Result<Vec<Vec<TibetanToken>>, serde_json::Error> {
    serde_json::from_slice(output)
}

fn is_tibetan_break(ch: char) -> bool {
    matches!(ch, '་' | '༌' | '།' | '༎' | '༏' | '༐' | '༑' | '༔')
}

fn push_token(tokens: &mut Vec<String>, current: &mut String) {
    if !current.trim().is_empty() {
        tokens.push(std::mem::take(current));
    } else {
        current.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_botok_json_output() {
        let output =
            r#"[[{"text":"བཀྲ་ཤིས་","wylie":"bkra shis "},{"text":"བདེ་ལེགས","wylie":"bde legs"}]]"#;

        assert_eq!(
            parse_botok_output(output.as_bytes()).unwrap(),
            vec![vec![
                TibetanToken {
                    text: "བཀྲ་ཤིས་".to_string(),
                    wylie: "bkra shis ".to_string(),
                },
                TibetanToken {
                    text: "བདེ་ལེགས".to_string(),
                    wylie: "bde legs".to_string(),
                }
            ]]
        );
    }

    #[test]
    fn tokenizes_tibetan_syllables_with_delimiters() {
        assert_eq!(tokenize_syllables("བཀྲ་ཤིས།"), vec!["བཀྲ་", "ཤིས།"]);
    }

    #[test]
    #[ignore = "requires Python with botok installed"]
    fn tokenizes_with_botok_when_installed() {
        let tokenized = tokenize_batch_with_botok(&["བཀྲ་ཤིས་བདེ་ལེགས།"]).unwrap();

        assert_eq!(tokenized.len(), 1);
        assert!(tokenized[0].len() > 1);
    }

    #[test]
    #[ignore = "requires Python with pyewts installed"]
    fn transliterates_with_pyewts_when_installed() {
        assert_eq!(
            transliterate_batch_to_wylie(&["བཀྲ་ཤིས"]).unwrap(),
            vec!["bkra shis".to_string()]
        );
    }
}
