// ~keep Rust inner attributes below are crate-level attributes, not a shell shebang.
#![allow(missing_docs)]
#![cfg(feature = "testkit")]

//! Regression tests for issue #692: in a table cell, the text after a `<center>`, `<search>`,
//! `<hgroup>` or `<dialog>` joined the container's last word, so a heading inside one ran into
//! the text after it. These convert like a `<div>`, so the text after them gets the cell break,
//! and both converters write the same cell.

use html_to_markdown_rs::prescan::PrescanReport;
use html_to_markdown_rs::{ConversionOptions, TierStrategy, convert, tier1};

fn tier2_options(br_in_tables: bool) -> ConversionOptions {
    ConversionOptions {
        extract_metadata: false,
        br_in_tables,
        tier_strategy: TierStrategy::Tier2,
        ..ConversionOptions::default()
    }
}

fn tier2(html: &str, br_in_tables: bool) -> String {
    convert(html, Some(tier2_options(br_in_tables)))
        .expect("conversion must succeed")
        .content
        .unwrap_or_default()
}

fn tier1_run(html: &str, br_in_tables: bool) -> Result<String, tier1::BailReason> {
    let options = ConversionOptions {
        tier_strategy: TierStrategy::Tier1,
        ..tier2_options(br_in_tables)
    };
    tier1::run(html, &PrescanReport::default(), &options)
}

/// The first row each tier writes for `html`, as `(html, br_in_tables off, br_in_tables on)`.
fn check(cases: &[(&str, &str, &str)]) {
    let mut failures = Vec::new();
    for (html, off, on) in cases {
        for (br_in_tables, expected) in [(false, off), (true, on)] {
            let tier2_out = tier2(html, br_in_tables);
            let tier1_out = tier1_run(html, br_in_tables);
            if tier2_out.lines().next() != Some(*expected) || tier1_out.as_deref().ok() != Some(tier2_out.as_str()) {
                failures.push(format!(
                    "{html:?} br_in_tables={br_in_tables}: tier2 {tier2_out:?} tier1 {tier1_out:?}, want {expected:?}"
                ));
            }
        }
    }
    assert!(failures.is_empty(), "row differs:\n{}", failures.join("\n"));
}

#[test]
fn should_keep_a_heading_in_a_div_apart_from_the_text_after_it_in_a_cell() {
    check(&[(
        "<table><tr><td>a<div><h2>h</h2>x</div>y</td><td>z</td></tr></table>",
        "| a h x y | z |",
        "| a<br>h<br>x<br>y | z |",
    )]);
}

#[test]
fn should_keep_a_heading_in_a_div_like_container_apart_from_the_text_after_it_in_a_cell() {
    check(&[
        (
            "<table><tr><td>a<address><h2>h</h2>x</address>y</td></tr></table>",
            "| a h x y |",
            "| a<br>h<br>x<br>y |",
        ),
        (
            "<table><tr><td>a<center><h2>h</h2>x</center>y</td></tr></table>",
            "| a h x y |",
            "| a<br>h<br>x<br>y |",
        ),
        (
            "<table><tr><td>a<search><h2>h</h2>x</search>y</td></tr></table>",
            "| a h x y |",
            "| a<br>h<br>x<br>y |",
        ),
        (
            "<table><tr><td>a<hgroup><h2>h</h2>x</hgroup>y</td></tr></table>",
            "| a h x y |",
            "| a<br>h<br>x<br>y |",
        ),
        (
            "<table><tr><td>a<dialog><h2>h</h2>x</dialog>y</td></tr></table>",
            "| a h x y |",
            "| a<br>h<br>x<br>y |",
        ),
    ]);
}

#[test]
fn should_keep_a_heading_in_a_dialog_after_a_line_break_apart_from_the_text_after_it_in_a_cell() {
    check(&[(
        "<table><tr><td>a<br><dialog><h2>h</h2>x</dialog>y</td></tr></table>",
        "| a h x y |",
        "| a<br>h<br>x<br>y |",
    )]);
}

#[test]
fn should_separate_text_after_a_div_like_container_in_a_cell() {
    check(&[
        (
            "<table><tr><td>a<center>x</center>y</td></tr></table>",
            "| a x y |",
            "| a<br>x<br>y |",
        ),
        (
            "<table><tr><td>a<search>x</search>y</td></tr></table>",
            "| a x y |",
            "| a<br>x<br>y |",
        ),
        (
            "<table><tr><td>a<hgroup>x</hgroup>y</td></tr></table>",
            "| a x y |",
            "| a<br>x<br>y |",
        ),
        (
            "<table><tr><td><dialog>x</dialog>y</td></tr></table>",
            "| x y |",
            "| x<br>y |",
        ),
    ]);
}

/// The same block test decides where text after these containers goes in a list item, so it
/// starts a paragraph in the item there, as it does after a `<div>`.
#[test]
fn should_keep_text_after_a_div_like_container_in_its_list_item_like_after_a_div() {
    let mut failures = Vec::new();
    for container in ["center", "search", "hgroup"] {
        for shape in [
            "<ul><li>a<X>b</X>c</li></ul>",
            "<ol><li><X>a</X>b</li></ol>",
            "<ul><li>a<X><h2>b</h2></X>c</li></ul>",
        ] {
            let html = shape.replace('X', container);
            let expected = tier2(&shape.replace('X', "div"), false);
            let actual = tier2(&html, false);
            if actual != expected {
                failures.push(format!("{html:?}: {actual:?}, want {expected:?}"));
            }
        }
    }
    assert!(
        failures.is_empty(),
        "list item differs from a div:\n{}",
        failures.join("\n")
    );
}
