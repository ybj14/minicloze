pub mod game;
pub mod langs;
mod local_corpora;
pub mod sentence;
pub mod srs;
mod tibetan;
pub mod tokenizer;

// handles wiktionary lookup
pub mod wiktionary {
    pub fn wiktionary_try_open(lookup: String, language: &str) {
        webbrowser::open(&generate_url(&lookup, language)).unwrap();
    }

    pub fn generate_url(lookup: &str, language: &str) -> String {
        let lang_codes = crate::langs::propagate();
        let language = crate::local_corpora::lookup_language(language);

        let mut full_language = String::new();
        // gets key from value
        for pair in lang_codes {
            if pair.1 == language {
                full_language = pair.0.to_string();
            }
        }

        let titlecase_language = format!(
            "{}{}",
            full_language[..1].to_uppercase(),
            &full_language[1..]
        );

        [
            "https://en.wiktionary.org/wiki/",
            lookup.trim(),
            "#",
            titlecase_language.as_str(),
        ]
        .join("")
    }
}
