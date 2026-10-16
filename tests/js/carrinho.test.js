import test from "node:test";
import assert from "node:assert";
import { Carrinho, formatarBRL, linkPedido } from "../../static/js/carrinho.js";

test("formatarBRL", () => {
  assert.strictEqual(formatarBRL(4290), "R$ 42,90");
  assert.strictEqual(formatarBRL(123450), "R$ 1.234,50");
  assert.strictEqual(formatarBRL(5), "R$ 0,05");
  assert.strictEqual(formatarBRL(0), "R$ 0,00");
});
test("total exato em centavos", () => {
  const c = new Carrinho();
  c.adicionar("a", "A", 10);
  c.adicionar("b", "B", 20);
  assert.strictEqual(c.totalCentavos(), 30);
  c.adicionar("a", "A", 10);
  assert.strictEqual(c.quantidade(), 3);
  assert.strictEqual(c.totalCentavos(), 40);
});
test("alterar com qtd <= 0 remove", () => {
  const c = new Carrinho();
  c.adicionar("a", "A", 10);
  c.alterar("a", 0);
  assert.deepStrictEqual(c.itens(), []);
});
test("mensagem no formato do pedido", () => {
  const c = new Carrinho();
  c.adicionar("1", "X-Bacon & Cia 🍔", 2990);
  c.alterar("1", 2);
  c.adicionar("2", "Fritas", 1800);
  const m = c.mensagem("Burger Lab", "Sem cebola\nbem passado");
  assert.strictEqual(m,
    "Olá! Pedido pelo cardápio digital — Burger Lab\n\n" +
    "2x X-Bacon & Cia 🍔 — R$ 59,80\n1x Fritas — R$ 18,00\n\n" +
    "Total: R$ 77,80\nObs.: Sem cebola\nbem passado");
  assert.ok(!c.mensagem("L", "").includes("Obs."));
  assert.ok(!c.mensagem("L", "  ").includes("Obs."));
});
test("linkPedido codifica & e quebra de linha", () => {
  const l = linkPedido("5511999999999", "a & b\nc");
  assert.ok(l.startsWith("https://wa.me/5511999999999?text="));
  assert.ok(l.includes("%26") && l.includes("%0A"));
});
test("dados persistidos reidratam e lixo é ignorado", () => {
  const c = new Carrinho([{ id: "a", nome: "A", centavos: 10, qtd: 2 }, { lixo: 1 }]);
  assert.strictEqual(c.totalCentavos(), 20);
  assert.strictEqual(c.itens().length, 1);
});
