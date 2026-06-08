// logic which handles parsing a raw JSON from tatoeba into sentences

use rand::{thread_rng, Rng};
use serde::{Deserialize, Serialize};
use std::error::Error;

const NON_SPACED: [&str; 12] = [
    "cmn", "lzh", "hak", "cjy", "nan", "hsn", "gan", "jpn", "tha", "khm", "lao", "mya",
];

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
}

impl Sentence {
    // get the sentence's translation
    pub fn get_translation(&self) -> Option<&Translation> {
        self.translations.first()
    }

    // split string into vec of words, depends on whether the language uses spaces or not (e.g.
    // japanese is not spaced)
    pub fn as_words(&self, language: &str, inverse: bool) -> Vec<String> {
        let translation = if inverse {
            &self.text
        } else {
            &self.get_translation().unwrap().text
        };

        let words: Vec<String> = if NON_SPACED.contains(&language) {
            let char_strings = translation.trim().chars().map(|x| x.to_string());
            char_strings.collect::<Vec<String>>()
        } else {
            translation
                .trim()
                .split_inclusive(' ')
                .map(std::string::ToString::to_string)
                .collect::<Vec<String>>()
        };

        words
    }

    // splits a sentence into a prompt consisting of three parts
    pub fn generate_prompt(&self, language: &str, inverse: bool) -> Prompt {
        let words: Vec<String> = self.as_words(language, inverse);
        let halved = words.split_at(thread_rng().gen_range(0..words.len()));

        let word = remove_punctuation(&halved.1[0]);

        Prompt {
            first_half: halved.0.join(""),
            word,
            second_half: halved.1[1..].join(""),
        }
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
    word.replace(
        &[
            '(', ')', ',', '.', ';', ':', '?', '¿', '!', '¡', '"', '«', '»', '。', ' ',
        ][..],
        "",
    )
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
}
