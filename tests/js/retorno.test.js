import test from "node:test";
import assert from "node:assert";
import { rotuloDuracao } from "../../static/js/retorno.js";

test("rotuloDuracao", () => {
  assert.strictEqual(rotuloDuracao(40), "40 min");
  assert.strictEqual(rotuloDuracao(60), "1h");
  assert.strictEqual(rotuloDuracao(70), "1h10");
  assert.strictEqual(rotuloDuracao(125), "2h05");
});
