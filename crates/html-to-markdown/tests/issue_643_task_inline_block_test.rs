#![allow(missing_docs)]

//! Regression test for issue #643: a block in an inline wrapper must leave the checkbox line.

use html_to_markdown_rs::{ConversionOptions, TierStrategy, convert};

#[test]
fn should_start_a_bold_quote_below_the_task_checkbox() {
    let html = r#"<ul><li><input type="checkbox"><b><blockquote>q</blockquote></b></li></ul>"#;
    let options = ConversionOptions {
        extract_metadata: false,
        tier_strategy: TierStrategy::Tier2,
        ..ConversionOptions::default()
    };
    let markdown = convert(html, Some(options))
        .expect("conversion must succeed")
        .content
        .unwrap_or_default();

    assert_eq!(markdown, "- [ ] &#32;\n  > **q**\n");
    let rendered = comrak::markdown_to_html(&markdown, &comrak::Options::default());
    assert!(rendered.contains("<blockquote>\n<p><strong>q</strong></p>\n</blockquote>"));
}
