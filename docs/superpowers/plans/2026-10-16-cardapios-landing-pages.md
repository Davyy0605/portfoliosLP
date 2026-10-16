# Portfólio de Cardápios e Landing Pages: plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** construir um gerador em Python que transforma um arquivo `site.toml` por estabelecimento em landing page + cardápio digital estáticos. O resultado é o portfólio "Davy", com seis demos (bar, restaurante, hamburgueria, cafeteria, fino, bistrô), e o mesmo gerador publica clientes reais.

**Arquitetura:** o `build.py` lê `config.toml` e os `site.toml`, valida os dados, otimiza imagens (WebP) e renderiza templates Jinja2. Cada segmento tem um tema próprio em `temas/<slug>/`. Todos os temas usam macros compartilhadas de `temas/_base/` e três módulos JS sem framework: cardápio, eventos e carrinho. A saída é estática, em `dist/`, publicada na Netlify.

**Stack:** Python ≥ 3.11 (`tomllib`), Jinja2, Pillow, segno; pytest; HTML/CSS/JS puros (ES modules), testados com `node --test`; Playwright (só em desenvolvimento, para capturas de tela).

**Spec:** `docs/superpowers/specs/2026-10-16-cardapios-landing-pages-design.md`

## Restrições globais

- Python é obrigatório: o gerador e as ferramentas são em Python. Versão mínima 3.11, porque o projeto usa `tomllib`.
- Front-end em HTML, CSS e JS puros, sem framework de front-end e sem etapa de bundler.
- Dependências de runtime: apenas `jinja2`, `Pillow` e `segno`. Dependências de desenvolvimento: `pytest` e `playwright`.
- Um arquivo de dados por estabelecimento: `sites/<slug>/site.toml` (demos) ou `clientes/<slug>/site.toml` (clientes). Trocar um preço nunca exige editar HTML.
- Saída do portfólio: `dist/index.html` (hub), `dist/<slug>/index.html` (landing), `dist/<slug>/cardapio/index.html` (cardápio).
- Saída de um cliente (`--site <slug>`): landing em `/`, cardápio em `/cardapio/`, sem hub.
- Marca do hub: nome **"Davy"**, detalhes em **roxo** (`#7C3AED`), definidos em `config.toml`.
- Todos os botões de WhatsApp das demos usam `config.toml → whatsapp`. Enquanto ele for o provisório `5500000000000`, o build imprime um aviso, mas não falha.
- Eventos aceitam `data = AAAA-MM-DD` **ou** `em_dias = N` (exatamente um dos dois). Eventos já passados ficam ocultos. Se não sobrar nenhum, aparece `eventos.vazio_mensagem`.
- O módulo `eventos` fica ligado nas demos de bar, fino e bistrô. O módulo `pedido` (carrinho → WhatsApp) fica ligado na hamburgueria. Os dois estão disponíveis para qualquer site via `site.modulos`.
- Estabelecimentos fictícios: nada de nomes, marcas ou fotos de lugares reais. Fotos vêm da Unsplash/Pexels, com crédito.
- Metas: Lighthouse mobile com Performance ≥ 90 e Acessibilidade ≥ 95 em cada cardápio. Os seis temas precisam ser visualmente distintos (layout, tipografia e paleta), não só trocas de cor.
- Fora do escopo: painel administrativo, pagamento, iFood, multi-idioma, sistema de reservas.
- Textos visíveis em português do Brasil. Preços em formato `R$ 42,90`.

## Pontos de revisão

1. **`site.toml` editado à mão com erro** (campo ausente, preço como texto, imagem inexistente, evento com `data` e `em_dias` ao mesmo tempo): o build deve parar com uma mensagem que cite o arquivo e o caminho do campo, nunca com um traceback. Teste em: Task 1.
2. **Carrinho com centavos e textos especiais** (`0,10 + 0,20`, nomes com acento, `&`, emoji, observação com quebra de linha): o total deve ser exato e a mensagem do WhatsApp precisa chegar íntegra, com URL-encoding correto. Teste em: Task 5.
3. **Evento de hoje e virada de dia** (evento com data igual a hoje no fuso local do navegador, todos os eventos passados): o evento de hoje continua visível, e a lista vazia mostra a mensagem configurada. Teste em: Task 5.
4. **Item sem foto, categoria sem itens, busca sem resultado**: o item aparece sem imagem quebrada, a categoria vazia some (inclusive da navegação) e a busca vazia mostra "Nenhum item encontrado". Teste em: Task 6 (Python) e Task 5 (JS).
5. **Texto com HTML no `site.toml`** (`<script>`, `&`, aspas): o conteúdo deve aparecer escapado e nunca ser interpretado como HTML. Teste em: Task 4.

---

## Estrutura de arquivos

```
build.py                      CLI: portfólio, --site, --saida, --serve
config.toml                   marca, cor, whatsapp, url_base
requirements.txt / requirements-dev.txt / package.json / netlify.toml / README.md
gerador/
  dados.py                    leitura + validação de config.toml e site.toml
  formatos.py                 brl, centavos, WhatsApp
  qr.py                       QR code em SVG inline
  imagens.py                  otimização WebP + srcset
  render.py                   ambiente Jinja2, render_site, render_hub, estáticos
ferramentas/
  baixar_fotos.py             baixa as fotos listadas em site.toml → sites/<slug>/imagens/
  capturar.py                 capturas 390px e 1440px via Playwright (QA visual)
static/
  css/base.css                reset, utilitários, estilos estruturais dos componentes
  js/cardapio.js eventos.js carrinho.js
temas/
  _base/pagina.html macros.html
  hub/index.html hub.css
  <slug>/landing.html cardapio.html tema.css     (bar, restaurante, hamburgueria, cafeteria, fino, bistro)
sites/<slug>/site.toml imagens/
clientes/.gitkeep
tests/
  fixtures/completo/site.toml imagens/   site de teste com todos os módulos
  test_dados.py test_formatos.py test_imagens.py test_render.py test_build.py test_temas.py
  js/cardapio.test.js eventos.test.js carrinho.test.js
```

## Esquema do `site.toml` (contrato usado por todas as tasks)

```toml
[site]
slug = "bar"            # obrigatório; igual ao nome da pasta
tema = "bar"            # obrigatório; pasta em temas/
nome = "…"              # obrigatório
segmento = "Bar"        # obrigatório; rótulo no hub
ordem = 1               # ordem no hub (padrão 99)
slogan = "…"
descricao = "…"         # meta description
modulos = ["eventos"]   # subconjunto de ["eventos", "pedido"]
cor = "#…"              # opcional; cor de destaque (theme-color)

[contato]
whatsapp = ""           # opcional; vazio → usa config.whatsapp
telefone = ""  instagram = ""  endereco = ""  mapa_url = ""   # mapa_url = URL de embed

[[horarios]]
dias = "Ter a Qui"   horas = "18h às 00h"

[capa]
titulo = "…"  subtitulo = "…"  imagem = "capa.jpg"  cta = "cardapio"   # cardapio | reservar | pedir

[sobre]
titulo = "…"  texto = "…"  imagens = ["a.jpg"]

[[destaques]]
titulo = "…"  texto = "…"  imagem = "x.jpg"      # imagem opcional
galeria = ["…"]                                  # chave de topo; lista de arquivos

[[cardapio.categorias]]
id = "drinks"  nome = "Drinks"  descricao = ""
  [[cardapio.categorias.itens]]
  nome = "…"  descricao = ""  preco = 32.0  imagem = ""  selos = ["vegano"]
  adicionais = [{ nome = "Bacon", preco = 6.0 }]   # opcional; só exibido

[eventos]
vazio_mensagem = "Novas atrações em breve. Siga-nos no Instagram."
  [[eventos.lista]]
  titulo = "…"  em_dias = 3  hora = "21h"  atracao = "…"  descricao = ""  imagem = ""  valor = "Couvert R$ 20"

[[fotos]]               # origem e crédito das imagens; usado por baixar_fotos.py e pelo rodapé
arquivo = "capa.jpg"  url = "https://images.unsplash.com/…"  autor = "…"  fonte = "Unsplash"
```

Selos válidos: `vegano`, `vegetariano`, `sem-gluten`, `picante`, `novo`, `chef`. Todos os nomes de imagem se referem a `sites/<slug>/imagens/`.

---

### Task 1: Base do projeto, configuração e validação de dados

**Arquivos:**
- Criar: `requirements.txt` (`jinja2>=3.1`, `Pillow>=10`, `segno>=1.6`), `requirements-dev.txt` (`-r requirements.txt`, `pytest>=8`, `playwright>=1.45`), `.gitignore` (`dist/`, `__pycache__/`, `.superpowers/`, `node_modules/`, `.venv/`), `config.toml`, `gerador/__init__.py`, `gerador/dados.py`, `clientes/.gitkeep`, `tests/fixtures/completo/site.toml` (+ imagens JPG pequenas geradas com Pillow no próprio teste via fixture `conftest.py`)
- Testar: `tests/test_dados.py`, `tests/conftest.py`

**Interfaces:**
- Produz:
  - `class ErroDeDados(Exception)`: a mensagem segue o formato `"<caminho relativo do arquivo>: <campo.caminho>: <problema>"`.
  - `carregar_config(caminho: Path) -> dict` → `{"marca": {"nome", "cor"}, "whatsapp": str, "url_base": str}`. A `url_base` sempre termina em `/`, e o `whatsapp` passa por `normalizar_whatsapp` (Task 2; nesta task, valide apenas que contém 12 ou 13 dígitos).
  - `avisos_config(config: dict) -> list[str]`: retorna o aviso `"config.toml: whatsapp ainda é o número provisório 5500000000000"` quando for o caso.
  - `carregar_site(pasta: Path) -> dict`: valida o esquema acima e aplica os padrões (`ordem=99`, `modulos=[]`, listas vazias, `eventos.lista=[]`). Converte `eventos.lista[i].data` em string ISO. Adiciona `site["_pasta"] = pasta`. Confere que toda imagem referenciada existe em `pasta/imagens/`.
  - `listar_sites(raiz: Path) -> list[dict]`: carrega cada `raiz/*/site.toml` e ordena por `(ordem, slug)`.
- `config.toml` inicial: `url_base = "https://davy.netlify.app/"`, `whatsapp = "5500000000000"`, `[marca] nome = "Davy"`, `cor = "#7C3AED"`.

- [ ] **Passo 1:** `git init`, criar `.gitignore`, `python -m venv .venv`, instalar `requirements-dev.txt`.
- [ ] **Passo 2: escrever os testes que falham** em `tests/test_dados.py`:
  - `test_carrega_fixture_completa`: `carregar_site(fixture)["site"]["slug"] == "completo"`; os padrões estão aplicados.
  - `test_erro_cita_arquivo_e_campo`: com o preço `"abc"` no item 0 da categoria 0, `pytest.raises(ErroDeDados, match=r"site\.toml: cardapio\.categorias\[0\]\.itens\[0\]\.preco")`.
  - `test_slug_diferente_da_pasta_falha`, `test_tema_inexistente_falha` (o tema precisa existir em `temas/`; use o parâmetro `temas_dir: Path` com o padrão `<raiz>/temas`).
  - `test_imagem_inexistente_falha`: a mensagem contém `capa.imagem` e o nome do arquivo.
  - `test_evento_data_e_em_dias_juntos_falha`, `test_evento_sem_data_nem_em_dias_falha`, `test_modulo_desconhecido_falha`, `test_selo_desconhecido_falha`.
  - `test_toml_invalido_vira_erro_de_dados`: um `tomllib.TOMLDecodeError` é convertido em `ErroDeDados` com o nome do arquivo.
  - `test_aviso_whatsapp_provisorio`: `avisos_config` retorna 1 aviso com o número provisório e 0 com o número real.
  - `test_listar_sites_ordena_por_ordem`.
- [ ] **Passo 3:** rodar `pytest tests/test_dados.py -v` → FAIL (módulo inexistente).
- [ ] **Passo 4:** implementar `gerador/dados.py`. Use validadores pequenos por tipo (`_texto`, `_numero`, `_lista`) que recebem o caminho do campo, para manter as mensagens no formato do contrato.
- [ ] **Passo 5:** rodar `pytest -v` → PASS.
- [ ] **Passo 6:** commit `feat: base do projeto e validação de site.toml`.

### Task 2: Formatos, WhatsApp e QR

**Arquivos:** criar `gerador/formatos.py`, `gerador/qr.py`; testar `tests/test_formatos.py`; modificar `gerador/dados.py` (usar `normalizar_whatsapp`).

**Interfaces:**
- Produz:
  - `NUMERO_PROVISORIO = "5500000000000"`.
  - `brl(valor: float) -> str`: `brl(42.9) == "R$ 42,90"`, `brl(1234.5) == "R$ 1.234,50"`, `brl(0) == "R$ 0,00"`.
  - `centavos(valor: float) -> int`: `round(valor * 100)`; `centavos(0.1) + centavos(0.2) == 30`.
  - `normalizar_whatsapp(numero: str) -> str`: mantém só os dígitos e prefixa `55` quando há 10 ou 11 dígitos. Se o resultado não tiver 12 ou 13 dígitos, levanta `ValueError`. `"(11) 98765-4321" → "5511987654321"`.
  - `link_whatsapp(numero: str, texto: str) -> str`: `"https://wa.me/<num>?text=" + urllib.parse.quote(texto, safe="")`.
  - `qr_svg(url: str) -> str`: SVG inline gerado com segno (`error="m"`, `scale=4`, `border=2`, módulos escuros `#1a1a1a`), sem a declaração XML.

- [ ] **Passo 1:** escrever os testes que falham, com os valores acima. Inclua também `link_whatsapp("5511…", "Olá & tchau 🍔\nok")`, que deve conter `%26`, `%0A` e o emoji codificado. Inclua ainda `qr_svg("https://x/")`, que deve começar com `<svg`.
- [ ] **Passo 2:** `pytest tests/test_formatos.py -v` → FAIL.
- [ ] **Passo 3:** implementar. Em `dados.py`, `carregar_config` e `contato.whatsapp` passam por `normalizar_whatsapp`, e um `ValueError` vira `ErroDeDados` com o caminho do campo.
- [ ] **Passo 4:** `pytest -v` → PASS.
- [ ] **Passo 5:** commit `feat: formatos de preço, links de WhatsApp e QR`.

### Task 3: Imagens otimizadas e download de fotos

**Arquivos:** criar `gerador/imagens.py`, `ferramentas/baixar_fotos.py`; testar `tests/test_imagens.py`.

**Interfaces:**
- Produz:
  - `otimizar_imagens(origem: Path, destino: Path, larguras: tuple[int, ...] = (800, 1600)) -> dict[str, dict]`. Para cada `.jpg/.jpeg/.png/.webp` em `origem`, grava `destino/<stem>-<w>.webp` (qualidade 78) e retorna `{"capa.jpg": {"src": "img/capa-1600.webp", "srcset": "img/capa-800.webp 800w, img/capa-1600.webp 1600w", "largura": 1600, "altura": 900}}`. Os caminhos ficam relativos à pasta da página que contém `img/`. Larguras maiores que a original são substituídas pela largura original, sem ampliar a imagem e sem repetir valores. A imagem não é regerada quando o `.webp` é mais novo que a origem. EXIF orientation aplicada (`ImageOps.exif_transpose`).
  - CLI `python ferramentas/baixar_fotos.py <pasta do site>`: para cada `[[fotos]]`, baixa a `url` para `imagens/<arquivo>` quando o arquivo ainda não existe. Usa `urllib.request` com User-Agent, timeout de 30 s e uma mensagem clara em caso de falha. Para URLs da Unsplash, anexa `?w=2000&q=85&fm=jpg` quando não houver query.
- [ ] **Passo 1:** testes que falham: imagem 3000×2000 → duas saídas e `srcset` com as duas; imagem 600×400 → uma única variante de 600 com `largura == 600`; PNG com transparência converte sem erro; a segunda chamada não reescreve (mtime inalterado).
- [ ] **Passo 2:** `pytest tests/test_imagens.py -v` → FAIL. **Passo 3:** implementar. **Passo 4:** PASS.
- [ ] **Passo 5:** commit `feat: otimização de imagens e download de fotos`.

### Task 4: Renderização e CLI de build

**Arquivos:** criar `gerador/render.py`, `build.py`, `temas/_base/pagina.html`, temas mínimos `temas/teste/landing.html` + `cardapio.html` + `tema.css` (usados só pela fixture); testar `tests/test_render.py`, `tests/test_build.py`.

**Interfaces:**
- Consome: `carregar_config`, `carregar_site`, `listar_sites`, `avisos_config`, `ErroDeDados` (Task 1); `brl`, `centavos`, `link_whatsapp`, `qr_svg` (Task 2); `otimizar_imagens` (Task 3).
- Produz:
  - `criar_ambiente(raiz: Path) -> jinja2.Environment`: `FileSystemLoader(raiz / "temas")`, `autoescape=True`, `trim_blocks`/`lstrip_blocks`; filtros `brl`, `centavos`, `wa(numero, texto)`.
  - `render_site(env, site: dict, config: dict, destino: Path, raiz_rel: str) -> None`: gera `destino/index.html` a partir de `<tema>/landing.html` e `destino/cardapio/index.html` a partir de `<tema>/cardapio.html`, e otimiza as imagens para `destino/img/` e `destino/cardapio/img/`. Shortcut: as imagens são duplicadas no cardápio para manter os caminhos relativos simples; se o tamanho do deploy pesar, troque por um prefixo `../`. Copia `temas/<tema>/tema.css` para `destino/tema.css`.
    - Contexto de cada template: `site`, `config`, `imagens` (dict da Task 3), `wa_numero` (`site.contato.whatsapp` ou `config.whatsapp`), `raiz` (prefixo relativo até a raiz de `dist`: `raiz_rel` na landing e `raiz_rel + "../"` no cardápio), `tema_css` (`"tema.css"` na landing e `"../tema.css"` no cardápio), `pagina` (`"landing"` | `"cardapio"`).
  - `render_hub(env, sites: list[dict], config: dict, destino: Path) -> None`: gera `destino/index.html` a partir de `hub/index.html`, com `cards = [{"site", "url": "<slug>/", "url_cardapio", "qr": qr_svg(config.url_base + slug + "/cardapio/"), "capa": imagens[capa]}]`. As capas são otimizadas para `destino/img/<slug>/` (larguras `(800,)`), e os `src`/`srcset` retornados recebem o prefixo `img/<slug>/` no lugar de `img/`.
  - `copiar_estaticos(raiz: Path, destino: Path) -> None`: `static/` → `destino/static/`.
  - `build.construir_portfolio(raiz: Path, saida: Path) -> list[str]`: apaga e recria `saida`, renderiza o hub e cada site de `sites/` em `saida/<slug>/` (`raiz_rel="../"`) e retorna os avisos.
  - `build.construir_cliente(raiz: Path, slug: str, saida: Path) -> list[str]`: procura `clientes/<slug>`, e depois `sites/<slug>`. Renderiza na raiz de `saida` (`raiz_rel=""`), sem hub.
  - `build.main(argv: list[str] | None = None) -> int`: opções `--site SLUG`, `--saida` (padrão `dist`), `--serve [PORTA]` (padrão 8000, `http.server` servindo `saida`). Imprime os avisos com o prefixo `AVISO:`. Um `ErroDeDados` é impresso em stderr e retorna 1.
  - `temas/_base/pagina.html`: documento base com `lang="pt-BR"`, viewport, `<title>`, meta description, OG tags (`og:image` = capa), `theme-color = site.cor or config.marca.cor`, link para `{{ raiz }}static/css/base.css` e depois `{{ tema_css }}`, e os blocos `fontes`, `conteudo` e `scripts`.
- [ ] **Passo 1:** testes que falham:
  - `test_render`: a fixture gera `index.html` e `cardapio/index.html`, os dois contêm o nome do site, e o cardápio contém `R$ 42,90`. Um item com nome `<script>alert(1)</script> & "x"` aparece como `&lt;script&gt;` (Ponto de revisão 5). O CSS linkado é `static/css/base.css` com o prefixo correto em cada página.
  - `test_build`:
    - `main(["--saida", tmp])` gera hub + sites (use `monkeypatch` em `sites/` com a fixture) e retorna 0.
    - `main(["--site", "completo", ...])` gera `index.html` na raiz e não gera o hub.
    - Com um `site.toml` inválido, retorna 1 e a stderr contém o caminho do campo, sem `Traceback`.
    - Com o WhatsApp provisório, a saída contém `AVISO:`.
  - Para isolar dos sites reais, `construir_portfolio`/`construir_cliente` usam `raiz` como raiz do projeto e os testes montam uma raiz temporária com `temas/`, `static/`, `config.toml` e `sites/completo` copiados.
- [ ] **Passo 2:** `pytest -v` → FAIL. **Passo 3:** implementar. **Passo 4:** `pytest -v` → PASS; `python build.py --saida /tmp/x` funciona mesmo com `sites/` vazio.
- [ ] **Passo 5:** commit `feat: renderização Jinja2 e CLI de build`.

### Task 5: Módulos JavaScript (cardápio, eventos, carrinho)

**Arquivos:** criar `package.json` (`{"private": true, "type": "module", "scripts": {"test": "node --test tests/js/"}}`), `static/js/cardapio.js`, `static/js/eventos.js`, `static/js/carrinho.js`; testar `tests/js/*.test.js`.

**Interfaces:** cada módulo exporta funções puras + `iniciar(raiz = document)`, chamada pelo próprio módulo quando `typeof document !== "undefined"`. O contrato de DOM, consumido pela Task 6, é:
- `cardapio.js`
  - Funções puras: `normalizar(t: string): string` (minúsculas, sem acento via `NFD` + remoção de `\p{Diacritic}`); `corresponde(item: {nome, descricao}, termo: string): boolean` (termo vazio → true).
  - Contrato de DOM: o campo de busca `input[data-busca]`; os itens `[data-item]` com `data-nome` e `data-descricao`; as categorias `section[data-categoria]`; a navegação `nav[data-abas] a[href="#<id>"]`; e o aviso `[data-sem-resultado]` (oculto por padrão).
  - Comportamento: a busca oculta itens e categorias sem itens visíveis, e mostra o aviso quando não sobra nada. A aba ativa acompanha a rolagem (IntersectionObserver) e recebe `aria-current="true"`.
- `eventos.js`
  - Funções puras: `resolverData({data, emDias}, hoje: Date): string` retorna `AAAA-MM-DD` no fuso local; `visivel(dataISO: string, hoje: Date): boolean`, verdadeiro quando a data é hoje ou depois; `formatarData(dataISO: string): string` usa `Intl.DateTimeFormat("pt-BR", {weekday: "short", day: "numeric", month: "short"})`.
  - Contrato de DOM: os eventos `[data-evento]` têm `data-data` ou `data-em-dias`, e o texto da data vai em `[data-evento-data]`. Quando não sobra nenhum, aparece `[data-eventos-vazio]`.
  - Comportamento: o módulo preenche as datas, oculta os eventos passados e mostra o aviso de lista vazia quando for o caso.
- `carrinho.js`
  - `class Carrinho`: `adicionar(id, nome, centavos)`, `alterar(id, qtd)` (qtd ≤ 0 remove), `itens(): {id, nome, centavos, qtd}[]`, `totalCentavos(): number`, `quantidade(): number`, `mensagem(nomeLoja: string, observacao: string): string`. Exporta também `formatarBRL(centavos): string` ("R$ 42,90") e `linkPedido(numero, mensagem): string` (`encodeURIComponent`).
  - Contrato de DOM:
    - botões `button[data-adicionar]` com `data-id`, `data-nome`, `data-centavos`;
    - contêiner `[data-carrinho]` com `data-whatsapp` e `data-loja`, contendo `[data-carrinho-lista]`, `[data-carrinho-total]`, `[data-carrinho-qtd]`, `textarea[data-carrinho-obs]` e `a[data-carrinho-enviar]`;
    - botão flutuante `[data-carrinho-abrir]`. O painel é um `<dialog>`.
  - Comportamento: o estado persiste em `sessionStorage` (chave `carrinho:<loja>`), com leitura e escrita em try/catch. Com o carrinho vazio, o link de envio fica `aria-disabled="true"` e sem `href`.
  - Formato de `mensagem`:
    ```
    Olá! Pedido pelo cardápio digital — <loja>

    2x X-Bacon — R$ 59,80
    1x Fritas — R$ 18,00

    Total: R$ 77,80
    Obs.: <observacao>        (linha omitida se vazia)
    ```
- [ ] **Passo 1:** testes que falham (`node:test` + `node:assert`):
  - `normalizar("Pão de Açúcar") === "pao de acucar"`; `corresponde({nome: "Café Coado", descricao: ""}, "cafe") === true`.
  - Com `hoje = new Date(2026, 9, 16, 23, 30)`: `resolverData({emDias: 3}, hoje) === "2026-10-19"`; `visivel("2026-10-16", hoje) === true`; `visivel("2026-10-15", hoje) === false`; `resolverData({data: "2026-11-20"}, hoje) === "2026-11-20"`.
  - Itens de 10 e 20 centavos têm `totalCentavos() === 30`; `alterar(id, 0)` remove o item; `mensagem` bate com o formato acima (nome com `&` e emoji preservados); `linkPedido` contém `%26` e `%0A`.
- [ ] **Passo 2:** `npm test` → FAIL. **Passo 3:** implementar. **Passo 4:** `npm test` → PASS.
- [ ] **Passo 5:** commit `feat: módulos JS de cardápio, eventos e carrinho`.

### Task 6: Componentes compartilhados e ferramenta de captura

**Arquivos:** criar `temas/_base/macros.html`, `static/css/base.css`, `ferramentas/capturar.py`; modificar `temas/teste/*.html` para usar as macros; testar `tests/test_render.py` (adicionar casos).

**Interfaces:**
- Consome: o contrato de DOM da Task 5 e o contexto de template da Task 4.
- Produz (macros em `_base/macros.html`; os temas importam com `{% import "_base/macros.html" as m %}`):
  - `m.imagem(imagens, nome, alt, sizes="100vw", classe="", prioridade=False)`: gera `<img>` com `src`, `srcset`, `sizes`, `width`, `height`, `decoding="async"` e `loading="lazy"` (ou `fetchpriority="high"` quando houver prioridade). Com o nome vazio, não gera nada.
  - `m.cardapio(site, imagens, pedido=False)`: monta a busca, as abas e as categorias, ignorando as que estão vazias. Cada item mostra nome, descrição, `brl`, os selos (texto + `aria-label`), a imagem (quando houver), os adicionais (quando houver) e, com `pedido`, um botão `data-adicionar` com `data-centavos="{{ item.preco|centavos }}"`. Termina com o aviso `data-sem-resultado` e o `<script type="module" src="{{ raiz }}static/js/cardapio.js">`.
  - `m.eventos(site, imagens, wa_numero)`: monta a lista de `data-evento`. Cada evento tem um botão "Reservar" que gera um `wa(...)` com o texto `"Olá! Quero reservar para <titulo> (<atracao>)."`, além do aviso `data-eventos-vazio` com `site.eventos.vazio_mensagem` e do script `eventos.js`. As datas fixas são renderizadas no servidor. As relativas recebem "Em breve" como fallback quando não há JS.
  - `m.carrinho(site, wa_numero)`: monta o botão flutuante e o `<dialog data-carrinho>` (contrato da Task 5) e carrega o script `carrinho.js`.
  - `m.horarios(site)`, `m.contato(site, wa_numero)` (endereço, telefone, Instagram, WhatsApp e iframe do mapa com `loading="lazy"` e `title`), e `m.rodape(site, config)`. O rodapé traz os créditos das `[[fotos]]` e o texto "Site de demonstração por <config.marca.nome>" quando o site está em `sites/`.
  - `m.cta(site, wa_numero, raiz)`: `cardapio` aponta para o link `cardapio/`, `reservar` monta um `wa(...)` com "Olá! Gostaria de fazer uma reserva." e `pedir` aponta para o link `cardapio/#pedido`.
  - `base.css`: contém apenas a estrutura e a acessibilidade (reset, `:focus-visible`, `.sr-only`, `prefers-reduced-motion`, layout funcional do dialog do carrinho e das abas *sticky*). Ele não define cor nem fonte, porque cada tema define as suas via custom properties: `--cor-fundo`, `--cor-texto`, `--cor-destaque`, `--fonte-titulo`, `--fonte-texto`, `--raio`.
  - `python ferramentas/capturar.py <url ou pasta dist> <saida_png_dir>`: abre o hub, cada landing e cada cardápio, em 390×844 e 1440×900, página inteira, e grava `<slug>-<pagina>-<largura>.png`. Para uma pasta, sobe um `http.server` temporário.
- [ ] **Passo 1:** testes que falham, com a fixture completa e os dois módulos ligados (Ponto de revisão 4):
  - Um item sem `imagem` não gera `<img`, e uma categoria sem itens não aparece nem nas abas nem nas seções.
  - A saída tem exatamente um `data-sem-resultado`.
  - O botão do item de R$ 42,90 tem `data-centavos="4290"`.
  - Um evento com `em_dias` tem `data-em-dias`, e um evento com `data` tem `data-data="2026-11-20"`.
  - O `<dialog data-carrinho` está presente somente quando `pedido` faz parte de `modulos`.
- [ ] **Passo 2:** FAIL. **Passo 3:** implementar. **Passo 4:** `pytest -v && npm test` → PASS.
- [ ] **Passo 5:** `python build.py --saida dist`, abrir o cardápio da fixture via `--serve` e testar no navegador a busca, as abas e o carrinho: o link do WhatsApp abre com a mensagem certa e o estado sobrevive ao reload.
- [ ] **Passo 6:** commit `feat: macros compartilhadas, base.css e captura de tela`.

### Procedimento comum às Tasks 7–13 (temas)

Cada tema é um trabalho de design. **Antes de escrever o tema, carregue a skill `design-taste-frontend`** e siga a direção do segmento definida na spec (seção 2.2). Os temas não podem compartilhar layout: a ordem e a forma das seções, a capa, os cards do cardápio e a tipografia têm de ser próprios de cada um. Use fontes do Google Fonts (no máximo duas famílias, com `display=swap` e `preconnect`).

Passos de cada tema:
- [ ] **A. Conteúdo:**
  - Escreva `sites/<slug>/site.toml` com um estabelecimento fictício. Antes, faça uma busca rápida na web pelo nome para evitar coincidência com uma marca conhecida no Brasil.
  - O cardápio precisa ter entre 5 e 7 categorias e entre 25 e 40 itens, com preços realistas para o segmento (capital do Sudeste, 2026) e pelo menos 30% dos itens com foto.
  - Inclua os textos de capa, sobre, destaques e horários.
- [ ] **B. Fotos:** encontre entre 12 e 25 fotos na Unsplash/Pexels coerentes com o tema, registre todas em `[[fotos]]` e rode `python ferramentas/baixar_fotos.py sites/<slug>`. Nada de fotos com logotipos ou fachadas de lugares reais identificáveis.
- [ ] **C. Templates:** crie `temas/<slug>/landing.html`, `cardapio.html` e `tema.css`, usando as macros da Task 6 e definindo as custom properties.
- [ ] **D. Teste:** rode `pytest tests/test_temas.py -v`. O teste é parametrizado sobre `listar_sites(Path("sites"))` (veja a Task 7) e precisa passar para o novo slug.
- [ ] **E. QA visual:**
  - Rode `python build.py` e depois `python ferramentas/capturar.py dist capturas/` (adicione `capturas/` ao `.gitignore`).
  - Leia os PNGs do tema em 390 e 1440. Corrija o que a skill de design apontaria: hierarquia, espaçamento, contraste, texto sobre foto e aparência de template.
  - Compare com as capturas dos temas já prontos: se a estrutura parecer a mesma, refaça.
- [ ] **F. Commit:** `feat(tema): <slug>`.

### Task 7: Hub do portfólio "Davy" + teste dos temas

**Arquivos:** criar `temas/hub/index.html`, `temas/hub/hub.css`, `tests/test_temas.py`. O `render_hub` copia `hub.css` para `destino/hub.css`, então é preciso ajustar `gerador/render.py` se a Task 4 ainda não fizer isso.

**Interfaces:**
- `tests/test_temas.py`: parametrizado por `slug` de `listar_sites(Path("sites"))`. Ele roda `construir_portfolio` uma vez (fixture `scope="module"`) em `tmp_path_factory` e, para cada site, verifica:
  - os dois HTML existem e nenhum contém `{{` ou `{%`;
  - a landing tem `id="contato"` e um link para `cardapio/`;
  - o cardápio tem `data-busca` e pelo menos 5 `section[data-categoria]`;
  - `data-evento` aparece se e somente se `"eventos" in modulos`;
  - `data-carrinho` aparece se e somente se `"pedido" in modulos`;
  - toda `<img` tem `alt=` e `width=`.
  - Teste extra: o hub contém um card por site e um `<svg` (QR) em cada card.
- Hub:
  - Topo com o nome "Davy", os detalhes em roxo `config.marca.cor` e uma frase de proposta: cardápios digitais e sites para bares e restaurantes.
  - Uma grade de cards, um por site, com capa, segmento, nome, "Ver site", "Ver cardápio" e o QR do cardápio rotulado "Aponte a câmera para abrir no celular".
  - Uma seção curta "Como funciona" com três passos: escolher o modelo, personalizar e publicar.
  - Um CTA de WhatsApp com o texto "Olá, Davy! Vi o portfólio e quero um site para o meu estabelecimento."
  - Visual sóbrio, para não competir com as demos. Siga o procedimento comum (carregar a skill de design e fazer QA visual).
- [ ] Passos: escrever o `test_temas.py` (o teste do hub falha), implementar o hub, rodar `pytest -v` → PASS, fazer o QA visual e o commit `feat: hub do portfólio Davy`.

### Task 8: Tema Bar
Slug `bar`, `ordem = 1`, `modulos = ["eventos"]`, CTA `reservar`.
- **Direção:** noturno, fundo escuro, âmbar/neon, tipografia condensada.
- **Conteúdo:** drinks autorais em destaque, faixa de happy hour com horário e oferta, agenda de shows com 4 a 6 eventos em `em_dias` (1 a 20 dias) e um evento antigo com `data` fixa no passado, para comprovar que ele some.
- Siga o procedimento comum.

### Task 9: Tema Restaurante
Slug `restaurante`, `ordem = 2`, `modulos = []`, CTA `reservar`.
- **Direção:** claro, acolhedor, fotos grandes de pratos.
- **Conteúdo:** bloco "Prato do dia / Executivo" com os pratos de segunda a sexta (é uma categoria do cardápio destacada na landing), espaço família e reservas.
- Siga o procedimento comum.

### Task 10: Tema Hamburgueria
Slug `hamburgueria`, `ordem = 3`, `modulos = ["pedido"]`, CTA `pedir`.
- **Direção:** cores fortes, tipografia grande e pesada, ritmo de street food.
- **Conteúdo:** combos, burgers com `adicionais` e o carrinho → WhatsApp no cardápio, com a âncora `#pedido`.
- **Validação adicional:** testar no navegador um pedido completo com 3 itens e observação, e conferir a mensagem gerada.
- Siga o procedimento comum.

### Task 11: Tema Cafeteria
Slug `cafeteria`, `ordem = 4`, `modulos = []`, CTA `cardapio`.
- **Direção:** creme e café, suave, aconchegante.
- **Conteúdo:** cafés especiais (origem e método), doces, bloco "ambiente para trabalhar" (wi-fi, tomadas) e chamada para o Instagram.
- Siga o procedimento comum.

### Task 12: Tema Restaurante Fino
Slug `fino`, `ordem = 5`, `modulos = ["eventos"]`, CTA `reservar`.
- **Direção:** editorial, serifada, muito respiro, quase sem cor.
- **Conteúdo:**
  - Menu degustação como categoria com os passos numerados e a harmonização na descrição.
  - Informações de dress code e reserva.
  - Eventos: jantares harmonizados e música ao vivo, de 3 a 5 eventos.
- **Restrição:** no cardápio, as fotos são poucas e grandes.
- Siga o procedimento comum.

### Task 13: Tema Bistrô
Slug `bistro`, `ordem = 6`, `modulos = ["eventos"]`, CTA `reservar`.
- **Direção:** intimista, estética de lousa/giz e papel.
- **Conteúdo:** "Menu do dia" em destaque com visual de lousa, carta de vinhos como categoria e eventos (noite de vinhos, jazz) de 3 a 5.
- Siga o procedimento comum.

### Task 14: Deploy, README e auditoria final

**Arquivos:** criar `netlify.toml`, `README.md`.

- `netlify.toml`:
  ```toml
  [build]
  command = "pip install -r requirements.txt && python build.py"
  publish = "dist"
  [build.environment]
  PYTHON_VERSION = "3.12"
  ```
  Inclua headers de cache longo em `/static/*` e `/*/img/*`.
- `README.md` em português, cobrindo:
  - instalação;
  - `python build.py` / `--serve`;
  - como trocar um preço;
  - como criar um cliente (`cp -r sites/bar clientes/<slug>`, ajustar `slug`, `python build.py --site <slug> --saida dist-<slug>`);
  - como publicar um cliente como um projeto Netlify separado (mesmo repositório, comando `python build.py --site <slug>`);
  - onde trocar a marca, o WhatsApp e a `url_base`.
- [ ] **Passo 1:** rode `pytest -v && npm test`, com tudo passando.
- [ ] **Passo 2:** rode `python build.py --serve` e depois `npx lighthouse http://localhost:8000/<slug>/cardapio/ --preset=perf --form-factor=mobile --only-categories=performance,accessibility --output=json --quiet --chrome-flags="--headless"` para cada slug. A meta é Performance ≥ 90 e Acessibilidade ≥ 95. Corrija o que ficar abaixo e registre os números finais no README. Se o Chrome não estiver disponível, informe isso em vez de dar a meta como cumprida.
- [ ] **Passo 3:** confira que `python build.py --site bar --saida dist-bar` gera a landing em `dist-bar/index.html` e que os links e o CSS funcionam via `--serve`.
- [ ] **Passo 4:** commit `chore: deploy Netlify, README e auditoria`. O push e a conexão com a Netlify ficam com o Davy (repositório privado dele).
