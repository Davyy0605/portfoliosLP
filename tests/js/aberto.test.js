import test from "node:test";
import assert from "node:assert";
import { readFileSync } from "node:fs";

// aberto.js é um script clássico incluído inline pelo Jinja; aqui ele é avaliado como função.
const fonte = readFileSync(new URL("../../temas/cafeteria/aberto.js", import.meta.url), "utf8");
const statusAberto = new Function(`${fonte}; return statusAberto;`)();

const ter10 = new Date(2026, 9, 20, 10, 0); // terça
const sab10 = new Date(2026, 9, 24, 10, 0); // sábado
const h = (dias, horas) => ({ dias, horas });
const txt = (lista, quando) => statusAberto(lista, quando)?.texto ?? null;

test("formatos de dias da semana", () => {
  for (const dias of ["Seg a Sex", "Seg-Sex", "Seg – Sex", "De segunda a sexta", "segunda-feira a sexta-feira", "Todos os dias", "Diariamente"]) {
    assert.strictEqual(txt([h(dias, "7h às 19h")], ter10), "Aberto agora, até 19h", dias);
  }
});

test("fins de semana e dias soltos", () => {
  const l = [h("Seg a Sex", "7h30 às 19h"), h("Fins de semana", "9h às 15h")];
  assert.strictEqual(txt(l, sab10), "Aberto agora, até 15h");
  assert.strictEqual(txt([h("Ter, Qui e Sáb", "9h às 12h")], sab10), "Aberto agora, até 12h");
});

test("turno partido lê todos os pares de horas", () => {
  const l = [h("Seg a Sex", "7h às 12h e 14h às 19h")];
  assert.strictEqual(txt(l, new Date(2026, 9, 20, 15, 0)), "Aberto agora, até 19h");
  assert.strictEqual(txt(l, new Date(2026, 9, 20, 13, 0)), "Fechado agora. Abre hoje às 14h");
});

test("próxima abertura e virada da meia-noite", () => {
  assert.strictEqual(txt([h("Seg a Sex", "7h30 às 19h")], new Date(2026, 9, 20, 20, 0)), "Fechado agora. Abre amanhã às 7h30");
  assert.strictEqual(txt([h("Seg a Sex", "7h30 às 19h")], sab10), "Fechado agora. Abre segunda às 7h30");
  assert.strictEqual(txt([h("Sex", "18h às 2h")], new Date(2026, 9, 24, 1, 0)), "Aberto agora, até 2h");
});

test("texto que não entende esconde o bloco", () => {
  assert.strictEqual(statusAberto([h("Seg a Sex", "7h às 19h"), h("Feriados", "9h às 13h")], ter10), null);
  assert.strictEqual(statusAberto([h("Seg a Sex", "a partir das 7h")], ter10), null);
  assert.strictEqual(statusAberto([], ter10), null);
  // "Fechado" é entendido e não abre o dia
  assert.strictEqual(txt([h("Seg a Sáb", "8h às 18h"), h("Domingo", "Fechado")], new Date(2026, 9, 25, 10, 0)), "Fechado agora. Abre amanhã às 8h");
});
