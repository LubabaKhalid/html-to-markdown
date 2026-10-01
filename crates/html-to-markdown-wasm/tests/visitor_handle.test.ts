// Regression test for #517: assigning a WasmVisitorHandle to ConversionOptions.visitor must borrow
// the handle, not consume it, and convert() must honour the options field when no explicit visitor
// argument is passed.
import { describe, expect, it } from "vitest";
import {
  convert,
  WasmConversionOptions,
  WasmConversionOptionsUpdate,
  WasmConversionResult,
  WasmDocumentStructure,
  WasmImageDimensions,
  WasmImageMetadata,
  WasmPreprocessingOptionsUpdate,
  WasmVisitorHandle,
} from "../pkg/nodejs/html_to_markdown_wasm.js";

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

  it("a plain-object visitor argument wins over options.visitor", () => {
    const { calls, handle } = headingVisitor();

    const options = new WasmConversionOptions();
    options.visitor = handle;
    const explicit = {
      visitHeading(_ctx: unknown, _level: number, text: string) {
        return { custom: `EXPLICIT ${text}` };
      },
    };

    const content = convert(HTML, options, explicit).content;
    expect(content).toContain("EXPLICIT Title");
    expect(content).not.toContain("VISITED");
    expect(calls).toEqual([]);
  });
});

// Each optional class-typed field borrows the value it is given and has a clear*() method to unset it.
// Assigning null or undefined throws: the clear*() method is the way to unset the field.
type Field = {
  name: string;
  owner: () => Record<string, unknown>;
  field: string;
  clear: string;
  value: () => object;
  className: string;
};

const FIELDS: Field[] = [
  {
    name: "ConversionOptions.visitor",
    owner: () => new WasmConversionOptions() as unknown as Record<string, unknown>,
    field: "visitor",
    clear: "clearVisitor",
    value: () => headingVisitor().handle,
    className: "WasmVisitorHandle",
  },
  {
    name: "ConversionOptionsUpdate.visitor",
    owner: () => WasmConversionOptionsUpdate.default() as unknown as Record<string, unknown>,
    field: "visitor",
    clear: "clearVisitor",
    value: () => headingVisitor().handle,
    className: "WasmVisitorHandle",
  },
  {
    name: "ConversionOptionsUpdate.preprocessing",
    owner: () => WasmConversionOptionsUpdate.default() as unknown as Record<string, unknown>,
    field: "preprocessing",
    clear: "clearPreprocessing",
    value: () => new WasmPreprocessingOptionsUpdate(true),
    className: "WasmPreprocessingOptionsUpdate",
  },
  {
    name: "ConversionResult.document",
    owner: () => WasmConversionResult.default() as unknown as Record<string, unknown>,
    field: "document",
    clear: "clearDocument",
    value: () => new WasmDocumentStructure([], "html"),
    className: "WasmDocumentStructure",
  },
  {
    name: "ImageMetadata.dimensions",
    owner: () => WasmImageMetadata.default() as unknown as Record<string, unknown>,
    field: "dimensions",
    clear: "clearDimensions",
    value: () => new WasmImageDimensions(1, 2),
    className: "WasmImageDimensions",
  },
];

describe.each(FIELDS)("$name", ({ owner, field, clear, value, className }) => {
  it("reuses one value across two owners", () => {
    const shared = value();

    const first = owner();
    first[field] = shared;
    const second = owner();
    second[field] = shared;

    expect(first[field]).toBeDefined();
    expect(second[field]).toBeDefined();
  });

  it(`${clear}() unsets the field and a later assignment sets it again`, () => {
    const target = owner();
    target[field] = value();
    (target[clear] as () => void).call(target);
    expect(target[field]).toBeUndefined();

    target[field] = value();
    expect(target[field]).toBeDefined();
  });

  it.each([null, undefined])("rejects %s", (empty) => {
    const target = owner();
    target[field] = value();

    expect(() => {
      target[field] = empty;
    }).toThrow(`expected instance of ${className}`);
  });
});

describe("borrowed values stay usable", () => {
  it("a visitor handle on an update still drives a conversion", () => {
    const { calls, handle } = headingVisitor();

    const update = WasmConversionOptionsUpdate.default();
    update.visitor = handle;
    const options = new WasmConversionOptions();
    options.visitor = handle;

    expect(convert(HTML, options).content).toContain("VISITED Title");
    expect(calls).toEqual(["Title"]);
  });

  it("image dimensions keep their values after assignment", () => {
    const dimensions = new WasmImageDimensions(3, 4);

    const image = WasmImageMetadata.default();
    image.dimensions = dimensions;

    expect(dimensions.width).toBe(3);
    expect(image.dimensions?.height).toBe(4);
  });
});
