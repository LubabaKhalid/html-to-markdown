#![allow(missing_docs)]

use html_to_markdown_rs::{ConversionOptions, OutputFormat, convert};

fn djot(html: &str) -> String {
    let options = ConversionOptions {
        output_format: OutputFormat::Djot,
        ..ConversionOptions::default()
    };
    convert(html, Some(options))
        .expect("conversion should succeed")
        .content
        .unwrap_or_default()
}

#[test]
fn should_escape_a_backtick_in_a_djot_table_text_cell() {
    let output = djot("<table><tr><td>a`b</td><td>z</td></tr></table>");

    assert_eq!(output, "| a\\`b | z |\n| ---- | --- |\n");
}

#[test]
fn should_escape_backticks_and_pipes_in_a_wrapped_djot_table_text_cell() {
    let output = djot("<table><tr><td><span>a`b|c</span></td><td>z</td></tr></table>");

    assert_eq!(output, "| a\\`b\\|c | z |\n| ------- | --- |\n");
}

#[test]
fn should_not_escape_the_delimiters_of_a_djot_verbatim_span() {
    let output = djot("<table><tr><td><code>a`b</code></td><td>z</td></tr></table>");

    assert_eq!(output, "| ``a`b`` | z |\n| ------- | --- |\n");
}
