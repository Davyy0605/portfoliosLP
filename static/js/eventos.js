const iso = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export function resolverData({ data, emDias }, hoje) {
  if (data) return data;
  if (emDias == null || emDias === "" || !Number.isFinite(Number(emDias))) return null;
  // new Date(a, m, d + n) normaliza o mês e evita cair no fuso UTC
  return iso(new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + Number(emDias)));
}

// AAAA-MM-DD compara certo como texto
export function visivel(dataISO, hoje) {
  return Boolean(dataISO) && dataISO >= iso(hoje);
}

export function formatarData(dataISO) {
  const [a, m, d] = dataISO.split("-").map(Number);
  return new Intl.DateTimeFormat("pt-BR", { weekday: "short", day: "numeric", month: "short" }).format(
    new Date(a, m - 1, d)
  );
}

export function iniciar(raiz = document, hoje = new Date()) {
  let restantes = 0;
  for (const el of raiz.querySelectorAll("[data-evento]")) {
    const d = resolverData({ data: el.dataset.data, emDias: el.dataset.emDias }, hoje);
    if (!visivel(d, hoje)) {
      el.hidden = true;
      continue;
    }
    restantes++;
    const alvo = el.querySelector("[data-evento-data]");
    if (alvo) alvo.textContent = formatarData(d);
  }
  const vazio = raiz.querySelector("[data-eventos-vazio]");
  if (vazio) vazio.hidden = restantes > 0;
}

if (typeof document !== "undefined") iniciar();
