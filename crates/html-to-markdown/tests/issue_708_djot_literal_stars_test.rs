#![allow(missing_docs)]

use html_to_markdown_rs::{ConversionOptions, OutputFormat, convert};

fn djot(html: &str) -> String {
    convert(
        html,
        Some(ConversionOptions {
            output_format: OutputFormat::Djot,
            ..ConversionOptions::default()
        }),
    )
    .expect("conversion should succeed")
    .content
    .unwrap_or_default()
}

#[test]
fn should_escape_literal_stars_in_thematic_break_shaped_djot_text() {
    for (html, expected) in [
        ("<p>* - *</p>", "\\* - \\*\n"),
        ("<p>***</p>", "\\*\\*\\*\n"),
        ("<p>* * *</p>", "\\* \\* \\*\n"),
        ("<p>*-*</p>", "\\*-\\*\n"),
        ("<p>*</p>", "\\*\n"),
    ] {
        assert_eq!(djot(html), expected, "{html}");
    }
}

#[test]
fn should_escape_only_literal_stars_around_djot_strong_markup() {
    assert_eq!(djot("<p>*<b>-</b>*</p>"), "\\**-*\\*\n");
    assert_eq!(djot("<p><b>- *</b></p>"), "*- \\**\n");
}

#[test]
fn should_not_escape_stars_in_ordinary_djot_text() {
    assert_eq!(djot("<p>2 * 3</p>"), "2 * 3\n");
    assert_eq!(djot("<p>* hello</p>"), "* hello\n");
}
