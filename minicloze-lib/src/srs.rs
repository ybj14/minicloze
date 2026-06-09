use rand::{seq::SliceRandom, thread_rng};
use serde::{Deserialize, Serialize};
use std::{
    collections::{HashMap, HashSet},
    env, fs, io,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

pub const CLOZEMASTER_INTERVAL_DAYS: [i64; 4] = [1, 10, 30, 180];

const SECONDS_PER_DAY: i64 = 24 * 60 * 60;

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub struct SrsProgress {
    #[serde(default)]
    pub cards: HashMap<String, SrsCard>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct SrsCard {
    #[serde(default)]
    pub interval_index: usize,
    #[serde(default)]
    pub due_at: i64,
    #[serde(default)]
    pub last_reviewed_at: Option<i64>,
    #[serde(default)]
    pub reviews: u32,
    #[serde(default)]
    pub correct: u32,
    #[serde(default)]
    pub wrong: u32,
    #[serde(default)]
    pub lapses: u32,
}

impl Default for SrsCard {
    fn default() -> Self {
        Self {
            interval_index: 0,
            due_at: 0,
            last_reviewed_at: None,
            reviews: 0,
            correct: 0,
            wrong: 0,
            lapses: 0,
        }
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct SrsSelection {
    pub keys: Vec<String>,
    pub due: usize,
    pub new: usize,
    pub upcoming: usize,
}

pub fn supports_language(language: &str) -> bool {
    matches!(language, "mon-a1" | "bod-a1")
}

pub fn card_key(language: &str, inverse: bool, sentence_id: i32) -> String {
    let direction = if inverse { "inverse" } else { "normal" };
    format!("{language}:{direction}:{sentence_id}")
}

pub fn now_timestamp() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs() as i64)
        .unwrap_or(0)
}

pub fn default_store_path() -> PathBuf {
    if let Some(path) = env::var_os("MINICLOZE_SRS_PATH") {
        return PathBuf::from(path);
    }

    let base = env::var_os("XDG_DATA_HOME")
        .map(PathBuf::from)
        .or_else(|| env::var_os("HOME").map(|home| PathBuf::from(home).join(".local/share")))
        .unwrap_or_else(|| PathBuf::from("."));

    base.join("minicloze").join("srs.json")
}

pub fn load_progress(path: &Path) -> io::Result<SrsProgress> {
    match fs::read_to_string(path) {
        Ok(contents) => serde_json::from_str(&contents).map_err(invalid_data),
        Err(err) if err.kind() == io::ErrorKind::NotFound => Ok(SrsProgress::default()),
        Err(err) => Err(err),
    }
}

pub fn save_progress(path: &Path, progress: &SrsProgress) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let contents = serde_json::to_string_pretty(progress).map_err(invalid_data)?;
    fs::write(path, contents)
}

pub fn select_keys(
    candidate_keys: &[String],
    progress: &SrsProgress,
    now: i64,
    count: usize,
) -> SrsSelection {
    let count = count.min(candidate_keys.len());
    let candidates = unique_candidates(candidate_keys);
    let mut selection = SrsSelection::default();
    let mut selected = HashSet::new();

    let mut due = candidates
        .iter()
        .filter_map(|key| {
            progress
                .cards
                .get(key)
                .and_then(|card| (card.due_at <= now).then_some((key.clone(), card.due_at)))
        })
        .collect::<Vec<_>>();
    due.sort_by(|left, right| left.1.cmp(&right.1).then_with(|| left.0.cmp(&right.0)));
    append_keys(
        due.into_iter().map(|(key, _)| key),
        count,
        &mut selected,
        &mut selection.keys,
        &mut selection.due,
    );

    let mut new = candidates
        .iter()
        .filter(|key| !progress.cards.contains_key(*key))
        .cloned()
        .collect::<Vec<_>>();
    new.shuffle(&mut thread_rng());
    append_keys(
        new,
        count,
        &mut selected,
        &mut selection.keys,
        &mut selection.new,
    );

    let mut upcoming = candidates
        .iter()
        .filter_map(|key| {
            progress
                .cards
                .get(key)
                .and_then(|card| (card.due_at > now).then_some((key.clone(), card.due_at)))
        })
        .collect::<Vec<_>>();
    upcoming.sort_by(|left, right| left.1.cmp(&right.1).then_with(|| left.0.cmp(&right.0)));
    append_keys(
        upcoming.into_iter().map(|(key, _)| key),
        count,
        &mut selected,
        &mut selection.keys,
        &mut selection.upcoming,
    );

    selection
}

pub fn record_review(progress: &mut SrsProgress, key: &str, correct: bool, now: i64) -> SrsCard {
    let card = progress.cards.entry(key.to_string()).or_default();
    let was_new = card.reviews == 0;

    if correct {
        card.correct += 1;
        if !was_new {
            card.interval_index =
                (card.interval_index + 1).min(CLOZEMASTER_INTERVAL_DAYS.len() - 1);
        }
    } else {
        card.wrong += 1;
        card.lapses += 1;
        card.interval_index = 0;
    }

    card.reviews += 1;
    card.last_reviewed_at = Some(now);
    card.due_at = now + CLOZEMASTER_INTERVAL_DAYS[card.interval_index] * SECONDS_PER_DAY;
    card.clone()
}

fn unique_candidates(candidate_keys: &[String]) -> Vec<String> {
    let mut seen = HashSet::new();
    candidate_keys
        .iter()
        .filter_map(|key| seen.insert(key.as_str()).then_some(key.clone()))
        .collect()
}

fn append_keys(
    keys: impl IntoIterator<Item = String>,
    count: usize,
    selected: &mut HashSet<String>,
    output: &mut Vec<String>,
    source_count: &mut usize,
) {
    for key in keys {
        if output.len() >= count {
            break;
        }
        if selected.insert(key.clone()) {
            output.push(key);
            *source_count += 1;
        }
    }
}

fn invalid_data(err: serde_json::Error) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, err)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn correct_reviews_follow_clozemaster_intervals() {
        let mut progress = SrsProgress::default();
        let now = 1_700_000_000;

        let card = record_review(&mut progress, "mon-a1:normal:1", true, now);
        assert_eq!(card.interval_index, 0);
        assert_eq!(card.due_at, now + SECONDS_PER_DAY);

        let card = record_review(
            &mut progress,
            "mon-a1:normal:1",
            true,
            now + SECONDS_PER_DAY,
        );
        assert_eq!(card.interval_index, 1);
        assert_eq!(card.due_at, now + SECONDS_PER_DAY + 10 * SECONDS_PER_DAY);
    }

    #[test]
    fn wrong_review_resets_to_first_interval() {
        let mut progress = SrsProgress::default();
        let now = 1_700_000_000;

        record_review(&mut progress, "bod-a1:normal:1", true, now);
        record_review(
            &mut progress,
            "bod-a1:normal:1",
            true,
            now + SECONDS_PER_DAY,
        );
        let card = record_review(&mut progress, "bod-a1:normal:1", false, now + 20);

        assert_eq!(card.interval_index, 0);
        assert_eq!(card.due_at, now + 20 + SECONDS_PER_DAY);
        assert_eq!(card.lapses, 1);
    }

    #[test]
    fn selection_prefers_due_then_new_then_upcoming() {
        let now = 1_700_000_000;
        let mut progress = SrsProgress::default();
        progress.cards.insert(
            "due".to_string(),
            SrsCard {
                due_at: now - 5,
                reviews: 1,
                ..SrsCard::default()
            },
        );
        progress.cards.insert(
            "upcoming".to_string(),
            SrsCard {
                due_at: now + 5,
                reviews: 1,
                ..SrsCard::default()
            },
        );

        let keys = vec!["new".to_string(), "upcoming".to_string(), "due".to_string()];
        let selection = select_keys(&keys, &progress, now, 3);

        assert_eq!(selection.keys.len(), 3);
        assert_eq!(selection.keys[0], "due");
        assert_eq!(selection.due, 1);
        assert_eq!(selection.new, 1);
        assert_eq!(selection.upcoming, 1);
    }
}
