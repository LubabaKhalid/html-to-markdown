#![allow(missing_docs)]

use html_to_markdown_rs::{ConversionOptions, NewlineStyle, TierStrategy, WhitespaceMode, convert};

fn convert_strict(html: &str, newline_style: NewlineStyle) -> String {
    convert(
        html,
        Some(ConversionOptions {
            extract_metadata: false,
            newline_style,
            whitespace_mode: WhitespaceMode::Strict,
            tier_strategy: TierStrategy::Tier2,
            ..ConversionOptions::default()
        }),
    )
    .expect("conversion should succeed")
    .content
    .unwrap_or_default()
}

#[test]
fn should_keep_a_strict_br_on_its_own_source_line_as_a_hard_break() {
    assert_eq!(
        convert_strict("First\n<br>\nSecond", NewlineStyle::Spaces),
        "First  \nSecond\n"
    );
    assert_eq!(
        convert_strict("First\n<br>\nSecond", NewlineStyle::Backslash),
        "First\\\nSecond\n"
    );
}

#[test]
fn should_preserve_a_strict_source_newline_when_no_br_follows() {
    assert_eq!(
        convert_strict("<span>First\n</span>Second", NewlineStyle::Spaces),
        "First\nSecond\n"
    );
}
