// ~keep Rust inner attributes below are crate-level attributes, not a shell shebang.
#![allow(missing_docs)]
#![cfg(feature = "testkit")]

//! Regression tests for issue #683: a `<br>` on its own source line became a paragraph
//! break. The text node before it (`"First\n"`) turned its trailing source newline into a
//! `'\n'` outside a paragraph, so the `<br>`'s hard-break marker landed on a line of its
//! own (`"First\n  \n"`). Cleanup then reduced that whitespace-only line to a blank line.
//! Under the backslash style, the `\` was left stranded on its own line instead.
//!
//! Tier 1 had the same defect in `trailing_single_newline_join`, and on top of it dropped a
//! top-level `<br>` that followed text and kept the next line's leading source space. Every
//! Spaces case is checked on both tiers under options that clear the router's gates, so the
//! Tier-1 check covers the path those callers really take. The router sends the backslash
//! style to Tier 2, so those cases run there only.

use html_to_markdown_rs::{ConversionOptions, HighlightStyle, NewlineStyle, TierStrategy, convert, prescan, tier1};

fn options(tier_strategy: TierStrategy, newline_style: NewlineStyle) -> ConversionOptions {
    ConversionOptions {
        tier_strategy,
        newline_style,
        extract_metadata: false,
        highlight_style: HighlightStyle::None,
        ..ConversionOptions::default()
    }
}

// ~keep Calls `tier1::run` directly: a forced Tier-1 `convert` falls back to Tier 2 on a
// ~keep bail, and a silent fallback would make the Tier-1 check vacuous.
fn tier1(html: &str) -> String {
    let (cleaned, report) = prescan::run(html);
    tier1::run(
        cleaned.as_ref(),
        &report,
        &options(TierStrategy::Tier1, NewlineStyle::Spaces),
    )
    .unwrap_or_else(|reason| panic!("tier1 bailed on {html:?}: {reason}"))
}

fn tier2(html: &str, newline_style: NewlineStyle) -> String {
    convert(html, Some(options(TierStrategy::Tier2, newline_style)))
        .expect("conversion should succeed")
        .content
        .unwrap_or_default()
}

fn assert_both_tiers(html: &str, expected: &str) {
    assert_eq!(tier1(html), expected, "tier1, html={html:?}");
    assert_eq!(tier2(html, NewlineStyle::Spaces), expected, "tier2, html={html:?}");
}

#[test]
fn should_keep_a_top_level_br_on_its_own_line_as_a_hard_break() {
    assert_both_tiers("First\n<br>\nSecond", "First  \nSecond\n");
}

#[test]
fn should_keep_a_br_preceded_only_by_a_source_newline_as_a_hard_break() {
    assert_both_tiers("First\n<br>Second", "First  \nSecond\n");
}

#[test]
fn should_keep_a_br_on_its_own_line_in_a_div_as_a_hard_break() {
    assert_both_tiers("<div>First\n<br>\nSecond</div>", "First  \nSecond\n");
}

#[test]
fn should_keep_a_br_on_its_own_line_in_a_list_item_as_a_hard_break() {
    assert_both_tiers("<ul><li>First\n<br>\nSecond</li></ul>", "- First  \n  Second\n");
}

#[test]
fn should_keep_a_br_on_its_own_line_in_a_blockquote_as_a_hard_break() {
    assert_both_tiers("<blockquote>First\n<br>\nSecond</blockquote>", "> First  \n> Second\n");
}

#[test]
fn should_see_past_a_comment_between_the_text_and_the_br() {
    assert_both_tiers("<div>First\n<!-- note -->\n<br>\nSecond</div>", "First  \nSecond\n");
}

#[test]
fn should_keep_a_br_after_an_indented_source_line_as_a_hard_break() {
    assert_both_tiers("<div>First  \n  <br>  \n  Second</div>", "First  \nSecond\n");
}

#[test]
fn should_match_the_inline_form_for_a_br_run_on_their_own_lines() {
    assert_both_tiers("A\n<br>\n<br>\nB", "A  \n\nB\n");
}

#[test]
fn should_keep_a_br_after_a_span_ending_in_a_newline_as_a_hard_break() {
    assert_both_tiers("<span>First\n</span><br>Second", "First  \nSecond\n");
    assert_both_tiers("<div><span>First\n</span><br>Second</div>", "First  \nSecond\n");
    assert_both_tiers("<span><span>First\n</span></span><br>Second", "First  \nSecond\n");
}

// ~keep Parity guard for the Tier-1 lookahead rather than a #683 reproduction: Tier 2 ends a
// ~keep `<label>` with its own block separator, so the `<br>` after it opens no line of the
// ~keep label's text, and Tier 1 must not look past `</label>` as it does past `</span>`.
#[test]
fn should_agree_between_tiers_on_a_br_after_a_label() {
    let html = "<div><label>First\n</label><br>Second</div>";
    assert_eq!(tier1(html), tier2(html, NewlineStyle::Spaces), "html={html:?}");
}

#[test]
fn should_attach_the_backslash_marker_to_the_preceding_line() {
    assert_eq!(
        tier2("First\n<br>\nSecond", NewlineStyle::Backslash),
        "First\\\nSecond\n"
    );
    assert_eq!(tier2("A\n<br>\n<br>\nB", NewlineStyle::Backslash), "A\\\n\\\nB\n");
    assert_eq!(
        tier2("<span>First\n</span><br>Second", NewlineStyle::Backslash),
        "First\\\nSecond\n"
    );
}
