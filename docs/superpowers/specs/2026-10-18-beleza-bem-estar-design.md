# Design: ramo "Beleza e bem-estar" no portfólio (6 modelos com agendamento)

Data: 2026-10-18
Status: rascunho, aguardando aprovação
Base: `docs/superpowers/specs/2026-10-16-cardapios-landing-pages-design.md`. Tudo o que aquele documento decidiu continua valendo, salvo o que este altera.

## 1. Intenção e motivo

O Davy quer expandir as vendas além da gastronomia para **negócios de serviço que vivem de agenda**. O portfólio ganha um segundo ramo, **Beleza e bem-estar**, com modelos prontos para mostrar a um lead.

O que o dono do negócio precisa sentir ao abrir um modelo, nas palavras do Davy: *"isso vai me ajudar a alcançar mais clientes com certeza"*. A página precisa parecer profissional e despertar a vontade de ter uma igual. Nos cardápios, o argumento de venda era o pedido e a reserva. Aqui é o **agendamento**: agenda cheia é o que esse dono quer.

Junto com isso, entram duas correções no que já existe, pedidas pelo Davy:
- no carrinho da hamburgueria, a escolha do usuário não fica visível em lugar nenhum;
- os QR codes do hub aparecem cortados.

## 2. O que será construído

### 2.1 Hub dividido em ramos (decisão do Davy: opção "entrada geral + página por ramo")
- **`/` (entrada geral):** apresenta o Davy ("sites que trazem clientes para o seu negócio") e dois cartões grandes, um por ramo: **Bares e restaurantes** (6 modelos, cardápio com QR) e **Beleza e bem-estar** (6 modelos, agendamento online). Mantém o contato por WhatsApp.
- **`/gastronomia/`:** é o hub atual (cards, QR, "como funciona"), com o texto que já existe.
- **`/beleza/`:** a mesma estrutura de cards, QR e "como funciona", com o texto adaptado para serviços. A mensagem de WhatsApp do topo também muda, ex.: "quero um site para o meu salão/estúdio".
- Cada página de ramo tem um link de volta para a entrada.
- **Decisão minha:** os modelos continuam em endereços planos (`/bar/`, `/hamburgueria/`, `/barbearia/`...), sem prefixo de ramo. Os QR codes e links que o Davy já enviou continuam funcionando.
- O ramo de cada modelo vem do próprio `site.toml` (ex.: `ramo = "gastronomia"` ou `ramo = "beleza"` em `[site]`). Os 6 modelos que já existem recebem `gastronomia`.
- O build deve continuar aceitando um terceiro ramo no futuro sem reescrever o hub. Nada além disso é preparado agora.

### 2.2 Seis modelos novos, um por segmento
Os segmentos foram escolhidos pelo Davy: **maquiagem, salão de beleza, manicure/nail designer, barbearia, pet shop (banho e tosa) e estética**.

Cada modelo é um negócio **fictício**, com nome, marca, textos e fotos próprios, e tem duas páginas:
1. **Landing** (`/<slug>/`).
2. **Agendamento** (`/<slug>/agendar/`), o equivalente ao `/cardapio/` dos restaurantes. Todos os botões "Agendar" da landing levam para ela.

**Conteúdo da landing** (aprovado pelo Davy em conversa):
- capa com o botão **"Agendar horário"** em destaque;
- serviços com preço e duração;
- equipe ou profissionais;
- galeria de trabalhos, com antes e depois quando fizer sentido;
- depoimentos de clientes fictícios;
- horários;
- endereço com mapa;
- Instagram;
- perguntas frequentes;
- WhatsApp sempre à mão.

Cada tema escolhe quais blocos usa e em que ordem.

| Segmento | Direção visual (decisão minha, refinada na fase de design) | Diferenciais |
|---|---|---|
| Barbearia | escura e clássica, couro, latão, tipografia forte | combos corte + barba; profissional por especialidade |
| Salão de beleza | sofisticado e luminoso, editorial | preços "a partir de R$ X" (dependem do cabelo); coloração, tratamentos |
| Manicure / nail designer | delicado e moderno, tons pastel ou nude, galeria em destaque | galeria de unhas como vitrine; manutenção de alongamento |
| Maquiagem | glamour, contraste, retratos grandes | **atendimento a domicílio** (pede o bairro); chamada para **noivas** e eventos |
| Pet shop (banho e tosa) | alegre e colorido, arredondado, sem cara infantil | **nome e porte do pet (P/M/G) mudam o preço**; táxi dog opcional |
| Estética | clara, calma, quase clínica, muito respiro | sessões avulsas e **pacotes** (ex.: 10 sessões de drenagem) |

Os seis têm que ser **claramente diferentes entre si**, e não apenas trocas de cor (mesmo antiobjetivo da spec original).

### 2.3 Agendamento (nível 2, decisão do Davy)
É uma página em passos, sem backend, que termina no WhatsApp com a mensagem pronta. Os passos aprovados no esboço:

1. **Serviços:** escolha de um ou mais, com soma da duração e do preço.
2. **Profissional:** um da equipe ou **"Sem preferência"**.
3. **Dia e horário:** próximos dias, com os dias fechados bloqueados. Os horários são gerados a partir do funcionamento da casa e mostram o aviso **"O horário é confirmado pelo [negócio] no WhatsApp."**
4. **Seus dados:** nome, observação opcional e resumo. O botão **"Agendar pelo WhatsApp"** abre o `wa.me` com a mensagem montada (serviços com preço, profissional, dia e hora, duração, total e nome).

Variações por segmento:
- **Pet shop:** antes dos serviços, pede nome e porte do pet; o preço segue o porte.
- **Estética:** pacotes aparecem como serviços.
- **Maquiagem:** opção de domicílio que pede o bairro.
- **Salão:** "a partir de" no preço e no total.

A página não sabe quais horários estão ocupados. Isso é aceito: o dono confirma pelo WhatsApp, como já faz hoje.

**Regras decididas pelo Davy:**
- **Um profissional para o agendamento inteiro.** O passo 2 lista só quem faz **todos** os serviços escolhidos, além de "Sem preferência". Se ninguém faz todos, sobra apenas "Sem preferência", e o dono acerta os detalhes no WhatsApp.
- **Cada profissional tem os próprios dias e horários de trabalho.** Ao escolher um profissional, o passo 3 bloqueia os dias e horários em que ele não trabalha. "Sem preferência" usa o funcionamento da casa. Quem não tem agenda própria segue o horário da casa.
- **Adicionais com preço somam no total:** domicílio na maquiagem e táxi dog no pet shop. No motor, é um "adicional" genérico (nome, preço opcional). Sem preço, aparece **"a combinar"** e não soma. O domicílio pede o bairro.

**Decisões minhas (o Davy pode revisar):**
- **Funcionamento com mais de um período por dia**, para cobrir a pausa de almoço (ex.: 9h–12h e 13h30–19h). Vale para a casa e para cada profissional.
- **Na página, um horário só aparece se o atendimento inteiro** (soma das durações) cabe dentro de um período aberto. Dias e horários que já passaram não aparecem.
- **Pet shop:** um pet por agendamento. Para dois pets, faz-se um segundo agendamento.
- **Pacotes da estética:** são agendados como um serviço. A duração é a da primeira sessão e o preço é o do pacote.
- **Preços no `site.toml` continuam em reais** (ex.: `preco = 45.0`), como nos cardápios. O build converte para centavos inteiros, e o JavaScript só trabalha com centavos (`carrinho.js`). Assim há uma só convenção para quem edita.
- **`ramo` é opcional e vale `"gastronomia"` por padrão**, para que os `site.toml` existentes, de modelos e de clientes, continuem funcionando sem mudança.

Os dados vêm do `site.toml`:
- serviços: id, nome, duração em minutos, preço, flag "a partir de", preço por porte;
- adicionais;
- equipe: nome, especialidade, foto, serviços que faz, agenda própria opcional;
- funcionamento estruturado por dia da semana, com um ou mais períodos;
- intervalo da grade de horários.

**Nível 3 (agenda real, com horários ocupados e confirmação automática):** fora desta versão. Se um cliente pedir, a adaptação é estudada à parte.

### 2.4 Retorno visual das escolhas (decisão do Davy: opção A)
Vale para o **carrinho atual** (hamburgueria e qualquer modelo com o módulo `pedido`) e para o **agendamento**:
- **Aviso rápido** ao adicionar ("✓ Barba completa adicionada" / "✓ X-Bacon adicionado"). Some sozinho após cerca de 2 a 3 s e também é anunciado para leitor de tela.
- **Barra fixa embaixo com o resumo**, sempre visível quando há algo escolhido: quantidade, total (e duração, no agendamento) e os nomes do que foi escolhido como etiquetas. Tocar nela abre a revisão (o diálogo do carrinho) ou avança o passo (agendamento). Ela substitui o botão "Ver pedido" atual.
- O botão do item escolhido muda de estado (ex.: "+" vira "✓").
- A correção fica nos componentes compartilhados (`static/js/carrinho.js`, macro `carrinho` em `temas/_base/macros.html`, `static/css/base.css`). O visual de cada tema continua no `tema.css` dele. Assim ela chega à hamburgueria, a qualquer tema com `pedido` e aos clientes reais.

### 2.5 Correção do QR code cortado
- **Causa (verificada):** `gerador/qr.py` gera o SVG com `width`/`height` fixos e sem `viewBox`. O CSS do hub reduz o SVG para `5.5rem`, e o navegador recorta em vez de escalar, sobrando só o canto superior esquerdo.
- **Correção:** gerar com `omitsize=True` no `segno` (produz `viewBox`) e garantir no CSS que o QR mantém a proporção quadrada. Vale para o hub atual e para as páginas de ramo.
- Para os modelos de beleza, o QR do card abre a página de **agendamento**.

## 3. Como é feito
- **Mesma base do projeto** (decisão já existente): Python + Jinja2 + TOML, HTML/CSS/JS puros, site estático na Netlify, `python build.py`. Nenhuma dependência nova é necessária.
- **Componentes novos compartilhados:** o motor de agendamento (`static/js/agendamento.js`) e os blocos de landing de serviço (serviços, equipe, depoimentos, FAQ) como macros. O retorno visual (aviso e barra) é **um só** código, usado pelo carrinho e pelo agendamento.
- O build hoje gera sempre `landing` e `cardapio` para cada site (`gerador/render.py`). Ele precisa passar a gerar as páginas de acordo com o ramo: cardápio para gastronomia e agendar para beleza.
- O `--site <slug>` de cliente real continua funcionando para os dois ramos. Para beleza, gera `/` e `/agendar/`.
- **Design:** cada tema é criado com as skills de design, **ui-ux-pro-max** e outras como o construtor achar melhor (pedido do Davy). Visual premium, sem cara de template ou de site feito por IA.
- Fotos gratuitas (Unsplash/Pexels) com créditos, WebP no build, nada de marcas ou pessoas reais identificáveis como "clientes". Mesma regra da spec original.

## 4. Metas
- Um dono de salão ou de barbearia abre o modelo no celular e quer um igual.
- O agendamento completo (serviço → WhatsApp) cabe em menos de um minuto no celular.
- A cada escolha, fica óbvio o que foi adicionado e o que já está escolhido (carrinho e agendamento).
- O QR de cada card é lido pela câmera do celular a partir da tela do computador.
- As metas de Lighthouse da spec original valem para a página de agendamento (Performance ≥ 90, Acessibilidade ≥ 95 no mobile).
- Criar um cliente real de beleza a partir de um modelo é editar dados, sem tocar em HTML.

## 5. Fora do escopo
- Agenda real com horários ocupados, confirmação automática e lembretes (nível 3).
- Pagamento ou sinal online.
- Painel para o cliente editar sozinho.
- Link para sistemas de agendamento externos (Trinks, AgendaPro etc.). Decisão do Davy: poucos clientes usam, e o agendamento sempre termina no WhatsApp.
- Os nichos que ficaram de fora desta leva (sobrancelhas/cílios, tatuagem, massagem, depilação, pilates, podologia). A estrutura de ramos permite adicioná-los depois.

## 6. Antiobjetivos
- Seis modelos de beleza que são o mesmo layout com outra cor.
- Um agendamento que parece formulário de contato genérico.
- Prometer horário garantido: o texto deixa claro que é uma solicitação.
- Quebrar endereços, QR codes ou o build de clientes que já existem.
- Precisar mexer em HTML para trocar um serviço, um preço ou um horário.

## 7. Deixado para quem construir
- Nomes, marcas, textos e fotos dos 6 negócios fictícios.
- A identidade visual final de cada tema, dentro da direção da tabela.
- Quantos dias à frente o agendamento mostra e o intervalo padrão da grade.
- O texto exato das páginas de entrada e de beleza.
