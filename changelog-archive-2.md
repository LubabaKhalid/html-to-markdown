## [3.11.4] - 2026-08-22

### Fixed

- `alef.toml`'s `[workspace.docs.snippets]` `timeout_secs` was 120s, which also bounds every
  session's `before` hook. On a cold checkout the kotlin_android (`assembleDebug`), wasm
  (`pnpm run build:all`) and swift (`swift build`) sessions could not finish their `before` build
  within that window, so their snippets were reclassified `unresolved_dependency` and reported
  `Unavailable` — failing CI's `alef snippets check --strict` (`Failed: 0` but a large
  `Unavailable` count) even though no snippet itself was broken. Raised to 900s, matching the
  precedent in tree-sitter-language-pack's `alef.toml`.
- The benchmark regression gate no longer fails at random on the CPU the runner happened to draw.
  `htmbench compare` compared the whole `Provenance` struct for equality, so a capture from an
  Intel Xeon host could not be evaluated against a baseline calibrated on an AMD EPYC host: it
  aborted with `benchmark provenance mismatch` before any timing was compared, even though the
  timings themselves passed every threshold. GitHub's `ubuntu-24.04` label spans both vendors and
  the calibration campaign is `workflow_dispatch`-only, so which host each side drew was a coin
  flip. `cpu_model` and `cpu_count` are now excluded from the provenance contract; every other
  field — rustc, Cargo, profile, build flags, core features, measurement mode, tier and visitor
  selection, iteration/warmup settings, runner image and class — still hard-fails on drift. A
  differing CPU is reported instead as a host mismatch, and the new off-by-default
  `--allow-host-mismatch` flag (passed only by the CI regression job) downgrades timing violations
  to advisory on hardware the baseline was never calibrated on. Thresholds are unchanged and the
  baseline was not re-cut: a regression measured on the calibrated CPU still fails the run.

- The FFI Symbols CI gate is green again. It was failing on two independent findings.

  The `htm_register_html_visitor` allowlist entry is retired. It claimed "visitor registration
  never landed in the FFI crate", which is no longer true: registration landed as the vtable API
  `htm_visitor_create` / `htm_options_set_visitor` / `htm_visitor_free`, and the alef 0.62.6 regen
  (`4765a4139`) replaced the last phantom caller — a Java Panama `SymbolLookup.find(...)` in
  `NativeLib.java` — with lookups of those real symbols. The checker reported the entry as
  *orphaned* rather than *resolved* only because it matches on exact symbol names and the
  replacement uses different ones. The C# visitor surface reaches the same exports through
  `NativeMethods.cs` and `HtmlToMarkdownConverter.Convert`, and all 49 tests in
  `e2e/csharp/tests/VisitorTests.cs` pass against the built native library, so the public
  `IHtmlVisitor` / `HtmlVisitorBridge` API is wired end to end.

  `htm_node_type_from_json` is allowlisted, replacing it. The alef 0.62.9 regen (`dc27e0560`)
  re-added a C# P/Invoke for it, but `NodeType` is a fieldless `Copy` enum: it crosses the C ABI
  as `int32_t`, so the FFI exports `htm_node_type_from_i32` / `htm_node_type_from_str` and no
  handle-returning `from_json`. Nothing calls `NodeTypeFromJson`, so the declaration is latent
  rather than a live crash. This is a re-regression — the same symbol was allowlisted and retired
  once before in `555a29d20`. Fixed upstream in alef's C# backend, which now skips scalar-crossing
  named types when emitting handle-lifecycle P/Invokes; the entry comes out with the first regen
  on an alef release carrying that fix.

- A failed per-language artifact build no longer aborts the release. In v3.11.3 four
  `Build PHP extension (... windows-x86_64)` legs failed and nothing else did, yet the GitHub
  release was never promoted out of draft, never finalized and never announced, and the Homebrew
  bottles, `cargo-binstall` verification, Packagist trigger and asset audit never ran — 3.11.3
  reached every language registry but its release page stayed a draft.

  Two GitHub Actions behaviours caused it, and the publish workflow now accounts for both. A
  failure propagates down the entire `needs` chain, so a job's implicit `success()` gate is false
  even when its own direct needs succeeded; and the propagated failure also poisons the *value* of
  `needs.<job>.result`, so `upload-php-pie-release` reported `failure` to downstream jobs despite
  concluding `success` — which is why `always()` plus `!contains(needs.*.result, 'failure')` still
  skipped `verify-assets`, `release-finalize` and `announce-discord`.

  The release spine (`promote-release` → `release-finalize` → `announce-discord`, plus
  `verify-binstall` and the Homebrew bottle jobs) now gates only on jobs whose whole ancestry is
  release-blocking: version validation, crates.io, and the CLI and C FFI assets. Per-language
  artifact jobs stay in `needs` for ordering — the draft still flips only after every asset upload
  has settled — but their results no longer appear in any gate. `promote-release` publishes a
  `promoted` output for downstream jobs to gate on, because job outputs carry no failure poison.

### Added

- A `Report release outcome` job closes the workflow. It reads the run's real job conclusions from
  the API and writes a job summary stating whether the tag shipped and naming every artifact that
  is missing, then fails the run if anything failed. A release that ships without one language's
  binary is now red and explicitly labelled incomplete rather than silently green.

### Changed

- `Verify release assets` is a reporting gate rather than a release gate. It runs on every real
  tag and no longer guards itself with `!contains(needs.*.result, 'failure')`, which had skipped
  the asset audit in exactly the situation the audit exists for. Nothing in the release spine
  depends on its result.

## [3.11.3] - 2026-08-21

### Fixed

- Leading normalized whitespace at the start of a paragraph is no longer emitted before an image,
  preventing CommonMark from interpreting the image as an indented code block
  ([#460](https://github.com/xberg-io/html-to-markdown/issues/460)).

- The Swift crate compiles again. Codegen emitted a bare `EnumName::Variant` path for
  data-carrying variants when converting a Swift string back into a Rust enum, which rustc rejects
  with `E0533: expected value, found struct variant`; the regenerated crate routes those through
  per-enum string conversion helpers instead.

- The e2e freshness gate no longer fails on formatting it cannot produce. It installs Elixir, so
  alef's `mix format` pass runs there as it does locally — without it the job emitted unformatted
  `.exs` and reported the difference as fixture staleness.

- The crates.io skip guard reads a real output again. The publish workflow asked
  `check-registry` for an `extra-packages` key (`cli_exists`), but a composite action propagates
  only the outputs it declares, so that key arrived as an empty string and the derived `all_exist`
  could never be true. The guard has therefore never once skipped an already-published version. It
  now reads the action's declared `all-exist` output.

### Changed

- `packages/java/pom.xml` is alef-owned and regenerated. It had drifted out of alef's ownership
  since roughly alef 0.60.x for want of a provenance marker, so this release lands the accumulated
  template changes at once: the file is reindented to four spaces, gains `<excludes>` /
  `<sourceFileIncludes>` blocks, and moves checkstyle to 13.11.0 and jackson-databind /
  jackson-datatype-jdk8 to 2.22.2. Those versions are alef's pinned template defaults, not
  html-to-markdown-specific choices.

- All Rust dependencies taken to their latest versions (`cargo upgrade --incompatible` followed by
  `cargo update`): `rmcp` / `rmcp-macros` 3.1.2 to 3.1.4 plus twelve transitive bumps. Fourteen
  packages changed, none downgraded.

- alef pinned to 0.62.8.

- The benchmark harness now records nine timing samples with median and median absolute deviation,
  captures runner and toolchain provenance, and supports reviewed fixture-specific noise floors
  without changing the existing percentage regression thresholds
  ([#461](https://github.com/xberg-io/html-to-markdown/issues/461),
  [#462](https://github.com/xberg-io/html-to-markdown/issues/462)).

- Java's `VisitResult` is now a plain sealed interface. Its Jackson `@JsonSerialize` /
  `@JsonDeserialize` annotations and the nested serializer and deserializer classes are gone; the
  visitor bridge marshals the type directly and never routed it through Jackson.

### Removed

- The unused Java visitor classes `IHtmlVisitor`, `HtmlVisitorAdapter` and `HtmlVisitorBridge`.
  They shipped alongside the live `HtmlVisitor`, `VisitorBridge` and `VisitorHandle` surface but
  nothing in the binding referenced them, so an implementation of `IHtmlVisitor` was never
  invoked. Implement `HtmlVisitor` instead.

## [3.11.2] - 2026-08-19

### Fixed

- The R package now builds against the vendored core crate instead of failing to resolve it.
  `configure` stripped the `path = ...` clause from `src/rust/Cargo.toml` and wrote a cargo source
  replacement to `src/rust/.cargo/config.toml`, but cargo reads `.cargo/config.toml` only from the
  working directory and its ancestors, and `Makevars.in` runs cargo from `packages/r/src` — so
  `src/rust/.cargo` is a descendant and that config was never read on any build. With the path
  clause gone the dependency fell through to crates.io, which did not have the workspace version.
  The path is now rewritten to point at the vendored copy, which needs no cargo config, no
  `.cargo-checksum.json`, and no complete vendor tree.

- Newlines inside a table cell no longer leak into the rendered row when `br_in_tables` is enabled
  ([#456](https://github.com/xberg-io/html-to-markdown/issues/456),
  [#457](https://github.com/xberg-io/html-to-markdown/issues/457)). The whole-cell newline backstop
  was gated on `!br_in_tables`, so enabling `br_in_tables` disabled the last-resort guarantee that a
  raw newline never reaches a cell. Two consequences: a `<pre>` inside a cell now renders inline,
  dropping its fence, indentation and language info string, matching how headings and list items
  already render in cells; and under `WhitespaceMode::Strict` a newline inside a cell now folds to a
  single space. Every other whitespace byte is still preserved exactly under `Strict`, and text
  outside table cells is unaffected.
- The Tier-1 fast path now honours `br_in_tables` inside table cells. It previously emitted a
  sentinel that always expanded to three spaces, ignoring the option, so a document routed through
  Tier-1 could render `<br>` in a cell differently from the same document routed through Tier-2.
  Tier-1 also folds a text node's trailing newline the way Tier-2 does, fixing cells that were
  double-spaced against Tier-2 when the source HTML was pretty-printed across several lines.
- A literal backslash in HTML prose is no longer silently lost when the Markdown is read back
  ([#458](https://github.com/xberg-io/html-to-markdown/issues/458)). CommonMark consumes a backslash
  that precedes ASCII punctuation, so emitting `3\*4` from `<p>3\*4</p>` produced Markdown that
  reparsed as `3*4` — the source character was gone. Such a backslash is now doubled, and so is one
  that sits immediately before a line ending (where CommonMark would read it as a hard line break)
  or at the end of a text run (where whatever the emitter appends next would become its escape
  target). This changes output under default options: any document whose prose contains a backslash
  in one of those three positions gains a second backslash there. A backslash before anything else
  is already literal and is still emitted bare, so Windows paths such as `C:\Users\Alice` are
  unchanged. Code spans, code blocks and link titles are also unaffected — the first two are
  verbatim by design and the third already escaped backslashes through its own rule. The escape is
  deliberately not gated behind `escape_misc` or `escape_ascii`, because it preserves a character
  the source actually contained rather than neutralising Markdown syntax the way those flags do.

## [3.11.1] - 2026-08-15

> Prepared but never published: no `v3.11.1` tag was pushed and no 3.11.1 reached crates.io,
> so 3.11.0 is followed directly by 3.11.2. The entries below ship as part of 3.11.2.

### Upgrade note — the C ABI changed

This release changes the C header, so it is not drop-in for C, Go (cgo) or any other consumer that
links the native library directly. Rebuild against the new header rather than reusing an existing
build. Managed bindings (Python, Node, Ruby, PHP, Java, C#, Elixir, R, WASM) are unaffected.

- `HTMHtmHtmlVisitorBridge` and `HTMHtmHtmlVisitorVTable` are gone. Borrowed types that cannot enter
  the process-global handle registry are no longer exported, so the bridge entry points
  `htm_htm_html_visitor_bridge_new` and `htm_htm_html_visitor_bridge_free` are removed with them.
  Use the `HTMHtmVisitorCallbacks` vtable instead.
- `htm_free_bytes` is removed. The exported function count goes from 307 to 304.
- `HTMHtmVisitorCallbacks` gains a `void (*free_string)(char*)` member, which changes the struct
  layout. Any code that constructs this struct must be recompiled, and callers that hand out heap
  strings from a callback should set it so the library releases them with the matching allocator.

The header previously in the tree described a surface the sources had already stopped providing;
it is now regenerated from them.

### Fixed

- The generated FFI, Swift and Node sources did not compile, so the native library, the Swift
  package and the Node addon could not be built from a checkout. A comment-reflow pass had merged
  `unsafe {` into the preceding `// SAFETY:` comment at 40 sites in the FFI bridge and collapsed a
  doc block in the Swift bridge over the `SwiftHtmlVisitorWrapper` declaration, so neither file
  parsed; the Node addon applied a napi `getter` to three free functions, which napi allows only
  inside an `impl` block. This also blocked every commit to the repository, because the pre-commit
  hook compiles the staged snapshot and the FFI build script runs cbindgen over `lib.rs`.
- The FFI null-safety test called `htm_htm_html_visitor_bridge_free`, a symbol the crate had
  deliberately stopped exporting, so the test target did not build.

## [3.11.0] - 2026-08-13

### Upgrade note

Rendered Markdown output changes in this release. The CSS-hidden/`hidden`-attribute fix below alone
moved 56 of the 116 benchmark oracle snapshots when they were reblessed, and roughly a dozen other
correctness fixes in this range shift output for the documents they affect — 64 of the 116
snapshots changed in total. Consumers who pin byte-exact golden files against this library's
output should expect to regenerate them when upgrading past this release.

A further 16 snapshots moved when hidden-element detection was corrected to read attribute
structure instead of scanning raw tag text. Every one of those 16 **restores content that was
previously deleted**: a Wikipedia link whose `title` attribute contained the word "hidden" was
being stripped in full. If you saw links or sections disappear from converted pages, this is why.

### Added

- Documentation snippets are generated from the complete E2E fixture corpus with Alef 0.60.2 and checked for
  fixture-by-language coverage parity in local tasks and CI; strict validation is scoped to the generated root so
  the 85 maintained examples remain independently audited.
- The MCP server validates its inputs, bounds its HTTP surface and is instrumented. It previously
  had no instrumentation at all despite being a public RPC surface: a failed request returned an
  error to the client and left no trace. There are now debug spans on `convert_html` and
  `extract_metadata` (re-entered inside `spawn_blocking`, which does not inherit the caller's
  span), warnings on rejected enum values and conversion errors, and an error event on a panicking
  blocking task. Behaviorally, unknown enum values from a client are rejected instead of silently
  falling back to a default, a `max_depth` that does not fit `usize` warns instead of silently
  becoming `usize::MAX`, five serialization fallbacks that returned `null`/`[]` on failure now
  report the failure, and the HTTP transport gained a body-size limit, a concurrency cap, a request
  timeout, and Origin/Host checks.
- `VisitResult` now serializes with an adjacently tagged, snake_case wire schema
  (`{"type": …, "output": …}`), so every binding encodes against one documented shape instead of
  inventing its own. The field names are public API and a conformance test pins them.

### Changed

- Table rendering: each cell's Markdown is now produced once and reused between the column-width
  pre-pass and the render pass, instead of being rendered twice, for the common case (no nested
  table, no visitor installed). Rendered Markdown is unchanged — reblessing the benchmark oracle
  snapshots before and after produced byte-identical output. This also fixed the metadata
  collector recording every element inside a `<td>` twice, once per pass, on the default
  extraction path. See `crates/html-to-markdown/tests/table_cell_metadata_duplication_test.rs`.
- Link handling: fewer anchor traversals and allocations per `<a>` element. Output-neutral.
- Removed the internal `text_content` LRU cache and with it the `lru` dependency. Because every
  caller needs an owned `String`, a cache hit still cloned, so the cache cost an allocation per
  miss and saved none; after the table change above, the dominant table path cannot hit it at all.
  Measured 3.7% faster across the 29-fixture benchmark. Output-neutral.
- DOM context building: the per-document context maps (parent, children, sibling-index, and
  related lookup tables) are now sized once from the arena's node count up front instead of
  growing incrementally as new node ids are seen. Output-neutral.
- `alef` is pinned to `0.60.2` for binding generation, in `alef.toml` and in the CI lint workflow.
  The two had drifted apart (`0.60.2` locally, `0.60.1` in CI), so CI generated with a different
  generator than every developer.
- `poly`'s whole-project lint phase is now disabled through `[workspace.poly] lint-workspace` in
  `alef.toml` rather than a hand-edit to the generated `poly.toml`. The shared CI validate job
  installs only Rust/Python/Java, so the remaining whole-workspace linters cannot run there; they
  run via the pre-commit hooks and each language's own CI job. The previous hand-edit did not
  survive `alef all --clean`.
- Dependency upgrades, including `base64` and `tower-http` to their next major versions.
- `html-to-markdown-cli` gained optional `mimalloc` and `jemalloc` global-allocator features
  (`--features mimalloc` / `--features jemalloc`). Neither is enabled by default; if both are
  enabled, `jemalloc` takes precedence, so `--all-features` builds continue to work.
- `mcp-http` is no longer a default feature of `html-to-markdown-cli`. It was on by default, so a
  CLI installed via brew, cargo, npm or pip shipped the ability to start an unauthenticated HTTP
  service. Build with `--features mcp-http` if you need it; stdio `mcp` stays on by default, since
  it opens no listening socket.

### Fixed

- `<br>` inside a table cell no longer depends on `newline_style` or on the source HTML's own
  whitespace ([#453](https://github.com/xberg-io/html-to-markdown/issues/453)). Two separate
  defects: with `br_in_tables: false` the `<br>` fell through to the paragraph hard-break path and
  emitted `newline_style` bytes into the cell, leaking a literal `\` under `Backslash` and a stray
  extra space under `Spaces`; and a newline in the source before the `<br>` survived normalization,
  so with `br_in_tables: true` it reached the output as a real newline and split the row's pipe
  syntax across physical lines, corrupting the table. A cell cannot contain a hard line break, so
  `<br>` now collapses to a single space, or renders as a literal `<br>` when `br_in_tables` is
  enabled, in every combination of the two options and regardless of source formatting.
- `<div>` and `<p>` continuations inside a table cell follow the same rule as `<br>`
  ([#454](https://github.com/xberg-io/html-to-markdown/issues/454)). The two disagreed with each
  other: a `<div>` continuation honoured `br_in_tables` but emitted `newline_style` bytes, which are
  not valid inside a cell, while a `<p>` continuation always emitted `<br>` and ignored
  `br_in_tables` entirely. Both now emit a literal `<br>` when `br_in_tables` is enabled and collapse
  to a single space otherwise, sharing one code path with the `<br>` handler.
- A `<code>` span inside a table cell no longer corrupts the row
  ([#455](https://github.com/xberg-io/html-to-markdown/issues/455)). Verbatim content — `<code>`,
  and `<kbd>`/`<samp>`, which share the same path — skipped cell whitespace handling entirely, so a
  newline inside the span reached the output and split the row's pipe syntax across physical lines
  whenever `br_in_tables` was enabled. Line breaks in that content are now folded to a single space,
  independent of `whitespace_mode`, because a raw newline in a cell is a structural impossibility in
  GFM rather than a formatting preference. All other whitespace, including repeated spaces, is still
  preserved byte-for-byte, and code spans outside a table cell are unaffected.
- Document-structure and inline-image collectors also record table-cell content exactly once.
  Images, code blocks and nested tables inside a `<td>` were recorded up to three times with
  `include_document_structure: true`, and inline images twice with `extract_images: true`. Note the
  companion change: a table that renders to nothing (a blank table, or one a visitor skips) now
  contributes nothing to `document` or the inline-image set, matching what it emits; `result.tables`
  still reports its grid.
- Metadata extracted from inside a table cell (links, images) is now recorded exactly once in
  every configuration. Previously a link in a `<td>` was recorded twice with
  `link_style: Reference`, and three times with `include_document_structure: true`, because the
  column-width pre-pass, the render pass, and the document-structure grid walk each re-walked the
  cell through a shared collector. The internal passes no longer record; exactly one walk does.
  Affects `metadata.links` / `metadata.images` counts for documents with tables — de-duplication
  on the consumer side is no longer needed.
- Rows with more cells than the header no longer lose them. The separator row was sized from the
  first row alone, so any later row with more cells had the surplus silently dropped by compliant
  renderers; it is now sized from the table-wide maximum and every row is padded to match.
  Separately, `scan_table_node` counted nested tables and rows transitively across nested `<table>`
  boundaries, so the layout-table heuristic misfired for every level of a nested chain except the
  innermost, turning real table structure into a mix of bullet lists and stray pipe text.
- Consecutive `<li>` elements inside a table cell no longer fuse into one word. A cell strips list
  markers, and nothing separated the items, so `<li>a</li><li>b</li>` rendered as the fabricated
  word `ab`. Both tiers now emit the same `<br>` boundary already used between sibling `<p>`/`<div>`
  in a cell.
- Content that a browser never renders is no longer emitted. `<template>` and `<noscript>` fell
  through to the unknown-element handler, which recurses into children and renders their text — a
  template's contents are inert per spec and must never appear in the output — and
  `strip_hidden_elements` honoured only the `hidden` attribute, so `style="display:none"` and
  `visibility:hidden` leaked in full. This is the single largest source of output drift in this
  release: it alone moved 56 of the 116 benchmark oracle snapshots. `aria-hidden` is deliberately
  untouched, because that content is visually rendered and hidden only from assistive technology.
- Hidden-element detection no longer misreads the tag it is inspecting, in three separate ways.
  `declaration_hides_element` split each declaration on the first `:`, so a CSS comment ahead of the
  property name left `/* note */ display` as the property and never matched —
  `<div style="/* note */ display:none">SECRET</div>` emitted its content; comments are now
  stripped before the split. `tag_has_hidden_attribute` scanned the raw tag text for the word
  `hidden` and matched inside quoted values, so a perfectly visible
  `<div title="… hidden from search engines">` was deleted whole; it now walks `name=value` pairs
  and matches attribute *names*. And `tag_has_hidden_style` used `.any()` over declarations,
  ignoring the CSS cascade, so `display:none; display:block` was stripped even though the last
  declaration wins; it now resolves per property. The second of these is why 16 oracle snapshots
  gained content back — see the Upgrade note.
- Content nested inside a CSS-hidden element (`style="display:none"` / `visibility:hidden`, or the
  `hidden` attribute) no longer leaks into the output when the hidden element contains a nested
  element of the *same* tag name (e.g. a hidden `<div>` containing another `<div>`). The stripper
  previously matched the closing tag of the *inner* element rather than the outer one, so text
  after the inner close tag — and, for deeper nesting, several more layers of "hidden" text — was
  emitted as if it were visible. This affects any document with same-tag-name nesting inside a
  hidden element, including a common Wikipedia infobox pattern; see
  `crates/html-to-markdown/tests/hidden_element_nesting_test.rs` for the affected shapes. Output
  changes for documents that hit this pattern.
- Hidden content no longer escapes through a `</tag>` sequence that is not really markup. The
  depth-counting stripper still treated any `</tag>` byte sequence as a close tag, so four measured
  shapes leaked against the release binary on default options: a `<!-- </div> -->` end-of-block
  marker (an ordinary authoring idiom, requiring no crafting) leaked the trailing text, a quoted
  attribute value containing `</div>` leaked, a `</div>` inside a preserved `application/ld+json`
  raw-text body leaked, and an unbalanced `<div>` inside a comment inflated the depth counter far
  enough that the scan overshot and dropped the following visible sibling. The scan now skips
  comments, CDATA and raw-text bodies, and advances non-target tags through a quote-aware
  tag-end search.
- Alt text, titles and media URLs are escaped before they are spliced into Markdown. The hardening
  applied to `<a href>` was never propagated to images, graphics or embedded media, so inert input
  produced live output: an alt of `a](https://evil.example)` emitted a real image pointing at that
  URL; `<audio>`, `<video>` and `<iframe>` used `src` as both label and destination with no
  escaping at all; `<graphic>` had no paren handling whatsoever; and a bare quote in a title closed
  the Markdown title early, leaving the remainder to parse as document text. The `<a>` path's
  `append_url_destination` and `escape_markdown_title` are now shared by all of them, so
  balanced-paren checking (which had treated `)(` as balanced) guards image destinations too. Alt
  and title text containing brackets or quotes is now escaped, which changes output for benign
  documents as well.
- The HTML serializers are depth-bounded and quote-safe. `serialize_element`/`serialize_node` in
  the SVG and utility paths mutually recursed over arbitrary-depth subtrees with no depth parameter
  at all — a remote stack overflow, reproduced as a SIGABRT with 50k nested `<g>` or `<mrow>` — and
  are reachable from roughly twenty call sites via `preserve_tags` and the visitor's `PreserveHtml`
  result. They now truncate with a warning at the native stack-safe depth. Both also re-quoted
  every reconstructed attribute with double quotes without escaping an embedded one, so a
  single-quoted attribute holding a literal quote — valid, inert HTML — reconstructed into extra
  live attributes, turning an inert `title` into a real `onclick` handler. Values are now escaped
  regardless of the source delimiter.
- Deeply nested documents no longer exhaust the machine. Three separate defects made the depth
  guard ineffective: roughly two dozen call sites forwarded the recursion depth unchanged while
  descending into a child, every table-cell walk passed a literal `0` and so reset the budget at
  each cell boundary (a remote stack-overflow SIGSEGV from repeated `<table><tr><td>`), and two
  passes outside the depth-bounded walk were quadratic in nesting depth —
  `has_inline_block_misnest` ran once per block node and walked to the root each time, and
  `scan_table_node` re-walked the whole remaining nested-table chain from every table. A 220KB
  document of 20k nested `<div>`s went from 30.5s to 0.06s, and 50k-deep table, div, svg, ol and
  blockquote payloads — three of which previously ran past two minutes — now all finish in under a
  second. This was remote resource exhaustion: the guard bounded the walk but not these passes.
- A code block containing a run of three or more backticks — an embedded Markdown sample, say — no
  longer closes early and corrupts everything after it. The opening fence was hardcoded to three
  characters; its length is now `max(3, longest_run + 1)`. Inline code spans use a different rule
  on purpose: the smallest delimiter length not present in the content, because CommonMark closes a
  span at a backtick string of the *same* length, so `max_run + 1` would over-escape (CommonMark
  examples 330 and 331).
- An out-of-range `<ol start>` no longer panics the whole conversion. `start` was parsed as `usize`
  with an unchecked per-item increment, so `start="18446744073709551615"` with a single `<li>`
  overflowed and failed the entire document rather than just the list. The counter is now `i64`,
  so a negative start counts down as browsers do, out-of-range magnitudes clamp with a warning, and
  the increment pins at `i64::MAX` instead of wrapping. The saturation warning fires once per list
  rather than once per item, so a long list cannot flood the logs.
- Blockquotes preserve significant leading whitespace. The per-line loop trimmed every content
  line, so indented code blocks and nested-list continuations inside a `<blockquote>` lost their
  indentation entirely; only whitespace-only lines are blanked now. Nested blockquotes also pushed
  a hardcoded three newlines regardless of what preceded them, emitting stray blank `>` lines, and
  a paragraph following bare inline text inside a blockquote merged onto the same line because the
  separator was gated off inside blockquotes altogether. The gate is now depth-aware, which leaves
  the compact heading-then-paragraph style alone (CommonMark example 228 depends on it).
- A list nested inside an ordered list is now indented to its parent marker's content column
  instead of a uniform `list_depth * list_indent_width`. That uniform width happens to match `"- "`
  but not `"1. "` (3 columns) or `"10. "` (4), so a nested ordered list was indented 2 columns and
  CommonMark parsed the child as a sibling of its parent. The indent is now the cumulative width of
  the ancestors' own markers, with `list_indent_width` as the floor.
- A panicking visitor callback no longer poisons the handle for every later call. The panic
  unwound out of `convert()` and left the visitor's `Mutex` poisoned, so every subsequent
  conversion reusing that handle failed permanently. The pipeline now runs under `catch_unwind` and
  clears the poison flag, confining the failure to the call that caused it.
- Three inline-image options finally do something. `InlineImageConfig::new` seeded its own
  defaults and the conversion path never overwrote them, so `capture_svg`, `infer_dimensions` and
  `max_image_size` were inert despite each having both a builder setter and an update field — and
  two of those internal defaults were the inverse of the documented ones: `capture_svg` documented
  `false` but always behaved as `true`, and `infer_dimensions` documented `true` but always behaved
  as `false`. `max_image_size` was ignored outright and only ever coincided with the internal
  constant. Callers who set any of the three will see behavior change to what the documentation
  always promised.
- The Tier-1 byte-scanner path agrees with Tier-2 again. It carried independently duplicated
  copies of the code-fence and inline-delimiter bugs fixed above, had no depth ceiling, silently
  returned an empty `result.metadata`, emitted hidden elements that Tier-2 strips, and left link,
  image and SVG-title labels unescaped — the last being the injection vector Tier-2 has guarded for
  some time. It also evaluated only one of Tier-2's three layout-table conditions, so a
  `<table border="0">` with a `colspan`, or two nested tables, produced a GFM table (in the nested
  case, a malformed one) where Tier-2 produced a bullet list. Tier-1 now bails on both shapes
  rather than reimplementing them, and the router defers to Tier-2 for metadata rather than
  maintaining a second collector — a second implementation of that collector is precisely what
  produced the duplicated fence bugs. Default options never reach Tier-1, so this affects only
  callers who force `TierStrategy::Tier1` or disable metadata extraction.

- Python visitor callbacks now honor the documented `type`/`output` action dictionaries for
  custom link output and image `skip`/`continue` actions ([#452]).

- Dart: the native loader downloads and caches the library again on a cold cache. It only read
  the versioned cache and then threw a `StateError`, even though `nativeDownloadAndCacheLibrary()`
  was defined and exported for exactly that case — so a machine that had never run
  `dart run h2m:download_libs` could not self-heal. The loader also now searches for the
  `_dart`-suffixed cdylib that is actually built, opens every candidate by absolute path (a
  hardened runtime rejects a relative `dlopen`), walks up from `Platform.script` to find the
  package root as a last resort, and names the real environment variable in its error message
  instead of printing the identifier `$nativeLibDirEnv` literally. Fixed upstream in alef 0.55.6.

  Behavior change: an unresolvable native now throws a descriptive `StateError` naming the asset
  URL and the download command, where it previously returned `null` and let flutter_rust_bridge
  attempt its own relative-path `dlopen` — which would fail anyway, but later and less legibly.

- Java: `TierStrategy` serializes to the wire names the core actually accepts. Alef 0.55.7 changed
  the Java backend's no-`rename_all` fallback to emit variants verbatim, but it could not see
  `rename_all` when it sat behind a `cfg_attr` with an `any(...)` condition — exactly how
  `TierStrategy` declares it. The generated Java therefore sent `Auto` to a core that deserializes
  `auto`, and every Java conversion failed with `unknown variant`. Fixed upstream in alef 0.55.8,
  which parses the `cfg_attr` condition structurally.

- CI: the Node e2e job no longer runs the Rust test suite. It invoked `task rust:test`
  (`cargo test --release --no-default-features --workspace`), a full release-mode build that took
  3047s of the job's 60-minute budget on `windows-latest` and left `Install alef` to be cancelled
  mid-step — the Windows Node e2e job had never once completed. `CI Rust` already runs the suite on
  ubuntu, windows and macos via `task rust:test:ci` and compile-checks `--no-default-features`
  separately, and no other language's e2e job ran it. The job now passes in 925s.

- Node: the named ESM re-exports that work around napi's `module.exports = nativeBinding` tail
  (#450) are now committed in `crates/html-to-markdown-node/index.js`, not only appended at publish
  time. `cjs-module-lexer` cannot analyse that tail, so `import { convert } from ...` broke for
  anyone consuming the repo directly. Published packages were already correct — both
  `task alef:generate` and the publish workflow run the fixup script — but the committed file was
  not, which also meant a regenerate-and-diff freshness check could never pass.

- `--newline-style`, `--code-block-style` and `--bullets` all documented the wrong default in the
  CLI's `--help`, so users following the help text got output they did not expect. Tests now
  assert the real defaults, so help text and behavior cannot drift apart silently again.

- The CLI's outbound User-Agent is derived from the crate version. It was a literal pinned at
  `2.10` while the crate shipped `3.10.x`, so every fetch advertised a version four majors stale.

- The coding-agent plugin's launcher downloads the right asset and verifies it. It fetched
  `html-to-markdown-<triple>` while releases publish `cli-<triple>`, so every download 404'd and
  silently fell through to the slow path — the fast path had never once worked — and it then
  executed whatever it did fetch, with only TLS vouching for the bytes. It now resolves the
  checksum from `cli-SHA256SUMS`, retries while GitHub propagates release assets, and refuses to
  execute a binary it cannot verify.

- The Dart, Swift and Zig package READMEs are full documents again (276 / 271 / 260 lines). A
  partial generator run had replaced all three with fallback stubs of ~30 lines; Dart's stub was
  the pub.dev landing page rather than the package README.

- Internal: `strip_css_comments` uses `let ... else` instead of a single-arm `match`, which was a
  `clippy::single-match-else` error under `-D warnings` and failed the workspace clippy gate.

## [3.10.6] - 2026-08-05

### Fixed

- Node.js: the `linux-x64-musl` and `linux-arm64-musl` packages really are published now. 3.10.5
  added them, but both cross-compiles failed to link (`cannot find libgcc_s.so.1`) and, because the
  npm publish job requires every matrix leg, no Node package reached the registry at all. The build
  action exported `CC`/`CARGO_TARGET_*_LINKER` pointing at `musl-gcc`, and cargo-zigbuild only sets
  those when they are unset, so the zig cross-compile was silently replaced by a host-arch musl-gcc
  that cannot produce a musl cdylib. The musl legs now opt out of that export.

### Added

- CI: the musl Node cross-compiles are built on every core/node change instead of only at publish
  time, and the job fails if a platform package ends up without a native module.

## [3.10.5] - 2026-08-05

### Fixed

- Node.js: the `linux-x64-musl` and `linux-arm64-musl` packages are now built and published. They
  were advertised in the main package's `optionalDependencies` but never produced, so Alpine and
  other musl installs silently fell back to no native binding, and `pnpm install --frozen-lockfile`
  could not resolve them.
- Ruby: the gem no longer publishes its generated types into the global `Object` namespace, which
  collided with unrelated libraries (notably the `parser` gem's `Parser` constant). Generated types
  now stay namespaced under `HtmlToMarkdown` (tree-sitter-language-pack issue #173).
- Documentation: every code snippet in the READMEs, the docs site, and the coding-agent plugin
  references was executed against the real API and corrected. The Rust README's metadata and custom
  visitor examples did not compile, the Rust API reference showed `Result<_, Error>` instead of
  `Result<_, ConversionError>`, the docs site shipped 102 empty language tabs across five pages, and
  several bindings' snippets referenced helpers that no longer exist.

## [3.10.4] - 2026-08-04

### Fixed

- Node.js: named ESM imports such as `import { convert } from "@xberg-io/html-to-markdown"` now
  resolve. The napi-generated `index.js` ended with `module.exports = nativeBinding`, which Node's
  ESM↔CJS interop (`cjs-module-lexer`) cannot statically analyze, so named imports threw
  `SyntaxError: The requested module ... does not provide an export named 'convert'`. The build now
  appends explicit `module.exports.<name> = nativeBinding.<name>` re-exports for every public
  runtime export; `require()` is unaffected ([#450]).

[#450]: https://github.com/xberg-io/html-to-markdown/issues/450
[#452]: https://github.com/xberg-io/html-to-markdown/issues/452

## [3.10.3] - 2026-08-04

### Fixed

- The Swift package now builds under Xcode/XCBuild, not just `swift build`. The `RustBridgeC`
  target was header-only, so XCBuild failed to link (`RustBridgeC.o` was never emitted) for every
  iOS/macOS consumer of the published SwiftPM package. It now ships a translation unit with an
  anchor symbol so the object is always produced ([#449]).

### Changed

- The PHP binding sources now live in the `html-to-markdown-php` crate alongside the other
  in-crate bindings; the standalone `packages/php` layout has been removed. Composer consumers are
  unaffected.

[#449]: https://github.com/xberg-io/html-to-markdown/issues/449

## [3.10.2] - 2026-08-01

### Added

- `cargo binstall html-to-markdown-cli` support (#448) — prebuilt CLI binaries can now be
  installed directly from GitHub Releases without compiling from source. Adds
  `[package.metadata.binstall]` to the CLI crate plus a release-time `verify-binstall` CI
  job that installs via `cargo binstall` and smoke-tests the binary.

### Changed

- Updated dependencies.

## [3.10.1] - 2026-07-31

### Fixed

- The Android AAR (`io.xberg:html-to-markdown-android`) now bundles its JNI native libraries.
  Previously the published AAR contained no `.so` files, so every consumer crashed at runtime with
  `UnsatisfiedLinkError: library "libhtm_jni.so" not found` ([#446]). The publish workflow built
  the wrong crate (the C-FFI `html-to-markdown-ffi`) and uploaded it from a path the build action
  never wrote, staging nothing. It now builds the JNI crate (`html-to-markdown-rs-jni` →
  `libhtm_jni.so`) and stages it for every ABI, and a regenerated Gradle guard (alef 0.48.16) fails
  the build if a correctly-named `lib*_jni.so` is ever missing.

### Added

- The core library now emits structured `tracing` spans and events as a first-class observability
  surface: an `html_to_markdown::convert` span (`input_len`, `output_format`, `wrap`,
  `extract_metadata`, `extract_images`, `tier_strategy` fields) wraps every conversion, with
  `DEBUG` events at parse/walk/render stage boundaries and `WARN`/`ERROR` events on recovered or
  fatal failures. The library never installs a subscriber — attach one in your application to
  observe it. The CLI now initializes a `tracing-subscriber` (respecting `RUST_LOG`, with
  `--debug` raising the default level) and routes all diagnostics through `tracing` instead of raw
  `stdout`/`stderr` writes.

### Changed

- Android AAR now ships four ABIs (`arm64-v8a`, `x86_64`, `armeabi-v7a`, `x86`).
- Upgraded dependencies to latest, including `base64` 0.23 and `rmcp` 3.0.1.

[#446]: https://github.com/xberg-io/html-to-markdown/issues/446

## [3.10.0] - 2026-07-30

### Changed

- Upgraded the MCP server to `rmcp` 3.0 (MCP `2026-07-28` specification). The server now advertises
  protocol version `2026-07-28` and negotiates down for older clients, so existing integrations keep
  working. Minimum supported Rust version is now 1.88.

### Added

- Structured tool output (SEP-2106): `convert_html` (with `json:true`) and `extract_metadata` now
  return `structuredContent` alongside the text JSON, so clients can consume the result as data.
- Cache hints (SEP-2549) on the static prompt/resource catalogs (`prompts/list`, `resources/list`,
  `resources/read`): `ttlMs` of one hour with a `public` cache scope.

## [3.9.2] - 2026-07-27

### Fixed

- Java (Maven Central) and C# (NuGet) publishing, which failed in 3.9.1. Regenerated all language
  bindings on alef 0.48.4: the generated pom's Maven enforcer floor no longer exceeds the CI
  runner's Maven version, and the C# package now renders `runtime.json` (from the newly generated
  `runtime.json.template`) before `dotnet pack` via the `xberg-io/actions/render-runtime-json` step.

### Changed

- Upgrade dependencies to their latest incompatible versions.

## [3.9.1] - 2026-07-26

### Changed

- Refine the depth-limit warning (#434): the `DepthLimitExceeded` message now reports the effective
  limit value, and the warning is emitted exactly once when a deeply-nested DOM is truncated.
  Thanks @br411 (#428).
- Regenerate all language bindings on alef 0.48.2.
- Update dependencies to their latest compatible versions.

### Removed

- Remove unused Java PMD ruleset and stale linter configuration.

## [3.9.0] - 2026-07-19

### Added

- **Configurable traversal-depth ceiling** (#434): callers may now raise the recursion limit above the
  conservative native default (64) by setting an explicit `max_depth`, honored up to an internal
  backstop of 1024. Deeply-nested email HTML that previously lost content past depth 64 now converts.
  When the limit does truncate a subtree, a `DepthLimitExceeded` warning is surfaced instead of the
  content being dropped silently.

### Fixed

- **`<br>` in table cells with `br_in_tables`** (#429): a `<br>` inside a table cell now emits a literal
  `<br>` (valid single-line GFM) instead of a physical newline that broke the row.
- **Newline-only inline span separator** (#430): in normalized whitespace mode a `<span>` whose sole
  content is a newline now collapses to a single separating space instead of being dropped, so adjacent
  inline text no longer glues together.
- **Paragraph after a table inside a blockquote** (#431): the span newline-pop no longer crosses a
  table-row boundary, so a following paragraph is not glued onto the delimiter row.
- **Intentional hard break inside a span** (#432): the span newline-pop no longer eats a `<br>` hard
  break (`  \n` / `\\\n`), preserving the line break.
- **`keep_inline_images_in` inside layout-table cells** (#433): images inside a `td`/`th` listed in
  `keep_inline_images_in` now stay as markdown when a Tier-2 layout table converts cells as inline,
  instead of reducing to alt text.

### Changed

- Regenerate all bindings with alef 0.37.0.
- Update dependencies across language packages.

## [3.8.3] - 2026-07-09

### Fixed

- **Java visitor API** (#426): `ConversionOptions.builder().withVisitor(...)` now works. The visitor
  upcall `FunctionDescriptor`s were generated with a `JAVA_LONG` return layout while the `handleVisit*`
  bridge methods return `int`, so the Java Linker rejected every stub with `IllegalArgumentException:
  Wrong method handle type: (MemorySegment×5)int` — even a no-op visitor threw before any callback ran.
  Fixed upstream in the Alef generator (0.34.4); the descriptor return layout is now `JAVA_INT`.

### Changed

- Regenerate all bindings with alef 0.34.4.
- Formatting is now poly-only: removed the `alef:format`, `ruby:format`, and `csharp:format` tasks
  (which invoked `alef fmt`); `task format` / `poly fmt --fix .` is the single formatter.

## [3.8.0] - 2026-06-27

Stable release promoting 3.8.0-rc.2 (fully published). Version-only bump synced across all manifests.

## [3.8.0-rc.2] - 2026-06-27

### Changed

- Regenerate all bindings with alef 0.29.3.

## [3.8.0-rc.1] - 2026-06-26

### Changed

- **Rebrand Kreuzberg → Xberg across every published package identity.** The Node binding now ships as
  `@xberg-io/html-to-markdown` (the NAPI-RS crate itself — the separate `-node` package and the
  TypeScript wrapper under `packages/typescript/` are removed) with platform packages
  `@xberg-io/html-to-markdown-<platform>`; WASM and CLI move to `@xberg-io/html-to-markdown-wasm` and
  `@xberg-io/html-to-markdown-cli`. Java/Kotlin Maven coordinates and namespace move to `io.xberg`
  (`io.xberg:html-to-markdown[-android]`, JNI symbols `Java_io_xberg_android_…`), and the C# NuGet id to
  `XbergIo.HtmlToMarkdown`. The GitHub org (`github.com/xberg-io`), Homebrew tap
  (`xberg-io/homebrew-tap`), publisher GitHub App, sponsors links, and all docs/badges follow. The legal
  entity name **Kreuzberg, Inc.** is unchanged.

### Fixed

- **Swift publish now creates the `release/swift/<version>` branch carrying the substituted
  XCFramework checksum.** The alef-generated Swift e2e/test-app pins
  `.package(url: …, branch: "release/swift/<version>")`, but the publish workflow only force-moved
  the `v<version>` tag and never created that branch, so SwiftPM could not resolve the package. The
  checksummed commit is now also pushed to `refs/heads/release/swift/<version>`.
  (`.github/workflows/publish.yaml`)
- **test(test_apps/go): extract the module version with `$NF` instead of `$2`.** The smoke harness'
  `download_ffi.sh` read the version from `$2`, which only holds in the block `require (…)` go.mod form;
  the inline `require <path> <version>` form (emitted by the v3.7.2 regen) shifts the version to `$NF`,
  so the script built a malformed module-cache path and failed with "Binding directory not found". This
  is test-harness only — the published Go package is unaffected.

## [3.7.2] - 2026-06-23

### Fixed

- **chore(deps): bump `alef.toml.alef_version` to 0.26.6 and regenerate every binding.** Fixes the dart
  wrapper crate failing to build under `cargo build --no-default-features`: alef 0.26.x had regressed
  the 0.25.33 fix and re-emitted `#[cfg(feature = ...)]` on the generated `lib.rs` mirror struct /
  opaque-wrapper declarations, their `From` conversions, and `from_json` bridge fns, while
  `frb_generated.rs` references those types/functions unconditionally (`E0425: cannot find type
  VisitorHandle` / `create_html_metadata_from_json`). alef 0.26.6 keeps those declarations
  unconditional again. Verified: the regenerated dart crate compiles under `--no-default-features`,
  default, and `--all-features`. (alef 0.26.6)
- **ci(publish): the Homebrew Swift artifactbundle no longer forces `kreuzberg/openssl-vendored`.** The
  shared `build-swift-artifactbundle` action hardcoded that feature for its Linux (cargo-zigbuild)
  targets, but it only exists in the kreuzberg core swift crate — so html-to-markdown's swift bundle
  build failed (`the package '…' does not contain this feature`), which cascaded to skip
  `release-finalize` (and with it the `packages/go/vX.Y.Z` Go module tag). The action now takes a
  `linux-features` input (left empty here). (shared `xberg-io/actions/build-swift-artifactbundle`)

## [3.7.1] - 2026-06-23

### Fixed

- **ci(homebrew): drop the Intel-macOS `sonoma` bottle from the publish matrix.** The formula intentionally has no `x86_64-apple-darwin` url (Apple-Silicon only), but the bottle matrix still built a `sonoma` (Intel) bottle, which failed with `formula requires at least a URL`. Because `release-finalize` gates on `publish-homebrew-bottles` with `if: !contains(needs.*.result, 'failure')`, that one chronic failure silently **skipped release-finalize for three releases** (v3.6.20, v3.6.21, v3.7.0) — and with it the `packages/go/vX.Y.Z` Go module tag, leaving `go get …/packages/go/v3@vX.Y.Z` unresolvable. Removing the Intel bottle restores release-finalize (and the Go tag) for every future release. (`.github/workflows/publish.yaml`)
- **ci(e2e, C# on Windows): keep `cargo` on PATH in the test before-hook.** The "Run E2E tests (Windows)" step overrode `PATH` via `env:` with `${{ env.PATH }}`, which omits cargo's `$GITHUB_PATH` additions under Git Bash, so the `cargo build … html-to-markdown-ffi` before-hook failed with `cargo: command not found`. Prepend the target dirs to the live `$PATH` at runtime instead. (`.github/workflows/ci-e2e.yaml`)
- **ci(e2e/docs, Elixir): force the NIF to build from source.** Under `MIX_ENV=test` the `force_build: … or Mix.env() in [:dev]` clause does not apply, so `mix test` tried to download a precompiled NIF for the current (unreleased) version and failed with `the precompiled NIF file does not exist in the checksum file`. Set `RUSTLER_PRECOMPILED_FORCE_BUILD_ALL=1` so the test/doc compile builds the NIF locally. (`scripts/ci/elixir/run-tests.sh`)
- **ci(e2e, Swift): build the FFI crate the generated `Package.swift` links.** The swift e2e before-hook built only `html-to-markdown-rs-swift`, but the generated manifest links `html_to_markdown_ffi`, so `swift test` failed with `library 'html_to_markdown_ffi' not found`. Build `html-to-markdown-ffi` in the before-hook too (matching Go/C#/C). (`alef.toml`)
- **ci(e2e, PHP): drop `--locked` from the PHP test before-hook.** The PHP e2e job's extension build rewrites the native package deps to the published registry version and runs `cargo update`, mutating the workspace `Cargo.lock`; the subsequent `cargo build --locked -p html-to-markdown-php` then failed with `cannot update the lock file … --locked`. (`alef.toml`)
- **ci(node/wasm): use `--no-frozen-lockfile` for the NAPI binding install.** `build-node-napi` ran a frozen `pnpm install`, but the napi platform packages in `optionalDependencies` are pinned to the unpublished release version and can never be in `pnpm-lock.yaml`, so the install failed with `ERR_PNPM_OUTDATED_LOCKFILE` across every Node build/e2e. (shared `xberg-io/actions/build-node-napi`, `alef.toml`)
- **docs(php): recommend `pie install` over `composer require`.** The PHP package is a native `ext-php-rs` extension that `composer require` cannot load (the cause of #420); every PHP install snippet now leads with `pie install xberg-io/html-to-markdown`. (`docs/`, `readme_templates/`)

### Changed

- **ci(publish): require all 16 PHP PIE cells by explicit per-cell pattern in `verify-release-assets`.** A dropped cell now fails the release instead of silently shipping a partial PIE matrix (#333). (`.github/workflows/publish.yaml`)
- **chore(deps): re-pin `alef.toml.alef_version` to 0.26.5 and regenerate every binding, e2e suite, README, and API doc.** (alef 0.26.5)

## [3.7.0] - 2026-06-22

### Added

- **feat(mcp): expand the MCP server to full API parity with typed, discoverable options and complete tool annotations.** The `convert_html` tool now accepts a typed `config` object covering every settable `ConversionOptions` field (heading/list/escaping/whitespace/wrapping, preprocessing, image extraction, output format, tier strategy, …) instead of an opaque untyped JSON blob, so MCP clients discover all options through the tool's generated `inputSchema`; enum options are accepted as case-insensitive strings parsed by the core parsers. A new `extract_metadata` tool returns structured `<head>`/`<meta>` metadata (title, Open Graph, Twitter Card, JSON-LD/microdata, headers, links, images) as JSON. Both tools carry the full MCP annotation set (`title`, `read_only_hint=true`, `idempotent_hint=true`, `destructive_hint=false`, `open_world_hint=false`). The typed `ConvertConfig` mirror is implemented MCP-side (no changes to the alef-tracked core option types) and guarded by a drift test that fails if a core option is added without being mirrored. The `mcp` feature now implies `metadata`. (`crates/html-to-markdown/src/mcp/`)
- **feat(mcp): add prompts, resources, and completions capabilities.** Beyond tools, the server now advertises three more MCP capabilities: **prompts** — ready-made workflow templates (`convert_to_markdown`, `extract_main_content`, `inspect_metadata`) that drive the tools, with arguments; **resources** — `htmltomarkdown://options-schema` (the JSON Schema of every conversion option) and `htmltomarkdown://output-formats` (the markdown/djot/plain guide); and **completions** — argument autocompletion for prompt arguments (e.g. `output_format` → markdown/djot/plain). (`crates/html-to-markdown/src/mcp/catalog.rs`)

## [3.6.21] - 2026-06-22

### Changed

- **chore(deps): re-pin `alef.toml.alef_version` to 0.25.60 and regenerate every binding, e2e suite, README, and API doc.** Folds in the 0.25.59–0.25.60 generator fixes: the R/extendr by-reference DTO rework now emits a non-optional Named param following an optional param as `&T` (passed by reference via an owned `name_core` binding) instead of the non-compiling `Nullable<&T>::into_option()` path; Kotlin/Kotlin-Android content-union `text()` accessors reference the actual data-class payload property (`value`) instead of the non-existent `field0`; generated binding rustdoc de-links core intra-doc references (e.g. ``[`Error::LanguageNotFound`]``) to plain code spans so `rustdoc -D rustdoc::broken-intra-doc-links` passes; and `sync-versions` now runs the same `format_generated` pass as `alef all`, so version-bumped manifests (`package.json`, `composer.json`, `Package.swift`) are byte-identical to the generate path and no longer trip freshness gates. (alef 0.25.60)

