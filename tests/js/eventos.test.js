import test from "node:test";
import assert from "node:assert";
import { resolverData, visivel, formatarData } from "../../static/js/eventos.js";

const hoje = new Date(2026, 9, 16, 23, 30);
test("resolverData usa data local, mesmo às 23h30", () => {
  assert.strictEqual(resolverData({ emDias: 3 }, hoje), "2026-10-19");
  assert.strictEqual(resolverData({ emDias: 0 }, hoje), "2026-10-16");
  assert.strictEqual(resolverData({ data: "2026-11-20" }, hoje), "2026-11-20");
});
test("visivel: hoje e futuro sim, passado não", () => {
  assert.strictEqual(visivel("2026-10-16", hoje), true);
  assert.strictEqual(visivel("2026-10-17", hoje), true);
  assert.strictEqual(visivel("2026-10-15", hoje), false);
});
test("formatarData devolve texto pt-BR", () => {
  const norm = (s) => s.replace(/ /g, " ");
  assert.strictEqual(norm(formatarData("2026-10-16")), "sex., 16 de out.");
  assert.strictEqual(norm(formatarData("2026-12-01")), "ter., 1 de dez.");
});
test("sem data nem em-dias: null e invisível", () => {
  assert.strictEqual(resolverData({}, hoje), null);
  assert.strictEqual(resolverData({ emDias: "abc" }, hoje), null);
  assert.strictEqual(visivel(null, hoje), false);
});
