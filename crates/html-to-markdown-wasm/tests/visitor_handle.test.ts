// Regression test for #517: assigning a WasmVisitorHandle to ConversionOptions.visitor must borrow
// the handle, not consume it, and convert() must honour the options field when no explicit visitor
// argument is passed.
import { describe, expect, it } from "vitest";
import { convert, WasmConversionOptions, WasmVisitorHandle } from "../pkg/nodejs/html_to_markdown_wasm.js";

const HTML = "<h1>Title</h1>";

function headingVisitor() {
	const calls: string[] = [];
	const handle = new WasmVisitorHandle({
		visitHeading(_ctx: unknown, _level: number, text: string) {
			calls.push(text);
			return { custom: `VISITED ${text}` };
		},
	});
	return { calls, handle };
}

describe("ConversionOptions.visitor", () => {
	it("reuses one handle across two options objects", () => {
		const { calls, handle } = headingVisitor();

		const first = new WasmConversionOptions();
		first.visitor = handle;
		const second = new WasmConversionOptions();
		second.visitor = handle;

		expect(convert(HTML, first).content).toContain("VISITED Title");
		expect(convert(HTML, second).content).toContain("VISITED Title");
		expect(calls).toEqual(["Title", "Title"]);
	});

	it("clearVisitor() unsets the field", () => {
		const { calls, handle } = headingVisitor();

		const options = new WasmConversionOptions();
		options.visitor = handle;
		options.clearVisitor();

		expect(convert(HTML, options).content).not.toContain("VISITED");
		expect(calls).toEqual([]);
	});
});
