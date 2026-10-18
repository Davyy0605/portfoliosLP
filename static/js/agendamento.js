// Motor de agendamento: funções puras + iniciar(raiz) para a página. Nada toca o DOM ao importar em Node.
import { formatarBRL, linkPedido } from "./carrinho.js";
import { avisar, prepararAviso, desenharBarra, rotuloDuracao } from "./retorno.js";

export const DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"];
const DIAS_EXTENSO = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"];

const dois = (n) => String(n).padStart(2, "0");

function formatarHora(minutos) {
  return `${dois(Math.floor(minutos / 60))}:${dois(minutos % 60)}`;
}

// Horários de início possíveis num dia. Um atendimento só cabe se termina dentro do período.
export function horariosDoDia(periodos, duracao, intervalo, agoraMin) {
  const horarios = [];
  for (const [inicio, fim] of periodos) {
    for (let s = inicio; s + duracao <= fim; s += intervalo) {
      if (agoraMin !== null && s <= agoraMin) continue;
      horarios.push(formatarHora(s));
    }
  }
  return horarios;
}

// Próximos n dias corridos a partir de hoje; dias sem funcionamento vêm com periodos [].
export function diasDaAgenda(funcionamento, hoje, n) {
  const dias = [];
  for (let i = 0; i < n; i++) {
    const data = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + i);
    const chave = DIAS[data.getDay()];
    dias.push({ data, chave, periodos: funcionamento?.[chave] ?? [] });
  }
  return dias;
}

// Só quem faz todos os serviços pedidos.
export function profissionaisPara(equipe, ids) {
  return equipe.filter((p) => ids.every((id) => (p.servicos ?? []).includes(id)));
}

// Preço de um serviço: pelo porte quando ele existe; senão, o preço fixo.
function precoServico(servico, porte) {
  if (porte && Number.isInteger(servico.porte?.[porte])) {
    return { centavos: servico.porte[porte], pelePorte: true };
  }
  if (Number.isInteger(servico.centavos)) {
    return { centavos: servico.centavos, pelePorte: false };
  }
  return null;
}

export function totais(servicos, adicionais, porte) {
  let centavos = 0;
  let minutos = 0;
  let aPartirDe = false;
  for (const s of servicos) {
    minutos += s.minutos;
    aPartirDe ||= Boolean(s.aPartirDe);
    centavos += precoServico(s, porte)?.centavos ?? 0;
  }
  const aCombinar = [];
  for (const a of adicionais) {
    if (Number.isInteger(a.centavos)) centavos += a.centavos;
    else aCombinar.push(a.nome);
  }
  return { centavos, minutos, aPartirDe, aCombinar };
}

export function mensagemAgendamento({ loja, servicos, adicionais, porte, pet, profissional, data, hora, nome, bairro, obs }) {
  const linhas = [`Olá! Quero agendar pela página da ${loja}.`, ""];

  for (const s of servicos) {
    const preco = precoServico(s, porte);
    if (!preco) {
      linhas.push(`• ${s.nome} (a combinar)`);
      continue;
    }
    const valor = formatarBRL(preco.centavos);
    let corpo = s.aPartirDe ? `a partir de ${valor}` : valor;
    if (preco.pelePorte) corpo += `, porte ${porte}`;
    linhas.push(`• ${s.nome} (${corpo})`);
  }
  for (const a of adicionais) {
    linhas.push(Number.isInteger(a.centavos) ? `• ${a.nome} (${formatarBRL(a.centavos)})` : `• ${a.nome} (a combinar)`);
  }
  linhas.push("");

  const petNome = (pet ?? "").trim();
  if (petNome) linhas.push(`Pet: ${petNome}${porte ? ` (porte ${porte})` : ""}`);
  linhas.push(`Profissional: ${profissional ? profissional.nome : "sem preferência"}`);
  linhas.push(`Dia: ${DIAS_EXTENSO[data.getDay()]}, ${dois(data.getDate())}/${dois(data.getMonth() + 1)} às ${hora}`);
  if (adicionais.some((a) => a.pedeBairro)) linhas.push(`Bairro: ${bairro}`);

  const t = totais(servicos, adicionais, porte);
  const prefixo = t.aPartirDe ? "a partir de " : "";
  const combinar = t.aCombinar.length ? " + a combinar" : "";
  linhas.push(`Duração: ${rotuloDuracao(t.minutos)} · Total: ${prefixo}${formatarBRL(t.centavos)}${combinar}`);
  linhas.push(`Nome: ${nome}`);

  const observacao = (obs ?? "").trim();
  if (observacao) linhas.push(`Obs.: ${observacao}`);

  return linhas.join("\n");
}

// ---------------------------------------------------------------------------
// Página de agendamento (só no navegador; os testes em Node importam as funções puras acima).

const DIAS_CURTOS = DIAS_EXTENSO.map((d) => d.slice(0, 3));

export function iniciar(raiz = document) {
  prepararAviso(raiz);
  const form = raiz.querySelector("[data-agendamento]");
  const dadosEl = raiz.querySelector("[data-agenda-dados]");
  if (!form) return;
  if (!dadosEl) { form.dataset.pronto = ""; return; }
  const agenda = JSON.parse(dadosEl.textContent);
  const whatsapp = form.dataset.whatsapp;
  const q = (s) => form.querySelector(s);

  const passos = [...form.querySelectorAll("[data-passo]")];
  const barra = q("[data-barra]");
  const voltar = q("[data-passo-voltar]");
  const erro = q("[data-erro]");
  const enviar = q("[data-agendar-enviar]");
  const nome = q("input[name=nome]");
  const bairro = q("input[name=bairro]");
  const obs = q("textarea[name=obs]");
  const pet = q("input[name=pet]");
  const reduzMovimento = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  const estado = { passo: 0, dia: null, hora: null, profissional: "" };
  const marcados = (campo, lista) =>
    lista.filter((x) => form.querySelector(`input[name=${campo}][value="${x.id}"]`)?.checked);
  const servicos = () => marcados("servico", agenda.servicos);
  const adicionais = () => marcados("adicional", agenda.adicionais);
  const porte = () => form.querySelector("input[name=porte]:checked")?.value ?? "";
  const profissional = () => agenda.equipe.find((p) => p.id === estado.profissional) ?? null;
  const pedeBairro = () => adicionais().some((a) => a.pedeBairro);
  const hoje = new Date();

  function diasDisponiveis() {
    const t = totais(servicos(), adicionais(), porte());
    const func = profissional()?.funcionamento ?? agenda.funcionamento;
    return diasDaAgenda(func, hoje, agenda.dias).map((d, i) => {
      const agoraMin = i === 0 ? hoje.getHours() * 60 + hoje.getMinutes() : null;
      const horarios = t.minutos > 0 ? horariosDoDia(d.periodos, t.minutos, agenda.intervalo, agoraMin) : [];
      return { ...d, horarios };
    });
  }

  function radio(campo, valor, rotulo, marcado, extra = {}) {
    const label = raiz.createElement("label");
    label.className = "opcao";
    const input = raiz.createElement("input");
    input.type = "radio";
    input.name = campo;
    input.value = valor;
    input.checked = marcado;
    Object.assign(input.dataset, extra);
    label.append(input, " ", rotulo);
    return label;
  }

  function desenharProfissionais() {
    const lista = profissionaisPara(agenda.equipe, servicos().map((s) => s.id));
    if (!lista.some((p) => p.id === estado.profissional)) estado.profissional = "";
    q("[data-profissionais]").replaceChildren(
      radio("profissional", "", "Sem preferência", estado.profissional === ""),
      ...lista.map((p) =>
        radio("profissional", p.id, p.especialidade ? `${p.nome} · ${p.especialidade}` : p.nome, estado.profissional === p.id, { nome: p.nome })
      )
    );
  }

  function desenharHoras(dias) {
    const horarios = estado.dia === null ? [] : dias[estado.dia].horarios;
    if (!horarios.includes(estado.hora)) estado.hora = null;
    q("[data-horas]").replaceChildren(...horarios.map((h) => radio("hora", h, h, estado.hora === h)));
  }

  function desenharQuando() {
    const dias = diasDisponiveis();
    if (estado.dia !== null && !dias[estado.dia]?.horarios.length) estado.dia = null;
    q("[data-dias]").replaceChildren(
      ...dias.map((d, i) => {
        const rotulo = `${DIAS_CURTOS[d.data.getDay()]} ${dois(d.data.getDate())}/${dois(d.data.getMonth() + 1)}`;
        const l = radio("dia", String(i), rotulo, estado.dia === i);
        if (!d.horarios.length) {
          l.querySelector("input").disabled = true;
          l.classList.add("indisponivel");
        }
        return l;
      })
    );
    desenharHoras(dias);
  }

  function mensagem() {
    return mensagemAgendamento({
      loja: agenda.loja, servicos: servicos(), adicionais: adicionais(), porte: porte(), pet: pet?.value,
      profissional: profissional(), data: diasDisponiveis()[estado.dia].data, hora: estado.hora,
      nome: nome.value.trim(), bairro: bairro.value.trim(), obs: obs.value,
    });
  }

  function desenharEnvio() {
    q("[data-campo-bairro]").hidden = !pedeBairro();
    const pronto = servicos().length > 0 && estado.dia !== null && estado.hora !== null &&
      nome.value.trim() !== "" && (!pedeBairro() || bairro.value.trim() !== "");
    if (pronto) {
      enviar.removeAttribute("aria-disabled");
      enviar.href = linkPedido(whatsapp, mensagem());
    } else {
      enviar.setAttribute("aria-disabled", "true");
      enviar.removeAttribute("href");
    }
  }

  function desenharResumo() {
    const sv = servicos();
    const ad = adicionais();
    const t = totais(sv, ad, porte());
    desenharBarra(barra, {
      linha: `${sv.length} ${sv.length === 1 ? "serviço" : "serviços"} · ${rotuloDuracao(t.minutos)}`,
      total: `${t.aPartirDe ? "a partir de " : ""}${formatarBRL(t.centavos)}${t.aCombinar.length ? " + a combinar" : ""}`,
      etiquetas: [...sv, ...ad].map((x) => x.nome),
    });
    // No último passo o botão de enviar assume; a barra some para não cobri-lo.
    if (estado.passo === passos.length - 1) barra.hidden = true;
    // Antes do passo de serviços (ex.: pet) ainda não há resumo, mas é a barra que avança.
    else if (estado.passo < passos.findIndex((p) => p.dataset.passo === "servicos")) {
      barra.hidden = false;
      const l = q("[data-barra-linha]");
      const tt = q("[data-barra-total]");
      if (l) l.textContent = "";
      if (tt) tt.textContent = "";
    }
    q("[data-barra-acao]").textContent = "Continuar";
  }

  // Motivo pelo qual o passo atual ainda não permite avançar ("" quando pode).
  function pendencia() {
    switch (passos[estado.passo].dataset.passo) {
      case "pet":
        return !pet.value.trim() || !porte() ? "Informe o nome e o porte do pet." : "";
      case "servicos":
        return servicos().length === 0 ? "Escolha ao menos um serviço." : "";
      case "quando":
        return estado.dia === null || estado.hora === null ? "Escolha o dia e o horário." : "";
      default:
        return "";
    }
  }

  function irPara(i, foco = true) {
    estado.passo = i;
    erro.textContent = "";
    passos.forEach((p, k) => {
      p.hidden = k !== i;
    });
    voltar.hidden = i === 0;
    desenharProfissionais();
    desenharQuando();
    desenharResumo();
    desenharEnvio();
    if (!foco) return;
    const legenda = passos[i].querySelector("legend");
    legenda.focus({ preventScroll: true });
    legenda.scrollIntoView({ block: "start", behavior: reduzMovimento ? "auto" : "smooth" });
  }

  barra.addEventListener("click", () => {
    const motivo = pendencia();
    if (motivo) {
      erro.textContent = motivo;
      return;
    }
    if (estado.passo < passos.length - 1) irPara(estado.passo + 1);
  });
  voltar.addEventListener("click", () => irPara(estado.passo - 1));
  enviar.addEventListener("click", (e) => {
    if (enviar.getAttribute("aria-disabled") === "true") e.preventDefault();
  });

  // Redesenha só o que depende do campo alterado, para não destruir o foco do radio clicado.
  form.addEventListener("change", (e) => {
    const alvo = e.target;
    erro.textContent = "";
    if (alvo.name === "profissional") {
      estado.profissional = alvo.value;
      desenharQuando();
    } else if (alvo.name === "dia") {
      estado.dia = Number(alvo.value);
      desenharHoras(diasDisponiveis());
    } else if (alvo.name === "hora") {
      estado.hora = alvo.value;
    } else if (alvo.name === "servico" || alvo.name === "adicional" || alvo.name === "porte") {
      if (alvo.type === "checkbox" && alvo.checked) {
        avisar("✓ Adicionado: " + alvo.closest("label").querySelector("span").textContent, raiz);
      }
      desenharProfissionais();
      desenharQuando();
    }
    desenharResumo();
    desenharEnvio();
  });
  form.addEventListener("input", (e) => {
    if (e.target === nome || e.target === bairro || e.target === obs || e.target === pet) desenharEnvio();
  });
  form.addEventListener("submit", (e) => e.preventDefault());

  irPara(0, false);
  form.dataset.pronto = "";
}

if (typeof document !== "undefined") iniciar();
