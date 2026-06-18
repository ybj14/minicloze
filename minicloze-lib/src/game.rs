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
    let _ = language;
    if let Some(transliteration) = &prompt.word_transliteration {
        return format!(
            "{} ({})",
            prompt.word.to_lowercase().trim(),
            transliteration
        );
    }

    prompt.word.to_lowercase().trim().to_string()
}

#[allow(dead_code)]
pub fn is_tibetan(language: &str) -> bool {
    local_corpora::lookup_language(language) == "bod"
}

pub fn answer_distance(guess: &str, prompt: &Prompt) -> usize {
    let native_distance = levenshtein(
        &remove_punctuation(&guess.trim().to_lowercase()),
        prompt.word.to_lowercase().trim(),
    );

    let normalized_guess = normalize_latin_answer(guess);
    if normalized_guess.is_empty() {
        return native_distance;
    }

    transliterated_answers(prompt)
        .into_iter()
        .map(|transliterated_word| levenshtein(&normalized_guess, &transliterated_word))
        .fold(native_distance, usize::min)
}

pub fn transliterated_answer(prompt: &Prompt) -> Option<String> {
    transliterated_answers(prompt).into_iter().next()
}

pub fn transliterated_answers(prompt: &Prompt) -> Vec<String> {
    let mut answers = Vec::new();
    let transliteration = prompt
        .word_transliteration
        .as_deref()
        .unwrap_or(&prompt.word);
    push_normalized_answer(&mut answers, transliteration);
    for transliteration in &prompt.word_answer_transliterations {
        push_normalized_answer(&mut answers, transliteration);
    }

    answers
}

fn push_normalized_answer(answers: &mut Vec<String>, answer: &str) {
    let normalized = normalize_latin_answer(answer);
    if !normalized.is_empty() && !answers.iter().any(|item| item == &normalized) {
        answers.push(normalized);
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
            word_answer_transliterations: transliteration
                .map(|item| vec![item.to_string()])
                .unwrap_or_default(),
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
    fn accepts_tibetan_thl_and_wylie_aliases() {
        let mut prompt = prompt_for("བཀྲ་ཤིས", Some("tra shi"));
        prompt
            .word_answer_transliterations
            .push("bkra shis".to_string());

        assert_eq!(answer_distance("tra shi", &prompt), 0);
        assert_eq!(answer_distance("bkra shis", &prompt), 0);
    }

    #[test]
    fn ignores_diacritics_in_latin_answers() {
        let prompt = prompt_for("été", None);

        assert_eq!(answer_distance("ete", &prompt), 0);
    }
}
