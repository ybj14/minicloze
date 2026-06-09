use crate::local_corpora;
use crate::sentence::{remove_punctuation, Prompt};
use deunicode::deunicode;
use levenshtein::levenshtein;
use serde::{Deserialize, Serialize};

pub const DISTANCE_FOR_CLOSE: usize = 3;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AnswerOutcome {
    Correct,
    Close,
    Wrong,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AnswerCheck {
    pub outcome: AnswerOutcome,
    pub distance: usize,
    pub answer: String,
}

pub fn check_answer(guess: &str, prompt: &Prompt, language: &str) -> AnswerCheck {
    let distance = answer_distance(guess, prompt);
    let outcome = if distance == 0 {
        AnswerOutcome::Correct
    } else if distance < DISTANCE_FOR_CLOSE {
        AnswerOutcome::Close
    } else {
        AnswerOutcome::Wrong
    };

    AnswerCheck {
        outcome,
        distance,
        answer: answer_with_transliteration(prompt, language),
    }
}

pub fn answer_with_transliteration(prompt: &Prompt, language: &str) -> String {
    if is_tibetan(language) {
        if let Some(transliteration) = &prompt.word_transliteration {
            return format!(
                "{} ({})",
                prompt.word.to_lowercase().trim(),
                transliteration
            );
        }
    }

    prompt.word.to_lowercase().trim().to_string()
}

pub fn is_tibetan(language: &str) -> bool {
    local_corpora::lookup_language(language) == "bod"
}

pub fn answer_distance(guess: &str, prompt: &Prompt) -> usize {
    let native_distance = levenshtein(
        &remove_punctuation(&guess.trim().to_lowercase()),
        prompt.word.to_lowercase().trim(),
    );

    let Some(transliterated_word) = transliterated_answer(prompt) else {
        return native_distance;
    };

    let normalized_guess = normalize_latin_answer(guess);
    if normalized_guess.is_empty() {
        return native_distance;
    }

    native_distance.min(levenshtein(&normalized_guess, &transliterated_word))
}

pub fn transliterated_answer(prompt: &Prompt) -> Option<String> {
    let transliteration = prompt
        .word_transliteration
        .as_deref()
        .unwrap_or(&prompt.word);
    let normalized = normalize_latin_answer(transliteration);

    if normalized.is_empty() {
        None
    } else {
        Some(normalized)
    }
}

pub fn normalize_latin_answer(answer: &str) -> String {
    deunicode(answer)
        .to_lowercase()
        .chars()
        .filter(|ch| ch.is_ascii_alphanumeric())
        .collect()
}

pub fn format_transliteration_cloze(first_half: &str, blank: &str, second_half: &str) -> String {
    let first_half = first_half.trim_end();
    let second_half = second_half.trim_start();

    match (first_half.is_empty(), second_half.is_empty()) {
        (true, true) => blank.to_string(),
        (true, false) => format!("{blank} {second_half}"),
        (false, true) => format!("{first_half} {blank}"),
        (false, false) => format!("{first_half} {blank} {second_half}"),
    }
}

#[derive(Deserialize)]
struct VocabularyEntry {
    word: String,
}

pub fn local_vocabulary_words(language: &str) -> Result<Vec<String>, String> {
    let Some(vocabulary) = local_corpora::vocabulary_for_language(language) else {
        return Ok(Vec::new());
    };

    serde_json::from_str::<Vec<VocabularyEntry>>(vocabulary.json)
        .map(|entries| entries.into_iter().map(|entry| entry.word).collect())
        .map_err(crate::sentence::convert_error)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn prompt_for(word: &str, transliteration: Option<&str>) -> Prompt {
        Prompt {
            first_half: String::new(),
            word: word.to_string(),
            second_half: String::new(),
            first_half_transliteration: None,
            word_transliteration: transliteration.map(str::to_string),
            second_half_transliteration: None,
        }
    }

    #[test]
    fn accepts_mongolian_cyrillic_latin_transliteration() {
        let prompt = prompt_for("дөрөв", None);

        assert_eq!(answer_distance("dorov", &prompt), 0);
    }

    #[test]
    fn accepts_tibetan_wylie_transliteration() {
        let prompt = prompt_for("བཀྲ་ཤིས", Some("bkra shis"));

        assert_eq!(answer_distance("bkra shis", &prompt), 0);
        assert_eq!(answer_distance("bkrashis", &prompt), 0);
    }

    #[test]
    fn ignores_diacritics_in_latin_answers() {
        let prompt = prompt_for("été", None);

        assert_eq!(answer_distance("ete", &prompt), 0);
    }
}
