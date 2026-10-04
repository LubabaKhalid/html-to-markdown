## [3.14.0] - 2026-09-16

### Changed

- **Upgraded `html5ever` to 0.40.1, which fixes silent content loss on the HTML repair path.**
  0.40.0's serializer dropped the leading `0xC2` byte of a two-byte UTF-8 sequence, corrupting
  every character in U+0080..U+00BF except NBSP -- `§`, `©`, `°`, `·` among them. Because
  `repair_with_html5ever` serializes the repaired tree back to a string for the primary parser to
  re-read, a single such character made the whole re-parse fail and everything after it vanish.
  This repo was pinned to 0.39.0 to avoid it; 0.40.1 carries the upstream fix, verified here by
  building the same tree against both versions rather than by trusting the release note. A
  regression test now pins the behaviour with non-ASCII fixtures -- the existing repair-path tests
  are ASCII-only and passed on the broken release, which is why the defect was invisible.
- Upgraded `rmcp` to 3.4.0. It deprecates the `ServerInfo` alias in favour of `ServerConfig`
  (the same type, renamed because it collided with the protocol's own `serverInfo` field), so
  the MCP server's `get_info` moved with it. No wire-visible change.

### Fixed

- **Character references in attribute values are now decoded**
  ([#494](https://github.com/xberg-io/html-to-markdown/issues/494)). `<a href>` was the only
  attribute in the converter that called the entity decoder, so every other user-visible
  attribute emitted its raw source text: `title="A&amp;B"` reached the output as the literal
  `A&amp;B`, and `alt="it&#39;s"` as `it&#39;s`. Twelve sites were affected -- `title` on `<a>`,
  `<img>`, `<graphic>` and `<abbr>`; `alt` on `<img>` and `<graphic>`; `src` on `<img>`,
  `<audio>`, `<video>`, `<iframe>` and `<source>`; `cite` on `<blockquote>`; the `language-`
  class on a code fence; and `<meta content>` in extracted metadata. They were found by probing
  every attribute that reaches output, not by reading the ones that looked likely.
  Attribute reads now go through one shared accessor so a new attribute cannot reopen the gap.
  The Markdown escaping is unchanged and was never at fault -- a literal `"` in a title was
  always escaped correctly; the decoded character simply never arrived. Tier 1 carried the same
  defect independently and moves in lockstep.

- **Three Tier-1 divergences that entity decoding made reachable.** Each was latent long before
  it could be triggered, and each is now pinned by a parity test. An `<img>` in a heading was
  emitted as `![alt](src)` by the fast scanner whenever `keepInlineImagesIn` was empty, where
  the DOM path correctly replaces it with its alt text -- an empty list names no heading, so it
  permits nothing. A heading whose body merely *ended* in whitespace was never trimmed, because
  the trim only ran for bodies containing a newline; a decoded `&nbsp;` therefore survived where
  the DOM path dropped it. And a link title containing a quote was escaped as `&quot;` rather
  than `\"`. The first two were found by the generated-corpus parity test over 3,000 documents,
  the third by a sweep over every character decoding newly makes reachable.

- **A wrapper element no longer defeats the nested-table fix**
  ([#488](https://github.com/xberg-io/html-to-markdown/issues/488)). A nested `<table>` inside a
  `<td>` was detected with a single-node tag-name test over the cell's *direct* children, so
  wrapping it in a `<div>` bypassed the 3.12.4 deferral, the pipe escaping and the row fold all at
  once. The inner table's raw `|` characters then read as the *outer* row's cell boundaries on
  reparse -- content loss, not a cosmetic diff. The nested-table *counter* has always descended
  through wrappers; the two now agree. The same line fixes the sibling-cell shape, which was
  corrupt in the same way.

- **Content after a table whose last row is never closed is no longer lost**
  ([#489](https://github.com/xberg-io/html-to-markdown/issues/489)). In
  `<table>...<tr></table><p>Visible footer</p>`, the primary parser discards a close tag that does
  not match the top of its open-element stack, so `</table>` vanished and the paragraph was
  adopted by the still-open `<tr>` -- where the cell collector, which keeps only `td`/`th`, dropped
  it. Such a document now takes the same html5ever repair path that #336, #479 and #486 already
  use. A row that yields no cells also stops emitting a phantom empty row, so the next real row
  becomes the header, matching Tier 1. Two further shapes are fixed by the same gate: a second
  `<tr>` opened without closing the first (its row was silently dropped) and a `<td>` placed
  directly inside `<tbody>` (which produced no output at all). Text-only children are deliberately
  excluded from the gate, so a `<tr>&nbsp;</tr>` spacer does not pay for a full re-parse.

- **An anchor wrapping a table renders the table, not an escaped link label**
  ([#490](https://github.com/xberg-io/html-to-markdown/issues/490)). Any block content inside an
  `<a>` became link-label content, so `<a href="..."><table>...</table></a>` crushed the whole
  table into a single label -- and the label escaper then correctly escaped the markdown that
  produced, leaving an unreadable run of `\|`. The escaping was never the bug; handing a table to
  the label builder was. The anchor's direct children are now partitioned, the inline half forms
  the label and the deferred half renders as blocks after it. Only a deferred subtree that
  actually contains a `<table>` triggers this, and never inside a heading or an inline context,
  so every other anchor shape is byte-identical.

- **A whitespace-only inline wrapper still separates the words around it**
  ([#491](https://github.com/xberg-io/html-to-markdown/issues/491)).
  `Alpha<span style="white-space:pre">\n</span>13` rendered as `Alpha13`. The predicate added for
  #430 asks whether the *next sibling is an element*, so a bare text node after the wrapper took
  the failing path and the newline vanished. Tier 1 was already correct, so the two tiers
  disagreed on this input; they are now pinned together by a parity test. Note that the reported
  `white-space: pre` is incidental -- that property is not implemented, and the defect reproduced
  without it, exactly as a browser collapses the newline to a space either way.
  The wrapper contributes a separator only when the next word butts straight up against it;
  text that already opens with whitespace supplies its own, and is left alone.

- **`keepInlineImagesIn` now means something for `<a>`**
  ([#492](https://github.com/xberg-io/html-to-markdown/issues/492)). The option was consulted for
  headings and for layout cells, but never for anchors, so an `<img>` inside a link that also held
  a block element was replaced by its alt text (or dropped entirely when it had none) no matter
  what the option said. Listing `"a"` now keeps the image as markdown, in both the block and inline
  anchor paths, and for `<graphic>` as well as `<img>`. The change is purely additive -- it can
  turn an image on, never off -- so output is byte-identical for anyone not naming `"a"` in the
  option. The Tier-1 scanner was updated in lockstep.
