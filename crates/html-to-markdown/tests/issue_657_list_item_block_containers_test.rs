#![allow(missing_docs)]

use html_to_markdown_rs::{ConversionOptions, TierStrategy, convert};

fn markdown(html: &str) -> String {
    let options = ConversionOptions {
        extract_metadata: false,
        tier_strategy: TierStrategy::Tier2,
        ..ConversionOptions::default()
    };
    convert(html, Some(options))
        .expect("conversion should succeed")
        .content
        .unwrap_or_default()
}

#[test]
fn should_keep_block_container_content_inside_the_list_item() {
    let mut failures = Vec::new();
    for (html, expected) in [
        (
            "<ul><li><details><summary>s</summary>d</details></li></ul>",
            "- **s**\n\n  d\n",
        ),
        (
            "<ul><li><figure><figcaption>f</figcaption>d</figure></li></ul>",
            "- *f*\n\n  d\n",
        ),
        (
            "<ul><li><fieldset><legend>s</legend>d</fieldset></li></ul>",
            "- **s**\n\n  d\n",
        ),
        ("<ul><li><menu><li>m</li></menu></li></ul>", "- * m\n"),
        ("<ul><li><hgroup><h2>h</h2></hgroup>t</li></ul>", "- ## h\n\n  t\n"),
    ] {
        let actual = markdown(html);
        if actual != expected {
            failures.push(format!("{html}: {actual:?}, expected {expected:?}"));
        }
    }
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}

#[test]
fn should_keep_text_after_an_hgroup_inside_the_task_item() {
    let html = "<ul><li><input type=\"checkbox\"><hgroup><h2>h</h2></hgroup>t</li></ul>";
    assert_eq!(markdown(html), "- [ ] &#32;\n  ## h\n\n  t\n");
}
