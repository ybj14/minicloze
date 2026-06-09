use crate::sentence::Sentence;
use crate::tibetan::{self, TibetanToken};
use std::error::Error;

const NON_SPACED: [&str; 12] = [
    "cmn", "lzh", "hak", "cjy", "nan", "hsn", "gan", "jpn", "tha", "khm", "lao", "mya",
];

const TIBETAN: &str = "bod";

pub fn prepare_sentences(
    language: &str,
    sentences: &mut [Sentence],
) -> Result<(), Box<dyn Error + Send + Sync>> {
    if language != TIBETAN {
        return Ok(());
    }

    let translations = sentences
        .iter()
        .map(|sentence| {
            sentence
                .get_translation()
                .map(|translation| translation.text.as_str())
                .unwrap_or("")
        })
        .collect::<Vec<_>>();

    let tokenized = match tibetan::tokenize_batch_with_botok(&translations) {
        Ok(tokenized) => tokenized,
        Err(_err) if tibetan_fallback_enabled() => translations
            .iter()
            .map(|translation| {
                tibetan::tokenize_syllables(translation)
                    .into_iter()
                    .map(|text| TibetanToken {
                        text,
                        wylie: String::new(),
                    })
                    .collect()
            })
            .collect(),
        Err(err) => return Err(err),
    };

    for (sentence, words) in sentences.iter_mut().zip(tokenized) {
        sentence.set_tokenized_translation(words);
    }

    Ok(())
}

pub fn tokenize_prompt_text(language: &str, text: &str) -> Vec<String> {
    if NON_SPACED.contains(&language) {
        text.trim().chars().map(|ch| ch.to_string()).collect()
    } else if language == TIBETAN {
        tibetan::tokenize_syllables(text)
    } else {
        text.trim()
            .split_inclusive(' ')
            .map(std::string::ToString::to_string)
            .collect()
    }
}

fn tibetan_fallback_enabled() -> bool {
    std::env::var("MINICLOZE_TIBETAN_FALLBACK")
        .map(|value| value == "syllable")
        .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tokenizes_spaced_languages_on_spaces() {
        assert_eq!(
            tokenize_prompt_text("deu", "Das ist gut."),
            vec!["Das ", "ist ", "gut."]
        );
    }

    #[test]
    fn tokenizes_non_spaced_languages_as_characters() {
        assert_eq!(
            tokenize_prompt_text("jpn", "日本語"),
            vec!["日", "本", "語"]
        );
    }

    #[test]
    fn tibetan_syllable_fallback_does_not_return_the_whole_sentence() {
        let words = tokenize_prompt_text("bod", "བཀྲ་ཤིས་བདེ་ལེགས།");

        assert!(words.len() > 1);
        assert_ne!(words, vec!["བཀྲ་ཤིས་བདེ་ལེགས།"]);
    }
}
