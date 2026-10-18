import { avisar, prepararAviso, desenharBarra } from "./retorno.js";

// Dinheiro sempre em centavos inteiros; sem ponto flutuante.
export function formatarBRL(centavos) {
  const reais = String(Math.trunc(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${reais},${String(centavos % 100).padStart(2, "0")}`;
}

export function linkPedido(numero, mensagem) {
  return `https://wa.me/${numero}?text=${encodeURIComponent(mensagem)}`;
}

export class Carrinho {
  #mapa = new Map();

  constructor(salvos = []) {
    for (const i of Array.isArray(salvos) ? salvos : []) {
      if (i && i.id && Number.isInteger(i.centavos) && Number.isInteger(i.qtd) && i.qtd > 0) {
        this.#mapa.set(String(i.id), { id: String(i.id), nome: String(i.nome), centavos: i.centavos, qtd: i.qtd });
      }
    }
  }

  adicionar(id, nome, centavos) {
    const i = this.#mapa.get(id);
    if (i) i.qtd++;
    else this.#mapa.set(id, { id, nome, centavos, qtd: 1 });
  }

  alterar(id, qtd) {
    const i = this.#mapa.get(id);
    if (!i) return;
    if (qtd <= 0) this.#mapa.delete(id);
    else i.qtd = qtd;
  }

  itens() {
    return [...this.#mapa.values()].map((i) => ({ ...i }));
  }

  totalCentavos() {
    return this.itens().reduce((s, i) => s + i.centavos * i.qtd, 0);
  }

  quantidade() {
    return this.itens().reduce((s, i) => s + i.qtd, 0);
  }

  mensagem(nomeLoja, observacao) {
    const linhas = this.itens().map((i) => `${i.qtd}x ${i.nome} — ${formatarBRL(i.centavos * i.qtd)}`);
    let m = `Olá! Pedido pelo cardápio digital — ${nomeLoja}\n\n${linhas.join("\n")}\n\nTotal: ${formatarBRL(this.totalCentavos())}`;
    const obs = (observacao ?? "").trim();
    if (obs) m += `\nObs.: ${obs}`;
    return m;
  }
}

export function iniciar(raiz = document) {
  prepararAviso(raiz);
  const painel = raiz.querySelector("[data-carrinho]");
  if (!painel) return;
  const { whatsapp = "", loja = "" } = painel.dataset;
  const chave = `carrinho:${loja}`;
  const q = (s) => painel.querySelector(s);
  const lista = q("[data-carrinho-lista]");
  const total = q("[data-carrinho-total]");
  const qtdEl = q("[data-carrinho-qtd]");
  const obs = q("textarea[data-carrinho-obs]");
  const enviar = q("a[data-carrinho-enviar]");
  const abrir = raiz.querySelector("[data-carrinho-abrir]");
  const barra = raiz.querySelector("[data-barra]");

  let salvos = [];
  try {
    salvos = JSON.parse(sessionStorage.getItem(chave) ?? "[]");
  } catch {}
  const carrinho = new Carrinho(salvos);

  // região viva discreta: anuncia quantidade e total após cada mudança
  let viva = q("[data-carrinho-viva]");
  if (!viva) {
    viva = document.createElement("p");
    viva.setAttribute("role", "status");
    viva.className = "sr-only";
    viva.dataset.carrinhoViva = "";
    painel.append(viva);
  }

  const desenhar = () => {
    try {
      sessionStorage.setItem(chave, JSON.stringify(carrinho.itens()));
    } catch {}
    // o replaceChildren destrói o botão apertado: guardamos qual era para devolver o foco
    const ativo = lista && lista.contains(document.activeElement) ? document.activeElement : null;
    const pedido = ativo && { id: ativo.dataset.id, acao: ativo.dataset.acao };
    const posicao = ativo ? [...lista.children].indexOf(ativo.closest("li")) : -1;
    lista?.replaceChildren(
      ...carrinho.itens().map((i) => {
        const li = document.createElement("li");
        const nome = document.createElement("span");
        nome.textContent = `${i.nome} — ${formatarBRL(i.centavos * i.qtd)}`;
        const botao = (rotulo, delta, simbolo, acao) => {
          const b = document.createElement("button");
          b.type = "button";
          b.textContent = simbolo;
          b.dataset.id = i.id;
          b.dataset.acao = acao;
          b.setAttribute("aria-label", `${rotulo} quantidade de ${i.nome}`);
          b.addEventListener("click", () => {
            carrinho.alterar(i.id, i.qtd + delta);
            desenhar();
          });
          return b;
        };
        const n = document.createElement("span");
        n.textContent = String(i.qtd);
        li.append(nome, botao("Diminuir", -1, "−", "menos"), n, botao("Aumentar", 1, "+", "mais"));
        return li;
      })
    );
    if (pedido) {
      const igual = [...lista.querySelectorAll("button")].find(
        (b) => b.dataset.id === pedido.id && b.dataset.acao === pedido.acao
      );
      const linha = lista.children[Math.min(posicao, lista.children.length - 1)];
      // item removido: foco vai para a linha vizinha; sem linhas, para a observação
      const alvo = igual ?? linha?.querySelector("button") ?? obs ?? painel;
      if (alvo === painel) painel.tabIndex = -1;
      alvo.focus();
    }
    const n = carrinho.quantidade();
    const totalTxt = formatarBRL(carrinho.totalCentavos());
    if (total) total.textContent = totalTxt;
    if (qtdEl) qtdEl.textContent = String(n);
    const linha = `${n} ${n === 1 ? "item" : "itens"}`;
    viva.textContent = `${linha}, total ${totalTxt}`;
    const itens = carrinho.itens();
    if (barra) desenharBarra(barra, { linha, total: totalTxt, etiquetas: itens.map((i) => i.nome) });
    const ids = new Set(itens.map((i) => i.id));
    for (const b of raiz.querySelectorAll("button[data-adicionar]")) b.toggleAttribute("data-escolhido", ids.has(b.dataset.id));
    if (!enviar) return;
    if (n === 0) {
      enviar.removeAttribute("href");
      enviar.setAttribute("aria-disabled", "true");
    } else {
      enviar.href = linkPedido(whatsapp, carrinho.mensagem(loja, obs ? obs.value : ""));
      enviar.removeAttribute("aria-disabled");
    }
  };

  enviar?.addEventListener("click", (e) => {
    if (enviar.getAttribute("aria-disabled") === "true") e.preventDefault();
  });
  if (obs) obs.addEventListener("input", desenhar);

  for (const b of raiz.querySelectorAll("button[data-adicionar]")) {
    b.addEventListener("click", () => {
      const centavos = Number(b.dataset.centavos);
      if (!b.dataset.id || !Number.isInteger(centavos) || centavos < 0) return; // dado inválido no botão
      carrinho.adicionar(b.dataset.id, b.dataset.nome, centavos);
      desenhar();
      avisar("✓ Adicionado: " + b.dataset.nome, raiz);
    });
  }

  // <dialog>: showModal já prende o foco e fecha com Esc; devolvemos o foco ao botão
  const dialogo = painel.matches("dialog") ? painel : painel.closest("dialog");
  if (abrir && dialogo && typeof dialogo.showModal === "function") {
    abrir.addEventListener("click", () => dialogo.showModal());
    dialogo.addEventListener("close", () => abrir.focus());
  }
  desenhar();
}

if (typeof document !== "undefined") iniciar();
