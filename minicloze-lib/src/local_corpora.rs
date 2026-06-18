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
        "mon-swadesh" => Some(LocalCorpus {
            base_language: "mon",
            json: include_str!("../corpora/mongolian_swadesh.json"),
        }),
        "bod-a1" => Some(LocalCorpus {
            base_language: "bod",
            json: include_str!("../corpora/tibetan_a1.json"),
        }),
        "bod-swadesh" => Some(LocalCorpus {
            base_language: "bod",
            json: include_str!("../corpora/tibetan_swadesh.json"),
        }),
        "tgk-a1" => Some(LocalCorpus {
            base_language: "tgk",
            json: include_str!("../corpora/tajik_a1.json"),
        }),
        "tgk-swadesh" => Some(LocalCorpus {
            base_language: "tgk",
            json: include_str!("../corpora/tajik_swadesh.json"),
        }),
        "tha-a1" => Some(LocalCorpus {
            base_language: "tha",
            json: include_str!("../corpora/thai_a1.json"),
        }),
        "tha-swadesh" => Some(LocalCorpus {
            base_language: "tha",
            json: include_str!("../corpora/thai_swadesh.json"),
        }),
        "mya-a1" => Some(LocalCorpus {
            base_language: "mya",
            json: include_str!("../corpora/burmese_a1.json"),
        }),
        "mya-swadesh" => Some(LocalCorpus {
            base_language: "mya",
            json: include_str!("../corpora/burmese_swadesh.json"),
        }),
        "khm-a1" => Some(LocalCorpus {
            base_language: "khm",
            json: include_str!("../corpora/khmer_a1.json"),
        }),
        "khm-swadesh" => Some(LocalCorpus {
            base_language: "khm",
            json: include_str!("../corpora/khmer_swadesh.json"),
        }),
        _ => None,
    }
}

pub fn vocabulary_for_language(language: &str) -> Option<LocalVocabulary> {
    match language {
        "mon-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/mongolian_a1_vocab.json"),
        }),
        "mon-swadesh" => Some(LocalVocabulary {
            json: include_str!("../corpora/mongolian_swadesh_vocab.json"),
        }),
        "bod-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/tibetan_a1_vocab.json"),
        }),
        "bod-swadesh" => Some(LocalVocabulary {
            json: include_str!("../corpora/tibetan_swadesh_vocab.json"),
        }),
        "tgk-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/tajik_a1_vocab.json"),
        }),
        "tgk-swadesh" => Some(LocalVocabulary {
            json: include_str!("../corpora/tajik_swadesh_vocab.json"),
        }),
        "tha-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/thai_a1_vocab.json"),
        }),
        "tha-swadesh" => Some(LocalVocabulary {
            json: include_str!("../corpora/thai_swadesh_vocab.json"),
        }),
        "mya-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/burmese_a1_vocab.json"),
        }),
        "mya-swadesh" => Some(LocalVocabulary {
            json: include_str!("../corpora/burmese_swadesh_vocab.json"),
        }),
        "khm-a1" => Some(LocalVocabulary {
            json: include_str!("../corpora/khmer_a1_vocab.json"),
        }),
        "khm-swadesh" => Some(LocalVocabulary {
            json: include_str!("../corpora/khmer_swadesh_vocab.json"),
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
            add_tibetan_transliterations_to_explanations(language, &mut explanations);
            sentence.set_word_explanations(explanations);
        }
    }

    Ok(())
}

fn add_tibetan_transliterations_to_explanations(
    language: &str,
    explanations: &mut [WordExplanation],
) {
    if lookup_language(language) != "bod" {
        return;
    }

    add_wylie_to_explanations(explanations);
    add_thl_to_explanations(explanations);
}

fn add_wylie_to_explanations(explanations: &mut [WordExplanation]) {
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

fn add_thl_to_explanations(explanations: &mut [WordExplanation]) {
    let indices = explanations
        .iter()
        .enumerate()
        .filter_map(|(index, explanation)| {
            explanation
                .thl
                .as_ref()
                .map(|thl| thl.trim().is_empty())
                .unwrap_or(true)
                .then_some(index)
        })
        .collect::<Vec<_>>();
    let words = indices
        .iter()
        .map(|index| explanations[*index].word.as_str())
        .collect::<Vec<_>>();

    let Ok(thls) = tibetan::transliterate_batch_to_thl(&words) else {
        return;
    };

    for (index, thl) in indices.into_iter().zip(thls) {
        let thl = remove_transliteration_punctuation(&thl);
        if !thl.is_empty() {
            explanations[index].thl = Some(thl);
        }
    }
}

fn explanations_for_language(language: &str) -> Option<LocalExplanations> {
    match language {
        "mon-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/mongolian_a1_explanations.json"),
        }),
        "mon-swadesh" => Some(LocalExplanations {
            json: include_str!("../corpora/mongolian_swadesh_explanations.json"),
        }),
        "bod-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/tibetan_a1_explanations.json"),
        }),
        "bod-swadesh" => Some(LocalExplanations {
            json: include_str!("../corpora/tibetan_swadesh_explanations.json"),
        }),
        "tgk-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/tajik_a1_explanations.json"),
        }),
        "tgk-swadesh" => Some(LocalExplanations {
            json: include_str!("../corpora/tajik_swadesh_explanations.json"),
        }),
        "tha-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/thai_a1_explanations.json"),
        }),
        "tha-swadesh" => Some(LocalExplanations {
            json: include_str!("../corpora/thai_swadesh_explanations.json"),
        }),
        "mya-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/burmese_a1_explanations.json"),
        }),
        "mya-swadesh" => Some(LocalExplanations {
            json: include_str!("../corpora/burmese_swadesh_explanations.json"),
        }),
        "khm-a1" => Some(LocalExplanations {
            json: include_str!("../corpora/khmer_a1_explanations.json"),
        }),
        "khm-swadesh" => Some(LocalExplanations {
            json: include_str!("../corpora/khmer_swadesh_explanations.json"),
        }),
        _ => None,
    }
}

pub fn lookup_language(language: &str) -> &str {
    match language {
        "mon-a1" | "mon-swadesh" => "mon",
        "bod-a1" | "bod-swadesh" => "bod",
        "tgk-a1" | "tgk-swadesh" => "tgk",
        "tha-a1" | "tha-swadesh" => "tha",
        "mya-a1" | "mya-swadesh" => "mya",
        "khm-a1" | "khm-swadesh" => "khm",
        _ => language,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sentence;

    #[test]
    fn local_explanations_cover_local_corpora() {
        for language in [
            "mon-a1",
            "mon-swadesh",
            "bod-a1",
            "bod-swadesh",
            "tgk-a1",
            "tgk-swadesh",
            "tha-a1",
            "tha-swadesh",
            "mya-a1",
            "mya-swadesh",
            "khm-a1",
            "khm-swadesh",
        ] {
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
