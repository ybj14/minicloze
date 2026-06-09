// logic which handles parsing a raw JSON from tatoeba into sentences

use crate::tibetan::TibetanToken;
use crate::tokenizer;
use rand::{thread_rng, Rng};
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
    #[serde(skip)]
    tokenized_translation: Option<Vec<TibetanToken>>,
}

// represents a translation. id is the tatoeba id of the translation
#[derive(Deserialize, Serialize, Clone, Debug)]
pub struct Translation {
    id: i32,
    pub text: String,
}

#[derive(Clone)]
pub struct Prompt {
    pub first_half: String,
    pub word: String,
    pub second_half: String,
    pub first_half_transliteration: Option<String>,
    pub word_transliteration: Option<String>,
    pub second_half_transliteration: Option<String>,
}

#[derive(Clone)]
struct PromptToken {
    text: String,
    transliteration: Option<String>,
}

impl Sentence {
    // get the sentence's translation
    pub fn get_translation(&self) -> Option<&Translation> {
        self.translations.first()
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
                        transliteration: if token.wylie.trim().is_empty() {
                            None
                        } else {
                            Some(token.wylie.clone())
                        },
                    })
                    .collect();
            }
        }

        self.as_words(language, inverse)
            .into_iter()
            .map(|text| PromptToken {
                text,
                transliteration: None,
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
        let word_index = if candidates.is_empty() {
            0
        } else {
            candidates[thread_rng().gen_range(0..candidates.len())]
        };
        let halved = words.split_at(word_index);

        let word = remove_punctuation(&words[word_index].text);

        Prompt {
            first_half: join_prompt_token_text(halved.0),
            word,
            second_half: join_prompt_token_text(&words[word_index + 1..]),
            first_half_transliteration: join_prompt_token_transliteration(halved.0),
            word_transliteration: words[word_index]
                .transliteration
                .as_deref()
                .map(remove_transliteration_punctuation)
                .filter(|wylie| !wylie.is_empty()),
            second_half_transliteration: join_prompt_token_transliteration(
                &words[word_index + 1..],
            ),
        }
    }
}

fn join_prompt_token_text(tokens: &[PromptToken]) -> String {
    tokens
        .iter()
        .map(|token| token.text.as_str())
        .collect::<String>()
}

fn join_prompt_token_transliteration(tokens: &[PromptToken]) -> Option<String> {
    let transliteration = tokens
        .iter()
        .filter_map(|token| token.transliteration.as_deref())
        .collect::<String>();

    if transliteration.trim().is_empty() {
        None
    } else {
        Some(transliteration)
    }
}

// language: the language to request from tatoeba
pub async fn generate_sentences(
    language: &str,
) -> Result<Vec<Sentence>, Box<dyn Error + Send + Sync>> {
    // where the initial request happens
    let mut sentences = sentences_http_request(language).await?;

    let len = sentences.len();

    // makes sure we always get 10 sentences
    if len != 10 {
        let difference = 10 - len;
        // makes more requests if required
        let mut sentences_difference = sentences_http_request(language)
            .await?
            .into_iter()
            .take(difference)
            .collect::<Vec<_>>();

        sentences.append(&mut sentences_difference);
    }
    tokenizer::prepare_sentences(language, &mut sentences)?;
    Ok(sentences)
}

// language: the language to request from tatoeba
pub async fn sentences_http_request(
    language: &str,
) -> Result<Vec<Sentence>, Box<dyn Error + Send + Sync>> {
    let request = format!(
        "https://api.tatoeba.org/v1/sentences?lang=eng&trans:lang={language}&is_orphan=no&is_unapproved=no&trans:is_orphan=no&trans:is_unapproved=no&sort=random&limit=10&showtrans:lang={language}"
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
            '(', ')', ',', '.', ';', ':', '?', '¿', '!', '¡', '"', '«', '»', '。', ' ', '།', '༎',
            '༏', '༐', '༑', '༔',
        ][..],
        "",
    );

    cleaned
        .trim_matches(|ch| ch == '་' || ch == '༌')
        .to_string()
}

pub fn remove_transliteration_punctuation(word: &str) -> String {
    word.trim()
        .trim_matches(&['(', ')', ',', '.', ';', ':', '?', '!', '"', '/', ' '][..])
        .to_string()
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
            tokenized_translation: None,
        };
        sentence.set_tokenized_translation(vec![
            TibetanToken {
                text: "ཞོགས་པ་".to_string(),
                wylie: "zhogs pa ".to_string(),
            },
            TibetanToken {
                text: "བདེ་ལེགས".to_string(),
                wylie: "bde legs".to_string(),
            },
            TibetanToken {
                text: "།".to_string(),
                wylie: "/".to_string(),
            },
        ]);

        for _ in 0..20 {
            let prompt = sentence.generate_prompt("bod", false);

            assert_ne!(prompt.word, "ཞོགས་པ་བདེ་ལེགས");
            assert!(prompt.word == "ཞོགས་པ" || prompt.word == "བདེ་ལེགས");
            assert!(
                prompt.word_transliteration == Some("zhogs pa".to_string())
                    || prompt.word_transliteration == Some("bde legs".to_string())
            );
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
}
