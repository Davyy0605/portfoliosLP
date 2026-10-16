export function normalizar(t) {
  return String(t ?? "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}

export function corresponde(item, termo) {
  const t = normalizar(termo).trim();
  if (!t) return true;
  return normalizar(`${item.nome} ${item.descricao ?? ""}`).includes(t);
}

export function iniciar(raiz = document) {
  const campo = raiz.querySelector("input[data-busca]");
  const itens = [...raiz.querySelectorAll("[data-item]")];
  const categorias = [...raiz.querySelectorAll("section[data-categoria]")];
  const aviso = raiz.querySelector("[data-sem-resultado]");
  const abas = [...raiz.querySelectorAll("nav[data-abas] a[href^='#']")];

  const filtrar = () => {
    const termo = campo ? campo.value : "";
    let total = 0;
    for (const el of itens) {
      const ok = corresponde({ nome: el.dataset.nome, descricao: el.dataset.descricao }, termo);
      el.hidden = !ok;
      if (ok) total++;
    }
    const idsVisiveis = new Set();
    for (const cat of categorias) {
      const vazia = !cat.querySelector("[data-item]:not([hidden])");
      cat.hidden = vazia;
      if (!vazia) idsVisiveis.add(cat.id);
    }
    // a aba some junto com a categoria vazia
    for (const a of abas) a.hidden = !idsVisiveis.has(a.getAttribute("href").slice(1));
    if (aviso) aviso.hidden = total > 0;
  };
  if (campo) campo.addEventListener("input", filtrar);
  filtrar();

  if (typeof IntersectionObserver === "undefined" || !abas.length) return;
  const ativar = (id) => {
    for (const a of abas) {
      if (a.getAttribute("href") === `#${id}`) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    }
  };
  const obs = new IntersectionObserver(
    (entradas) => {
      for (const e of entradas) if (e.isIntersecting) ativar(e.target.id);
    },
    { rootMargin: "-20% 0px -70% 0px" }
  );
  categorias.forEach((c) => obs.observe(c));
}

if (typeof document !== "undefined") iniciar();
