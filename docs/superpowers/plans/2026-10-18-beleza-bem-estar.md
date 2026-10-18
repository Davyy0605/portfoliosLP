# Ramo "Beleza e bem-estar" — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Acrescentar ao portfólio um segundo ramo, com 6 modelos de serviços que terminam num agendamento pelo WhatsApp. O hub passa a ser dividido por ramo, e entram duas correções: o retorno visual do carrinho e o QR cortado.

**Architecture:** O ramo de cada site vem do `site.toml` (`ramo`, que por padrão é `"gastronomia"`). O `render_site` gera `landing` mais `cardapio` (gastronomia) ou `landing` mais `agendar` (beleza). O `render_hub` gera a entrada `/` e uma página `/<ramo>/` para cada ramo; os textos de cada ramo ficam em `config.toml`. O Python valida os dados de agenda e os entrega ao navegador como JSON, já com o dinheiro em centavos. O `agendamento.js` tem funções puras (testadas no Node) e uma função `iniciar()` que liga a página. O aviso e a barra de resumo ficam num só módulo, `retorno.js`, usado pelo carrinho e pelo agendamento.

**Tech Stack:** Python 3.12, Jinja2, TOML (`tomllib`), segno, Pillow, HTML/CSS/JS puros (módulos ES), pytest, Playwright (chromium), `node --test`.

**Spec:** `docs/superpowers/specs/2026-10-18-beleza-bem-estar-design.md`. A spec original é `docs/superpowers/specs/2026-10-16-cardapios-landing-pages-design.md`. Leia as duas.

## Global Constraints

- Nenhuma dependência nova (Python ou npm).
- Os preços no `site.toml` ficam em **reais** (`preco = 45.0`); no JavaScript, o dinheiro é sempre **centavos inteiros**. Converta com `gerador.formatos.centavos`.
- Os modelos existentes continuam com os mesmos endereços (`/<slug>/`, `/<slug>/cardapio/`). Os modelos de beleza ficam em `/<slug>/` e `/<slug>/agendar/`.
- Um `site.toml` sem `ramo` precisa continuar gerando exatamente o que gera hoje, seja de modelo ou de cliente.
- `python build.py --site <slug>` funciona nos dois ramos. Para beleza, gera `/` e `/agendar/`.
- Todo agendamento termina no WhatsApp (`wa.me`). Não existe link externo (Trinks etc.).
- Os dados de cada demo são fictícios. Nada de nome, marca ou foto de negócio real, e as fotos de pessoas não são apresentadas como clientes reais. As fotos vêm de Unsplash/Pexels e são creditadas em `[[fotos]]`.
- Os 6 temas de beleza precisam ser claramente diferentes entre si, e não a mesma estrutura com outra cor. O visual de cada tema é criado com a skill `ui-ux-pro-max:ui-ux-pro-max` e outras skills de design.
- Alvos mínimos de toque: 44×44 px. Mensagens dinâmicas usam `role="status"`. Respeite `prefers-reduced-motion`.
- Lighthouse mobile em `/<slug>/agendar/`: Performance ≥ 90 e Acessibilidade ≥ 95.
- Texto exato do aviso: `✓ Adicionado: <nome>`. Texto exato do aviso de confirmação: `O horário é confirmado pelo <nome do negócio> no WhatsApp.`

## Review Focus

1. **Serviços que não cabem antes de fechar:** um combo de 2 h num dia que fecha às 19h não pode oferecer 18:00. Testado na Tarefa 4 (`horariosDoDia`).
2. **Hoje, depois do horário:** às 18:50, o dia de hoje não oferece horários que já passaram. Se não sobrar nenhum, o dia aparece como sem horário. Testado na Tarefa 4.
3. **Nenhum profissional faz todos os serviços escolhidos:** sobra só "Sem preferência", sem erro. Testado na Tarefa 4 (`profissionaisPara`).
4. **Trocar os serviços depois de escolher profissional ou horário:** a escolha que ficou inválida (profissional que não faz o novo serviço, horário que já não cabe) é limpa e a barra volta ao passo certo. Testado na Tarefa 5 (Playwright).
5. **Site de gastronomia de cliente (`clientes/`) sem `ramo`:** continua gerando `cardapio/` e nunca `agendar/`. Testado na Tarefa 3 e na Tarefa 6.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `gerador/qr.py` | QR em SVG com `viewBox` |
| `static/js/retorno.js` (novo) | aviso rápido e barra de resumo, compartilhados |
| `static/js/carrinho.js` | usa o `retorno.js`; marca o item escolhido |
| `gerador/dados.py` | `ramo`, `[agenda]`, `[[servicos]]`, `[[adicionais]]`, `[[equipe]]`, `[[depoimentos]]`, `[[perguntas]]` |
| `gerador/agenda.py` (novo) | `dados_agendamento(site) -> dict` (JSON da página) |
| `static/js/agendamento.js` (novo) | funções puras de agenda e `iniciar()` |
| `temas/_base/servicos.html` (novo) | macros de beleza: serviços, equipe, depoimentos, perguntas, agendamento |
| `gerador/render.py` | páginas por ramo; hub com entrada e páginas de ramo |
| `temas/hub/index.html`, `temas/hub/ramo.html` (novo), `temas/hub/hub.css` | entrada e listagem por ramo |
| `config.toml` | `[ramos.gastronomia]`, `[ramos.beleza]` |
| `temas/<tema>/{landing,agendar}.html` e `tema.css`, `sites/<slug>/` | 6 modelos |
| `tests/fixtures/beleza/site.toml` (novo) | fixture de beleza usada nos testes |

---

### Task 1: QR code sem corte

**Files:**
- Modify: `gerador/qr.py`
- Modify: `temas/hub/hub.css:67`
- Test: `tests/test_render.py`

**Interfaces:**
- Produces: `qr_svg(url: str) -> str`, com a mesma assinatura. O SVG passa a ter `viewBox` e não tem `width`/`height`.

- [ ] **Step 1: Write the failing test** `test_qr_escala_sem_cortar` em `tests/test_render.py`

```python
def test_qr_escala_sem_cortar():
    from gerador.qr import qr_svg
    svg = qr_svg("https://exemplo.com/bar/cardapio/")
    tag = svg[:svg.index(">")]
    assert 'viewBox="0 0 ' in tag
    assert "width=" not in tag and "height=" not in tag
```

- [ ] **Step 2: Run** `pytest tests/test_render.py::test_qr_escala_sem_cortar -v`. Expected: FAIL (`viewBox` ausente).
- [ ] **Step 3: Implement.** Em `qr_svg`, passe `omitsize=True` para `svg_inline`. Em `hub.css`, `.card-qr svg` passa a ter `aspect-ratio: 1; height: auto;`.
- [ ] **Step 4: Run** `pytest tests/test_render.py -v`. Expected: PASS.
- [ ] **Step 5: Verificação visual.** Rode `python build.py` e `python ferramentas/capturar.py dist capturas/`. Na captura `hub-index-1440.png`, o QR aparece inteiro, com os três quadrados de canto.
- [ ] **Step 6: Commit** `fix: QR do hub escala com viewBox em vez de ser cortado`

---

### Task 2: Aviso rápido e barra de resumo (carrinho)

**Files:**
- Create: `static/js/retorno.js`
- Modify: `static/js/carrinho.js`, `temas/_base/macros.html` (macro `carrinho`), `static/css/base.css`, `temas/hamburgueria/cardapio.html` (remover o `<script>` inline do resumo, linhas 33–53), `temas/hamburgueria/tema.css:419-430` (estilizar a barra no lugar de `.carrinho-abrir`)
- Test: `tests/js/retorno.test.js` (novo), `tests/test_navegador.py`

**Interfaces:**
- Produces (em `static/js/retorno.js`):
  - `avisar(texto: string, raiz: Document = document): void`. Escreve o texto em `[data-aviso]` (um `<p role="status" class="aviso">`, criado no `<body>` se não existir), mostra o elemento e o esconde após 2500 ms. Uma chamada nova reinicia o tempo.
  - `desenharBarra(barra: HTMLElement, { linha: string, total: string, etiquetas: string[] }): void`. Preenche `[data-barra-linha]`, `[data-barra-total]` e `[data-barra-etiquetas]` (um `<li>` por etiqueta, criado com `textContent`). Quando `etiquetas` está vazio, define `barra.hidden = true`.
  - `rotuloDuracao(minutos: number): string`, com o formato `"40 min"`, `"1h"`, `"1h10"`.
- Marcação da barra (na macro `carrinho`, substituindo o botão "Ver pedido"):
  `<button type="button" class="barra-resumo" data-barra data-carrinho-abrir hidden>` contendo `<span data-barra-linha>`, `<strong data-barra-total>` e `<ul data-barra-etiquetas>`.
- `carrinho.js`: depois de `adicionar`, chama `avisar("✓ Adicionado: " + nome)`. A cada `desenhar()`, chama `desenharBarra` com `linha = "<n> item|itens"`, `total = formatarBRL(...)` e `etiquetas = nomes`, e ainda põe `data-escolhido` em cada `button[data-adicionar]` cujo id está no carrinho.

- [ ] **Step 1: Write the failing tests**

`tests/js/retorno.test.js`:
```js
test("rotuloDuracao", () => {
  assert.strictEqual(rotuloDuracao(40), "40 min");
  assert.strictEqual(rotuloDuracao(60), "1h");
  assert.strictEqual(rotuloDuracao(70), "1h10");
  assert.strictEqual(rotuloDuracao(125), "2h05");
});
```

`tests/test_navegador.py`:
```python
def test_carrinho_aviso_e_barra(abrir):
    p = abrir("cardapio/")
    assert p.locator("[data-barra]").is_hidden()
    p.click("button[data-adicionar][data-nome='Gin']")
    assert p.locator("[data-aviso]").inner_text() == "✓ Adicionado: Gin"
    barra = p.locator("[data-barra]")
    assert barra.is_visible()
    assert barra.locator("[data-barra-etiquetas] li").all_inner_texts() == ["Gin"]
    assert "1 item" in barra.locator("[data-barra-linha]").inner_text()
    assert p.locator("button[data-adicionar][data-nome='Gin'][data-escolhido]").count() == 1
    barra.click()
    assert p.locator("dialog[data-carrinho]").is_visible()
```

Ajuste `test_carrinho`: troque `p.click("[data-carrinho-abrir]")` com o carrinho vazio pela verificação de que `[data-barra]` está oculto. Com itens, ele continua abrindo por `[data-carrinho-abrir]`.

- [ ] **Step 2: Run** `npm test` e `pytest tests/test_navegador.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `retorno.js` e as mudanças em `carrinho.js` e na macro. Em `base.css`: a barra fica fixa embaixo (`position: fixed; left/right/bottom: .5rem`), `.aviso` aparece acima da barra, e com `prefers-reduced-motion` não há animação. Em `hamburgueria/tema.css`, dê à `.barra-resumo` o visual que `.carrinho-abrir` tinha, mostrando as etiquetas, e dê `.item-adicionar[data-escolhido]` um estado ✓. Remova o script inline e o `.carrinho-resumo`.
- [ ] **Step 4: Run** `npm test && pytest -v`. Expected: PASS, incluindo `test_tema[hamburgueria]` e `test_sem_rolagem_lateral`.
- [ ] **Step 5: Verificação visual.** Capture `hamburgueria/cardapio/` a 390 px, com 2 itens adicionados. A barra mostra os dois nomes e o total, e não cobre o último item da lista (dê `padding-bottom` ao `main.com-pedido`).
- [ ] **Step 6: Commit** `feat: aviso "adicionado" e barra fixa com resumo no carrinho`

---

### Task 3: Dados de beleza no `site.toml`

**Files:**
- Modify: `gerador/dados.py`
- Create: `gerador/agenda.py`, `tests/fixtures/beleza/site.toml`, `tests/test_agenda.py`
- Modify: `tests/conftest.py` (fixture `site_beleza`: cópia de `fixtures/beleza/site.toml` para `sites/studio-teste/`, com `capa.jpg` e `a.jpg` gerados, como `site_dir`), `tests/test_dados.py`

**Conteúdo da fixture** (os testes seguintes dependem dele): `slug = "studio-teste"`, `tema = "teste"`, `ramo = "beleza"`, `nome = "Studio Teste"`. Funcionamento: `ter`–`sab` com `["09:00-12:00", "13:30-19:00"]`. Serviços: `corte` ("Corte masculino", 40 min, 45.0), `barba` ("Barba completa", 30 min, 35.0) e `luzes` ("Luzes", 120 min, 150.0, `a_partir_de = true`). Adicional: `domicilio` sem preço e com `pede_bairro = true`. Equipe: Rafael (`["corte", "barba"]`), Thiago (`["corte"]`, com funcionamento próprio só `sab`) e Ana (sem `servicos`, ou seja, faz todos). Tem 1 depoimento e 1 pergunta.

**Interfaces:**
- Formato TOML (este é o contrato, use-o na fixture e nos 6 modelos):
```toml
[site]
ramo = "beleza"                     # opcional; padrão "gastronomia"; valores: RAMOS = {"gastronomia", "beleza"}
[capa]
cta = "agendar"                     # CTAS ganha "agendar"
[agenda]
intervalo = 30                      # minutos entre horários; padrão 30; inteiro 5..240
dias = 14                           # dias exibidos a partir de hoje; padrão 14; 1..60
pede_pet = false                    # pet shop: pede nome e porte (P/M/G)
[[agenda.funcionamento]]            # obrigatório (≥1) quando ramo = "beleza"
dias = ["ter", "qua", "qui", "sex"] # subconjunto de DIAS = ["dom","seg","ter","qua","qui","sex","sab"]
periodos = ["09:00-12:00", "13:30-19:00"]  # HH:MM-HH:MM, início < fim, sem sobreposição no mesmo dia
[[servicos]]                        # obrigatório (≥1) quando ramo = "beleza"
id = "corte"                        # RE_ID, único
nome = "Corte masculino"
categoria = "Cabelo"                # opcional; agrupa na landing e no passo 1
descricao = ""
duracao = 40                        # minutos, inteiro > 0
preco = 45.0                        # obrigatório, exceto quando existe porte
a_partir_de = false
porte = { P = 50.0, M = 60.0, G = 80.0 }   # opcional; chaves ⊆ {"P","M","G"}; exige agenda.pede_pet = true
[[adicionais]]
id = "domicilio"
nome = "Atendimento a domicílio"
preco = 50.0                        # opcional; ausente = "a combinar"
pede_bairro = true
[[equipe]]
nome = "Rafael"
especialidade = "Corte e barba"
foto = "rafael.jpg"                 # opcional
servicos = ["corte", "barba"]       # ids existentes; vazio/ausente = faz todos
[[equipe.funcionamento]]            # opcional; mesmo formato de agenda.funcionamento; ausente = horário da casa
[[depoimentos]]
nome = "Ana P."
texto = "..."
servico = "Coloração"               # opcional
[[perguntas]]
pergunta = "..."
resposta = "..."
```
- Produces: `carregar_site(...)` passa a devolver `site["site"]["ramo"]` e as chaves `agenda`, `servicos`, `adicionais`, `equipe`, `depoimentos` e `perguntas`. Elas existem sempre, vazias em gastronomia. Os períodos já vêm convertidos em minutos: `agenda["funcionamento"] = {"ter": [[540, 720], [810, 1140]], ...}` (dias fechados não aparecem), e o mesmo vale para `equipe[i]["funcionamento"]` (ou `None`).
- Produces: `gerador.agenda.dados_agendamento(site: dict) -> dict`, que é o JSON entregue à página:
```python
{"loja": str, "intervalo": int, "dias": int, "pedePet": bool,
 "funcionamento": {dia: [[ini, fim], ...]},
 "servicos": [{"id", "nome", "categoria", "minutos": int, "centavos": int | None,
               "aPartirDe": bool, "porte": {"P": int, ...} | None}],
 "adicionais": [{"id", "nome", "centavos": int | None, "pedeBairro": bool}],
 "equipe": [{"id": "p<n>", "nome", "especialidade", "servicos": [ids], "funcionamento": {...} | None}]}
```
Quando `servicos` da equipe está vazio, ele vira a lista com todos os ids. O id do profissional é `"p1"`, `"p2"`… na ordem do arquivo.

- [ ] **Step 1: Write the failing tests** em `tests/test_dados.py` (use `editar` e `site_beleza`, como os testes atuais):
  - `test_ramo_padrao_gastronomia`: a fixture `completo` dá `ramo == "gastronomia"` e `servicos == []`.
  - `test_beleza_carrega`: na fixture `beleza`, `agenda["funcionamento"]["ter"] == [[540, 720], [810, 1140]]` e `"dom" not in agenda["funcionamento"]`.
  - `test_beleza_erros`: parametrize com pares (troca no TOML → trecho da mensagem):
    `periodos = ["19:00-09:00"]` → `"periodos[0]"`; `dias = ["segunda"]` → `"dias"`; `ramo = "padaria"` → `"site.ramo"`; um serviço com id repetido → `"repetido"`; `servicos = ["inexistente"]` na equipe → `"equipe[0].servicos"`; serviço sem `preco` e sem `porte` → `"preco"`; `porte` com `pede_pet = false` → `"porte"`; `ramo = "beleza"` sem `[[servicos]]` → `"servicos"`; `09:00-12:00` e `11:00-13:00` no mesmo dia → `"sobrep"`.
  - `test_dados_agendamento` em `tests/test_agenda.py`: `centavos` de `45.0` é `4500`; o adicional sem preço tem `centavos is None`; o profissional sem `servicos` recebe todos os ids; o JSON passa por `json.dumps` sem erro.
- [ ] **Step 2: Run** `pytest tests/test_dados.py tests/test_agenda.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** em `dados.py`, reaproveitando o validador `_V` e seu formato de mensagem `<arquivo>: <campo>: <problema>`. Crie um helper privado `_funcionamento(v, lista, caminho) -> dict[str, list[list[int]]]`, usado pela casa e pela equipe. Os campos novos são validados nos dois ramos (todos opcionais), e a obrigatoriedade de `servicos` e `agenda.funcionamento` vale só para `beleza`. Implemente `gerador/agenda.py`.
- [ ] **Step 4: Run** `pytest -v`. Expected: PASS. Os sites existentes carregam sem mudança.
- [ ] **Step 5: Commit** `feat: dados de serviços, equipe e agenda no site.toml (ramo beleza)`

---

### Task 4: Motor de agendamento (funções puras)

**Files:**
- Create: `static/js/agendamento.js` (só as funções exportadas por enquanto)
- Test: `tests/js/agendamento.test.js`

**Interfaces:**
- Consumes: o formato JSON de `dados_agendamento` (Tarefa 3) e `formatarBRL` de `carrinho.js`, `rotuloDuracao` de `retorno.js`.
- Produces (exportadas de `agendamento.js`):
  - `horariosDoDia(periodos: number[][], duracao: number, intervalo: number, agoraMin: number | null) -> string[]`. Os candidatos começam no início de cada período e avançam de `intervalo` em `intervalo`. Um horário `s` vale quando `s + duracao <= fim` do mesmo período e, se `agoraMin` não é `null`, quando `s > agoraMin`. Devolve no formato `"HH:MM"`.
  - `diasDaAgenda(funcionamento: object, hoje: Date, n: number) -> {data: Date, chave: string, periodos: number[][]}[]`. Devolve `n` dias corridos a partir de hoje. `chave` é um de `DIAS`, e `periodos` fica `[]` quando o dia está fechado.
  - `profissionaisPara(equipe: object[], ids: string[]) -> object[]`. Devolve quem tem todos os `ids` em `servicos`.
  - `totais(servicos: object[], adicionais: object[], porte: string | null) -> {centavos: number, minutos: number, aPartirDe: boolean, aCombinar: string[]}`. Com porte, usa `servico.porte[porte]` e, se faltar, `servico.centavos`. Adicionais sem `centavos` não somam e entram em `aCombinar` pelo nome.
  - `mensagemAgendamento(e: {loja, servicos, adicionais, porte, pet, profissional, data: Date, hora, nome, bairro, obs}) -> string`, no formato exato:
```
Olá! Quero agendar pela página da <loja>.

• <serviço> (R$ 45,00)            ← "(a partir de R$ X)" se aPartirDe; "(R$ X, porte M)" com porte
• <adicional> (R$ 50,00)          ← "(a combinar)" sem preço

Pet: <pet> (porte <P|M|G>)        ← só com pedePet
Profissional: <nome | sem preferência>
Dia: <terça>, <21/10> às <14:00>
Bairro: <bairro>                  ← só se algum adicional pede bairro
Duração: <1h10> · Total: <R$ 80,00>   ← "a partir de R$ X" se algum aPartirDe; " + a combinar" se aCombinar
Nome: <nome>
Obs.: <obs>                       ← só se obs não vazio (trim)
```
  Os dias da semana em `Dia:` vêm por extenso e em minúsculas: domingo, segunda, terça, quarta, quinta, sexta, sábado.

- [ ] **Step 1: Write the failing tests** `tests/js/agendamento.test.js`:
```js
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
test("mensagem exata", () => { /* caso do esboço: Navalha & Co., Corte 4500 + Barba 3500,
  sem preferência, terça 21/10/2026 14:00, nome "Lucas" → string exata do formato acima */ });
test("mensagem com pet, bairro, a partir de e obs", () => { /* checa as linhas Pet:, Bairro:, "a partir de", Obs. */ });
```
  Os dois últimos testes trazem a string completa esperada, montada a partir do formato acima.
- [ ] **Step 2: Run** `npm test`. Expected: FAIL (módulo inexistente).
- [ ] **Step 3: Implement** as funções. Garanta que o módulo não toca no DOM ao ser importado no Node (`iniciar` só roda com `typeof document !== "undefined"`, como em `carrinho.js`).
- [ ] **Step 4: Run** `npm test`. Expected: PASS.
- [ ] **Step 5: Commit** `feat: motor de agendamento (horários, profissionais, totais, mensagem)`

---

### Task 5: Páginas de beleza (render + macros + fluxo no navegador)

**Files:**
- Modify: `gerador/render.py` (`render_site`), `temas/_base/macros.html` (`cta` ganha `"agendar"`), `temas/_base/pagina.html` (título ` · Agendar`)
- Create: `temas/_base/servicos.html`, `temas/teste/agendar.html`
- Modify: `temas/teste/landing.html` (incluir os blocos de beleza quando `site.site.ramo == "beleza"`), `static/js/agendamento.js` (`iniciar`), `static/css/base.css`
- Test: `tests/test_render.py`, `tests/test_navegador.py`

**Interfaces:**
- Consumes: `dados_agendamento` (Tarefa 3), as funções da Tarefa 4, `avisar`/`desenharBarra` (Tarefa 2).
- `render_site`: as páginas passam a depender do ramo. Defina `PAGINAS = {"gastronomia": "cardapio", "beleza": "agendar"}` em `render.py`. A segunda página é renderizada a partir de `<tema>/<pagina>.html` em `destino/<pagina>/`. Passe `agenda=dados_agendamento(site)` ao contexto quando o ramo for beleza.
- Macros em `temas/_base/servicos.html` (importe com `{% import "_base/servicos.html" as b with context %}`). Elas só montam a estrutura e as marcações `data-*`; o visual fica no `tema.css`.
  - `servicos(site)`: lista por `categoria`, um `<li data-servico>` por serviço, com nome, duração (`rotulo` igual a `rotuloDuracao`; crie o filtro Jinja `duracao` em `gerador/formatos.py` e registre em `criar_ambiente`) e preço (`a partir de` / faixa por porte "R$ 50,00 a R$ 80,00").
  - `equipe(site, imagens)`: `<li data-profissional>` com foto (via `m.imagem`), nome e especialidade.
  - `depoimentos(site)` e `perguntas(site)` (`<details>`/`<summary>`).
  - `agendamento(site, agenda, wa_numero)`: o formulário em 4 passos (5 com `pedePet`, em que o primeiro é o pet) dentro de `<form data-agendamento data-whatsapp="{{ wa_numero }}">` (o mesmo padrão de `data-whatsapp` do carrinho). Cada passo é um `<fieldset data-passo="servicos|profissional|quando|dados">`, com `<legend>`. O JSON vai em `<script type="application/json" data-agenda-dados>{{ agenda|tojson }}</script>`. A barra usa a mesma marcação `data-barra` da Tarefa 2 e, aqui, avança o passo. O aviso de confirmação usa o texto exato das Global Constraints. O botão final é `<a data-agendar-enviar>` "Agendar pelo WhatsApp", com `aria-disabled` até haver serviço, dia/hora e nome.
- `iniciar(raiz)` em `agendamento.js`:
  - mostra um passo por vez e permite voltar;
  - serviços são checkboxes `input[data-servico-id]`, e cada marcação chama `avisar("✓ Adicionado: " + nome)`;
  - profissionais são radios (`value=""` para "Sem preferência", sempre presente);
  - dias e horários são radios gerados no JS a partir de `diasDaAgenda` e `horariosDoDia`, com a duração total de `totais`, a agenda do profissional ou da casa e `agoraMin` só para hoje; dias sem horário ficam `disabled`;
  - ao mudar serviços ou profissional, limpa a escolha que ficou inválida;
  - o `href` final vem de `linkPedido(whatsapp, mensagemAgendamento(...))`.

- [ ] **Step 1: Write the failing tests**
  - `tests/test_render.py::test_render_beleza(raiz_beleza)`: gera `index.html` e `agendar/index.html`, sem `cardapio/`. A landing tem `href="agendar/"`, `data-servico` (tantos quantos na fixture) e `data-profissional`. A página `agendar` tem `data-agendamento`, e o JSON de `[data-agenda-dados]` faz `json.loads` e tem `servicos[0]["centavos"] == 4500`. (Crie a fixture `raiz_beleza` em `conftest.py`, como `raiz`, mas usando `site_beleza`.)
  - `tests/test_render.py::test_gastronomia_sem_agendar(raiz)`: `out/agendar` não existe e `out/cardapio/index.html` existe.
  - `tests/test_navegador.py` (crie a fixture `abrir_beleza`, como `abrir`):
```python
def test_agendamento_fluxo_completo(abrir_beleza):
    p = abrir_beleza("agendar/")
    p.check("input[data-servico-id='corte']")
    assert p.locator("[data-aviso]").inner_text() == "✓ Adicionado: Corte masculino"
    p.check("input[data-servico-id='barba']")
    assert p.locator("[data-barra-etiquetas] li").all_inner_texts() == ["Corte masculino", "Barba completa"]
    p.click("[data-barra]")                          # → profissional
    assert p.locator("[data-passo='profissional'] input[type=radio]").count() == 3  # sem preferência, Rafael, Ana
    p.check("[data-passo='profissional'] input[value='']")
    p.click("[data-barra]")                          # → quando
    p.locator("[data-passo='quando'] input[name=dia]:not([disabled])").first.check()
    p.locator("[data-passo='quando'] input[name=hora]").first.check()
    p.click("[data-barra]")                          # → dados
    p.fill("input[name=nome]", "Lucas")
    msg = urllib.parse.unquote(p.locator("a[data-agendar-enviar]").get_attribute("href").split("?text=", 1)[1])
    assert "• Corte masculino (R$ 45,00)" in msg and "Profissional: sem preferência" in msg and "Nome: Lucas" in msg

def test_agendamento_troca_servico_limpa_profissional(abrir_beleza):
    # marca só corte, escolhe Thiago, volta ao passo de serviços, marca barba, avança →
    # o radio de Thiago não existe mais e o de "Sem preferência" (value="") está marcado

def test_agendamento_envio_bloqueado_sem_nome(abrir_beleza):
    # completa até o passo de dados sem nome → a[data-agendar-enviar] tem aria-disabled="true" e não tem href
```
- [ ] **Step 2: Run** `pytest tests/test_render.py tests/test_navegador.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** render, macros, `temas/teste/agendar.html` (mínimo, como o `cardapio.html` de teste) e `iniciar`.
- [ ] **Step 4: Run** `npm test && pytest -v`. Expected: PASS.
- [ ] **Step 5: Commit** `feat: páginas de beleza com agendamento em passos via WhatsApp`

---

### Task 6: Hub dividido por ramo

**Files:**
- Modify: `config.toml`, `gerador/dados.py` (`carregar_config` lê `[ramos.*]`), `gerador/render.py` (`render_hub`), `temas/hub/index.html` (vira a entrada), `temas/hub/hub.css`, `build.py` (`construir_cliente` sem mudança de comportamento; `construir_portfolio` passa o `url_base`), `README.md` (nova seção "Criar um cliente de beleza", com `ramo`, `[agenda]`, `[[servicos]]` e `[[equipe]]`, e a saída `dist/<ramo>/`)
- Create: `temas/hub/ramo.html`
- Test: `tests/test_render.py`, `tests/test_build.py`, `tests/test_temas.py`

**Interfaces:**
- `config.toml`:
```toml
[ramos.gastronomia]
nome = "Bares e restaurantes"
resumo = "Cardápio digital com QR na mesa"
titulo = "Cardápios digitais e sites para bares e restaurantes."
mensagem = "Olá, Davy! Vi o portfólio e quero um site para o meu estabelecimento."
[ramos.beleza]
nome = "Beleza e bem-estar"
resumo = "Agendamento online pelo WhatsApp"
titulo = "<texto final do builder>"
mensagem = "Olá, Davy! Vi o portfólio e quero um site com agendamento para o meu negócio."
```
  `carregar_config` devolve `config["ramos"]`: um dict na ordem do arquivo, cada valor com as 4 chaves de texto obrigatórias. Sem `[ramos]`, o padrão é só `gastronomia`, com os textos atuais do hub (assim configs antigas continuam funcionando).
- `render_hub(env, sites, config, destino, cache=None)`, com a mesma assinatura:
  - em `destino/index.html` (entrada), um cartão por ramo que tem sites, em `<a class="ramo" href="<ramo>/">`, com nome, resumo, número de modelos e a capa do primeiro site do ramo;
  - em `destino/<ramo>/index.html`, os cards atuais do hub, com `url = "../<slug>/"` e `url_secundaria = "../<slug>/<cardapio|agendar>/"` (rótulos "Ver cardápio" ou "Agendar"), o QR apontando para `url_base + slug + "/<cardapio|agendar>/"` e as imagens em `../img/<slug>/...`, com um link de volta para `../`;
  - um site cujo `ramo` não está em `config["ramos"]` gera `ErroDeDados("<slug>: ramo '<x>' sem textos em config.toml [ramos]")`.
- O nome `gastronomia`/`beleza` não pode ser usado como slug: acrescente ambos a `SLUGS_RESERVADOS`.

- [ ] **Step 1: Write the failing tests**
  - `test_render.py::test_hub_por_ramo(raiz, site_beleza)`: renderize o hub com `completo` + `beleza`. A entrada tem `href="gastronomia/"` e `href="beleza/"`. `gastronomia/index.html` tem o card "Casa Completa", com `href="../completo/"` e um QR com `viewBox`. `beleza/index.html` tem `href="../studio-teste/agendar/"` e um QR com `viewBox`. Nenhum card de beleza aparece em `gastronomia/`.
  - `test_render.py::test_hub_ramo_sem_texto`: com `ramo = "beleza"` e um config sem `[ramos.beleza]`, levanta `ErroDeDados` com `"ramos"` na mensagem.
  - `test_dados.py::test_slug_reservado_ramo`: uma pasta `sites/beleza` com `slug = "beleza"` gera erro de `site.slug`.
  - `test_build.py::test_cliente_beleza`: `construir_cliente(raiz_beleza, "studio-teste", saida)` gera `saida/index.html` e `saida/agendar/index.html`, e não gera `saida/gastronomia`.
  - `test_temas.py`: `test_hub` passa a ler `dist/gastronomia/index.html` e `dist/beleza/index.html`, e os cards de cada ramo batem com `SITES` filtrados por ramo. `test_tema` usa a segunda página por ramo (as asserções de beleza: `href` para `agendar/`, ≥ 4 `data-servico`, `data-agendamento` na página `agendar`, `id="contato"`). `test_sem_rolagem_lateral` percorre `""`, `"gastronomia/"`, `"beleza/"` e as duas páginas de cada site.
- [ ] **Step 2: Run** `pytest -v`. Expected: FAIL.
- [ ] **Step 3: Implement.** A entrada (`hub/index.html`) mantém o topo, o WhatsApp e o rodapé atuais, com o título "Sites que trazem clientes para o seu negócio." (texto final a critério do builder). `ramo.html` é o miolo atual do hub (abertura, grade, "como funciona", contato), lendo os textos de `config.ramos[ramo]`, e o "como funciona" de beleza fala em agenda e não em QR da mesa. Use as skills de design para a entrada, mantendo a marca Davy (roxo, Instrument Sans) do `hub.css`.
- [ ] **Step 4: Run** `npm test && pytest -v`. Expected: PASS.
- [ ] **Step 5: Verificação visual.** Rode `python build.py` e capture `/`, `/gastronomia/` e `/beleza/` a 390 e 1440 px.
- [ ] **Step 6: Commit** `feat: hub com entrada geral e página por ramo`

---

### Tasks 7–12: Os seis modelos de beleza

Cada modelo é uma tarefa, com o mesmo roteiro. A ordem sugerida é **barbearia → salão → manicure → maquiagem → estética → pet shop**. A barbearia é a mais próxima do esboço aprovado, e o pet shop é o único com `pede_pet`.

| # | slug / tema | Direção visual (spec §2.2) | Dados obrigatórios no `site.toml` |
|---|---|---|---|
| 7 | `barbearia` | escura e clássica, couro, latão, tipografia forte | ≥ 6 serviços com combo corte + barba; 3 profissionais com especialidades diferentes, sendo pelo menos 1 sem `servicos` = todos e 1 com folga própria (`[[equipe.funcionamento]]`) |
| 8 | `salao` | sofisticado e luminoso, editorial | ≥ 3 serviços com `a_partir_de = true` (coloração, escova progressiva…); pausa de almoço em `periodos` |
| 9 | `manicure` | delicado e moderno, pastel/nude, galeria em destaque | galeria ≥ 8 fotos; serviço de manutenção de alongamento |
| 10 | `maquiagem` | glamour, contraste, retratos grandes | adicional `domicilio` com `preco` e `pede_bairro = true`; bloco de noivas e eventos na landing |
| 11 | `estetica` | clara, calma, quase clínica, muito respiro | pacotes como serviços ("Drenagem — pacote 10 sessões"); `[[perguntas]]` ≥ 4 |
| 12 | `petshop` | alegre e colorido, arredondado, sem cara infantil | `pede_pet = true`; serviços com `porte`; adicional `taxi-dog` **sem preço** (mostra "a combinar") |

Todos: `ramo = "beleza"`, `capa.cta = "agendar"`, `[[depoimentos]]` ≥ 3, `[[fotos]]` com créditos, `ordem` de 1 a 6, `cor`, e nome e marca fictícios (verifique numa busca que o nome não é de um negócio conhecido).

**Files (por modelo):**
- Create: `sites/<slug>/site.toml`, `sites/<slug>/imagens/*` (baixadas com `python ferramentas/baixar_fotos.py sites/<slug>`), `temas/<slug>/landing.html`, `temas/<slug>/agendar.html`, `temas/<slug>/tema.css`

**Interfaces:**
- Consumes: as macros de `temas/_base/macros.html` (`imagem`, `horarios`, `contato`, `rodape`, `cta`) e de `temas/_base/servicos.html` (Tarefa 5). As duas páginas estendem `_base/pagina.html`. O `agendar.html` chama `b.agendamento(site, agenda, wa_numero)`.

- [ ] **Step 1: Direção de design.** Invoque `ui-ux-pro-max:ui-ux-pro-max` para o segmento e, se ajudar, `design-taste-frontend` ou `high-end-visual-design`. Registre em comentário no topo do `tema.css` a paleta, as fontes (Google Fonts, no máximo 2 famílias) e a composição da capa. Compare com os modelos de beleza já prontos: a capa e a ordem dos blocos precisam ser diferentes.
- [ ] **Step 2: Dados.** Escreva o `site.toml`, rode `baixar_fotos.py` e verifique com `python -c "from gerador.dados import carregar_site; carregar_site(__import__('pathlib').Path('sites/<slug>'))"` (sem erro).
- [ ] **Step 3: Run** `pytest tests/test_temas.py -v -k <slug>`. Expected: SKIP, porque o tema ainda não existe.
- [ ] **Step 4: Implement** `landing.html`, `agendar.html` e `tema.css`. Na landing, "Agendar horário" fica visível sem rolar a 390×844. A barra e o aviso seguem o visual do tema.
- [ ] **Step 5: Run** `pytest tests/test_temas.py -v`. Expected: PASS em `test_tema[<slug>]`, `test_hub` e `test_sem_rolagem_lateral`.
- [ ] **Step 6: Verificação visual e de fluxo.** Rode `python build.py` e `python ferramentas/capturar.py dist capturas/`, e confira a landing e o `agendar` a 390 e 1440 px. Faça o fluxo completo à mão em `python build.py --serve`, até a mensagem do WhatsApp (sem enviar).
- [ ] **Step 7: Commit** `feat: modelo <segmento> (<nome fictício>)`

---

### Task 13: Verificação final

**Files:** nenhum arquivo novo. Corrija o que aparecer.

- [ ] **Step 1: Run** `npm test && pytest -v`. Expected: tudo PASS, sem SKIP de tema.
- [ ] **Step 2: Lighthouse.** Com `python build.py --serve`, rode `npx lighthouse http://localhost:8000/<slug>/agendar/ --form-factor=mobile --only-categories=performance,accessibility --quiet --chrome-flags="--headless"` para os 6 slugs. Expected: Performance ≥ 90 e Acessibilidade ≥ 95. Se o `npx` não estiver disponível, use o painel Lighthouse do Chrome e anote os números no commit.
- [ ] **Step 3: Regressão.** Abra `/hamburgueria/cardapio/`, `/bar/` e um QR do hub (`/gastronomia/`) com a câmera do celular, na tela do computador. O QR é lido e abre a página certa.
- [ ] **Step 4: Commit** (se houve correções) `fix: ajustes da verificação final do ramo beleza`
