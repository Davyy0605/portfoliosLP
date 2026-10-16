# Davy: landing pages e cardápios digitais

Gerador estático em Python que monta um portfólio com um hub ("Davy") e 6 sites de demonstração de restaurantes fictícios (bar, restaurante, hamburgueria, cafeteria, fino, bistrô). Cada um tem landing page e cardápio digital. Front-end em HTML, CSS e JS puros.

## Instalação

Requer Python 3.11 ou mais novo.

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt          # jinja2, Pillow, segno
pip install -r requirements-dev.txt      # opcional: pytest e playwright
npm install                              # opcional: testes de JS
```

## Uso

```bash
python build.py                 # gera o portfólio completo em dist/
python build.py --serve         # gera e serve em http://localhost:8000/
python build.py --serve 9000    # outra porta
pytest && npm test              # testes
```

Saída do portfólio: `dist/index.html` (hub), `dist/<slug>/index.html` (landing), `dist/<slug>/cardapio/index.html` (cardápio). As imagens otimizadas ficam em cache em `.cache/` (a primeira build é lenta; as seguintes, rápidas).

## Trocar um preço

Abra `sites/<slug>/site.toml` (ou `clientes/<slug>/site.toml`), ache o item em `[[cardapio.categorias.itens]]` e mude `preco`:

```toml
nome = "Negroni"
preco = 34.0      # número, sem aspas; aparece como R$ 34,00
```

Rode `python build.py`. Nenhum HTML precisa ser editado. Erros no arquivo (campo ausente, preço como texto, imagem inexistente) param o build com uma mensagem que cita o arquivo e o campo.

## Criar um cliente

```bash
cp -r sites/bar clientes/meu-cliente
```

1. Em `clientes/meu-cliente/site.toml`, ajuste `slug` (igual ao nome da pasta), `tema`, `nome`, contato, horários, cardápio e eventos.
2. Troque as fotos em `clientes/meu-cliente/imagens/` (ou liste-as em `[[fotos]]` e rode `python ferramentas/baixar_fotos.py clientes/meu-cliente`; baixa no máximo 1600px de largura).
3. Gere o site isolado:

```bash
python build.py --site meu-cliente --saida dist-meu-cliente
```

A landing sai em `dist-meu-cliente/index.html` e o cardápio em `dist-meu-cliente/cardapio/index.html`, sem hub. Para ver: `python build.py --site meu-cliente --saida dist-meu-cliente --serve`.

Módulos opcionais, em `modulos = [...]`: `eventos` (agenda com datas fixas `data = AAAA-MM-DD` ou relativas `em_dias = N`) e `pedido` (carrinho que envia o pedido por WhatsApp).

## Publicar um cliente como projeto Netlify separado

Use o mesmo repositório. Em um novo site Netlify:

- Não altere build command nem publish directory: o `netlify.toml` do repositório manda neles.
- Em **Environment variables**, crie `SITE = meu-cliente`. Com essa variável, o build publica só esse cliente (landing na raiz, cardápio em `/cardapio/`); sem ela, publica o portfólio.

Antes, ajuste o `config.toml` do repositório (ou use um branch do cliente) com a `url_base` e o `whatsapp` do cliente. O WhatsApp do próprio cliente também pode ficar em `[contato] whatsapp` do `site.toml`, que tem prioridade sobre o do `config.toml`.

## Primeiros passos no Netlify (portfólio)

1. Suba o repositório para o GitHub (privado).
2. No Netlify: Add new site, Import from Git, escolha o repositório. O `netlify.toml` já define o comando (`pip install -r requirements.txt && python build.py`), a pasta de publicação (`dist`) e o Python 3.12.
3. Depois do primeiro deploy, copie o endereço real e edite `config.toml`: troque `url_base` (com barra final, ex.: `https://meu-portfolio.netlify.app/`) e `whatsapp` (só dígitos com DDI, ex.: `5511999998888`). Faça commit e push.
4. A build a frio no Netlify reprocessa todas as imagens (não há cache persistente), por isso as fotos em `sites/*/imagens/` ficam limitadas a 1600px.

Enquanto o `whatsapp` for o provisório `5500000000000` ou a `url_base` for a provisória `https://davy.netlify.app/` (os QR codes apontam para ela), o build imprime um `AVISO` para cada um, mas não falha.

## Onde trocar marca, WhatsApp e URL

Tudo em `config.toml`:

```toml
url_base = "https://davy.netlify.app/"   # endereço público (usado nos QR codes)
whatsapp = "5500000000000"               # todos os botões das demos
[marca]
nome = "Davy"
cor = "#7C3AED"                          # roxo do hub
```

### Trocar a marca Davy

- Nome e cor: `[marca]` no `config.toml`. O hub e o rodapé "Site de demonstração por …" usam esses valores.
- Estilo do hub: `temas/hub/index.html` e `temas/hub/hub.css`.
- WhatsApp por estabelecimento: `[contato] whatsapp` no `site.toml` (vazio usa o do `config.toml`).

## Fotos e créditos

As fotos vêm da Unsplash e da Pexels e ficam listadas em `[[fotos]]` de cada `site.toml`. O rodapé mostra os créditos agrupados por fonte. Para recomprimir/baixar de novo: `python ferramentas/baixar_fotos.py sites/<slug>`.

## QA visual

```bash
python ferramentas/capturar.py dist capturas/     # hub + 6 sites, 390px e 1440px
python ferramentas/capturar.py dist-meu-cliente capturas/   # build de cliente
```

## Lighthouse (mobile)

Metas: Performance ≥ 90 e Acessibilidade ≥ 95 em cada cardápio.

Medido com Lighthouse (mobile, simulação padrão, Chromium headless) em máquina lenta; os números oscilam alguns pontos entre execuções (na pior, uma execução com a máquina ocupada derrubou a nota de 98 para 41). Valores abaixo: melhor execução sem contenção.

| Página | Performance | Acessibilidade |
|---|---|---|
| Hub | 94 | 100 |
| Bar, cardápio | 98 | 100 |
| Restaurante, cardápio | 99 | 100 |
| Hamburgueria, cardápio | 98 | 96 |
| Cafeteria, cardápio | 98 | 100 |
| Fino, cardápio | 91 | 100 |
| Bistrô, cardápio | 95 | 100 |
| Bar, landing | 89 | 100 |
| Restaurante, landing | 96 | 100 |
| Hamburgueria, landing | 98 | 100 |
| Cafeteria, landing | 87 | 100 |
| Fino, landing | 86 | 100 |
| Bistrô, landing | 84 | 100 |

Todos os cardápios cumprem a meta. As landings não têm meta; ficam mais baixas por causa do mapa incorporado e das fotos maiores.
