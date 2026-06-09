pub struct LocalCorpus {
    pub base_language: &'static str,
    pub json: &'static str,
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

pub fn lookup_language(language: &str) -> &str {
    match language {
        "mon-a1" => "mon",
        "bod-a1" => "bod",
        _ => language,
    }
}
