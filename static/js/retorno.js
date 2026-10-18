// Retorno visual compartilhado: aviso rápido (toast) e barra de resumo.
// Sem efeitos ao importar: todo o trabalho com o DOM acontece dentro das funções.
let temporizador;

export function avisar(texto, raiz = document) {
  let el = raiz.querySelector("[data-aviso]");
  if (!el) {
    el = raiz.createElement("p");
    el.className = "aviso";
    el.setAttribute("role", "status");
    el.dataset.aviso = "";
    el.hidden = true;
    raiz.body.append(el);
  }
  el.textContent = texto;
  el.hidden = false;
  clearTimeout(temporizador);
  temporizador = setTimeout(() => {
    el.hidden = true;
  }, 2500);
}

export function desenharBarra(barra, { linha, total, etiquetas }) {
  const doc = barra.ownerDocument;
  const q = (s) => barra.querySelector(s);
  const l = q("[data-barra-linha]");
  const t = q("[data-barra-total]");
  const e = q("[data-barra-etiquetas]");
  if (l) l.textContent = linha;
  if (t) t.textContent = total;
  e?.replaceChildren(
    ...etiquetas.map((nome) => {
      const li = doc.createElement("li");
      li.textContent = nome;
      return li;
    })
  );
  barra.hidden = etiquetas.length === 0;
}

export function rotuloDuracao(minutos) {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h === 0) return `${m} min`;
  return m === 0 ? `${h}h` : `${h}h${String(m).padStart(2, "0")}`;
}
