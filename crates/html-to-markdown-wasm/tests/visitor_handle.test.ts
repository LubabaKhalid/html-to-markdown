// Regression test for #517: assigning a WasmVisitorHandle to ConversionOptions.visitor must borrow
// the handle, not consume it, and convert() must honour the options field when no explicit visitor
// argument is passed.
import { describe, expect, it } from "vitest";
import {
  convert,
  WasmConversionOptions,
  WasmConversionOptionsUpdate,
  WasmConversionResult,
  WasmDocumentMetadata,
  WasmDocumentStructure,
  WasmHtmlMetadata,
  WasmImageDimensions,
  WasmImageMetadata,
  WasmPreprocessingOptions,
  WasmPreprocessingOptionsUpdate,
  WasmTableData,
  WasmTableGrid,
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
interface OptionalField<Owner extends object, Value> {
  name: string;
  field: string;
  clearName: string;
  className: string;
  owner: () => Owner;
  value: () => Value;
  get: (owner: Owner) => Value | undefined;
  set: (owner: Owner, value: Value) => void;
  clear: (owner: Owner) => void;
}

function describeOptionalField<Owner extends object, Value>(c: OptionalField<Owner, Value>): void {
  describe(c.name, () => {
    it("reuses one value across two owners", () => {
      const shared = c.value();

      const first = c.owner();
      c.set(first, shared);
      const second = c.owner();
      c.set(second, shared);

      expect(c.get(first)).toBeDefined();
      expect(c.get(second)).toBeDefined();
    });

    it(`${c.clearName}() unsets the field and a later assignment sets it again`, () => {
      const target = c.owner();
      c.set(target, c.value());
      c.clear(target);
      expect(c.get(target)).toBeUndefined();

      c.set(target, c.value());
      expect(c.get(target)).toBeDefined();
    });

    it.each([null, undefined])("rejects %s", (empty) => {
      const target = c.owner();
      c.set(target, c.value());

      expect(() => Reflect.set(target, c.field, empty)).toThrow(`expected instance of ${c.className}`);
    });
  });
}

describeOptionalField({
  name: "ConversionOptions.visitor",
  field: "visitor",
  clearName: "clearVisitor",
  className: "WasmVisitorHandle",
  owner: () => new WasmConversionOptions(),
  value: () => headingVisitor().handle,
  get: (o: WasmConversionOptions) => o.visitor,
  set: (o: WasmConversionOptions, v: WasmVisitorHandle) => {
    o.visitor = v;
  },
  clear: (o: WasmConversionOptions) => o.clearVisitor(),
});

describeOptionalField({
  name: "ConversionOptionsUpdate.visitor",
  field: "visitor",
  clearName: "clearVisitor",
  className: "WasmVisitorHandle",
  owner: () => WasmConversionOptionsUpdate.default(),
  value: () => headingVisitor().handle,
  get: (o: WasmConversionOptionsUpdate) => o.visitor,
  set: (o: WasmConversionOptionsUpdate, v: WasmVisitorHandle) => {
    o.visitor = v;
  },
  clear: (o: WasmConversionOptionsUpdate) => o.clearVisitor(),
});

describeOptionalField({
  name: "ConversionOptionsUpdate.preprocessing",
  field: "preprocessing",
  clearName: "clearPreprocessing",
  className: "WasmPreprocessingOptionsUpdate",
  owner: () => WasmConversionOptionsUpdate.default(),
  value: () => new WasmPreprocessingOptionsUpdate(true),
  get: (o: WasmConversionOptionsUpdate) => o.preprocessing,
  set: (o: WasmConversionOptionsUpdate, v: WasmPreprocessingOptionsUpdate) => {
    o.preprocessing = v;
  },
  clear: (o: WasmConversionOptionsUpdate) => o.clearPreprocessing(),
});

describeOptionalField({
  name: "ConversionResult.document",
  field: "document",
  clearName: "clearDocument",
  className: "WasmDocumentStructure",
  owner: () => WasmConversionResult.default(),
  value: () => new WasmDocumentStructure([], "html"),
  get: (o: WasmConversionResult) => o.document,
  set: (o: WasmConversionResult, v: WasmDocumentStructure) => {
    o.document = v;
  },
  clear: (o: WasmConversionResult) => o.clearDocument(),
});

describeOptionalField({
  name: "ImageMetadata.dimensions",
  field: "dimensions",
  clearName: "clearDimensions",
  className: "WasmImageDimensions",
  owner: () => WasmImageMetadata.default(),
  value: () => new WasmImageDimensions(1, 2),
  get: (o: WasmImageMetadata) => o.dimensions,
  set: (o: WasmImageMetadata, v: WasmImageDimensions) => {
    o.dimensions = v;
  },
  clear: (o: WasmImageMetadata) => o.clearDimensions(),
});

// Each required class-typed field borrows the value it is given, so one value can go on two owners.
interface RequiredField<Owner extends object, Value> {
  name: string;
  owner: () => Owner;
  value: () => Value;
  get: (owner: Owner) => Value;
  set: (owner: Owner, value: Value) => void;
}

function describeRequiredField<Owner extends object, Value>(c: RequiredField<Owner, Value>): void {
  describe(c.name, () => {
    it("reuses one value across two owners", () => {
      const shared = c.value();

      const first = c.owner();
      c.set(first, shared);
      const second = c.owner();
      c.set(second, shared);

      expect(c.get(first)).toBeDefined();
      expect(c.get(second)).toBeDefined();
    });
  });
}

describeRequiredField({
  name: "ConversionOptions.preprocessing",
  owner: () => new WasmConversionOptions(),
  value: () => WasmPreprocessingOptions.default(),
  get: (o: WasmConversionOptions) => o.preprocessing,
  set: (o: WasmConversionOptions, v: WasmPreprocessingOptions) => {
    o.preprocessing = v;
  },
});

describeRequiredField({
  name: "ConversionResult.metadata",
  owner: () => WasmConversionResult.default(),
  value: () => WasmHtmlMetadata.default(),
  get: (o: WasmConversionResult) => o.metadata,
  set: (o: WasmConversionResult, v: WasmHtmlMetadata) => {
    o.metadata = v;
  },
});

describeRequiredField({
  name: "HtmlMetadata.document",
  owner: () => WasmHtmlMetadata.default(),
  value: () => WasmDocumentMetadata.default(),
  get: (o: WasmHtmlMetadata) => o.document,
  set: (o: WasmHtmlMetadata, v: WasmDocumentMetadata) => {
    o.document = v;
  },
});

describeRequiredField({
  name: "TableData.grid",
  owner: () => WasmTableData.default(),
  value: () => WasmTableGrid.default(),
  get: (o: WasmTableData) => o.grid,
  set: (o: WasmTableData, v: WasmTableGrid) => {
    o.grid = v;
  },
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
