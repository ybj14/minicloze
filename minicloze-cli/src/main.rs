use minicloze_lib::{
    game::{
        answer_distance, answer_with_transliteration, format_transliteration_cloze, is_tibetan,
        DISTANCE_FOR_CLOSE,
    },
    langs::{normalize_language_input, propagate},
    sentence::{generate_sentences, Prompt, Sentence},
    wiktionary::generate_url,
};

use std::io;
use std::io::Write;
use std::time::Instant;
use std::{env, process::exit};

use inline_colorization::*;
use inquire::*;
use terminal_link::*;

use async_recursion::async_recursion;

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

    let sentences = match generate_sentences(&language).await {
        Ok(sentences) => sentences,
        Err(err) => {
            eprintln!(" Failed to fetch sentences: {err}");
            exit(1);
        }
    };
    let len = sentences.len();
    let elapsed = now.elapsed();

    println!(
        " Processing complete in {:.2?}, {} sentences parsed.",
        elapsed, len
    );

    start_game(sentences, len, language, 0, 0, inverse).await;
}

// sentences: sentences for the game
// len: how many sentences there are. always 10 if the language has enough sentences
// language: what language the game is in
// previous_correct: the total previous correct score
// total: the previous total

#[async_recursion]
async fn start_game(
    sentences: Vec<Sentence>,
    len: usize,
    language: String,
    previous_correct: i32,
    total: i32,
    inverse: bool,
) {
    clear_screen();
    let mut correct = 0;

    for sentence in sentences {
        let prompt = sentence.generate_prompt(&language, inverse);

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

        let levenshtein_distance = answer_distance(&guess, &prompt);

        if levenshtein_distance == 0 {
            correct += 1;
            let answer = answer_with_transliteration(&prompt, &language);
            println!(
                "Correct, {color_white}{bg_green}{}{color_reset}{bg_reset}",
                Link::new(
                    &answer,
                    &generate_url(prompt.word.to_lowercase().trim(), &language)
                )
            );
        } else if levenshtein_distance < DISTANCE_FOR_CLOSE {
            let answer = answer_with_transliteration(&prompt, &language);
            println!(
                "Close, {style_bold}{color_bright_white}{bg_yellow}{}{bg_reset}{color_reset}{style_reset}.",
                Link::new(
                    &answer,
                    &generate_url(prompt.word.to_lowercase().trim(), &language)
                )
            );
        } else {
            let answer = answer_with_transliteration(&prompt, &language);
            println!(
                "Wrong, {style_bold}{color_bright_white}{bg_red}{}{bg_reset}{color_reset}{style_reset}.",
                Link::new(
                    &answer,
                    &generate_url(prompt.word.to_lowercase().trim(), &language)
                )
            );
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
    }

    let new_correct = previous_correct + correct;
    let new_total = total + len as i32;

    let message = if (new_total) / len as i32 == 1 {
        format!("{}/{} sentences correct. Play again?", correct, len)
    } else {
        format!(
            "{}/{} sentences correct locally, {}/{} sentences correct overall. Play again?",
            correct, len, new_correct, new_total
        )
    };

    let replay = Select::new(&message, vec!["No", "Yes"])
        .without_help_message()
        .prompt_skippable();

    if let Ok(o) = replay {
        if let Some(c) = o {
            if c == "Yes" {
                let sentences = match generate_sentences(language.as_str()).await {
                    Ok(sentences) => sentences,
                    Err(err) => {
                        eprintln!("Failed to fetch sentences: {err}");
                        exit(1);
                    }
                };
                let len = sentences.len();
                start_game(sentences, len, language, new_correct, new_total, inverse).await;
            } else {
                exit(0);
            }
        } else {
            exit(0);
        }
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
