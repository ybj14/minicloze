// logic which handles parsing a raw JSON from tatoeba into sentences

use crate::local_corpora;
use crate::tibetan::{self, TibetanToken};
use crate::tokenizer;
use rand::{seq::SliceRandom, thread_rng, Rng};
use serde::{Deserialize, Serialize};
use std::error::Error;

// represents the entire JSON response from Tatoeba. results is the sentences found.
#[derive(Deserialize, Serialize)]
pub struct Json {
    #[serde(alias = "results")]
    pub data: Vec<Sentence>,
}

// represents a sentence. id is the tatoeba id of the sentence, not used anywhere currently
#[derive(Deserialize, Serialize, Clone, Debug)]
pub struct Sentence {
    id: i32,
    pub text: String,
    pub translations: Vec<Translation>,
    #[serde(default)]
    cloze_word: Option<String>,
    #[serde(default)]
    pub word_explanations: Vec<WordExplanation>,
    #[serde(skip)]
    tokenized_translation: Option<Vec<TibetanToken>>,
}

// represents a translation. id is the tatoeba id of the translation
#[derive(Deserialize, Serialize, Clone, Debug)]
pub struct Translation {
    id: i32,
    pub text: String,
}

#[derive(Deserialize, Serialize, Clone, Debug, Eq, PartialEq)]
pub struct WordExplanation {
    pub word: String,
    pub gloss: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub note: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub wylie: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub thl: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub paiboon: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mlcts: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub okell: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transliteration: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transcription: Option<String>,
}

#[derive(Clone)]
pub struct Prompt {
    pub first_half: String,
    pub word: String,
    pub second_half: String,
    pub first_half_transliteration: Option<String>,
    pub word_transliteration: Option<String>,
    pub second_half_transliteration: Option<String>,
    pub word_answer_transliterations: Vec<String>,
}

#[derive(Clone)]
struct PromptToken {
    text: String,
    transliteration: Option<String>,
    answer_transliterations: Vec<String>,
}

impl Sentence {
    pub fn id(&self) -> i32 {
        self.id
    }

    // get the sentence's translation
    pub fn get_translation(&self) -> Option<&Translation> {
        self.translations.first()
    }

    pub(crate) fn set_word_explanations(&mut self, explanations: Vec<WordExplanation>) {
        self.word_explanations = explanations;
    }

    pub(crate) fn set_tokenized_translation(&mut self, words: Vec<TibetanToken>) {
        self.tokenized_translation = Some(words);
    }

    // split string into vec of words, depends on whether the language uses spaces or not (e.g.
    // japanese is not spaced)
    pub fn as_words(&self, language: &str, inverse: bool) -> Vec<String> {
        let translation = if inverse {
            &self.text
        } else {
            &self.get_translation().unwrap().text
        };

        if !inverse {
            if let Some(tokens) = &self.tokenized_translation {
                return tokens.iter().map(|token| token.text.clone()).collect();
            }
        }

        if inverse {
            tokenizer::tokenize_prompt_text("eng", translation)
        } else {
            tokenizer::tokenize_prompt_text(language, translation)
        }
    }

    fn as_prompt_tokens(&self, language: &str, inverse: bool) -> Vec<PromptToken> {
        if !inverse {
            if let Some(tokens) = &self.tokenized_translation {
                return tokens
                    .iter()
                    .map(|token| PromptToken {
                        text: token.text.clone(),
                        transliteration: token_preferred_transliteration(token),
                        answer_transliterations: token_answer_transliterations(token),
                    })
                    .collect();
            }
        }

        self.as_words(language, inverse)
            .into_iter()
            .map(|text| PromptToken {
                text,
                transliteration: None,
                answer_transliterations: Vec::new(),
            })
            .collect()
    }

    // splits a sentence into a prompt consisting of three parts
    pub fn generate_prompt(&self, language: &str, inverse: bool) -> Prompt {
        let words = self.as_prompt_tokens(language, inverse);
        let candidates = words
            .iter()
            .enumerate()
            .filter_map(|(index, word)| {
                if remove_punctuation(&word.text).is_empty() {
                    None
                } else {
                    Some(index)
                }
            })
            .collect::<Vec<_>>();
        let word_index = self
            .preferred_cloze_index(&words, &candidates, inverse)
            .unwrap_or_else(|| {
                if candidates.is_empty() {
                    0
                } else {
                    candidates[thread_rng().gen_range(0..candidates.len())]
                }
            });
        let halved = words.split_at(word_index);

        let word = remove_punctuation(&words[word_index].text);
        let trailing = trailing_whitespace(&words[word_index].text);

        Prompt {
            first_half: join_prompt_token_text(halved.0),
            word,
            second_half: format!(
                "{}{}",
                trailing,
                join_prompt_token_text(&words[word_index + 1..])
            ),
            first_half_transliteration: join_prompt_token_transliteration(halved.0),
            word_transliteration: words[word_index]
                .transliteration
                .as_deref()
                .map(remove_transliteration_punctuation)
                .filter(|wylie| !wylie.is_empty()),
            second_half_transliteration: join_prompt_token_transliteration(
                &words[word_index + 1..],
            ),
            word_answer_transliterations: words[word_index].answer_transliterations.clone(),
        }
    }

    fn preferred_cloze_index(
        &self,
        words: &[PromptToken],
        candidates: &[usize],
        inverse: bool,
    ) -> Option<usize> {
        if inverse {
            return None;
        }

        let target = self.cloze_word.as_deref()?;
        let target = normalize_cloze_match(target);

        candidates
            .iter()
            .copied()
            .find(|index| normalize_cloze_match(&words[*index].text) == target)
    }
}

fn token_preferred_transliteration(token: &TibetanToken) -> Option<String> {
    [
        &token.thl,
        &token.paiboon,
        &token.okell,
        &token.transcription,
        &token.mlcts,
        &token.transliteration,
        &token.wylie,
    ]
    .into_iter()
    .find_map(|value| {
        let value = value.trim();
        (!value.is_empty()).then(|| value.to_string())
    })
}

fn token_answer_transliterations(token: &TibetanToken) -> Vec<String> {
    let mut values = Vec::new();
    push_unique_transliteration(&mut values, &token.thl);
    push_unique_transliteration(&mut values, &token.wylie);
    push_unique_transliteration(&mut values, &token.paiboon);
    push_unique_transliteration(&mut values, &token.okell);
    push_unique_transliteration(&mut values, &token.mlcts);
    push_unique_transliteration(&mut values, &token.transcription);
    push_unique_transliteration(&mut values, &token.transliteration);
    values
}

fn push_unique_transliteration(values: &mut Vec<String>, value: &str) {
    let value = remove_transliteration_punctuation(value);
    if !value.is_empty() && !values.iter().any(|existing| existing == &value) {
        values.push(value);
    }
}

fn trailing_whitespace(text: &str) -> &str {
    let trimmed = text.trim_end_matches(char::is_whitespace);
    &text[trimmed.len()..]
}

fn leading_whitespace(text: &str) -> &str {
    let trimmed = text.trim_start_matches(char::is_whitespace);
    &text[..text.len() - trimmed.len()]
}

fn join_prompt_token_text(tokens: &[PromptToken]) -> String {
    tokens
        .iter()
        .map(|token| token.text.as_str())
        .collect::<String>()
}

fn join_prompt_token_transliteration(tokens: &[PromptToken]) -> Option<String> {
    let parts = tokens
        .iter()
        .filter_map(|token| token.transliteration.as_deref())
        .map(str::trim)
        .filter(|token| !token.is_empty())
        .collect::<Vec<_>>();

    if parts.is_empty() {
        None
    } else {
        Some(parts.join(" "))
    }
}

// language: the language to request from tatoeba
pub async fn generate_sentences(
    language: &str,
) -> Result<Vec<Sentence>, Box<dyn Error + Send + Sync>> {
    generate_sentences_with_count(language, 10).await
}

pub async fn generate_sentences_with_count(
    language: &str,
    count: usize,
) -> Result<Vec<Sentence>, Box<dyn Error + Send + Sync>> {
    let count = count.max(1);

    if let Some(mut sentences) = local_sentence_pool(language)? {
        sentences.shuffle(&mut thread_rng());
        sentences.truncate(count);
        prepare_local_sentences(language, &mut sentences)?;
        return Ok(sentences);
    }

    // where the initial request happens
    let mut sentences = sentences_http_request_with_limit(language, count).await?;

    // makes sure we always get 10 sentences
    while sentences.len() < count {
        let difference = count - sentences.len();
        // makes more requests if required
        let mut sentences_difference = sentences_http_request_with_limit(language, difference)
            .await?
            .into_iter()
            .take(difference)
            .collect::<Vec<_>>();

        if sentences_difference.is_empty() {
            break;
        }

        sentences.append(&mut sentences_difference);
    }
    sentences.truncate(count);
    tokenizer::prepare_sentences(language, &mut sentences)?;
    Ok(sentences)
}

pub fn is_local_language(language: &str) -> bool {
    local_corpora::corpus_for_language(language).is_some()
}

pub fn local_sentence_pool(
    language: &str,
) -> Result<Option<Vec<Sentence>>, Box<dyn Error + Send + Sync>> {
    let Some(corpus) = local_corpora::corpus_for_language(language) else {
        return Ok(None);
    };

    let sentences = parse(corpus.json)
        .map_err(|err| std::io::Error::new(std::io::ErrorKind::InvalidData, err))?;
    Ok(Some(sentences))
}

pub fn prepare_local_sentences(
    language: &str,
    sentences: &mut [Sentence],
) -> Result<(), Box<dyn Error + Send + Sync>> {
    let Some(corpus) = local_corpora::corpus_for_language(language) else {
        return Ok(());
    };

    local_corpora::attach_word_explanations(language, sentences)
        .map_err(|err| std::io::Error::new(std::io::ErrorKind::InvalidData, err))?;
    if let Err(err) = tokenizer::prepare_sentences(corpus.base_language, sentences) {
        if corpus.base_language == "bod" {
            prepare_local_tibetan_syllable_fallback(sentences);
        } else {
            return Err(err);
        }
    } else if corpus.base_language == "bod" {
        ensure_local_tibetan_cloze_targets(sentences);
    }
    if corpus.base_language == "tha"
        || corpus.base_language == "mya"
        || corpus.base_language == "khm"
        || corpus.base_language == "amh"
        || corpus.base_language == "hye"
        || corpus.base_language == "kat"
    {
        prepare_local_explanation_tokens(
            sentences,
            corpus.base_language == "mya"
                || corpus.base_language == "amh"
                || corpus.base_language == "hye"
                || corpus.base_language == "kat",
        );
    } else if corpus.base_language != "bod" && tokenizer::is_non_spaced(corpus.base_language) {
        prepare_local_non_spaced_target_tokens(corpus.base_language, sentences);
    } else if corpus.base_language != "bod" {
        prepare_local_spaced_target_tokens(corpus.base_language, sentences);
    }

    Ok(())
}

// language: the language to request from tatoeba
pub async fn sentences_http_request(
    language: &str,
) -> Result<Vec<Sentence>, Box<dyn Error + Send + Sync>> {
    sentences_http_request_with_limit(language, 10).await
}

pub async fn sentences_http_request_with_limit(
    language: &str,
    limit: usize,
) -> Result<Vec<Sentence>, Box<dyn Error + Send + Sync>> {
    let request = format!(
        "https://api.tatoeba.org/v1/sentences?lang=eng&trans:lang={language}&is_orphan=no&is_unapproved=no&trans:is_orphan=no&trans:is_unapproved=no&sort=random&limit={limit}&showtrans:lang={language}"
    );
    let response = reqwest::get(request).await?.text().await?;

    let resp_str = response.as_str();

    let sentences =
        parse(resp_str).map_err(|err| std::io::Error::new(std::io::ErrorKind::InvalidData, err))?;
    Ok(sentences)
}

// converts a serde error into a string
pub fn convert_error(err: serde_json::Error) -> String {
    format!(
        "{:#?} error thrown by serde at {}:{}.",
        err.classify(),
        err.line(),
        err.column()
    )
}

// parse plaintext JSON response string into a Vec of Sentences results: the JSON
pub fn parse(results: &str) -> Result<Vec<Sentence>, String> {
    let sentences: Json = serde_json::from_str(results).map_err(convert_error)?;
    Ok(sentences.data)
}

pub fn remove_punctuation(word: &str) -> String {
    let cleaned = word.replace(
        &[
            '(', ')', ',', '.', ';', ':', '?', '¿', '!', '¡', '"', '«', '»', '。', '།', '༎', '༏',
            '༐', '༑', '༔', '።', '፣', '፤', '፥', '፦', '፧', '։', '՞', '՜', '՛', '՝', '჻',
        ][..],
        "",
    );

    cleaned
        .trim()
        .trim_matches(|ch| ch == '་' || ch == '༌')
        .to_string()
}

pub fn remove_transliteration_punctuation(word: &str) -> String {
    word.trim()
        .trim_matches(&['(', ')', ',', '.', ';', ':', '?', '!', '"', '/', ' '][..])
        .to_string()
}

fn normalize_cloze_match(word: &str) -> String {
    remove_punctuation(word).to_lowercase()
}

fn prepare_local_tibetan_syllable_fallback(sentences: &mut [Sentence]) {
    for sentence in sentences {
        let Some(translation) = sentence.get_translation() else {
            continue;
        };
        let tokens =
            tokenize_tibetan_with_target(&translation.text, sentence.cloze_word.as_deref());
        sentence.set_tokenized_translation(tokens);
    }
}

fn ensure_local_tibetan_cloze_targets(sentences: &mut [Sentence]) {
    for sentence in sentences {
        let Some(target) = sentence.cloze_word.as_deref() else {
            continue;
        };
        let Some(tokens) = sentence.tokenized_translation.as_ref() else {
            continue;
        };
        let target = normalize_cloze_match(target);
        let has_target = tokens
            .iter()
            .any(|token| normalize_cloze_match(&token.text) == target);

        if !has_target {
            let Some(translation) = sentence.get_translation() else {
                continue;
            };
            let tokens =
                tokenize_tibetan_with_target(&translation.text, sentence.cloze_word.as_deref());
            sentence.set_tokenized_translation(tokens);
        }
    }
}

fn tokenize_tibetan_with_target(text: &str, target: Option<&str>) -> Vec<TibetanToken> {
    let Some(target) = target else {
        return tibetan_tokens_with_wylie(tibetan::tokenize_syllables(text));
    };

    let Some(index) = text.find(target) else {
        return tibetan_tokens_with_wylie(tibetan::tokenize_syllables(text));
    };

    let before = &text[..index];
    let after_start = index + target.len();
    let after = &text[after_start..];

    let mut token_texts = tibetan::tokenize_syllables(before);
    token_texts.push(target.to_string());
    token_texts.extend(tibetan::tokenize_syllables(after));
    tibetan_tokens_with_wylie(token_texts)
}

fn prepare_local_non_spaced_target_tokens(language: &str, sentences: &mut [Sentence]) {
    for sentence in sentences {
        let Some(target) = sentence.cloze_word.as_deref() else {
            continue;
        };
        let Some(translation) = sentence.get_translation() else {
            continue;
        };
        if !translation.text.contains(target) {
            continue;
        }

        let tokens = tokenize_non_spaced_with_target(language, &translation.text, target);
        sentence.set_tokenized_translation(tokens);
    }
}

fn prepare_local_spaced_target_tokens(language: &str, sentences: &mut [Sentence]) {
    for sentence in sentences {
        let Some(target) = sentence.cloze_word.as_deref() else {
            continue;
        };
        if !target.chars().any(char::is_whitespace) {
            continue;
        }
        let Some(translation) = sentence.get_translation() else {
            continue;
        };
        if !translation.text.contains(target) {
            continue;
        }

        let tokens = tokenize_non_spaced_with_target(language, &translation.text, target);
        sentence.set_tokenized_translation(tokens);
    }
}

fn prepare_local_explanation_tokens(sentences: &mut [Sentence], preserve_spaces: bool) {
    for sentence in sentences {
        if sentence.word_explanations.is_empty() {
            continue;
        }
        let word_count = sentence.word_explanations.len();
        let tokens = sentence
            .word_explanations
            .iter()
            .enumerate()
            .map(|(index, explanation)| TibetanToken {
                text: if preserve_spaces && index + 1 < word_count {
                    format!("{} ", explanation.word)
                } else {
                    explanation.word.clone()
                },
                wylie: explanation.wylie.clone().unwrap_or_default(),
                thl: explanation.thl.clone().unwrap_or_default(),
                paiboon: explanation.paiboon.clone().unwrap_or_default(),
                mlcts: explanation.mlcts.clone().unwrap_or_default(),
                okell: explanation.okell.clone().unwrap_or_default(),
                transliteration: explanation.transliteration.clone().unwrap_or_default(),
                transcription: explanation.transcription.clone().unwrap_or_default(),
            })
            .collect::<Vec<_>>();
        sentence.set_tokenized_translation(tokens);
    }
}

fn tokenize_non_spaced_with_target(language: &str, text: &str, target: &str) -> Vec<TibetanToken> {
    let Some(index) = text.find(target) else {
        return tokens_without_wylie(tokenizer::tokenize_prompt_text(language, text));
    };

    let before = &text[..index];
    let after = &text[index + target.len()..];
    let target_trailing = leading_whitespace(after);
    let after = &after[target_trailing.len()..];
    let mut token_texts = tokenizer::tokenize_prompt_text(language, before);
    if let Some(last) = token_texts.last_mut() {
        let whitespace = trailing_whitespace(before);
        if !whitespace.is_empty() && !last.ends_with(whitespace) {
            last.push_str(whitespace);
        }
    }
    token_texts.push(format!("{target}{target_trailing}"));
    token_texts.extend(tokenizer::tokenize_prompt_text(language, after));
    tokens_without_wylie(token_texts)
}

fn tibetan_tokens_with_wylie(texts: Vec<String>) -> Vec<TibetanToken> {
    let text_refs = texts.iter().map(String::as_str).collect::<Vec<_>>();
    let wylies = tibetan::transliterate_batch_to_wylie(&text_refs).ok();
    let thls = tibetan::transliterate_batch_to_thl(&text_refs).ok();

    texts
        .into_iter()
        .enumerate()
        .map(|(index, text)| TibetanToken {
            text,
            wylie: wylies
                .as_ref()
                .and_then(|items| items.get(index))
                .cloned()
                .unwrap_or_default(),
            thl: thls
                .as_ref()
                .and_then(|items| items.get(index))
                .cloned()
                .unwrap_or_default(),
            paiboon: String::new(),
            mlcts: String::new(),
            okell: String::new(),
            transliteration: String::new(),
            transcription: String::new(),
        })
        .collect()
}

fn tokens_without_wylie(texts: Vec<String>) -> Vec<TibetanToken> {
    texts
        .into_iter()
        .map(|text| TibetanToken {
            text,
            wylie: String::new(),
            thl: String::new(),
            paiboon: String::new(),
            mlcts: String::new(),
            okell: String::new(),
            transliteration: String::new(),
            transcription: String::new(),
        })
        .collect()
}

#[allow(dead_code)]
fn tibetan_token_without_wylie(text: String) -> TibetanToken {
    TibetanToken {
        text,
        wylie: String::new(),
        thl: String::new(),
        paiboon: String::new(),
        mlcts: String::new(),
        okell: String::new(),
        transliteration: String::new(),
        transcription: String::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_tatoeba_v1_sentence_search_response() {
        let response = r#"{
            "data": [
                {
                    "id": 4471292,
                    "text": "Mary took the cookies out of the oven.",
                    "lang": "eng",
                    "script": null,
                    "license": "CC BY 2.0 FR",
                    "owner": "Hybrid",
                    "is_unapproved": false,
                    "translations": [
                        {
                            "id": 4473114,
                            "text": "Maria holte die Kekse aus dem Ofen.",
                            "lang": "deu",
                            "script": null,
                            "license": "CC BY 2.0 FR",
                            "owner": "Pfirsichbaeumchen",
                            "is_unapproved": false,
                            "is_direct": true
                        }
                    ]
                }
            ],
            "paging": {}
        }"#;

        let sentences = parse(response).expect("v1 responses should parse");

        assert_eq!(sentences.len(), 1);
        assert_eq!(sentences[0].text, "Mary took the cookies out of the oven.");
        assert_eq!(
            sentences[0]
                .get_translation()
                .map(|translation| translation.text.as_str()),
            Some("Maria holte die Kekse aus dem Ofen.")
        );
    }

    #[test]
    fn generate_prompt_uses_cached_tibetan_words() {
        let mut sentence = Sentence {
            id: 1,
            text: "Good morning.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "ཞོགས་པ་བདེ་ལེགས།".to_string(),
            }],
            cloze_word: None,
            word_explanations: Vec::new(),
            tokenized_translation: None,
        };
        sentence.set_tokenized_translation(vec![
            TibetanToken {
                text: "ཞོགས་པ་".to_string(),
                wylie: "zhogs pa ".to_string(),
                thl: "zhok pa".to_string(),
                paiboon: String::new(),
                mlcts: String::new(),
                okell: String::new(),
                transliteration: String::new(),
                transcription: String::new(),
            },
            TibetanToken {
                text: "བདེ་ལེགས".to_string(),
                wylie: "bde legs".to_string(),
                thl: "dé lek".to_string(),
                paiboon: String::new(),
                mlcts: String::new(),
                okell: String::new(),
                transliteration: String::new(),
                transcription: String::new(),
            },
            TibetanToken {
                text: "།".to_string(),
                wylie: "/".to_string(),
                thl: String::new(),
                paiboon: String::new(),
                mlcts: String::new(),
                okell: String::new(),
                transliteration: String::new(),
                transcription: String::new(),
            },
        ]);

        for _ in 0..20 {
            let prompt = sentence.generate_prompt("bod", false);

            assert_ne!(prompt.word, "ཞོགས་པ་བདེ་ལེགས");
            assert!(prompt.word == "ཞོགས་པ" || prompt.word == "བདེ་ལེགས");
            assert!(
                prompt.word_transliteration == Some("zhok pa".to_string())
                    || prompt.word_transliteration == Some("dé lek".to_string())
            );
            assert!(prompt
                .word_answer_transliterations
                .iter()
                .any(|item| item == "zhogs pa" || item == "bde legs"));
        }
    }

    #[test]
    fn remove_punctuation_trims_tibetan_terminal_tseks() {
        assert_eq!(remove_punctuation("བཀྲ་ཤིས་"), "བཀྲ་ཤིས");
    }

    #[test]
    fn remove_transliteration_punctuation_trims_wylie_spacing_and_shad() {
        assert_eq!(remove_transliteration_punctuation("cig / "), "cig");
    }

    #[test]
    fn generate_prompt_prefers_configured_cloze_word() {
        let sentence = Sentence {
            id: 1,
            text: "The sun is warm.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "Нар дулаан байна.".to_string(),
            }],
            cloze_word: Some("нар".to_string()),
            word_explanations: Vec::new(),
            tokenized_translation: None,
        };

        let prompt = sentence.generate_prompt("mon", false);

        assert_eq!(prompt.word, "Нар");
    }

    #[test]
    fn generate_prompt_preserves_space_after_configured_cloze_word() {
        let sentence = Sentence {
            id: 1,
            text: "This is a bed.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "Ин кат аст.".to_string(),
            }],
            cloze_word: Some("кат".to_string()),
            word_explanations: Vec::new(),
            tokenized_translation: None,
        };

        let prompt = sentence.generate_prompt("tgk", false);

        assert_eq!(prompt.first_half, "Ин ");
        assert_eq!(prompt.word, "кат");
        assert_eq!(prompt.second_half, " аст.");
    }

    #[test]
    fn local_non_spaced_sentences_prefer_configured_cloze_word() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "ฉันดื่มน้ำ".to_string(),
            }],
            cloze_word: Some("น้ำ".to_string()),
            word_explanations: Vec::new(),
            tokenized_translation: None,
        }];

        prepare_local_non_spaced_target_tokens("tha", &mut sentences);
        let prompt = sentences[0].generate_prompt("tha", false);

        assert_eq!(prompt.first_half, "ฉันดื่ม");
        assert_eq!(prompt.word, "น้ำ");
        assert_eq!(prompt.second_half, "");
    }

    #[test]
    fn local_thai_explanation_tokens_provide_paiboon() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "ฉันดื่มน้ำ".to_string(),
            }],
            cloze_word: Some("น้ำ".to_string()),
            word_explanations: vec![
                WordExplanation {
                    word: "ฉัน".to_string(),
                    gloss: "I".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: Some("chǎn".to_string()),
                    mlcts: None,
                    okell: None,
                    transliteration: None,
                    transcription: None,
                },
                WordExplanation {
                    word: "ดื่ม".to_string(),
                    gloss: "drink".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: Some("dʉ̀ʉm".to_string()),
                    mlcts: None,
                    okell: None,
                    transliteration: None,
                    transcription: None,
                },
                WordExplanation {
                    word: "น้ำ".to_string(),
                    gloss: "water".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: Some("náam".to_string()),
                    mlcts: None,
                    okell: None,
                    transliteration: None,
                    transcription: None,
                },
            ],
            tokenized_translation: None,
        }];

        prepare_local_explanation_tokens(&mut sentences, false);
        let prompt = sentences[0].generate_prompt("tha", false);

        assert_eq!(prompt.first_half, "ฉันดื่ม");
        assert_eq!(prompt.word, "น้ำ");
        assert_eq!(prompt.word_transliteration, Some("náam".to_string()));
        assert_eq!(
            prompt.first_half_transliteration,
            Some("chǎn dʉ̀ʉm".to_string())
        );
    }

    #[test]
    fn local_burmese_explanation_tokens_provide_mlcts_and_okell() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "ကျွန်တော် ရေ သောက် တယ်။".to_string(),
            }],
            cloze_word: Some("ရေ".to_string()),
            word_explanations: vec![
                WordExplanation {
                    word: "ကျွန်တော်".to_string(),
                    gloss: "I".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: Some("kywan to".to_string()),
                    okell: Some("cuñto".to_string()),
                    transliteration: None,
                    transcription: None,
                },
                WordExplanation {
                    word: "ရေ".to_string(),
                    gloss: "water".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: Some("re".to_string()),
                    okell: Some("yei".to_string()),
                    transliteration: None,
                    transcription: None,
                },
                WordExplanation {
                    word: "သောက်".to_string(),
                    gloss: "drink".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: Some("sauk".to_string()),
                    okell: Some("thauʔ".to_string()),
                    transliteration: None,
                    transcription: None,
                },
                WordExplanation {
                    word: "တယ်".to_string(),
                    gloss: "sentence marker".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: Some("tai".to_string()),
                    okell: Some("te".to_string()),
                    transliteration: None,
                    transcription: None,
                },
            ],
            tokenized_translation: None,
        }];

        prepare_local_explanation_tokens(&mut sentences, true);
        let prompt = sentences[0].generate_prompt("mya", false);

        assert_eq!(prompt.first_half, "ကျွန်တော် ");
        assert_eq!(prompt.word, "ရေ");
        assert_eq!(prompt.word_transliteration, Some("yei".to_string()));
        assert_eq!(prompt.first_half_transliteration, Some("cuñto".to_string()));
        assert!(prompt
            .word_answer_transliterations
            .contains(&"re".to_string()));
    }

    #[test]
    fn local_khmer_explanation_tokens_provide_transcription_and_transliteration() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "ខ្ញុំផឹកទឹក។".to_string(),
            }],
            cloze_word: Some("ទឹក".to_string()),
            word_explanations: vec![
                WordExplanation {
                    word: "ខ្ញុំ".to_string(),
                    gloss: "I".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("khnhom".to_string()),
                    transcription: Some("khñom".to_string()),
                },
                WordExplanation {
                    word: "ផឹក".to_string(),
                    gloss: "drink".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("phœ̆k".to_string()),
                    transcription: Some("phək".to_string()),
                },
                WordExplanation {
                    word: "ទឹក".to_string(),
                    gloss: "water".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("tœ̆k".to_string()),
                    transcription: Some("tək".to_string()),
                },
            ],
            tokenized_translation: None,
        }];

        prepare_local_explanation_tokens(&mut sentences, false);
        let prompt = sentences[0].generate_prompt("khm", false);

        assert_eq!(prompt.first_half, "ខ្ញុំផឹក");
        assert_eq!(prompt.word, "ទឹក");
        assert_eq!(prompt.word_transliteration, Some("tək".to_string()));
        assert!(prompt
            .word_answer_transliterations
            .contains(&"tœ̆k".to_string()));
    }

    #[test]
    fn local_amharic_explanation_tokens_provide_transliteration() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "እኔ ውሃ እጠጣለሁ።".to_string(),
            }],
            cloze_word: Some("ውሃ".to_string()),
            word_explanations: vec![
                WordExplanation {
                    word: "እኔ".to_string(),
                    gloss: "I".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("enE".to_string()),
                    transcription: None,
                },
                WordExplanation {
                    word: "ውሃ".to_string(),
                    gloss: "water".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("wha".to_string()),
                    transcription: None,
                },
                WordExplanation {
                    word: "እጠጣለሁ".to_string(),
                    gloss: "I drink".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("eTeTalehu".to_string()),
                    transcription: None,
                },
            ],
            tokenized_translation: None,
        }];

        prepare_local_explanation_tokens(&mut sentences, true);
        let prompt = sentences[0].generate_prompt("amh", false);

        assert_eq!(prompt.first_half, "እኔ ");
        assert_eq!(prompt.word, "ውሃ");
        assert_eq!(prompt.word_transliteration, Some("wha".to_string()));
        assert_eq!(prompt.first_half_transliteration, Some("enE".to_string()));
    }

    #[test]
    fn local_armenian_explanation_tokens_provide_transliteration() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "ես ջուր խմում եմ։".to_string(),
            }],
            cloze_word: Some("ջուր".to_string()),
            word_explanations: vec![
                WordExplanation {
                    word: "ես".to_string(),
                    gloss: "I".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("es".to_string()),
                    transcription: None,
                },
                WordExplanation {
                    word: "ջուր".to_string(),
                    gloss: "water".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("jur".to_string()),
                    transcription: None,
                },
                WordExplanation {
                    word: "խմում եմ".to_string(),
                    gloss: "I drink".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("khmum em".to_string()),
                    transcription: None,
                },
            ],
            tokenized_translation: None,
        }];

        prepare_local_explanation_tokens(&mut sentences, true);
        let prompt = sentences[0].generate_prompt("hye", false);

        assert_eq!(prompt.first_half, "ես ");
        assert_eq!(prompt.word, "ջուր");
        assert_eq!(prompt.word_transliteration, Some("jur".to_string()));
        assert_eq!(prompt.first_half_transliteration, Some("es".to_string()));
    }

    #[test]
    fn local_georgian_explanation_tokens_provide_transliteration() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "მე წყალი ვსვამ.".to_string(),
            }],
            cloze_word: Some("წყალი".to_string()),
            word_explanations: vec![
                WordExplanation {
                    word: "მე".to_string(),
                    gloss: "I".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("me".to_string()),
                    transcription: None,
                },
                WordExplanation {
                    word: "წყალი".to_string(),
                    gloss: "water".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("ts'q'ali".to_string()),
                    transcription: None,
                },
                WordExplanation {
                    word: "ვსვამ".to_string(),
                    gloss: "I drink".to_string(),
                    note: None,
                    wylie: None,
                    thl: None,
                    paiboon: None,
                    mlcts: None,
                    okell: None,
                    transliteration: Some("vsvam".to_string()),
                    transcription: None,
                },
            ],
            tokenized_translation: None,
        }];

        prepare_local_explanation_tokens(&mut sentences, true);
        let prompt = sentences[0].generate_prompt("kat", false);

        assert_eq!(prompt.first_half, "მე ");
        assert_eq!(prompt.word, "წყალი");
        assert_eq!(prompt.word_transliteration, Some("ts'q'ali".to_string()));
        assert_eq!(prompt.first_half_transliteration, Some("me".to_string()));
    }

    #[test]
    fn local_spaced_sentences_can_blank_multiword_targets() {
        let mut sentences = vec![Sentence {
            id: 1,
            text: "I drink water because it is hot.".to_string(),
            translations: vec![Translation {
                id: 2,
                text: "Би ус ууж яагаад гэвэл халуун байна.".to_string(),
            }],
            cloze_word: Some("яагаад гэвэл".to_string()),
            word_explanations: Vec::new(),
            tokenized_translation: None,
        }];

        prepare_local_spaced_target_tokens("mon", &mut sentences);
        let prompt = sentences[0].generate_prompt("mon", false);

        assert_eq!(prompt.first_half, "Би ус ууж ");
        assert_eq!(prompt.word, "яагаад гэвэл");
        assert_eq!(prompt.second_half, " халуун байна.");
    }
}
