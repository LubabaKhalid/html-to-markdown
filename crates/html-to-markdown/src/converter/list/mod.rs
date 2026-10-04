//! List element handlers for HTML to Markdown conversion.
//!
//! This module provides specialized handling for various list types:
//! - **Ordered lists**: `<ol>` with counter management and formatting options
//! - **Unordered lists**: `<ul>` with bullet cycling based on nesting depth
//! - **List items**: `<li>` with task list and block-level detection
//! - **Definition lists**: `<dl>`, `<dt>`, `<dd>` elements
//! - **List utilities**: Indentation, loose/tight list detection, nesting depth calculation

pub mod definition;
pub mod item;
pub mod ordered;
pub mod unordered;
pub mod utils;

#[derive(Clone, Copy)]
pub struct ListContext<'a> {
    pub options: &'a crate::options::ConversionOptions,
    pub ctx: &'a super::Context,
    pub depth: usize,
    pub dom_ctx: &'a super::DomContext,
}

/// Dispatches list element handling to the appropriate handler.
///
/// Returns `true` if the element was handled, `false` otherwise.
///
/// # Supported Elements
///
/// - `ol`: Ordered list - routed to `ordered::handle`
/// - `ul`: Unordered list - routed to `unordered::handle`
/// - `li`: List item - routed to `item::handle_li`
/// - `dl`: Definition list - routed to `definition::handle_dl`
/// - `dt`: Definition term - routed to `definition::handle_dt`
/// - `dd`: Definition description - routed to `definition::handle_dd`
pub fn dispatch_list_handler(
    tag_name: &str,
    node_handle: &tl::NodeHandle,
    tag: &tl::HTMLTag,
    parser: &tl::Parser,
    output: &mut String,
    context: ListContext<'_>,
) -> bool {
    match tag_name {
        "ol" => {
            ordered::handle(node_handle, parser, output, context);
            true
        }
        "ul" => {
            unordered::handle(node_handle, parser, output, context);
            true
        }
        "li" => {
            item::handle_li(node_handle, tag, parser, output, context);
            true
        }
        "dl" => {
            definition::handle_dl(node_handle, parser, output, context);
            true
        }
        "dt" => {
            definition::handle_dt(node_handle, parser, output, context);
            true
        }
        "dd" => {
            definition::handle_dd(node_handle, parser, output, context);
            true
        }
        _ => false,
    }
}
