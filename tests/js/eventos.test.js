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
  assert.match(formatarData("2026-10-16"), /16/);
});
