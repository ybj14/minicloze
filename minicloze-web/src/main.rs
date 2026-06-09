use axum::{
    extract::{Path, State},
    http::{header, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use minicloze_lib::{
    game::{check_answer, local_vocabulary_words, AnswerCheck},
    langs::{language_code_for_input, language_label_for_code},
    sentence::{
        generate_sentences_with_count, local_sentence_pool, prepare_local_sentences, Prompt,
        Sentence, WordExplanation,
    },
    srs,
};
use rand::{seq::SliceRandom, thread_rng};
use serde::{Deserialize, Serialize};
use std::{
    collections::{HashMap, HashSet},
    env,
    net::{SocketAddr, TcpListener as StdTcpListener},
    sync::Arc,
};
use tokio::sync::RwLock;
use uuid::Uuid;

const DEFAULT_PORT: u16 = 3000;
const MAX_COUNT: usize = 50;

#[derive(Clone)]
struct AppState {
    rounds: Arc<RwLock<HashMap<Uuid, RoundSession>>>,
}

#[derive(Clone)]
struct RoundSession {
    language: String,
    language_label: String,
    inverse: bool,
    cards: Vec<Card>,
    cursor: usize,
    correct: usize,
    answered: usize,
}

#[derive(Clone)]
struct Card {
    id: usize,
    prompt: Prompt,
    translation: String,
    word_explanations: Vec<WordExplanation>,
    answer_options: Vec<String>,
    srs_key: Option<String>,
    srs_recorded: bool,
    result: Option<AnswerCheck>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum PlayMode {
    MultipleChoice,
    TextInput,
}

#[derive(Deserialize)]
struct CreateRoundRequest {
    language: String,
    #[serde(default = "default_mode")]
    mode: PlayMode,
    #[serde(default = "default_count")]
    count: usize,
    #[serde(default)]
    inverse: bool,
    #[serde(default = "default_srs")]
    srs: bool,
}

#[derive(Deserialize)]
struct AnswerRequest {
    card_id: usize,
    answer: String,
}

#[derive(Serialize)]
struct LanguageOption {
    code: &'static str,
    label: &'static str,
    slug: &'static str,
    sentence_count: usize,
}

#[derive(Serialize)]
struct CreateRoundResponse {
    round_id: Uuid,
    mode: PlayMode,
    card: CardView,
    summary: RoundSummary,
}

#[derive(Serialize)]
struct AnswerResponse {
    result: AnswerCheck,
    correct_answer: String,
    word_explanations: Vec<WordExplanation>,
    summary: RoundSummary,
    next_card: Option<CardView>,
}

#[derive(Clone, Serialize)]
struct CardView {
    id: usize,
    index: usize,
    total: usize,
    prompt_label: String,
    translation_label: String,
    prompt: ClozeLine,
    transliteration: Option<ClozeLine>,
    translation: String,
    answer_options: Vec<String>,
}

#[derive(Clone, Serialize)]
struct ClozeLine {
    first_half: String,
    blank: String,
    second_half: String,
}

#[derive(Serialize)]
struct RoundSummary {
    total: usize,
    answered: usize,
    correct: usize,
    finished: bool,
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
}

struct AppError {
    status: StatusCode,
    message: String,
}

impl AppError {
    fn bad_request(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::BAD_REQUEST,
            message: message.into(),
        }
    }

    fn not_found(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::NOT_FOUND,
            message: message.into(),
        }
    }

    fn internal(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: message.into(),
        }
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        (
            self.status,
            Json(ErrorResponse {
                error: self.message,
            }),
        )
            .into_response()
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let state = AppState {
        rounds: Arc::new(RwLock::new(HashMap::new())),
    };
    let app = Router::new()
        .route("/", get(index))
        .route("/app.css", get(styles))
        .route("/app.js", get(script))
        .route("/manifest.webmanifest", get(manifest))
        .route("/service-worker.js", get(service_worker))
        .route("/data/:file", get(data_asset))
        .route("/icons/:file", get(icon_asset))
        .route("/api/languages", get(languages))
        .route("/api/rounds", post(create_round))
        .route("/api/rounds/:round_id/answer", post(answer_round))
        .fallback(index)
        .with_state(state);

    let listener = bind_listener()?;
    let addr = listener.local_addr()?;
    listener.set_nonblocking(true)?;
    let listener = tokio::net::TcpListener::from_std(listener)?;

    println!("minicloze web is running at http://{addr}");
    axum::serve(listener, app).await?;
    Ok(())
}

async fn index() -> impl IntoResponse {
    (
        [
            (header::CONTENT_TYPE, "text/html; charset=utf-8"),
            (header::CACHE_CONTROL, "no-store, max-age=0"),
        ],
        include_str!("../static/index.html"),
    )
}

async fn styles() -> impl IntoResponse {
    (
        [
            (header::CONTENT_TYPE, "text/css; charset=utf-8"),
            (header::CACHE_CONTROL, "no-store, max-age=0"),
        ],
        include_str!("../static/app.css"),
    )
}

async fn script() -> impl IntoResponse {
    (
        [
            (header::CONTENT_TYPE, "text/javascript; charset=utf-8"),
            (header::CACHE_CONTROL, "no-store, max-age=0"),
        ],
        include_str!("../static/app.js"),
    )
}

async fn manifest() -> impl IntoResponse {
    (
        [
            (
                header::CONTENT_TYPE,
                "application/manifest+json; charset=utf-8",
            ),
            (header::CACHE_CONTROL, "no-store, max-age=0"),
        ],
        include_str!("../static/manifest.webmanifest"),
    )
}

async fn service_worker() -> impl IntoResponse {
    (
        [
            (header::CONTENT_TYPE, "text/javascript; charset=utf-8"),
            (header::CACHE_CONTROL, "no-cache, max-age=0"),
        ],
        include_str!("../static/service-worker.js"),
    )
}

async fn data_asset(Path(file): Path<String>) -> Result<Response, AppError> {
    let body = match file.as_str() {
        "mongolian_a1.json" => include_str!("../static/data/mongolian_a1.json"),
        "mongolian_a1_explanations.json" => {
            include_str!("../static/data/mongolian_a1_explanations.json")
        }
        "mongolian_a1_vocab.json" => include_str!("../static/data/mongolian_a1_vocab.json"),
        "tibetan_a1.json" => include_str!("../static/data/tibetan_a1.json"),
        "tibetan_a1_explanations.json" => {
            include_str!("../static/data/tibetan_a1_explanations.json")
        }
        "tibetan_a1_tokens.json" => include_str!("../static/data/tibetan_a1_tokens.json"),
        "tibetan_a1_vocab.json" => include_str!("../static/data/tibetan_a1_vocab.json"),
        _ => return Err(AppError::not_found("Asset not found")),
    };

    Ok((
        [
            (header::CONTENT_TYPE, "application/json; charset=utf-8"),
            (header::CACHE_CONTROL, "public, max-age=31536000, immutable"),
        ],
        body,
    )
        .into_response())
}

async fn icon_asset(Path(file): Path<String>) -> Result<Response, AppError> {
    match file.as_str() {
        "icon.svg" => Ok((
            [
                (header::CONTENT_TYPE, "image/svg+xml; charset=utf-8"),
                (header::CACHE_CONTROL, "public, max-age=31536000, immutable"),
            ],
            include_str!("../static/icons/icon.svg"),
        )
            .into_response()),
        "icon-192.png" => Ok((
            [
                (header::CONTENT_TYPE, "image/png"),
                (header::CACHE_CONTROL, "public, max-age=31536000, immutable"),
            ],
            include_bytes!("../static/icons/icon-192.png").to_vec(),
        )
            .into_response()),
        "icon-512.png" => Ok((
            [
                (header::CONTENT_TYPE, "image/png"),
                (header::CACHE_CONTROL, "public, max-age=31536000, immutable"),
            ],
            include_bytes!("../static/icons/icon-512.png").to_vec(),
        )
            .into_response()),
        _ => Err(AppError::not_found("Asset not found")),
    }
}

async fn languages() -> Json<Vec<LanguageOption>> {
    Json(vec![
        LanguageOption {
            code: "mon-a1",
            label: "Mongolian A1",
            slug: "mongolian-a1",
            sentence_count: 1500,
        },
        LanguageOption {
            code: "bod-a1",
            label: "Tibetan A1",
            slug: "tibetan-a1",
            sentence_count: 1500,
        },
    ])
}

async fn create_round(
    State(state): State<AppState>,
    Json(request): Json<CreateRoundRequest>,
) -> Result<Json<CreateRoundResponse>, AppError> {
    let language = language_code_for_input(&request.language)
        .ok_or_else(|| AppError::bad_request("Unknown language"))?;
    let language_label = language_label_for_code(language)
        .ok_or_else(|| AppError::bad_request("Unknown language"))?;
    let count = request.count.clamp(1, MAX_COUNT);

    let use_srs = request.srs && srs::supports_language(language);
    let sentences = if use_srs {
        match srs_sentences(language, request.inverse, count)? {
            Some(sentences) => sentences,
            None => generate_sentences_with_count(language, count)
                .await
                .map_err(|err| {
                    AppError::internal(format!("Could not generate sentences: {err}"))
                })?,
        }
    } else {
        generate_sentences_with_count(language, count)
            .await
            .map_err(|err| AppError::internal(format!("Could not generate sentences: {err}")))?
    };
    if sentences.is_empty() {
        return Err(AppError::internal("No sentences were generated"));
    }

    let cards = build_cards(
        sentences,
        language,
        language_label,
        request.inverse,
        request.mode,
        use_srs,
    );
    if cards.is_empty() {
        return Err(AppError::internal("No playable cards were generated"));
    }
    let round_id = Uuid::new_v4();
    let session = RoundSession {
        language: language.to_string(),
        language_label: language_label.to_string(),
        inverse: request.inverse,
        cards,
        cursor: 0,
        correct: 0,
        answered: 0,
    };
    let card = card_view(&session, &session.cards[0], 0);
    let summary = round_summary(&session);

    state.rounds.write().await.insert(round_id, session);

    Ok(Json(CreateRoundResponse {
        round_id,
        mode: request.mode,
        card,
        summary,
    }))
}

async fn answer_round(
    Path(round_id): Path<Uuid>,
    State(state): State<AppState>,
    Json(request): Json<AnswerRequest>,
) -> Result<Json<AnswerResponse>, AppError> {
    let mut rounds = state.rounds.write().await;
    let session = rounds
        .get_mut(&round_id)
        .ok_or_else(|| AppError::not_found("Round not found"))?;

    if session.cursor >= session.cards.len() {
        return Err(AppError::bad_request("Round is already finished"));
    }

    let card_index = session.cursor;
    let language = session.language.clone();
    let correct_answer = session
        .cards
        .get(card_index)
        .map(|card| card.prompt.word.clone())
        .unwrap_or_default();
    let word_explanations = session
        .cards
        .get(card_index)
        .map(|card| card.word_explanations.clone())
        .unwrap_or_default();
    let mut accepted_new_answer = false;
    let mut srs_update = None;
    let mut retry_card = None;
    let result = {
        let card = session
            .cards
            .get_mut(card_index)
            .ok_or_else(|| AppError::bad_request("Card not found"))?;

        if card.id != request.card_id {
            return Err(AppError::bad_request("That card is not active"));
        }

        if let Some(result) = &card.result {
            result.clone()
        } else {
            let result = check_answer(&request.answer, &card.prompt, &language);
            card.result = Some(result.clone());
            accepted_new_answer = true;
            let is_correct = result.outcome == minicloze_lib::game::AnswerOutcome::Correct;
            if let Some(srs_key) = card.srs_key.clone() {
                if !card.srs_recorded {
                    card.srs_recorded = true;
                    srs_update = Some((srs_key, is_correct));
                }
                if !is_correct {
                    let mut retry = card.clone();
                    retry.result = None;
                    retry.srs_recorded = true;
                    retry_card = Some(retry);
                }
            }
            result
        }
    };

    if accepted_new_answer {
        if result.outcome == minicloze_lib::game::AnswerOutcome::Correct {
            session.correct += 1;
        }
        session.answered += 1;
        session.cursor += 1;
        if let Some(retry_card) = retry_card {
            session.cards.push(retry_card);
        }
    }
    if let Some((srs_key, is_correct)) = srs_update {
        record_srs_review(&srs_key, is_correct)?;
    }

    let summary = round_summary(session);
    let next_card = session
        .cards
        .get(session.cursor)
        .map(|card| card_view(session, card, session.cursor));

    Ok(Json(AnswerResponse {
        result,
        correct_answer,
        word_explanations,
        summary,
        next_card,
    }))
}

fn build_cards(
    sentences: Vec<Sentence>,
    language: &str,
    _language_label: &str,
    inverse: bool,
    mode: PlayMode,
    with_srs: bool,
) -> Vec<Card> {
    let vocabulary = local_vocabulary_words(language).unwrap_or_default();
    let mut prompts = Vec::new();

    for sentence in sentences {
        let srs_key = with_srs.then(|| srs::card_key(language, inverse, sentence.id()));
        let translation = if inverse {
            sentence
                .get_translation()
                .map(|translation| translation.text.clone())
                .unwrap_or_default()
        } else {
            sentence.text.clone()
        };
        let word_explanations = sentence.word_explanations.clone();
        let prompt = sentence.generate_prompt(language, inverse);
        prompts.push((prompt, translation, word_explanations, srs_key));
    }

    let mut option_pool = vocabulary;
    option_pool.extend(prompts.iter().map(|(prompt, _, _, _)| prompt.word.clone()));

    prompts
        .into_iter()
        .enumerate()
        .map(|(id, (prompt, translation, word_explanations, srs_key))| {
            let answer_options = if mode == PlayMode::MultipleChoice {
                build_options(&prompt.word, &option_pool)
            } else {
                Vec::new()
            };

            Card {
                id,
                prompt,
                translation,
                word_explanations,
                answer_options,
                srs_key,
                srs_recorded: false,
                result: None,
            }
        })
        .collect()
}

fn srs_sentences(
    language: &str,
    inverse: bool,
    count: usize,
) -> Result<Option<Vec<Sentence>>, AppError> {
    let pool = local_sentence_pool(language)
        .map_err(|err| AppError::internal(format!("Could not load local corpus: {err}")))?;
    let Some(pool) = pool else {
        return Ok(None);
    };
    let path = srs::default_store_path();
    let progress = srs::load_progress(&path)
        .map_err(|err| AppError::internal(format!("Could not load SRS progress: {err}")))?;
    let candidate_keys = pool
        .iter()
        .map(|sentence| srs::card_key(language, inverse, sentence.id()))
        .collect::<Vec<_>>();
    let selection = srs::select_keys(&candidate_keys, &progress, srs::now_timestamp(), count);
    let mut by_key = pool
        .into_iter()
        .map(|sentence| (srs::card_key(language, inverse, sentence.id()), sentence))
        .collect::<HashMap<_, _>>();
    let mut sentences = selection
        .keys
        .iter()
        .filter_map(|key| by_key.remove(key))
        .collect::<Vec<_>>();

    prepare_local_sentences(language, &mut sentences)
        .map_err(|err| AppError::internal(format!("Could not prepare local sentences: {err}")))?;
    Ok(Some(sentences))
}

fn record_srs_review(srs_key: &str, is_correct: bool) -> Result<(), AppError> {
    let path = srs::default_store_path();
    let mut progress = srs::load_progress(&path)
        .map_err(|err| AppError::internal(format!("Could not load SRS progress: {err}")))?;
    srs::record_review(&mut progress, srs_key, is_correct, srs::now_timestamp());
    srs::save_progress(&path, &progress)
        .map_err(|err| AppError::internal(format!("Could not save SRS progress: {err}")))
}

fn build_options(answer: &str, pool: &[String]) -> Vec<String> {
    let answer_key = normalize_option(answer);
    let mut seen = HashSet::from([answer_key.clone()]);
    let mut distractors = pool
        .iter()
        .filter_map(|candidate| {
            let candidate = candidate.trim();
            let key = normalize_option(candidate);
            if candidate.is_empty() || key == answer_key || !seen.insert(key) {
                None
            } else {
                Some(candidate.to_string())
            }
        })
        .collect::<Vec<_>>();

    distractors.shuffle(&mut thread_rng());
    let mut options = Vec::with_capacity(4);
    options.push(answer.to_string());
    options.extend(distractors.into_iter().take(3));
    options.shuffle(&mut thread_rng());
    options
}

fn normalize_option(option: &str) -> String {
    option.trim().to_lowercase()
}

fn card_view(session: &RoundSession, card: &Card, index: usize) -> CardView {
    let blank = if session.inverse {
        "?".to_string()
    } else {
        "_".repeat(card.prompt.word.chars().count().max(3))
    };
    let transliteration = card
        .prompt
        .word_transliteration
        .as_ref()
        .map(|word_transliteration| {
            let transliteration_blank = "_".repeat(word_transliteration.chars().count().max(3));
            spaced_cloze_line(
                card.prompt
                    .first_half_transliteration
                    .as_deref()
                    .unwrap_or(""),
                &transliteration_blank,
                card.prompt
                    .second_half_transliteration
                    .as_deref()
                    .unwrap_or(""),
            )
        });

    CardView {
        id: card.id,
        index: index + 1,
        total: session.cards.len(),
        prompt_label: if session.inverse {
            "English".to_string()
        } else {
            session.language_label.clone()
        },
        translation_label: if session.inverse {
            session.language_label.clone()
        } else {
            "English".to_string()
        },
        prompt: ClozeLine {
            first_half: card.prompt.first_half.clone(),
            blank,
            second_half: card.prompt.second_half.clone(),
        },
        transliteration,
        translation: card.translation.clone(),
        answer_options: card.answer_options.clone(),
    }
}

fn spaced_cloze_line(first_half: &str, blank: &str, second_half: &str) -> ClozeLine {
    let first_half = first_half.trim_end();
    let second_half = second_half.trim_start();

    ClozeLine {
        first_half: if first_half.is_empty() {
            String::new()
        } else {
            format!("{first_half} ")
        },
        blank: blank.to_string(),
        second_half: if second_half.is_empty() {
            String::new()
        } else {
            format!(" {second_half}")
        },
    }
}

fn round_summary(session: &RoundSession) -> RoundSummary {
    RoundSummary {
        total: session.cards.len(),
        answered: session.answered,
        correct: session.correct,
        finished: session.answered >= session.cards.len(),
    }
}

fn bind_listener() -> std::io::Result<StdTcpListener> {
    if let Ok(addr) = env::var("MINICLOZE_WEB_ADDR") {
        return StdTcpListener::bind(addr);
    }

    for port in DEFAULT_PORT..DEFAULT_PORT + 20 {
        let addr = SocketAddr::from(([127, 0, 0, 1], port));
        if let Ok(listener) = StdTcpListener::bind(addr) {
            return Ok(listener);
        }
    }

    StdTcpListener::bind(SocketAddr::from(([127, 0, 0, 1], DEFAULT_PORT)))
}

fn default_mode() -> PlayMode {
    PlayMode::MultipleChoice
}

fn default_count() -> usize {
    10
}

fn default_srs() -> bool {
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn multiple_choice_options_include_answer_once() {
        let pool = vec![
            "сансар".to_string(),
            "ном".to_string(),
            "ус".to_string(),
            "гэр".to_string(),
            "нар".to_string(),
        ];

        let options = build_options("сансар", &pool);

        assert_eq!(options.iter().filter(|item| *item == "сансар").count(), 1);
        assert_eq!(options.len(), 4);
    }

    #[test]
    fn multiple_choice_options_ignore_duplicate_distractors() {
        let pool = vec![
            "བཀྲ་ཤིས".to_string(),
            "བཀྲ་ཤིས".to_string(),
            "ཇ".to_string(),
            "ཆུ".to_string(),
            "ཁང་པ".to_string(),
        ];

        let options = build_options("བཀྲ་ཤིས", &pool);

        assert_eq!(options.iter().filter(|item| *item == "བཀྲ་ཤིས").count(), 1);
        assert_eq!(options.len(), 4);
    }
}
