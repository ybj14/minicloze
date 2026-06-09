use crate::{
    sentence::{remove_transliteration_punctuation, Sentence, WordExplanation},
    tibetan,
};
use serde::Deserialize;
use std::collections::HashMap;

pub struct LocalCorpus {
    pub base_language: &'static str,
    pub json: &'static str,
}

pub struct LocalVocabulary {
    pub json: &'static str,
}

struct LocalExplanations {
    json: &'static str,
}

#[derive(Deserialize)]
struct ExplanationJson {
    data: Vec<SentenceExplanation>,
}

#[derive(Deserialize)]
struct SentenceExplanation {
    id: i32,
    words: Vec<WordExplanation>,
}

pub fn corpus_for_language(language: &str) -> Option<LocalCorpus> {
    match language {
        "mon-a1" => Some(LocalCorpus {
            base_language: "mon",
            json: include_str!("../corpora/mongolian_a1.json"),
        }),
        "bod-a1" => Some(LocalCorpus {
            base_language: "bod",
            json: include_str!("../corpora/tibetan_a1.json"),
        }),
        _ => None,
    }
}

pub fn vocabulary_for_language(language: &str) -> Option<LocalVocabulary> {
    match language {
        "mon-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/mongolian_a1_vocab.json"),
        }),
        "bod-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/tibetan_a1_vocab.json"),
        }),
        _ => None,
    }
}

pub fn attach_word_explanations(language: &str, sentences: &mut [Sentence]) -> Result<(), String> {
    let Some(explanations) = explanations_for_language(language) else {
        return Ok(());
    };

    let parsed: ExplanationJson =
        serde_json::from_str(explanations.json).map_err(crate::sentence::convert_error)?;
    let mut by_id = parsed
        .data
        .into_iter()
        .map(|item| (item.id, item.words))
        .collect::<HashMap<_, _>>();

    for sentence in sentences {
        if let Some(mut explanations) = by_id.remove(&sentence.id()) {
            add_wylie_to_explanations(language, &mut explanations);
            sentence.set_word_explanations(explanations);
        }
    }

    Ok(())
}

fn add_wylie_to_explanations(language: &str, explanations: &mut [WordExplanation]) {
    if lookup_language(language) != "bod" {
        return;
    }

    let indices = explanations
        .iter()
        .enumerate()
        .filter_map(|(index, explanation)| {
            explanation
                .wylie
                .as_ref()
                .map(|wylie| wylie.trim().is_empty())
                .unwrap_or(true)
                .then_some(index)
        })
        .collect::<Vec<_>>();
    let words = indices
        .iter()
        .map(|index| explanations[*index].word.as_str())
        .collect::<Vec<_>>();

    let Ok(wylies) = tibetan::transliterate_batch_to_wylie(&words) else {
        return;
    };

    for (index, wylie) in indices.into_iter().zip(wylies) {
        let wylie = remove_transliteration_punctuation(&wylie);
        if !wylie.is_empty() {
            explanations[index].wylie = Some(wylie);
        }
    }
}

fn explanations_for_language(language: &str) -> Option<LocalExplanations> {
    match language {
        "mon-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/mongolian_a1_explanations.json"),
        }),
        "bod-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/tibetan_a1_explanations.json"),
        }),
        _ => None,
    }
}

pub fn lookup_language(language: &str) -> &str {
    match language {
        "mon-a1" => "mon",
        "bod-a1" => "bod",
        _ => language,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sentence;

    #[test]
    fn local_explanations_cover_local_corpora() {
        for language in ["mon-a1", "bod-a1"] {
            let corpus = corpus_for_language(language).expect("local corpus exists");
            let explanations =
                explanations_for_language(language).expect("local explanations exist");
            let sentences = sentence::parse(corpus.json).expect("corpus parses");
            let parsed: ExplanationJson =
                serde_json::from_str(explanations.json).expect("explanations parse");

            let sentence_ids = sentences
                .iter()
                .map(sentence::Sentence::id)
                .collect::<Vec<_>>();
            let explanation_ids = parsed.data.iter().map(|item| item.id).collect::<Vec<_>>();

            assert_eq!(explanation_ids, sentence_ids);
            assert!(parsed
                .data
                .iter()
                .all(|item| item.words.iter().all(|word| {
                    !word.word.trim().is_empty() && !word.gloss.trim().is_empty()
                })));
        }
    }
}
