import test from "node:test";
import assert from "node:assert";
import { horariosDoDia, diasDaAgenda, profissionaisPara, totais, mensagemAgendamento } from "../../static/js/agendamento.js";

test("horário só se o atendimento cabe no período", () => {
  assert.deepStrictEqual(horariosDoDia([[540, 720]], 60, 30, null),
    ["09:00", "09:30", "10:00", "10:30", "11:00"]);
  assert.deepStrictEqual(horariosDoDia([[540, 720], [810, 1140]], 120, 60, null).slice(-2),
    ["15:30", "16:30"]);
  assert.deepStrictEqual(horariosDoDia([[1020, 1140]], 120, 30, null), ["17:00"]);
});
test("hoje não oferece horário que já passou", () => {
  assert.deepStrictEqual(horariosDoDia([[540, 1140]], 30, 30, 1130), []);
  assert.strictEqual(horariosDoDia([[540, 1140]], 30, 30, 600)[0], "10:30");
});
test("dias fechados vêm sem períodos", () => {
  const d = diasDaAgenda({ ter: [[540, 720]] }, new Date(2026, 9, 18), 3); // domingo
  assert.deepStrictEqual(d.map((x) => [x.chave, x.periodos.length]), [["dom", 0], ["seg", 0], ["ter", 1]]);
});
test("profissional precisa fazer todos os serviços", () => {
  const eq = [{ id: "p1", servicos: ["corte", "barba"] }, { id: "p2", servicos: ["corte"] }];
  assert.deepStrictEqual(profissionaisPara(eq, ["corte", "barba"]).map((p) => p.id), ["p1"]);
  assert.deepStrictEqual(profissionaisPara(eq, ["luzes"]), []);
});
test("totais com porte, a partir de e a combinar", () => {
  const s = [{ nome: "Banho", minutos: 60, centavos: null, aPartirDe: false, porte: { P: 5000, M: 6000 } }];
  const a = [{ nome: "Táxi dog", centavos: null }];
  assert.deepStrictEqual(totais(s, a, "M"), { centavos: 6000, minutos: 60, aPartirDe: false, aCombinar: ["Táxi dog"] });
});
test("mensagem exata", () => {
  const msg = mensagemAgendamento({
    loja: "Navalha & Co",
    servicos: [
      { nome: "Corte", minutos: 40, centavos: 4500, aPartirDe: false, porte: null },
      { nome: "Barba", minutos: 30, centavos: 3500, aPartirDe: false, porte: null },
    ],
    adicionais: [],
    porte: null,
    pet: null,
    profissional: null,
    data: new Date(2026, 9, 21),
    hora: "14:00",
    nome: "Lucas",
    bairro: "",
    obs: "",
  });
  assert.strictEqual(msg, [
    "Olá! Quero agendar pela página da Navalha & Co.",
    "",
    "• Corte (R$ 45,00)",
    "• Barba (R$ 35,00)",
    "",
    "Profissional: sem preferência",
    "Dia: quarta, 21/10 às 14:00",
    "Duração: 1h10 · Total: R$ 80,00",
    "Nome: Lucas",
  ].join("\n"));
});
test("mensagem com pet, bairro, a partir de e obs", () => {
  const msg = mensagemAgendamento({
    loja: "Navalha & Co",
    servicos: [
      { nome: "Tosa", minutos: 50, centavos: null, aPartirDe: true, porte: { P: 3000, M: 4000 } },
    ],
    adicionais: [{ nome: "Táxi dog", centavos: null, pedeBairro: true }],
    porte: "M",
    pet: "Rex",
    profissional: { id: "p1", nome: "Ana", servicos: ["tosa"] },
    data: new Date(2026, 9, 21),
    hora: "09:30",
    nome: "Lucas",
    bairro: "Centro",
    obs: "  Chegar cedo  ",
  });
  assert.strictEqual(msg, [
    "Olá! Quero agendar pela página da Navalha & Co.",
    "",
    "• Tosa (a partir de R$ 40,00, porte M)",
    "• Táxi dog (a combinar)",
    "",
    "Pet: Rex (porte M)",
    "Profissional: Ana",
    "Dia: quarta, 21/10 às 09:30",
    "Bairro: Centro",
    "Duração: 50 min · Total: a partir de R$ 40,00 + a combinar",
    "Nome: Lucas",
    "Obs.: Chegar cedo",
  ].join("\n"));
});
