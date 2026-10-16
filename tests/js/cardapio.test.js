import test from "node:test";
import assert from "node:assert";
import { normalizar, corresponde } from "../../static/js/cardapio.js";

test("normalizar remove acentos e caixa", () => {
  assert.strictEqual(normalizar("Pão de Açúcar"), "pao de acucar");
});
test("corresponde ignora acento; termo vazio casa tudo", () => {
  assert.strictEqual(corresponde({ nome: "Café Coado", descricao: "" }, "cafe"), true);
  assert.strictEqual(corresponde({ nome: "Café", descricao: "" }, ""), true);
  assert.strictEqual(corresponde({ nome: "Café", descricao: "quente" }, "QUEN"), true);
  assert.strictEqual(corresponde({ nome: "Café", descricao: "" }, "pizza"), false);
});
