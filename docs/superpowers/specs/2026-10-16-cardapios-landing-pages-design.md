# Design: portfólio de modelos de cardápios digitais e landing pages gastronômicas

Data: 2026-10-16
Status: rascunho, aguardando aprovação

## 1. Intenção e motivo

O dono do projeto vende sites para estabelecimentos gastronômicos. Ele precisa de um **portfólio de modelos prontos** para mostrar a um lead **antes de fechar a negociação**. O lead precisa abrir o modelo e pensar "isso já parece o meu negócio". O modelo prova o nível de qualidade da produção e fecha a venda.

Depois da venda há dois caminhos:
- o cliente fica com o modelo como está, trocando apenas o conteúdo dele;
- o modelo é personalizado ao gosto do cliente.

Isso significa que cada modelo é **vitrine** e também **ponto de partida** de um produto real. Criar um cliente novo a partir de um modelo precisa ser rápido e barato.

## 2. O que será construído

### 2.1 Página do portfólio (hub)
Apresenta a marca do dono do projeto, os seis modelos em cards (miniatura, segmento, link para a demo) e um contato via WhatsApp. Cada card também mostra um **QR code** para abrir o cardápio da demo no celular durante uma reunião presencial.

**Marca do hub (decisão do dono):** por enquanto não há marca própria. O hub usa apenas o nome **"Davy"**, com detalhes em **roxo**. Nome, cor, WhatsApp e domínio ficam num único arquivo de configuração (`config.toml`), para trocar fácil quando a marca existir.

**WhatsApp das demos (decisão do dono):** todos os botões de WhatsApp das demos (reserva, eventos, pedido) enviam para o **número real do Davy**. Um teste feito pelo lead também funciona como contato. O número fica em `config.toml`. Enquanto o Davy não informar o número, fica um valor provisório que o build sinaliza com um aviso.

### 2.2 Seis modelos, um por segmento
Cada modelo é um estabelecimento **fictício**, com nome, marca, conteúdo e fotos próprios, e tem duas páginas:

1. **Landing page**: capa com chamada principal (reservar / ver cardápio / pedir), sobre e ambiente, galeria, destaques, horários, endereço com mapa, contato e redes sociais.
2. **Cardápio digital**: aberto pelo QR da mesa, mobile-first, com navegação por categorias, itens (foto opcional, descrição, preço, selos como vegano, sem glúten, picante, novo, chef recomenda) e busca.

| Segmento | Direção visual (decisão minha) | Diferenciais de conteúdo |
|---|---|---|
| Bar | noturno, fundo escuro, âmbar/neon, tipografia condensada | drinks em destaque, happy hour, **agenda de shows** |
| Restaurante | claro, acolhedor, fotos de pratos em destaque | prato do dia / executivo, reservas, família |
| Hamburgueria | cores fortes, tipografia grande e pesada, ritmo de street food | combos, adicionais, **pedido via WhatsApp** |
| Cafeteria | creme e café, suave, aconchegante | cafés especiais, doces, "ambiente para trabalhar", Instagram |
| Restaurante fino | editorial, serifada, muito respiro, quase sem cor | menu degustação, harmonização, reserva, dress code, **eventos** (jantares harmonizados, música ao vivo) |
| Bistrô | intimista, estética de lousa/giz e papel | menu do dia, carta de vinhos, **eventos** |

A seção de **eventos e apresentações** é um módulo opcional, ligado nos modelos de bar, restaurante fino e bistrô e disponível para qualquer outro. Ela lista os próximos eventos (data, hora, artista ou atração, descrição, imagem, couvert ou ingresso, botão de reserva via WhatsApp) e esconde sozinha os eventos que já passaram.

O **pedido via WhatsApp** (hamburgueria, e opcional nos outros modelos) é um carrinho simples no navegador. Ao finalizar, ele abre o WhatsApp com a mensagem do pedido já montada. Não existe backend nem pagamento.

## 3. Como é feito (decisões tomadas)

- **Python é obrigatório** (exigência do dono). Python é o gerador: lê os dados de cada estabelecimento e monta as páginas estáticas.
- Front-end em **HTML, CSS e JavaScript puro**, linguagens que o dono domina, sem framework de front-end.
- **Hospedagem estática** na Vercel ou na Netlify. O Render continua sendo a casa de qualquer backend futuro.

### Decisões minhas (o dono pode revisar)
- **Templates com Jinja2** e dados em **TOML** (lidos com `tomllib`, da biblioteca padrão do Python 3.11+). TOML é fácil de editar à mão para um cardápio, e o projeto fica só com o Jinja2 e uma biblioteca de QR code (`segno`) como dependências.
- **Um arquivo de dados por estabelecimento** (`sites/<slug>/site.toml`), contendo identidade, contato, horários, seções da landing, cardápio e eventos. **Editar o modelo significa editar esse arquivo** e rodar o build. Criar um cliente novo significa copiar uma pasta de modelo e trocar os dados.
- **Cada modelo tem layout e CSS próprios**, não apenas troca de cor. Componentes compartilhados: o motor do cardápio (abas, busca, selos), o módulo de eventos, o carrinho do WhatsApp e os blocos de mapa/contato. Cada tema escolhe quais usa e define o próprio visual.
- **Estrutura de saída**: `dist/index.html` (hub), `dist/<slug>/index.html` (landing), `dist/<slug>/cardapio/index.html` (cardápio) e as imagens otimizadas.
- **Imagens**: fotos gratuitas (Unsplash/Pexels) baixadas para o projeto, redimensionadas e convertidas para WebP no build, com créditos registrados. Ficam fora as imagens de marcas reais.
- **Comando único**: `python build.py` gera `dist/`, e `python build.py --serve` gera e abre um servidor local.
- **Cliente real após a venda**: fica no mesmo repositório, em `clientes/<slug>/site.toml`, e usa os mesmos temas e componentes, que continuam compartilhados. Assim uma correção chega a todos os clientes. `python build.py --site <slug>` gera só aquele site, com a landing na raiz (`/`) e o cardápio em `/cardapio/`, sem o hub. Cada cliente é um projeto separado na Vercel/Netlify, apontando para o mesmo repositório com outro comando de build, e com domínio próprio. Se o cliente pedir uma personalização profunda, o tema dele é copiado para `temas/<slug>/` e passa a evoluir separado.
- **Eventos das demos não envelhecem**: no arquivo de dados, um evento pode ter uma data fixa (`data = 2026-11-20`) ou uma data relativa (`em_dias = 5`). O JavaScript calcula a data relativa no navegador a partir do dia de hoje. As demos usam datas relativas e os clientes reais usam datas fixas. O módulo esconde os eventos que já passaram e, se não sobrar nenhum, mostra uma mensagem configurável no lugar de uma seção vazia.
- **QR codes** são gerados a partir de uma `url_base` definida na configuração, para que funcionem quando o domínio final for definido.

## 4. Metas
- Um lead no celular abre qualquer demo e ela parece um produto pronto e caro.
- Cardápio rápido em 4G: Lighthouse mobile de Performance ≥ 90 e Acessibilidade ≥ 95.
- Criar um novo cliente a partir de um modelo leva minutos, editando só dados.
- Os seis modelos são claramente diferentes entre si à primeira vista.

## 5. Fora do escopo desta versão
- Painel administrativo para o cliente editar sozinho. Fica para uma fase 2 (Python no Render + Postgres) e só para quem pedir.
- Pagamento online, integração com iFood ou delivery próprio com backend.
- Múltiplos idiomas.
- Sistema real de reservas (por enquanto, reserva = WhatsApp ou link externo).

## 6. Antiobjetivos (falha mesmo que "funcione")
- Seis modelos que são o mesmo layout com outra cor.
- Visual genérico, com cara de template ou de site feito por IA.
- Cardápio lento ou desconfortável no celular, que é onde ele é usado.
- Usar nome, marca ou fotos de estabelecimentos reais.
- Precisar mexer em HTML para trocar um preço.

## 7. Deixado para quem construir
- Nomes, marcas e textos dos estabelecimentos fictícios.
- Paleta e fontes exatas de cada tema, dentro da direção da tabela da seção 2.2.
- Microanimações e interações.
- Escolha final entre Vercel e Netlify.
