use minicloze_lib::{
    game::{
        answer_distance, answer_with_transliteration, format_transliteration_cloze, is_tibetan,
        DISTANCE_FOR_CLOSE,
    },
    langs::{normalize_language_input, propagate},
    sentence::{
        generate_sentences, local_sentence_pool, prepare_local_sentences, Prompt, Sentence,
    },
    srs::{self, SrsProgress, SrsSelection},
    wiktionary::generate_url,
};

use std::collections::HashMap;
use std::io;
use std::io::Write;
use std::path::PathBuf;
use std::time::Instant;
use std::{env, process::exit};

use inline_colorization::*;
use inquire::*;
use terminal_link::*;

use async_recursion::async_recursion;

const ROUND_SIZE: usize = 10;

struct GameRound {
    cards: Vec<ReviewCard>,
    srs: Option<CliSrs>,
    selection: Option<SrsSelection>,
}

#[derive(Clone)]
struct ReviewCard {
    sentence: Sentence,
    prompt: Prompt,
    srs_key: Option<String>,
    srs_recorded: bool,
}

struct CliSrs {
    progress: SrsProgress,
    path: PathBuf,
}

#[tokio::main]
async fn main() {
    clear_screen();

    let args: Vec<_> = env::args().collect();

    // gets the tatoeba language codes from a separate file
    let lang_codes = propagate();
    let langs: Vec<&str> = lang_codes.clone().into_keys().collect();

    let inverse = args.len() > 2 && args[2] == "inverse";

    let language_input = if args.len() > 1 {
        normalize_language_input(&args[1])
    }
    // if compiled script is run
    else {
        let ans: Result<&str, InquireError> =
            Select::new("What language do you want to study?", langs)
                .without_help_message()
                .prompt();

        if let Ok(choice) = ans {
            String::from(choice)
        } else {
            String::new()
        }
    };
    print!("Fetching sentences for you...");
    io::stdout().flush().unwrap();

    let now = Instant::now();

    let language = lang_codes
        .get(&language_input.as_str())
        .expect("Please enter a valid language")
        .to_string();

    let round = match load_round(&language, inverse).await {
        Ok(round) => round,
        Err(err) => {
            eprintln!(" Failed to fetch sentences: {err}");
            exit(1);
        }
    };
    let len = round.cards.len();
    let elapsed = now.elapsed();

    println!(
        " Processing complete in {:.2?}, {} sentences parsed.",
        elapsed, len
    );

    start_game(round, len, language, 0, 0, inverse).await;
}

async fn load_round(
    language: &str,
    inverse: bool,
) -> Result<GameRound, Box<dyn std::error::Error + Send + Sync>> {
    if srs::supports_language(language) {
        if let Some(pool) = local_sentence_pool(language)? {
            let path = srs::default_store_path();
            let progress = srs::load_progress(&path)?;
            let candidate_keys = pool
                .iter()
                .map(|sentence| srs::card_key(language, inverse, sentence.id()))
                .collect::<Vec<_>>();
            let selection =
                srs::select_keys(&candidate_keys, &progress, srs::now_timestamp(), ROUND_SIZE);
            let mut by_key = pool
                .into_iter()
                .map(|sentence| (srs::card_key(language, inverse, sentence.id()), sentence))
                .collect::<HashMap<_, _>>();
            let mut sentences = selection
                .keys
                .iter()
                .filter_map(|key| by_key.remove(key))
                .collect::<Vec<_>>();

            if sentences.is_empty() {
                return Err(Box::new(io::Error::new(
                    io::ErrorKind::InvalidData,
                    "No SRS candidates were selected",
                )));
            }

            prepare_local_sentences(language, &mut sentences)?;
            let cards = build_review_cards(sentences, language, inverse, true);

            return Ok(GameRound {
                cards,
                srs: Some(CliSrs { progress, path }),
                selection: Some(selection),
            });
        }
    }

    let sentences = generate_sentences(language).await?;
    Ok(GameRound {
        cards: build_review_cards(sentences, language, inverse, false),
        srs: None,
        selection: None,
    })
}

fn build_review_cards(
    sentences: Vec<Sentence>,
    language: &str,
    inverse: bool,
    with_srs: bool,
) -> Vec<ReviewCard> {
    sentences
        .into_iter()
        .map(|sentence| {
            let srs_key = with_srs.then(|| srs::card_key(language, inverse, sentence.id()));
            let prompt = sentence.generate_prompt(language, inverse);
            ReviewCard {
                sentence,
                prompt,
                srs_key,
                srs_recorded: false,
            }
        })
        .collect()
}

fn print_srs_selection(round: &GameRound) {
    let Some(selection) = &round.selection else {
        return;
    };

    println!(
        " SRS queue: {} due, {} new, {} upcoming.",
        selection.due, selection.new, selection.upcoming
    );
}

// sentences: sentences for the game
// len: how many sentences there are. always 10 if the language has enough sentences
// language: what language the game is in
// previous_correct: the total previous correct score
// total: the previous total

#[async_recursion]
async fn start_game(
    mut round: GameRound,
    len: usize,
    language: String,
    previous_correct: i32,
    total: i32,
    inverse: bool,
) {
    clear_screen();
    print_srs_selection(&round);
    let mut correct = 0;
    let mut card_index = 0;

    while card_index < round.cards.len() {
        let card = round.cards[card_index].clone();
        let prompt = &card.prompt;
        let sentence = &card.sentence;

        let underscores_num = if inverse {
            String::from("?")
        } else {
            vec!['_'; prompt.word.chars().count()]
                .into_iter()
                .collect::<String>()
        };
        let transliteration_underscores_num = prompt
            .word_transliteration
            .as_ref()
            .map(|transliteration| {
                vec!['_'; transliteration.chars().count()]
                    .into_iter()
                    .collect::<String>()
            })
            .unwrap_or_else(|| underscores_num.clone());

        let print_language = if inverse { "eng" } else { &language };

        let non_english = format!(
            "{style_bold}{}{style_reset}{}{style_bold}{}{style_reset} {}",
            (print_language.to_uppercase() + ": "),
            prompt.first_half,
            underscores_num,
            prompt.second_half
        );

        if inverse {
            println!(
                "{color_black}{bg_bright_white}{}{}{}{color_reset}{bg_reset}",
                &language.to_uppercase(),
                &": ".to_string(),
                &sentence.get_translation().unwrap().text
            );
            println!("{}", &non_english);
        } else {
            print!(
                "{color_black}{bg_bright_white}{style_bold}{}:{style_reset}",
                // {color_black}{bg_bright_white}{}{style_bold}{}{style_reset}{color_black}{bg_bright_white} {}{color_reset}{bg_reset}"
                print_language.to_uppercase()
            );

            for word in prompt.first_half.split(' ') {
                print!(
                    "{color_black}{bg_bright_white} {}{style_reset}",
                    Link::new(
                        word,
                        &generate_url(
                            word.trim_matches(|c| char::is_ascii_punctuation(&c)),
                            &language
                        )
                    )
                )
            }

            print!("{color_black}{bg_bright_white}{underscores_num}{style_reset}");

            for word in prompt.second_half.split(' ') {
                print!(
                    "{color_black}{bg_bright_white} {}{style_reset}",
                    Link::new(
                        word,
                        &generate_url(
                            word.trim_matches(|c| char::is_ascii_punctuation(&c)),
                            &language
                        )
                    )
                )
            }

            println!();

            if is_tibetan(&language) && prompt.word_transliteration.is_some() {
                println!(
                    "{style_bold}WYL:{style_reset} {}",
                    format_transliteration_cloze(
                        prompt.first_half_transliteration.as_deref().unwrap_or(""),
                        &transliteration_underscores_num,
                        prompt.second_half_transliteration.as_deref().unwrap_or("")
                    )
                );
            }

            println!("{style_bold}ENG:{style_reset} {}", sentence.text);
        }

        let mut guess = String::new();

        print!("> ");
        read_into(&mut guess);

        let levenshtein_distance = answer_distance(&guess, prompt);

        let is_correct = levenshtein_distance == 0;

        if is_correct {
            correct += 1;
            let answer = answer_with_transliteration(prompt, &language);
            println!(
                "Correct, {color_white}{bg_green}{}{color_reset}{bg_reset}",
                Link::new(
                    &answer,
                    &generate_url(prompt.word.to_lowercase().trim(), &language)
                )
            );
        } else if levenshtein_distance < DISTANCE_FOR_CLOSE {
            let answer = answer_with_transliteration(prompt, &language);
            println!(
                "Close, {style_bold}{color_bright_white}{bg_yellow}{}{bg_reset}{color_reset}{style_reset}.",
                Link::new(
                    &answer,
                    &generate_url(prompt.word.to_lowercase().trim(), &language)
                )
            );
        } else {
            let answer = answer_with_transliteration(prompt, &language);
            println!(
                "Wrong, {style_bold}{color_bright_white}{bg_red}{}{bg_reset}{color_reset}{style_reset}.",
                Link::new(
                    &answer,
                    &generate_url(prompt.word.to_lowercase().trim(), &language)
                )
            );
        }
        record_srs_attempt(&mut round, &card, is_correct);
        if !is_correct && card.srs_key.is_some() {
            let mut retry = card.clone();
            retry.srs_recorded = true;
            round.cards.push(retry);
            println!("This one will come back near the end of the round.");
        }
        print_word_explanations(&sentence);
        println!();

        // Old lookup logic

        // loop {
        //     let mut lookup = String::new();
        //     println!("{} {}", "Lookup a word?", "[enter word or ignore]");
        //     print!("> ");
        //     read_into(&mut lookup);

        //     if lookup.trim().is_empty() {
        //         break;
        //     } else {
        //         wiktionary_try_open(lookup, &language);
        //     }
        // }
        println!();
        card_index += 1;
    }

    let new_correct = previous_correct + correct;
    let attempts = round.cards.len();
    let new_total = total + attempts as i32;

    let message = if (new_total) / attempts as i32 == 1 {
        if attempts == len {
            format!("{}/{} sentences correct. Play again?", correct, attempts)
        } else {
            format!(
                "{}/{} attempts correct across {} cards. Play again?",
                correct, attempts, len
            )
        }
    } else {
        format!(
            "{}/{} attempts correct locally, {}/{} attempts correct overall. Play again?",
            correct, attempts, new_correct, new_total
        )
    };

    let replay = Select::new(&message, vec!["No", "Yes"])
        .without_help_message()
        .prompt_skippable();

    if let Ok(o) = replay {
        if let Some(c) = o {
            if c == "Yes" {
                let round = match load_round(language.as_str(), inverse).await {
                    Ok(round) => round,
                    Err(err) => {
                        eprintln!("Failed to fetch sentences: {err}");
                        exit(1);
                    }
                };
                let len = round.cards.len();
                start_game(round, len, language, new_correct, new_total, inverse).await;
            } else {
                exit(0);
            }
        } else {
            exit(0);
        }
    }
}

fn record_srs_attempt(round: &mut GameRound, card: &ReviewCard, is_correct: bool) {
    let Some(srs_key) = &card.srs_key else {
        return;
    };
    if card.srs_recorded {
        return;
    }
    let Some(srs_state) = &mut round.srs else {
        return;
    };

    srs::record_review(
        &mut srs_state.progress,
        srs_key,
        is_correct,
        srs::now_timestamp(),
    );
    if let Err(err) = srs::save_progress(&srs_state.path, &srs_state.progress) {
        eprintln!("Could not save SRS progress: {err}");
    }
}

// clear the screen and position cursor at the top left
fn clear_screen() {
    print!("{esc}[2J{esc}[1;1H", esc = 27 as char);
}

// user input
fn read_into(buffer: &mut String) {
    io::stdout().flush().unwrap();
    io::stdin().read_line(buffer).unwrap();
}

fn print_word_explanations(sentence: &Sentence) {
    if sentence.word_explanations.is_empty() {
        return;
    }

    println!("{style_bold}Words:{style_reset}");
    for explanation in &sentence.word_explanations {
        let word = match explanation.wylie.as_deref() {
            Some(wylie) if !wylie.trim().is_empty() => {
                format!("{} ({})", explanation.word, wylie)
            }
            _ => explanation.word.clone(),
        };

        match explanation.note.as_deref() {
            Some(note) if !note.trim().is_empty() => {
                println!("  {} — {} ({})", word, explanation.gloss, note)
            }
            _ => println!("  {} — {}", word, explanation.gloss),
        }
    }
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
    fn ignores_diacritics_in_latin_answers() {
        let prompt = prompt_for("été", None);

        assert_eq!(answer_distance("ete", &prompt), 0);
    }

    #[test]
    fn normalizes_local_corpus_language_arguments() {
        assert_eq!(normalize_language_input("tibetan-a1"), "Tibetan A1");
        assert_eq!(normalize_language_input("bod-a2"), "Tibetan A2");
        assert_eq!(normalize_language_input("mongolian-a1"), "Mongolian A1");
        assert_eq!(normalize_language_input("mon-a2"), "Mongolian A2");
    }
}
