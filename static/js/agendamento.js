// Motor de agendamento: funções puras. Sem efeitos ao importar (nada toca o DOM aqui).
import { formatarBRL } from "./carrinho.js";
import { rotuloDuracao } from "./retorno.js";

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
