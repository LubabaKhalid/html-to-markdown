---
title: "Changelog archive: 3.1.0–2.14.1"
---

## [3.1.0] - 2026-04-01

### Added

- **Reference-style links**: New `link_style` option (`"inline"` default, `"reference"`) renders links as `[text][1]` with numbered `[1]: url "title"` definitions appended at the end of the output. Supports URL+title deduplication, images (`![alt][1]`), and media elements (audio, video, iframe). Available across all bindings (Python, Node.js, WASM, PHP, CLI `--link-style`, FFI via JSON).

## [3.0.2] - 2026-04-01

### Fixed

- **Structure collector in tables**: Suppressed `StructureCollector` calls for headings and lists inside table cells, preventing spurious document-structure nodes from table content.
- **Char boundary safety**: Fixed potential panics from slicing at non-UTF-8-char boundaries in `generate_id` hash truncation and list item text extraction.
- **Dead feature gates removed**: Cleaned up unused `document-structure` feature gates that were no longer wired to any Cargo feature.
- **Structure collector coverage**: Added missing `StructureCollector` calls for lists, images, and code blocks so document structure captures all block-level elements.

## [3.0.1] - 2026-03-31

### Fixed

- **WASM TypeScript types**: `convert()` now returns typed `WasmConversionResult` instead of `any`. All `WasmConversionTable`, `WasmGridCell`, `WasmTableGrid`, `WasmConversionWarning`, and `WasmInlineImage` interfaces are now emitted in generated `.d.ts` files. Added missing options fields (`skipImages`, `outputFormat`, `includeDocumentStructure`, `extractImages`, `maxImageSize`, `captureSvg`, `inferDimensions`). Fixes #265.
- **Python type stubs**: Synced crate `.pyi` stub with package stub — added keyword-only (`*`) parameter markers and `visitor` parameter to `convert()`.
- **PHP type stubs**: Expanded PHPStan stubs with full `ConversionResult`, `ConversionOptions`, and all nested type shapes. Wired stubs into `composer.json` PHPStan config.

## [3.0.0] - 2026-03-30

### Added

- **Single `convert()` API**: One entry point across all 12 language bindings returning `ConversionResult` with content, document, metadata, tables, images, and warnings.
- **`ConversionResult` type**: Structured result with `content` (markdown/djot/plain), `document` (optional `DocumentStructure`), `metadata` (`HtmlMetadata`), `tables` (grid-based), `images` (inline image data), and `warnings`.
- **`DocumentStructure`**: Structured document tree with flat node array, index-based parent/child references, and `TextAnnotation` for inline formatting.
- **Options support in all bindings**: Go, Java, C# now accept options. All generators wire fixture options into e2e tests.
- **GFM defaults**: Code blocks default to backtick fences (was indented). ATX headings remain default.
- **E2E contract validation**: Generators produce tests validating ConversionResult structure (metadata, tables, warnings) across all 12 languages.
- **New options**: `includeDocumentStructure`, `extractImages`, `maxImageSize`, `captureSvg`, `inferDimensions`, `outputFormat` (markdown/djot/plain).
- **`<q>` element**: Wraps content in quotation marks.
- **`<figure>`/`<figcaption>` elements**: Routed to semantic handler with caption separation.
- **`hidden` attribute**: Elements with `hidden` stripped before parsing.

### Changed

- **`convert()` returns `ConversionResult`** instead of `String` in all bindings (Go, Java, C#, Node, Python, PHP, Ruby, Elixir, R, WASM, C FFI).
- **`ExtendedMetadata` renamed to `HtmlMetadata`** across all crates and bindings.
- **Go `Convert()`** returns `*ConversionResult` with `Content`, `Metadata`, `Tables`, `Images`, `Warnings` fields. Accepts optional JSON options via variadic parameter.
- **Table data** uses grid-based schema (`TableGrid` with `GridCell`) instead of flat `cells [][]string`.
- **`serde(deny_unknown_fields)`** on `MetadataConfig`, `MetadataConfigUpdate`, `InlineImageConfigUpdate`.
- **Go 1.26**, golangci-lint@latest.

### Removed

- **All `convert_with_*` functions**: `convert_with_metadata`, `convert_with_inline_images`, `convert_with_visitor` (standalone), `convert_with_tables`, `convert_with_async_visitor` removed from public API. Single `convert()` replaces all.
- **Async visitor**: Feature removed entirely (`async-visitor` Cargo feature, `AsyncHtmlVisitor` trait, async bridge/dispatch code).
- **Profiling**: All profiling infrastructure removed (8 binding crates, CI workflow, C tests, `start_profiling`/`stop_profiling` APIs).
- **Benchmarks**: All benchmark scripts and harness removed.
- **hOCR support**: Entire `hocr` module deleted. The `hocr_spatial_tables` option removed.
- **Python v1 compatibility**: `convert_to_markdown()` and `markdownify()` removed.
- **Redundant binding tests**: Tests covered by e2e generators removed from Python, Ruby, Elixir, R.

## [2.30.0] - 2026-03-27

### Deprecated

- **hOCR support**: The `hocr_spatial_tables` option and all hOCR-related APIs are deprecated and will be removed in v3. All hOCR functionality continues to work but emits deprecation warnings. This is the final v2 release.

### Fixed

- **PHP PHPStan CI errors**: Removed redundant `@var` annotations and `is_array()` runtime checks in `ExtensionBridge.php` that PHPStan flagged as always-true due to stub-defined return types. Removed redundant `array_values()` calls in `ConversionOptions.php` on properties already typed as `list<string>`. Updated PHPStan baseline count for callable invocations.

## [2.29.0] - 2026-03-22

### Added

- **`full` feature group**: Added a `full` feature to core crate and all binding crates (PHP, Python, Node, WASM, FFI, Elixir, bindings-common) that enables all available features. All bindings now default to `full`.
- **Dublin Core metadata extraction**: `DC.*` and `DCTERMS.*` meta tags now map to dedicated `DocumentMetadata` fields (title, description, author, keywords). Other DC/DCTERMS fields stored in `meta_tags` with `dc_`/`dcterms_` prefix.
- **Extended keyword variants**: Keywords now extracted from `news_keywords`, `citation_keywords`, `DC.subject`, `DC.keywords`, `DCTERMS.subject`, `subject`, `topic`, `category`, and `classification` meta tags.
- **`cargo-sort` pre-commit hook**: Added for consistent Cargo.toml key ordering.
- **`checkmake` pre-commit hook**: Added for Makefile linting.
- **`typescript-typecheck` pre-commit hook**: Added TypeScript type checking via `tsc --noEmit`.
- **`typecheck` npm script**: Added to `packages/typescript/package.json`.

### Fixed

- **Case-insensitive meta tag matching** ([#251](https://github.com/xberg-io/html-to-markdown/issues/251)): All meta tag name matching is now case-insensitive per the HTML spec. `<meta name="Keywords">` and `<meta name="DC.keywords">` are now correctly captured.
- **PHP `convertWithTables()` not found** ([#250](https://github.com/xberg-io/html-to-markdown/issues/250)): The `visitor` feature was not enabled by default in the PHP binding crate, causing `html_to_markdown_convert_with_tables` to be missing from the extension.
- **PHP binding defaults**: PHP crate now defaults to `["full"]` (was `["metadata"]`), enabling visitor support.
- **Python binding defaults**: Python crate now defaults to `["full"]` (was `[]`), enabling metadata, visitor, async-visitor, and inline-images.
- **PHPStan 2.x compatibility**: Fixed 40+ PHPStan errors from the 1.x→2.x upgrade (type narrowing, property access on mixed, redundant assertions). Added `--memory-limit=512M` to prevent OOM.
- **Makefile `test` target**: Added missing `.PHONY: test` target to FFI test Makefile.

### Changed

- **Pre-commit config aligned with kreuzberg**: Added `cargo-sort`, `checkmake`, `typescript-typecheck`. Updated `taplo-format` to exclude `Cargo.toml`. Excluded `Makefile.frag` from checkmake.
- **Cargo.toml formatting**: All workspace Cargo.toml files sorted via `cargo-sort`.
- **pyproject.toml formatting**: All pyproject.toml files formatted via `pyproject-fmt`.

## [2.28.6] - 2026-03-20

### Changed

- **Ruby gem vendoring**: Replaced bash+embedded-Python vendoring script with a standalone Python vendoring script adapted from kreuzberg, using `vendor/` directory instead of `rust-vendor/` for core crate vendoring.
- **Ruby gem build**: Added `build-native-gem.rb` for platform-specific pre-compiled gem builds, following kreuzberg patterns.
- **Pre-commit hooks**: Switched Ruby hooks (rubocop, rbs-validate, steep-check) from inline bash commands to task-based delegation matching kreuzberg.
- **Dependabot config**: Expanded from GitHub Actions only to full multi-ecosystem coverage (Cargo, pip, npm, bundler, composer, gomod, maven, nuget, mix).
- **Task update commands**: Aligned all language update tasks with kreuzberg's comprehensive approach (outdated checks, aggressive updates).
- **C# update**: Switched from slow `dotnet list --outdated` Python script to `dotnet-outdated-tool` for faster dependency updates.

### Fixed

- **CI Validate shfmt failure**: Fixed `packages/r/configure.win` tab indentation to match shfmt 2-space requirement.
- **Java linting**: Added PMD plugin (3.28.0), JaCoCo coverage (0.8.14), and pinned checkstyle runtime (13.3.0). Bumped maven-compiler-plugin to 3.15.0, maven-surefire-plugin to 3.5.5, spotless to 3.4.0, central-publishing to 0.10.0.

### Updated

- **GitHub Actions**: Bumped `go-task/setup-task` from v1 to v2, `nick-fields/retry` from v3 to v4.
- **Dependencies**: Updated all language dependencies via `task update`.

## [2.28.5] - 2026-03-19

### Fixed

- **Table colspan parsing** ([#233](https://github.com/xberg-io/html-to-markdown/issues/233)): Fixed column count calculation to accurately use colspan values instead of incrementing by 1, and refined layout table heuristics to exempt simple data tables with colspans while correctly catching layout tables.
- **Ruby version.rb formatting**: Fixed missing space around `=` operator in `version.rb` that caused Rubocop lint failures in CI.
- **CI tooling alignment**: Aligned tooling and documentation with kreuzberg standards, fixing CI failures.

## [2.28.4] - 2026-03-13

### Fixed

- **Panic with cid image followed by italic paragraph** ([#222](https://github.com/xberg-io/html-to-markdown/issues/222)): Confirmed fix for panic ("byte index 53 is out of bounds of ``") when converting HTML containing `cid:` image paragraphs followed by italicized text. This was resolved in v2.28.0 via the block_content_start bounds fix (#216, #217) and multi-byte UTF-8 character boundary fix (#218).
- **Ruby gem installation on macOS** ([#219](https://github.com/xberg-io/html-to-markdown/issues/219)): Confirmed fix for `Cargo.lock` missing from published gem causing `magnus` dependency load failure. Resolved in v2.28.3 with native platform gem builds.

## [2.28.3] - 2026-03-10

### Fixed

- **Java visitor FFI struct return type**: Fixed `IllegalArgumentException: Wrong method handle type` when using visitors in Java. The Panama FFI callback descriptors incorrectly used `JAVA_LONG` (8 bytes) as the return type instead of the actual `HtmlToMarkdownVisitResult` C struct (24 bytes: enum + 2 pointers). All 14 callback descriptors now use a proper `StructLayout` matching the C ABI.
- **Homebrew bottle tarball structure**: Fixed bottle tarballs missing the required `html-to-markdown/{version}/` prefix directory. Homebrew expects this prefix for proper cellar installation.
- **Ruby gem publishing**: Added native platform gem builds (`rake native gem`) alongside source gems so precompiled extensions are available for Linux, macOS, and Windows.

## [2.28.2] - 2026-03-08

### Fixed

- **Publish workflow republish flag**: Fixed republish mode skipping all publish jobs because `INPUT_REF` resolved to a branch name instead of the tag ref.
- **Definition list fixture**: Aligned real-world test fixture for `<dl>`/`<dt>`/`<dd>` with actual converter output (plain text, no Pandoc-style `:` prefix).

## [2.28.1] - 2026-03-06

### Fixed

- **Panic with multi-byte UTF-8 and visitor** ([#218](https://github.com/xberg-io/html-to-markdown/issues/218)): Fixed a panic ("byte index N is not a char boundary") when converting HTML containing multi-byte UTF-8 characters (Cyrillic, CJK, emoji, etc.) with tabs between block elements and any visitor. The stale byte position captured before whitespace trimming could land inside a multi-byte character when new content was appended.
- **Java formatting**: Fixed spotless formatting violations in `HtmlToMarkdown.java`, `TableData.java`, and `TableExtractionResult.java`.

## [2.28.0] - 2026-03-05

### Added

- **Table extraction API**: New `convert_with_tables` function that extracts structured table data during HTML to Markdown conversion. Returns `TableData` structs containing cell contents as `Vec<Vec<String>>`, rendered markdown output, and per-row header flags. Uses the visitor pattern internally with a built-in `TableCollector` to capture table structure in a single pass. Available across all language bindings:
  - **Rust**: `convert_with_tables(html, options, metadata_config)` returning `ConversionWithTables`
  - **Python**: `convert_with_tables(html, options, preprocessing, metadata_config)` returning `TableExtractionResult`
  - **TypeScript/Node.js**: `convertWithTables(html, options?, metadataConfig?)` returning `TableExtraction`
  - **Ruby**: `HtmlToMarkdown.convert_with_tables(html, options, metadata_config)` returning a Hash
  - **PHP**: `HtmlToMarkdown::convertWithTables($html, $options, $metadataConfig)` returning `TableExtractionResult`
  - **Go**: `ConvertWithTables(html)` returning `TableExtractionResult`
  - **Java**: `HtmlToMarkdown.convertWithTables(html)` returning `TableExtractionResult`
  - **C#**: `HtmlToMarkdownConverter.ConvertWithTables(html)` returning `TableExtractionResult`
  - **Elixir**: `HtmlToMarkdown.convert_with_tables(html, options, metadata_config)` returning `{:ok, content, tables, metadata}`
  - **R**: `convert_with_tables(html, options, metadata_config)` returning a list
  - **C (FFI)**: `html_to_markdown_convert_with_tables(html, options_json, metadata_json)` returning JSON
  - **WASM**: `convertWithTables(html, options?, metadataConfig?)` returning a JS object

### Fixed

- **Plain text fast path skipping visitor callbacks**: When `OutputFormat::Plain` was used with `convert_with_tables`, the plain text fast path returned before the visitor could extract table data, resulting in empty tables. The conversion pipeline now runs the full visitor walk before returning plain text content.

## [2.27.3] - 2026-03-05

### Fixed

- **Panic on block_content_start out of bounds**: Fixed a crash (`byte index N is out of bounds`) in text node processing when inline handlers (e.g. `<strong>`, `<em>`) collected children into a fresh buffer while inheriting a parent paragraph context. The `block_content_start` index pointed into the wrong buffer, causing a panic on certain HTML structures — notably `<details>` containing `<p>` with inline formatting. (Issues #216, #217)

## [2.27.2] - 2026-03-02

### Fixed

- **Plain text list items missing markers**: `<ul>` and `<ol>` list items in `OutputFormat::Plain` were output without any bullet or number prefix. Now emits `-` for unordered lists and sequential `N.` for ordered lists, respecting the `start` attribute on `<ol>`.

## [2.27.1] - 2026-03-01

### Fixed

- **Colon introduced into definition list text**: `<dd>` elements inside `<dl>` were incorrectly prefixed with `:` (Pandoc definition list syntax), introducing spurious colons into converted text. Standard Markdown and GFM do not support definition list syntax, so `<dd>` content is now output as plain blocks. (Issue #214, thanks @smoyerx)
- **Go test app go.sum out of sync**: Updated `tests/test_apps/go/go.sum` to match the v2.27.0 module version, fixing the CI Go lint job.

## [2.27.0] - 2026-03-01

### Added

- **Plain text output format**: New `OutputFormat::Plain` option that strips all markup and returns only visible text content. Set `output_format` to `"plain"` (also accepts `"plaintext"` or `"text"`). This fast-path bypasses the full Markdown/Djot conversion pipeline — after DOM parsing, a lightweight text extractor walks the tree collecting only visible text with structural whitespace. Useful for search indexing, text extraction, and feeding content to LLMs.

## [2.26.3] - 2026-02-28

### Fixed

- **Subscript/superscript content silently dropped**: When `sub_symbol` or `sup_symbol` was empty (the default), text inside `<sub>` and `<sup>` tags was discarded entirely — e.g. `H<sub>2</sub>O` produced `HO` instead of `H2O`.
- **Missing whitespace between newline-separated inline elements**: Whitespace-only text nodes containing newlines between adjacent inline elements (e.g. `<a>…</a>\n<a>…</a>`) were dropped, causing links and other inline markup to merge without a word boundary. Now collapses to a single space per HTML white-space normalization rules.

## [2.26.2] - 2026-02-28

### Fixed

- **Inconsistent whitespace before inline elements across paragraphs**: Fixed a stateful bug where `\n` before `<a>`, `<strong>`, `<em>`, and other inline elements inside `<p>` tags was handled differently depending on the paragraph's position in the document. The second and subsequent paragraphs would drop the space before inline elements, producing `text[link](url)` instead of `text [link](url)`. (Issue #212, thanks @haroldparis)

## [2.26.1] - 2026-02-27

### Fixed

- **YAML frontmatter in `convert_with_metadata` output**: `convert_with_metadata` no longer prepends YAML frontmatter to the markdown string. Since metadata is returned as a structured `ExtendedMetadata` object, embedding it in the content string was redundant and polluted the output.

## [2.26.0] - 2026-02-26

### Added

- **C FFI distribution infrastructure**: Distribution-grade C FFI library with CMake/pkg-config integration, installation scripts, and packaging for system-level consumption.
- **C FFI test coverage**: Comprehensive C test suite covering conversion, metadata extraction, error handling, visitor pattern, profiling, and version queries.
- **C documentation and examples**: C API reference, getting-started snippets, and example programs for basic conversion, metadata extraction, and visitor pattern usage.

### Fixed

- **R package r-universe build**: Configure scripts now download the source archive from GitHub when the monorepo is unavailable, enabling r-universe and standalone source installs to vendor crates automatically.

## [2.25.2] - 2026-02-25

### Fixed

- **Visitor panic with metadata extraction**: Fixed an out-of-bounds slice panic when using visitors (e.g. image visitors returning `Custom`) combined with metadata extraction on minified HTML. The issue occurred because parent element output offsets became stale after child visitor truncations. (PR #204, thanks @gmalette)

### Added

- **R language bindings**: Full-parity R bindings via extendr framework with support for `convert()`, `convert_with_options()`, `convert_with_options_handle()`, `convert_with_metadata()`, `convert_with_inline_images()`, `convert_with_visitor()`, and profiling. Includes `conversion_options()` helper, testthat test suite, CI workflow, lintr/styler pre-commit hooks, and task automation.
- **R CRAN publishing infrastructure**: Added `publish-cran` job to publish workflow, `cran-comments.md`, and `NEWS.md` for CRAN submission compliance.

### Changed

- **Workspace restructuring**: Moved Ruby native crate out of the root Cargo workspace into a standalone workspace (matching Elixir/R pattern), resolving `clang-sys` link conflict with `ext-php-rs` 0.15.6.
- **Rust update task**: Now updates dependencies in all separate workspaces (Ruby, Elixir, R) via `--manifest-path` entries.
- **Upgraded `wasmtime`** from 41 to 42.
- **Upgraded `ext-php-rs`** from 0.15.4 to 0.15.6.
- **Upgraded `pyo3`** from 0.28.1 to 0.28.2.
- **Upgraded `wasm-bindgen`** from 0.2.112 to 0.2.113.
- **Upgraded `rustls`** from 0.23.36 to 0.23.37.

## [2.25.1] - 2026-02-17

### Fixed

- **hOCR heading detection**: Improved hierarchy logic to use font size (`x_fsize`) and bbox height as a proxy when detecting headings. Large-font paragraphs now support longer text (up to 80 chars) and single-word headings. Added comprehensive test coverage for heading detection edge cases.

## [2.25.0] - 2026-02-15

### Added

- **Bun runtime support**: Official support for Bun 1.2+ via Node-API compatibility. The existing NAPI-RS bindings work in Bun without changes. Added Bun to CI test matrix and updated documentation to reflect runtime compatibility.

### Changed

- **Vendored `markup5ever_rcdom`**: Brought the `markup5ever_rcdom` code (MIT/Apache-2.0) into the core crate as an internal `rcdom` module. This removes the external dependency on the "+unofficial" crate, eliminates the unused `xml5ever` transitive dependency, and removes the pinned `html5ever`/`markup5ever_rcdom` version constraints. See `ATTRIBUTIONS.md` for license details.
- **Upgraded `html5ever`** from 0.36.1 to 0.38.0 (now unpinned).
- **Upgraded `pyo3`** from 0.28.0 to 0.28.1.

## [2.24.6] - 2026-02-14

### Fixed

- **Dependency update stability**: Pinned compatible `html5ever`/`markup5ever_rcdom` versions to prevent trait-mismatch breakages during workspace dependency updates.
- **Python bindings build**: Added explicit `#[pyclass(from_py_object)]` on Python config wrapper classes to avoid PyO3 deprecation failures under `-D warnings`.
- **Rust lint consistency**: Aligned crate-level clippy configuration so `multiple_crate_versions` does not fail Node/WASM/FFI crate lint runs.
- **WASM dependency behavior**: Updated hashing dependency configuration to avoid wasm randomness backend breakage after dependency updates.
- **PHP PIE publish verification (macOS)**: Hardened PIE verification/build scripts for Darwin linker behavior and shell-safe package spec handling.
- **CI reliability**: Updated validation and Python CI tasks to reduce flakiness (PHP 8.4 setup in validate; avoid redundant Rust CLI release builds in Python test runs).

## [2.24.5] - 2026-02-01

### Fixed

- **Subscript/superscript whitespace handling**: Subscript and superscript tags now trim inner whitespace and place it outside delimiters, matching the behavior of bold, italic, and strikethrough (issue #202).

## [2.24.4] - 2026-01-31

### Performance

- **Reduced allocations in hot conversion paths**: Return `Cow<str>` from escape to avoid allocating on no-op paths, replace `.repeat()` with direct push loops in heading/list/table/div/paragraph formatters, eliminate `collect::<Vec>::join()` in text dedentation, and use `AHashMap` for hOCR property maps.

### Fixed

- **WASM builds**: Updated `getrandom` backend configuration from `"js"` to `"wasm_js"` for compatibility with getrandom 0.3.x.
- **Elixir/Ruby vendor scripts**: Added missing `ahash` workspace dependency replacement for standalone builds.

## [2.24.3] - 2026-01-31

### Fixed

- **Definition lists**: Ensure `<dl>/<dt>/<dd>` output is consistent regardless of HTML whitespace/minification, and properly indent multiline definition content (issue #200).
- **Link labels**: Removed hard truncation of long link labels to avoid broken Markdown for large image links (issue #199).

## [2.24.2] - 2026-01-29

### Fixed

- **Java packaging**: Bundle native FFI libraries in published Maven JAR for all platforms (linux-x86_64, linux-aarch64, osx-aarch64, windows-x86_64). The Java package now works out-of-the-box when installed from Maven Central without requiring local FFI builds or manual java.library.path configuration. Native libraries are automatically extracted to a temp directory on first use with platform detection and fallback support.

## [2.24.1] - 2026-01-27

### Fixed

- **UTF-16 recovery**: Automatically recovers UTF-16 HTML (including data without BOM) that was read via lossy UTF-8 decoding, instead of rejecting it as binary data.
- **URL sanitization**: Hardened markdown-like URL sanitization to extract the real URL from `...[text](url)` patterns in `href`/`src` attributes, preventing caller-side URL join/parsing errors.
- **Issue #190 coverage**: Added regression fixtures and tests covering the reported real-world HTML inputs.

## [2.24.0] - 2026-01-24

### Changed

- **Bindings API**: Removed `_json` conversion entrypoints across bindings; convert functions now pass full option payloads directly.

### Fixed

- **Visitor docs**: Corrected Python visitor documentation and examples (argument order + ctx access).
- **Python visitor options**: `convert_with_visitor` now respects full conversion options payloads.
- **skip_images**: Skip flag now suppresses SVG/graphic outputs in addition to `<img>`.
- **Code block dedent**: Handles Unicode whitespace without panicking on UTF-8 boundaries.
- **Input validation**: Tolerates small NUL byte artifacts and strips them before conversion.

## [2.23.6] - 2026-01-21

### Fixed

- **pnpm lockfile synchronization**: Fixed pnpm lockfile to include Node.js platform-specific optional dependency version updates (2.19.0-rc.1 → 2.23.6) that were applied during v2.23.5 version sync. This resolves the `ERR_PNPM_OUTDATED_LOCKFILE` errors that caused the v2.23.5 publish workflow to fail.
- **CI Java version**: Updated CI Java workflow from Java 24 to Java 25 to match maven.compiler.release=25 configuration, ensuring CI and local builds use the same compiler version.

## [2.23.5] - 2026-01-21

### Fixed

- **Maven Central publishing**: Corrected group ID in Maven Central check script from legacy `io.github.goldziher` to `dev.kreuzberg`, enabling successful Java package publishing. This resolves the issue where Java v2.23.4 failed to publish to Maven Central.
- **Go module publishing**: Added automated Go module tag creation (`packages/go/v{version}`) to publish workflow, ensuring Go packages are immediately available on Go proxy after release.
- **Go FFI version synchronization**: Updated Go FFI default version constants from outdated versions (2.19.1/2.23.0) to 2.23.5 in both `ffi_loader.go` and `cmd/install/main.go`, ensuring automatic downloads use the correct library version.
- **Node.js platform dependencies**: Synchronized all platform-specific optional dependencies in `@kreuzberg/html-to-markdown-node` package.json from 2.19.0-rc.1 to match main package version, preventing dependency resolution issues.
- **Java benchmark packaging**: Updated benchmark-pom.xml to use correct group ID (`dev.kreuzberg`), version (2.23.5), and main class namespace (`dev.kreuzberg.benchmark.Benchmark`). Removed outdated generated `dependency-reduced-pom.xml`.
- **PHP package references**: Updated all PHP package references from `goldziher/html-to-markdown` to `xberg-io/html-to-markdown` across composer.json, PIE verification scripts, and smoke test actions to reflect current package organization.
- **Java smoke tests**: Updated smoke-java GitHub action to use correct group ID (`dev.kreuzberg`) and package namespace (`dev.kreuzberg.htmltomarkdown.SmokeTest`) for JAR installation and test execution.
- **Build tooling**: Fixed Python script execution in task runner to use `uv run python3` instead of system python3, ensuring consistent dependency resolution. Added PyYAML and Jinja2 to workspace dev dependencies.
- **Version sync automation**: Enhanced version sync script to automatically update Node.js platform-specific optional dependencies alongside main package version, preventing manual version drift.

## [2.23.4] - 2026-01-20

### Fixed

- **TypeScript wrapper publishing**: Fixed TypeScript wrapper dependency resolution by installing dependencies directly from npm registry instead of from workspace after Node packages are published. This ensures `@kreuzberg/html-to-markdown-node` is available from npm when building the TypeScript wrapper, eliminating the workspace resolution issues that caused previous build failures.

## [2.23.3] - 2026-01-20

### Fixed

- **Go FFI packaging**: Fixed missing `html_to_markdown.h` header file in Go FFI archive tarballs, which caused `go:generate` installation to fail with "fatal error: 'html_to_markdown.h' file not found". The header is now included in all platform archives (tar.gz and zip).
- **TypeScript wrapper publishing**: Fixed pnpm lockfile frozen mode error during TypeScript wrapper dependency reinstallation by adding `--no-frozen-lockfile` flag. The reinstall step after publishing Node packages now correctly updates workspace dependencies despite lockfile version mismatches.

## [2.23.2] - 2026-01-20

### Fixed

- **TypeScript wrapper publishing**: Fixed TypeScript wrapper build failures by moving the build and publish steps into the same `publish-node` job. This eliminates npm CDN propagation delays that caused `@kreuzberg/html-to-markdown` to fail building because `@kreuzberg/html-to-markdown-node` wasn't available yet. Added workspace dependency reinstallation step to ensure pnpm correctly resolves the local package after publishing.
- **Go FFI library installation**: Fixed critical bugs in the `go:generate` install script that prevented automatic FFI library downloads:
  - Corrected artifact naming from `go-ffi-{platform}.tar.gz` to `html-to-markdown-ffi-{version}-{platform}.tar.gz`
  - Fixed platform mapping to match GitHub release artifacts (darwin-arm64, linux-x64, etc.)
  - Added support for all library formats (.dylib for macOS, .so for Linux, .dll for Windows)
- **Ruby native Cargo.toml**: Fixed workspace dependency configuration to use `workspace = true` instead of vendored path reference, preventing Cargo workspace resolution failures during builds.
- **CI workflows**: Upgraded all CI workflows from Java 24 to Java 25 to match maven.compiler.release=25 configuration in pom.xml.
- **Go linting**: Resolved golangci-lint warnings by adding constants for OS names and library names, and converting if-else chains to switch statements.

### Changed

- **Go README**: Updated installation documentation to explain the `go:generate` workflow for automatic FFI library installation, including details about caching in `~/.html-to-markdown/` and alternative manual configuration.

## [2.23.1] - 2026-01-19

### Fixed

- **Go module versioning**: Created 14 missing Go module tags (packages/go/v2.16.1, v2.19.1-v2.19.8, v2.20.1, v2.21.1, v2.22.1-v2.22.5) to ensure all versions since v2.15.0 are available via Go proxy. Users can now `go get` any version from v2.15.0 onwards.
- **TypeScript wrapper publishing**: Added missing `publish-typescript` job to publish workflow to properly publish `@kreuzberg/html-to-markdown` TypeScript wrapper package to npm alongside the native Node.js bindings (`@kreuzberg/html-to-markdown-node`).
- **Ruby gem vendoring**: Fixed Ruby gem installation failures due to missing `.cargo-checksum.json` files. Updated gemspec to include hidden files with `File::FNM_DOTMATCH` flag, and improved vendoring script to generate checksums correctly with `--locked` flag and proper cleanup.
- **Elixir package size**: Reduced Hex package size from 134 MB to under 128 MB limit by aggressively removing unnecessary files from vendored dependencies (tests, docs, examples, static libraries, Windows-only crates on Unix builds).

### Added

- **Go automatic FFI library installation**: Implemented `go:generate` pattern following Kreuzberg approach. Added `cmd/install` package that automatically downloads platform-specific FFI libraries from GitHub releases and generates CGO flags. Users can now run `go generate` after installation instead of manually setting `CGO_CFLAGS` and `CGO_LDFLAGS` environment variables. FFI loader updated to check `~/.html-to-markdown/` for installed libraries.

## [2.23.0] - 2026-01-18

### Added

- **Djot output format support**: New `output_format` option in `ConversionOptions` enables conversion to [Djot](https://djot.net/) lightweight markup language as an alternative to Markdown. Djot uses different syntax for emphasis (`_text_`), strong (`*text*`), strikethrough (`{-text-}`), inserted (`{+text+}`), highlighted (`{=text=}`), subscript (`~text~`), and superscript (`^text^`).
- **CLI**: Added `--output-format` / `-f` flag to specify output format (`markdown` or `djot`)
- **All language bindings**: OutputFormat enum/option added to Python, TypeScript/Node.js, Ruby, PHP, Elixir, Go, Java, and C# bindings
- **Documentation**: Added Djot output format section to all package READMEs with syntax comparison table

### Fixed

- **Python**: Fixed async visitor bridge to properly await coroutines. `PyAsyncVisitorBridge::call_visitor_method_sync()` now detects async methods via `__await__` attribute and uses `PYTHON_TASK_LOCALS` event loop for proper async execution (issue #187)
- **Ruby**: Fixed visitor parameter being ignored in `convert()` wrapper method. Now correctly passes visitor to native `convert_with_visitor` function when provided (issue #187)

### Changed

- **Rust**: Updated `async-visitor` feature to include required `tokio` "sync" feature for `Mutex` support
- **Documentation**: Added comprehensive visitor pattern support matrix showing which bindings support visitors
- **Documentation**: Documented WASM visitor pattern architectural limitation with four alternative approaches

## [2.22.6] - 2026-01-16

### Fixed

- **Ruby gem dependency resolution**: Ruby native extension now uses workspace version inheritance with vendoring approach. During gem build, the entire `html-to-markdown` crate is vendored with exact dependency versions into `packages/ruby/vendor/`, making gems completely self-contained and eliminating crates.io dependency resolution during installation. Local development uses symlink to workspace crate for seamless workflow.
- **URL parsing robustness**: Fixed IPv6 URL parsing error when processing malformed markdown-like URLs in HTML attributes (e.g., `//[domain.com/path](http://domain.com/path)`). New `sanitize_markdown_url()` function detects and extracts actual URLs from markdown syntax that wasn't properly converted in source HTML. Applied to both link `href` and image `src` attributes (fixes issue #186).

### Changed

- **Ruby gem build process**: Added `vendor-html-to-markdown.sh` script that creates standalone vendor workspace before gem packaging. Ruby native `Cargo.toml` now references vendored path for maximum reproducibility and build reliability.

## [2.22.5] - 2026-01-16

### Fixed

- **Core**: Added `#[serde(default)]` attribute to `ConversionOptions` struct to enable partial JSON deserialization. This allows deserializing JSON with only a subset of fields specified, using default values for missing fields. Fixes compatibility with language bindings (C#, Go, Java) that serialize partial configuration objects.

## [2.22.4] - 2026-01-15

### Fixed

- **Core**: Fixed `br_in_tables` option not being respected correctly. HTML `<br>` tags in table cells now properly convert to markdown line breaks (spaces or backslash style based on `newline_style` option), while block elements (divs, paragraphs) continue to generate literal `<br>` tags when needed for rowspan scenarios (issue #184)
- **WASM**: Updated GitHub Pages demo to v2.22.4 with latest BR tag handling fixes

## [2.22.3] - 2026-01-14

### Fixed

- **Python**: Exposed `skip_images` option in `ConversionOptions` API, including type stub files (.pyi) for proper type checking support (issue #183)
- **Elixir**: Added `skip_images` option to `HtmlToMarkdown.Options` module (was completely missing from Elixir binding)
- **Core**: Fixed `<br>` tags being output literally in table cells instead of converting to proper Markdown line breaks. Table cell paragraph and div separators now respect `newline_style` option (issue #184)

## [2.22.2] - 2026-01-13

### Fixed

- **Ruby gem standalone build** - Fixed Ruby gem failing to build when installed from RubyGems. Removed `lints.workspace = true` (which requires workspace context) and added inline lint configuration. This resolves issue #181.
- **Ruby gem version pinning** - Changed `html-to-markdown-rs` dependency from loose semver (`"2.x.x"`) to exact pin (`"=2.22.2"`) to prevent older gems from pulling incompatible newer crate versions.
- **Version sync script** - Updated `sync_versions.py` to preserve exact version pin prefix (`=`) when syncing Ruby gem dependencies.

## [2.22.1] - 2026-01-13

### Fixed

- **Java Maven Central publishing** - Fixed Maven Central deployment by adding proper `publish` profile with `central-publishing-maven-plugin` configuration. The plugin is now correctly activated with `-Ppublish` flag and uses `ossrh` server credentials.
- **Java Spotless formatting** - Updated google-java-format to 1.28.0 for Java 25 compatibility.

## [2.22.0] - 2026-01-13

### Fixed

- **C FFI visitor implementation** - Fixed `html_to_markdown_convert_with_visitor` to properly use the visitor handle during conversion instead of discarding it. Previously the visitor was created but the plain `convert()` function was called instead of `convert_with_visitor()`.
- **C# visitor callbacks** - P/Invoke bindings now correctly invoke visitor callbacks during HTML to Markdown conversion (42/42 tests passing).
- **Go visitor callbacks** - Removed regex-based post-processing workaround; Go bindings now use real FFI visitor callbacks with proper struct field ordering.
- **PHP visitor callbacks** - Wired up `PhpVisitorBridge` to pass visitor to Rust core instead of ignoring the visitor parameter.
- **Java visitor callbacks** - Added Panama FFI upcall stubs for all 38 visitor callbacks, enabling full visitor pattern support (95/95 tests passing).

### Added

- **Java `VisitorCallbackFactory`** - New class that creates Panama FFI upcall stubs for visitor callbacks, enabling Java code to receive callbacks from the Rust core during conversion.
- **Java `HtmlToMarkdown.convertWithVisitor()`** - Public API method for converting HTML with a custom visitor implementation.

## [2.21.1] - 2026-01-13

### Added

- **Serde serialization support for ConversionOptions** - Added `Serialize` and `Deserialize` traits to `ConversionOptions`, `PreprocessingOptions`, and all related structs. Enables JSON serialization/deserialization with camelCase field naming and lowercase string enum representations.

### Changed

- **Major refactor: Complete Phase 1 modular architecture** - Restructured core converter into modular handler components:
  - Extracted block element handlers (block-level HTML elements)
  - Extracted inline element handlers (2,363 lines of focused code)
  - Extracted table, list, and media handlers (2,528 lines)
  - Extracted semantic and form handlers (1,532 lines)
  - Improved code organization and maintainability across all language bindings
- **Unified FFI bindings architecture** - Consolidated common binding logic into shared crate, reducing duplication across Python, TypeScript, Ruby, PHP, Go, and Java bindings
- **Added visitor callback code generation system** - FFI now supports dynamic visitor callbacks for all language bindings (Python, Ruby, PHP, Elixir, etc.)
- **Enhanced preprocessing system** - Footer and nav element removal now integrated into preprocessing pipeline
- **Improved custom element detection** - Enhanced `has_custom_element_tags` to accurately detect only tag names with hyphens

### Internal

- Updated dependencies across all language bindings (Python, Ruby, PHP, JavaScript, Go, etc.)
- Refactored benchmark harness to modularize script adapters and reduce code duplication
- Refactored performance examples to extract and reuse shared utilities
- Improved sync_versions.py to handle all internal workspace dependency version pins
- Refactored README generation script to modularize template handling
- Improved clippy lint handling and CI coverage workflows
- Added documentation to Node.js binding example files

## [2.21.0] - 2026-01-10

### Added

- **`skip_images` configuration option** - New option to skip all `<img>` elements during conversion, enabling greater control over image handling in the output.
- **Optional visitor parameter across all convert functions** - Unified API for applying visitor patterns to all conversion modes:
  - `convert(html, options, visitor)` - Basic conversion with optional visitor
  - `convert_with_inline_images(html, options, image_cfg, visitor)` - Inline image extraction with optional visitor
  - `convert_with_metadata(html, options, metadata_cfg, visitor)` - Metadata extraction with optional visitor
- **Visitor pattern integration with advanced features** - Support for using visitor pattern simultaneously with inline images and metadata extraction, providing complete control over the conversion process.
- **Comprehensive test coverage** - Added tests validating `skip_images` functionality and visitor pattern integration across all conversion functions and language bindings.

### Changed

- **Visitor parameter unified across all APIs** - The visitor parameter is now optional on all conversion functions, enabling consistent API design across basic, inline-images, and metadata extraction paths.
- **Improved feature-gated architecture** - Refined the feature gate handling for better flexibility when combining visitor patterns with other optional features.

### Deprecated

- **`convert_with_visitor()` function** - Deprecated in favor of passing visitor as an optional parameter to `convert()`. The dedicated function will be removed in a future major release. Use `convert(html, options, visitor)` instead.

### Fixed

- **Unused dependency warnings in npm packages** - Resolved unused dependency warnings reported during builds of JavaScript/TypeScript packages.
- **Feature gate handling for visitor combinations** - Fixed issues with feature gate combinations when using visitor patterns alongside inline images and metadata extraction.

## [2.20.1] - 2026-01-09

### Code Quality

- **Resolved all clippy warnings comprehensively**: Fixed 207+ clippy pedantic/nursery warnings across entire workspace
  - Removed blanket `#![allow(clippy::pedantic)]` directives from all crate roots
  - Fixed trivial copy pass-by-ref issues in converter functions
  - Added missing documentation sections (# Errors) to public APIs
  - Fixed doc markdown formatting (added backticks to technical terms)
  - Applied selective allows only for architecturally justified cases
  - FFI/binding layers use targeted allows due to interop constraints
  - Core library maintains strict clippy compliance
- **Updated workspace lint configuration**: Changed pedantic lints from deny to warn to allow module-level selective overrides
- **Dependency modernization**: Migrated from `once_cell::sync::Lazy` to stdlib `std::sync::LazyLock` (stabilized in Rust 1.80+)

## [2.20.0] - 2026-01-05

### Dependencies

- **Updated reqwest to 0.13.1**: Migrated to new rustls defaults
  - rustls is now the default TLS backend (previously native-tls)
  - aws-lc is the default crypto provider (previously ring)
  - rustls-platform-verifier is used by default for root certificates
  - All reqwest features updated to new naming conventions
- **Updated development dependencies**: Updated pnpm packages, Ruby gems, and pre-commit hooks
  - oxlint pre-commit hook updated from v1.36.0 to v1.37.0
  - All language bindings dependencies refreshed

### Infrastructure

- **Fixed C# package update task**: Updated dotnet list command to specify project files explicitly
  - Prevents "project or solution file could not be found" errors
  - Now checks both HtmlToMarkdown.csproj and HtmlToMarkdown.Tests.csproj individually

## [2.19.8] - 2026-01-05

### Bug Fixes

- **Blockquote newline preservation**: Fixed Issue #176 - Newlines were not preserved when block elements like `<strong>` were directly adjacent to `<blockquote>` elements
  - Blockquotes now add proper spacing before and after themselves
  - Fixed blockquote+paragraph spacing to match CommonMark spec
  - Fixed blockquote+HR spacing to avoid extra newlines
  - Added comprehensive regression tests to prevent future regressions
  - Maintains CommonMark compliance (132/132 tests passing)

### Improvements

- **Debug logging cleanup**: Removed extensive debug logging from hOCR processing and core converter
  - Removed ~30 debug eprintln! statements that were spamming output
  - Removed unused debug parameters from hOCR functions (parse_properties, reconstruct_table, extract_hocr_document, etc.)
  - Cleaner output and reduced noise during HTML to Markdown conversion

## [2.19.7] - 2026-01-03

### Improvements

- **Homebrew bottle CI debugging**: Added verification steps to diagnose artifact upload/download issues
  - Added verification after bottle creation to confirm file exists in workspace
  - Added `if-no-files-found: error` to fail fast if bottle file not found during upload
  - Added verification after artifact download to show what was actually retrieved
  - These steps will help identify why Homebrew bottle artifacts aren't being found in release workflow

## [2.19.6] - 2026-01-03

### Bug Fixes

- **WASM npm package publishing**: Fixed Issue #172 - WASM package was published with only 3 files (LICENSE, package.json, README.md) instead of 25 files
  - Root cause: publish workflow downloaded WASM artifact tarballs but never extracted them before running `npm publish`
  - Added extraction step in `.github/workflows/publish.yaml` to unpack dist/, dist-node/, and dist-web/ directories
  - Added safeguard to remove .gitignore files from dist directories that could exclude content
  - Complete package now includes all WASM binaries and JavaScript wrappers (7.8 MB unpacked)

## [2.19.5] - 2025-01-02

### Bug Fixes

- **Homebrew bottle naming**: Fixed bottle filename format to match Homebrew convention
  - Changed from double-dash (`html-to-markdown--2.19.x`) to single-dash (`html-to-markdown-2.19.x`)
  - Homebrew constructs bottle URLs based on formula name and version, expecting single dash separator
  - Fixes bottle download failures when installing via `brew install`

## [2.19.4] - 2025-01-02

### Bug Fixes

- **Homebrew formula publishing**: Fixed publish workflow script that updates the Homebrew tap formula
  - Corrected bottle block deletion regex (was looking for `# bottle do` instead of `bottle do`), preventing duplicate bottle blocks from accumulating on each release
  - Added automatic source tarball SHA256 computation and formula update to ensure correct checksums
  - Formula now properly replaces old bottle blocks with new ones rather than appending

## [2.19.3] - 2025-01-02

### Bug Fixes

- **Table image processing**: Fixed Issue #175 - images inside Blogger-style HTML tables (e.g., `<table class="tr-caption-container">`) were being stripped during conversion. Enhanced table scanner to recognize images as content and properly process non-table elements like `<a>` and `<img>` that are direct children of table elements.
- **WASM npm package**: Fixed Issue #172 completely - package was published but missing all WASM binaries and JavaScript wrappers (only 23 KB with 3 files). Created `.npmignore` to include `dist/`, `dist-node/`, and `dist-web/` directories that were excluded by `.gitignore` during npm publish.
- **PHP Packagist publishing**: Fixed version mismatch that caused Packagist to reject v2.19.2 tag. Updated `sync_versions.py` to synchronize both root `composer.json` and `packages/php/composer.json`.
- **Test apps**: Fixed relative fixture paths in C#, Java, and Elixir test apps. Updated Elixir tests to handle tuple-returning API. Added Java native library path configuration.

### Infrastructure

- Enhanced `sync_versions.py` script to update root `composer.json` for Packagist validation
- Recreated v2.19.2 git tag with correct composer.json version

## [2.19.2] - 2025-12-30

### Bug Fixes

- **WASM npm package**: Fixed missing `.d.ts` files in published package by updating `files` field with glob patterns (fixes #172)
- **Test apps**: Fixed API mismatches across all language test apps (Python, Node.js, WASM, Go, Java, C#)
  - Python: Changed `convert_html_to_markdown()` to `convert()`
  - Node.js: Updated to scoped package `@kreuzberg/html-to-markdown`
  - WASM: Changed `convertHtmlToMarkdown()` to `convert()`
  - Go: Updated FFI version from 2.16.0 to 2.19.1 with enhanced error handling
  - Java: Added Maven wrapper files for portability
  - C#: Updated to `KreuzbergDev.HtmlToMarkdown` package name
- **Packagist publishing**: Added automated workflow job and moved `composer.json` to repository root
- **Maven Central publishing**: Fixed GitHub secrets configuration (corrected `GPG_PASSPHRASE` typo)
- **Go bindings**: Enhanced FFI download error messages with actionable troubleshooting guidance
- **Pre-commit hooks**: Fixed Go linting errors (errcheck, staticcheck) and formatting violations

### Infrastructure

- Created new WASM test app with comprehensive smoke and integration tests
- Updated all test apps to version 2.19.0 for consistent validation
- Enhanced Java package formatting to comply with 120-character line limit

## [2.19.1] - 2025-12-29

### Bug Fixes

- **Go formatting**: Applied `gofmt` to `packages/go/v2/htmltomarkdown/visitor.go` to align constant declarations
- **Java tooling**: Upgraded google-java-format from 1.21.0 to 1.25.2 for Java 25 compatibility
- **Homebrew distribution**: Added html-to-markdown formula to kreuzberg-dev homebrew tap for CLI installation

## [2.19.0] - 2025-12-29

### Breaking Changes

- **npm package namespace**: All npm packages now use the `@kreuzberg` scope for better organization and discoverability
  - `html-to-markdown-node` → `@kreuzberg/html-to-markdown-node`
  - `html-to-markdown-wasm` → `@kreuzberg/html-to-markdown-wasm`
- **Java package namespace**: Java binding now uses `dev.kreuzberg` package prefix instead of `com.goldziher`
  - Updated all Maven artifact IDs and Java package names for semantic clarity
  - Affects all public classes and imports in Java projects
- **C# namespace**: C# bindings now use `KreuzbergDev` namespace instead of `Goldziher`
  - Updated NuGet package ID to `KreuzbergDev.HtmlToMarkdown`
  - All public types now under `KreuzbergDev.HtmlToMarkdown` namespace

### Features

- **XML table support (TEI/JATS formats)**: Added support for TEI (Text Encoding Initiative) and JATS (Journal Article Tag Suite) table elements
  - `<row>` elements for table rows with proper cell grouping and nesting
  - `<cell>` elements with full attribute support including `role="head"` for header cells
  - `<graphic>` elements for figure/image references within cells and content blocks
  - Proper table structure preservation when converting scientific markup formats
  - Aligns with CommonMark table output while respecting source document semantics

### Bug Fixes

- Fixed Clippy warnings across Rust core and all binding crates for cleaner compilation
- Improved test suite with enhanced error messages and edge case coverage
- Refined table element handling for robustness with malformed markup

### Infrastructure

- **CI/CD improvements**: Enhanced C# workflow for improved reliability and platform coverage
- **Release distribution**: Added Homebrew bottle support for macOS CLI binary distribution
- **Version synchronization**: All language bindings now synchronized to v2.19.0

## [2.18.0] - 2025-12-28

### Added

- **Visitor Pattern**: Complete implementation of visitor pattern for custom HTML element processing across all 8 language bindings (Python, TypeScript, Ruby, PHP, Go, Java, C#, Elixir)
  - Synchronous and asynchronous visitor support (where applicable per language)
  - 40+ visitor methods with hooks for every HTML element type (text, links, images, headings, lists, tables, code blocks, and more)
  - `NodeContext` provides element metadata: tag name, attributes, depth, parent tag, inline status, and sibling index
  - Control flow options: Continue, Custom (provide custom markdown), Skip, PreserveHtml, or Error
  - Element lifecycle callbacks: `visit_element_start` and `visit_element_end` for complete control
  - **Python**: Full async visitor support with `convert_with_async_visitor()` function
  - **TypeScript**: Async visitor with full type definitions
  - **Ruby**: Sync visitor implementation with complete RBS type definitions
  - **PHP**: Full visitor support with PHPStan level 9 compliance
  - **Go**: Thread-safe visitor registry with markdown post-processing
  - **Java**: Panama FFI visitor (JDK 21+)
  - **C#**: P/Invoke visitor with cross-platform compatibility
  - **Elixir**: Rustler NIF visitor implementation

### Fixed

- **HTML parsing for modern websites**: Fixed issue where JavaScript-heavy websites (like Reuters) would lose article body content during conversion (GitHub issue #167)
  - The parser was incorrectly interpreting HTML-like strings inside `<script>` tags as actual HTML elements
  - Script and style tags are now properly stripped during preprocessing while preserving JSON-LD metadata
  - No performance impact on conversion speed
- **Python API**: Fixed missing `ConversionOptionsHandle` export in public API (GitHub issue #166)
  - Users can now import `ConversionOptionsHandle` directly from the `html_to_markdown` package
  - Maintains backward compatibility with existing `OptionsHandle` import

## [2.17.0] - 2025-12-22

### Added

- Go binding now auto-downloads the native FFI library from GitHub Releases with cache/override controls.
- Release pipeline now publishes per-platform Go FFI artifacts for Go installs.

## [2.16.1] - 2025-12-22

### Fixed

- Fast-path plain-text conversions now honor escape flags (asterisks/underscores/misc/ASCII).
- Fast-path plain-text conversions now normalize whitespace and trim trailing spaces.
- Fast-path plain-text conversions now respect `strip_newlines`.
- Python CLI proxy now only applies v1 translation defaults when v1-only flags are present.

## [2.16.0] - 2025-12-22

### Added

- Profiling harness and workflow for Rust core and bindings with consolidated flamegraph output.
- Benchmark scenarios for inline images, metadata extraction, and raw metadata output across fixtures.
- WASM profiling support with warmups and stable flamegraph parsing.
- FFI byte-based conversion path plus metadata-raw benchmark coverage.

### Changed

- Bench harness now supports expanded fixture coverage and results consolidation.
- Java benchmarks align on JDK 25 for consistent profiling runs.

### Fixed

- Node benchmark harness now runs from the package directory and uses native bindings.
- Profiling stability fixes across Go, Elixir, Java, and WASM adapters.
- Binary input detection now flags compressed/magic signatures and UTF-16 data with clearer errors.

### Performance

- Rust core conversion: metadata extraction, inline image handling, tag/whitespace caches, and text assembly hot paths.
- Bindings interop: tighter metadata serialization/deserialization paths.
- Rust bench harness (local, Apple M4): median ops/sec improved 18.8× on Wikipedia fixtures (53.7 → 1009.1).

## [2.15.0] - 2025-12-19

### Fixed

- Rust core: clamp table `colspan`/`rowspan` to prevent pathological allocations on malformed HTML.
- Rust core: reject binary-like inputs early to avoid OOMs when non-HTML data is passed to `convert`.

## [2.14.11] - 2025-12-16

### Fixed

- C# (NuGet): fix `ConvertWithMetadata()` deserialization for metadata enums (`link_type`, `image_type`, `data_type`, `text_direction`) by honoring the JSON wire values.

## [2.14.10] - 2025-12-16

### Fixed

- Python: release the GIL during native conversion so `ThreadPoolExecutor` parallelism doesn't regress performance, and always build the extension with metadata support (so `convert_with_metadata` is always available).

## [2.14.9] - 2025-12-16

### Fixed

- Structured data: JSON-LD is now extracted from `<script type="application/ld+json">` tags (including when placed in `<head>`), preserving the script contents for parsing.

## [2.14.8] - 2025-12-15

### Fixed

- Rust crate (`html-to-markdown-rs`): enable the `metadata` feature by default so `convert_with_metadata` is available without extra Cargo features.

## [2.14.7] - 2025-12-15

### Fixed

- Elixir (macOS): package now ships a `.cargo/config.toml` so Rustler can compile without requiring user-specific linker flags.

## [2.14.6] - 2025-12-15

### Fixed

- RubyGems publish: skip duplicate `ruby`-platform gems when multiple CI jobs produce identical artifacts for the same version.
- Hex publish: ensure the Rust core crate is staged into the Elixir package before publishing.

## [2.14.5] - 2025-12-15

### Fixed

- RubyGems publish: prevent corrupted gem pushes by downloading `rubygems-*` artifacts into separate directories (no merge), and publishing gems recursively with an integrity check.

## [2.14.4] - 2025-12-15

### Fixed

- Release pipeline: build the C# `osx-x64` native FFI library on `macos-15-intel` (macOS-13 runners are retired), unblocking NuGet publication.
- Elixir (Hex): package now vendors the Rust core crate so `mix deps.get && mix test` works outside this monorepo.

## [2.14.3] - 2025-12-15

### Fixed

- **Issue #150 / Discord report**: Python now always exports `convert_with_metadata` (no more `ImportError` on import).
- **Issue #149**: Blockquote text now word-wraps when `wrap=true`.
- **FFI JSON parity**: Metadata enums now serialize as snake_case (e.g. `external`, `relative`) to match cross-language expectations.
- PHP test runner now always builds the extension with the `metadata` feature enabled (avoids missing `html_to_markdown_convert_with_metadata` when the workspace was built with `--no-default-features`).

### Added

- Elixir: `convert_with_metadata/3` + `MetadataConfig` backed by the Rust metadata extractor.

### Changed

- WASM: metadata bindings are enabled by default so the published npm package exports `convertWithMetadata`.
- C# publish pipeline: stage native `html_to_markdown_ffi` libraries into the NuGet package under `runtimes/*/native`.
- Go: module path now uses semantic import versioning (`.../packages/go/v2`), and docs/examples were updated accordingly.
- Java: add `.sdkmanrc` for Java 25 + Maven 4; keep `maven-source-plugin` on `3.3.1` because `4.0.0-beta-1` is not compatible with Maven `4.0.0-rc-4`.

## [2.14.2] - 2025-12-13

### Changed

- CI/release automation: extracted Maven installer logic into `scripts/common/install-maven-latest.sh` and applied repo-wide lint/format cleanups.

## [2.14.1] - 2025-12-12

### Fixed

- **Issue #147**: Word wrap now works correctly in list items when using the `-w`/`--wrap` flag. List items with long text are properly wrapped while preserving list structure and indentation for both ordered and unordered lists.
- **Issue #146**: `strip_tags` and `preserve_tags` options now correctly prevent `<meta>` and `<title>` tags from being extracted into YAML frontmatter when `extract_metadata` is enabled.
- **Issue #145**: `strip_newlines=true` no longer causes excessive whitespace around block elements. Structural whitespace is now properly normalized while still removing newlines within paragraph content.
