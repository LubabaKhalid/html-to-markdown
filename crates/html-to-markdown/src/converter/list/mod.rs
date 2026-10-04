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

#[cfg(feature = "visitor")]
pub(super) enum ListStartResult {
    Continue(Option<String>),
    Stop,
}

#[cfg(feature = "visitor")]
pub(super) fn visit_list_start(
    node_handle: &tl::NodeHandle,
    tag: &tl::HTMLTag,
    parser: &tl::Parser,
    output: &mut String,
    context: ListContext<'_>,
    ordered: bool,
) -> ListStartResult {
    use crate::visitor::{NodeContext, NodeType, VisitResult};
    use std::borrow::Cow;

    let Some(visitor_handle) = context.ctx.visitor.as_ref() else {
        return ListStartResult::Continue(None);
    };
    let node_id = node_handle.get_inner();
    let parent_tag = context.dom_ctx.parent_tag_name(node_id, parser);
    let index = context.dom_ctx.get_sibling_index(node_id).unwrap_or(0);
    let tag_name = if ordered { "ol" } else { "ul" };
    let node_ctx = NodeContext::with_lazy_attributes(
        NodeType::List,
        Cow::Borrowed(tag_name),
        tag,
        context.depth,
        index,
        parent_tag.map(Cow::Borrowed),
        false,
    );
    let visit_result = {
        let mut visitor = visitor_handle.lock().expect("visitor mutex poisoned");
        visitor.visit_list_start(&node_ctx, ordered)
    };
    match visit_result {
        VisitResult::Continue => ListStartResult::Continue(None),
        VisitResult::Custom(custom) => ListStartResult::Continue(Some(custom)),
        VisitResult::Skip => ListStartResult::Stop,
        VisitResult::PreserveHtml => {
            crate::converter::serialize_node_to_html(node_handle, parser, output);
            ListStartResult::Stop
        }
        VisitResult::Error(err) => {
            if context.ctx.visitor_error.borrow().is_none() {
                *context.ctx.visitor_error.borrow_mut() = Some(err);
            }
            ListStartResult::Stop
        }
    }
}

#[cfg(feature = "visitor")]
pub(super) struct ListVisitorOutput {
    pub start: usize,
    pub custom_start: Option<String>,
    pub ordered: bool,
}

#[cfg(feature = "visitor")]
pub(super) fn visit_list_end(
    node_handle: &tl::NodeHandle,
    tag: &tl::HTMLTag,
    parser: &tl::Parser,
    output: &mut String,
    context: ListContext<'_>,
    visitor_output: ListVisitorOutput,
) {
    use crate::visitor::{NodeContext, NodeType, VisitResult};
    use std::borrow::Cow;

    let Some(ref visitor_handle) = context.ctx.visitor else {
        return;
    };
    let node_id = node_handle.get_inner();
    let parent_tag = context.dom_ctx.parent_tag_name(node_id, parser);
    let index = context.dom_ctx.get_sibling_index(node_id).unwrap_or(0);
    let tag_name = if visitor_output.ordered { "ol" } else { "ul" };
    let node_ctx = NodeContext::with_lazy_attributes(
        NodeType::List,
        Cow::Borrowed(tag_name),
        tag,
        context.depth,
        index,
        parent_tag.map(Cow::Borrowed),
        false,
    );
    let output_start =
        crate::converter::utility::content::floor_char_boundary(output, visitor_output.start.min(output.len()));
    let visit_result = {
        let mut visitor = visitor_handle.lock().expect("visitor mutex poisoned");
        visitor.visit_list_end(&node_ctx, visitor_output.ordered, &output[output_start..])
    };
    match visit_result {
        VisitResult::Continue => {
            if let Some(custom_start) = visitor_output.custom_start {
                output.insert_str(output_start, &custom_start);
            }
        }
        VisitResult::Custom(custom) => {
            let children_output = output[output_start..].to_string();
            output.truncate(output_start);
            if let Some(custom_start) = visitor_output.custom_start {
                output.push_str(&custom_start);
            }
            output.push_str(&children_output);
            output.push_str(&custom);
        }
        VisitResult::Skip => output.truncate(output_start),
        VisitResult::PreserveHtml => {
            output.truncate(output_start);
            crate::converter::serialize_node_to_html(node_handle, parser, output);
        }
        VisitResult::Error(err) => {
            if context.ctx.visitor_error.borrow().is_none() {
                *context.ctx.visitor_error.borrow_mut() = Some(err);
            }
            output.truncate(output_start);
        }
    }
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
