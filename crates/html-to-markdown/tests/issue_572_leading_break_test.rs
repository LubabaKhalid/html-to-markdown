#![allow(missing_docs)]
#![cfg(feature = "testkit")]

use html_to_markdown_rs::{ConversionOptions, TierStrategy, convert};

fn assert_all_tiers(html: &str, expected: &str) {
    for tier_strategy in [TierStrategy::Auto, TierStrategy::Tier1, TierStrategy::Tier2] {
        let options = ConversionOptions {
            tier_strategy,
            ..ConversionOptions::default()
        };
        let output = convert(html, Some(options))
            .expect("conversion should succeed")
            .content
            .unwrap_or_default();
        assert_eq!(output, expected, "unexpected output for {tier_strategy:?}");
    }
}

#[test]
fn should_drop_a_leading_break_before_plain_text_in_a_paragraph() {
    assert_all_tiers("<p><br>B</p>", "B\n");
}

#[test]
fn should_drop_a_leading_break_before_a_span_in_a_paragraph() {
    assert_all_tiers("<p><br><span>B</span></p>", "B\n");
}

#[test]
fn should_keep_a_break_inside_an_inline_wrapper_after_paragraph_text() {
    assert_all_tiers("<p>A<em><br>B</em></p>", "A  \n*B*\n");
}

#[test]
fn should_keep_a_leading_top_level_break() {
    assert_all_tiers("<br>B", "\nB\n");
}
