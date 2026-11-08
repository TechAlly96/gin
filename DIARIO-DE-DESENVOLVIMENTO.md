# GIN - Global Intelligence Network
## Diario de Desenvolvimento

App pessoal (sem acesso publico) de noticias diarias de fontes oficiais, pais por pais.

### Regras do projeto
- Uma instrucao por vez; so avancar com evidencia real do terminal.
- Edicao de arquivos via heredoc (nunca nano).
- Commit + push ao fim de cada fase.
- Um pais por vez: so e concluido quando governo, chancelaria, defesa, parlamento e agencia publica estiverem configurados com coleta comprovada, ou com a lacuna documentada.
- Projeto isolado: nada compartilhado com S2M, VIGIAI ou Render.

### Arquitetura decidida
- Coletor em Python (dependencias minimas) gerando JSON por pais.
- Execucao agendada no GitHub Actions (sem servidor).
- App PWA estatico em HTML/JS puro, com rolagem infinita por pais.
- Primeiro pais: Brasil.

---

## 23/10/2026

sprint-000: chore(ambiente) - diagnostico do celular matriz: Termux nativo aarch64, Python 3.13.13, pip 26.1.2, Git 2.54.0, Node 26.3.1, gh ausente (nao necessario). Armazenamento em 96% (2,2 GB livres) -> decisao: zero dependencias pesadas, sem npm no app. Projeto criado em ~/projetos/gin (Termux nativo, fora do proot Ubuntu).

sprint-001: chore(infra) - GitHub CLI 2.95.0 instalado no Termux nativo (pkg); autenticado como TechAlly96 via device flow, protocolo HTTPS, escopos repo/gist/read:org/workflow; gh auth setup-git configurado. Token salvo em texto plano em ~/.config/gh/hosts.yml (normal no Termux, sem keyring) -> cuidado: nao incluir ~/.config/gh em backup sem criptografia; revogar em github.com/settings/applications se perder o aparelho. Repositorio privado TechAlly96/gin criado e commit b8b3668 enviado (branch main rastreando origin/main). SPRINT 0 CONCLUIDA.

sprint-002: feat(ferramentas) + pesquisa(fontes-BR) - criadas 4 ferramentas de diagnostico em Python puro (sem dependencias), reutilizaveis para todos os paises: sondar_feeds.py (testa lista de candidatos), descobrir_feed.py (testa sufixos /RSS, rss.xml, atom.xml, feed, rss e <link rel=alternate>), listar_itens.py (lista data|titulo|link de um feed, com filtro e 3 tentativas), inspecionar_listagem.py (estrutura de paginas sem feed). Fontes do BRASIL validadas com evidencia: governo = Planalto gov.br/planalto/pt-br/acompanhe-o-planalto/noticias/RSS (Atom, 30 itens); chancelaria = Itamaraty SEM FEED -> leitura da pagina publica gov.br/mre/pt-br/canais_atendimento/imprensa/notas-a-imprensa (30 notas por pagina; estrutura article.tileItem, span.subtitle com numero da nota, a.summary.url com titulo/link, span.documentByLine com data); defesa = gov.br/defesa/pt-br/centrais-de-conteudo/noticias/RSS (Atom, 100 itens); parlamento = Camara camara.leg.br/noticias/rss/ultimas-noticias (20) + Senado www12.senado.leg.br/noticias/rss.xml (15, atual 22/10/2026); agencia = Agencia Brasil agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml (10; endereco antigo /feed/ redireciona). DESCARTADOS: gov.br/rss.xml (0 noticias em 100 itens, so servicos) e gov.br/mre/atom.xml (so atualizacoes tecnicas do site). Firewall do gov.br reseta conexoes com requisicoes seguidas (ConnectionResetError) -> coletor deve respeitar intervalo e repetir com espera.

sprint-003: feat(coletor) - coletor/leitores.py (somente biblioteca padrao): download educado (3 s entre acessos ao mesmo dominio, 3 tentativas com espera crescente, limite 8 MB, erro 4xx sem repeticao), leitura de RSS 2.0/RSS 1.0/Atom via xml.etree, leitores de pagina html-plone (Itamaraty) e html-govbr (ul.listagem-noticias-com-foto), datas RFC 822/ISO 8601/dd/mm/aaaa com hora 19h31 ou 19:31 e fuso por pais (fuso_horas no fontes/<pais>.json; BR = -3). Conteudo coletado tratado como NAO confiavel (so texto extraido, nada executado). fontes/br.json com 8 fontes. TESTE REAL: 8/8 OK, 235 itens, 100% com data. DESCOBERTAS: (1) feed /RSS do gov.br pode ATRASAR em relacao a propria pagina - Defesa: feed parou em 30/09, pagina tem noticia de 22/10 -> decisao: fontes gov.br usam feed + pagina em redundancia, duplicados removidos pelo link; (2) Planalto sem noticias desde 27/09 (feed e pagina concordam) - fonte funcionando porem quieta, provavel restricao de publicidade institucional no periodo eleitoral (2o turno 25/10/2026) -> regra: fonte sem publicar ha X dias = ALERTA, nao erro; (3) Itamaraty e listagens gov.br publicam so a data (sem hora) - limitacao da fonte; ordem do dia preservada pela posicao na pagina.

sprint-004: feat(coletor) - coletor/coletar.py: coleta todas as fontes do pais (falha de uma nao para as outras), normaliza (id = sha1 do link sem protocolo, pais, fonte, categoria, natureza, titulo, resumo ate 400 caracteres, link, publicado em UTC, precisao hora/dia/estimada, ordem na fonte, coletado), remove duplicados pelo link (mantem a data mais precisa), mescla com o historico sem nunca apagar (aborta se todos.json estiver corrompido; titulo corrigido pela fonte guarda titulos_anteriores), grava dados/<pais>/todos.json + pagina-N.json (50 por pagina, para rolagem infinita) + indice.json (estado de cada fonte e cobertura por categoria) e dados/paises.json. Alerta quando fonte fica mais de 7 dias sem publicar (configuravel por pais). dados/ no .gitignore (dados locais de teste nao versionados; publicacao sera via GitHub Actions). TESTE REAL: 1a execucao 195 noticias unicas (235 lidas - 21 midias - 19 duplicadas entre feed e pagina), 4 paginas, PAIS COMPLETO: SIM; 2a execucao novos 0 em todas as fontes, historico 195 -> 195 (deduplicacao e historico comprovados). Pagina da Defesa trouxe 10 noticias ausentes do feed e a do Planalto 1 (redundancia validada). INVESTIGACAO: 21 itens rejeitados do feed da Defesa sao TODOS arquivos de midia sem titulo (jpg/png/jfif/video) guardados na pasta de noticias -> descarte correto, nenhuma noticia perdida. BRASIL: coleta CONCLUIDA (5/5 categorias).

sprint-005: feat(app) - app/ em HTML/CSS/JS puros (sem npm, sem build): index.html com CSP restrita (somente 'self'), estilo.css tema escuro mobile-first, app.js com seletor de pais (dados/paises.json, rota por #codigo), filtro por categoria, ROLAGEM INFINITA (IntersectionObserver com margem de 600 px carrega pagina-N.json sob demanda; ids ja vistos ignorados; continua carregando enquanto a tela nao enche, inclusive com filtro), painel de estado das fontes (OK/ALERTA/ERRO + ultima publicacao) a partir do indice.json. Seguranca: conteudo das fontes inserido SO como texto (textContent, nunca innerHTML); apenas links http/https clicaveis, abertos com noopener noreferrer. TESTE REAL no Chrome do celular (servidor local python3 -m http.server em 127.0.0.1:8080): filtros Todas/Governo/Chancelaria/Defesa/Parlamento/Agencia OK; ordem cronologica OK; numero oficial da nota do Itamaraty exibido; precisao de data respeitada (hora quando a fonte informa, so o dia quando nao); painel '195 noticias - 3 alerta(s)' bate com o coletor. Log do servidor comprova a rolagem infinita: pagina-1 na abertura (05:13), pagina-2 (05:14), pagina-3 (05:15), pagina-4 no fim (05:18); respostas 304 = cache do navegador reaproveitado. Pendencias: acentuacao dos textos fixos (Agencia, noticias, Ministerio) e icone/manifest PWA (favicon 404).

sprint-006: fix(app+coletor) - acentuacao dos textos fixos (Agência, notícias, última, Índice, indisponível, há, válido) e dos 8 nomes de fonte em fontes/br.json; separador " · ". Melhoria de arquitetura: app exibe o nome ATUAL da fonte a partir de indice.json (mapa id -> nome), nao o nome gravado em cada noticia -> renomear fonte nao exige reescrever o historico. TESTE REAL: noticia coletada as 05:06 com nome antigo sem acento aparece como "Agência Brasil (EBC) · 22 de out." (nomes centralizados comprovados); painel "195 notícias · 3 alerta(s)"; app.js novo servido (200) e rolagem infinita mantida (pagina-2 carregada ao rolar).

sprint-007: feat(app) - PWA instalavel: ferramentas/gerar_icones.py (desenha globo azul e grava PNG com struct+zlib, sem biblioteca de imagem) -> app/icone-192.png, icone-512.png, icone-maskable-512.png; app/manifest.json (standalone, tema #0b1220, pt-BR); app/sw.js (service worker REDE PRIMEIRO: com internet sempre busca a versao nova; guarda copia de tudo o que foi aberto em caches separados gin-app-v1 e gin-dados-v1; sem internet devolve a copia); index.html com manifest/icone (resolve favicon 404); app.js registra o service worker e mostra "Offline ·" no painel sem conexao. TESTE REAL no celular: (1) Chrome ofereceu "Instalar aplicativo" com o icone e o nome "GIN · Notícias oficiais" (criterios de instalacao atendidos); (2) log mostra manifest.json e sw.js com 200 e a casca do app (index.html + 3 icones) guardada pelo service worker as 05:32; (3) app aberto pelo icone da tela inicial em tela cheia as 05:34; (4) OFFLINE (servidor parado + modo aviao): noticias apareceram normalmente a partir da copia guardada. BRASIL: coleta + app + PWA concluidos; falta automacao (GitHub Actions) e publicacao.

sprint-008: ci(coleta+pages) + seguranca(repo) - DECISAO: repositorio PUBLICO + GitHub Pages (risco baixo aceito: noticias publicas, sem segredos no repo; Actions ilimitado em repo publico). Antes de abrir: e-mail dos 8 commits reescrito para o noreply do GitHub (177716000+TechAlly96@users.noreply.github.com) via filter-branch, envio com --force-with-lease, conferido pela API do GitHub (8/8 noreply), user.email noreply configurado so neste repo, copia local do historico antigo removida. Repo tornado publico e Pages ativado em modo workflow. .github/workflows/coletar.yml: coleta a cada hora (cron 17 * * * *, UTC) + push em app/fontes/coletor + manual; recupera historico do ramo dados (cria orfao na 1a vez), coleta todos os paises de fontes/ (falha de um pais nao para os outros), salva no ramo dados so quando ha novidade, monta _site (app/ + dados/ sem todos.json + index.html que redireciona para app/) e publica com upload-pages-artifact@v4 + deploy-pages@v4; concorrencia travada, limite de 15 min. TESTE REAL: execucao 39933881355 com sucesso (coletar 30 s, publicar 19 s); ramo dados criado; https://techally96.github.io/gin/ responde 200 em app/, dados/paises.json, dados/br/indice.json e dados/br/pagina-1.json; indice publicado mostra 8/8 fontes OK coletando DO GITHUB, com os mesmos totais do celular (195 noticias, completo True) -> sem bloqueio dos sites gov.br aos servidores do GitHub. BRASIL CONCLUIDO (coleta + app + PWA + automacao + publicacao). PENDENCIAS: (1) atualizar actions de publicacao quando houver versoes Node 24 (aviso de deprecacao do Node 20, hoje funciona forcado em Node 24); (2) ubuntu-latest migra para Ubuntu 26 - acompanhar a primeira execucao; (3) ramo dados recebe ate 24 commits/dia - avaliar compactacao periodica do historico; (4) para paises com fuso diferente, datas so-com-dia precisam de exibicao no fuso de origem; (5) reinstalar o PWA no celular a partir do endereco publicado.

sprint-009: feat(argentina) - ARGENTINA, 2o pais (mesmo fuso -3; so o idioma muda).
- Nenhum site oficial argentino tem feed (404 ou pagina comum em todos os sufixos).
- Nova ferramenta ferramentas/mapear_links.py: agrupa links por pasta, conta manchetes e datas.
- Leitor generico html-links: padrao comparado ao endereco RESOLVIDO; titulo = cabecalho ou texto do link;
  data por extenso (es/pt) no link OU 1a data logo apos o link, ate o proximo link; resumo = texto restante.
- Data buscada DENTRO da noticia (data_no_artigo=true): so noticias novas sem data, ate 20 por execucao;
  falha de conexao ADIA para a proxima execucao (nunca grava data errada). Na Camara a 1a data = publicacao.
- LACUNAS documentadas por categoria em fontes/<pais>.json; coberta = fonte OK ou lacuna; app mostra [LACUNA].
- fontes/ar.json, 7 fontes:
  governo = Casa Rosada /informacion/actividad-oficial/9-noticias (36, data no link)
  chancelaria = Cancilleria /es/actualidad/noticias (20; quieta desde 01/10) + destaques /es/destacados/ (5, sem data -> estimada)
  defesa = argentina.gob.ar/defensa (8, data no link)
  parlamento = Diputados /prensa/ (40) + pagina inicial da Camara (10, mais nova) + Senado /prensa/eventos (10)
  agencia = LACUNA (Telam convertida em 2024 em agencia de publicidade; Radio Nacional lista so emissoras)
- TESTE do zero (simula 1a coleta do GitHub): 129 noticias, 7/7 OK, 30 datas buscadas sem falha,
  precisao 'dia' em tudo exceto 5 destaques (estimada), PAIS COMPLETO: SIM. Regressao Brasil OK (8/8).
- Corrigido: falha de conexao na busca de data gerava data estimada; agora adia.
FIM-sprint-009

sprint-010: fix(datas) - noticias sem data no topo do feed (visto no app: destaques da Cancilleria).
- Regra nova: item sem data visto na 1a coleta da fonte = precisao 'desconhecida' (fim do feed,
  rotulo "data nao informada pela fonte"); item sem data visto em coleta posterior = 'estimada' (+-1 h).
- 1a coleta da fonte detectada pela menor data de coleta dela: corrige sozinho itens ja publicados.
- Data estimada nunca substitui informacao ja guardada (sem essa trava o item voltaria ao topo a cada hora).
- 'ultima' publicacao e cobertura usam so precisao hora/dia.
- TESTE local AR: inicio do feed = noticias de 23/10 com data real; fim = 5 destaques 'desconhecida';
  129 noticias, PAIS COMPLETO: SIM.
FIM-sprint-010

sprint-011: feat(eua) - ESTADOS UNIDOS, 3o pais (ingles; feeds com fuso explicito).
- Identificacao do coletor por fonte, sempre HONESTA (declara ser o robo do GIN, nunca se passa
  por navegador): 'padrao' = Mozilla/5.0 (compatible; GIN-Coletor/0.3; +repo), 'simples' = GIN-Coletor/0.2.
- Evidencia: State Dept so aceita 'padrao' (celular); Department of War so aceita 'simples' e so a
  partir dos servidores do GitHub (celular: bloqueado em tudo). Workflow manual testar-acesso.yml criado.
- fontes/us.json (9): governo = White House /news/feed; chancelaria = State Dept press releases;
  defesa = war.gov releases + news ('simples'); parlamento = congress.gov (presented-to-president,
  house/senate floor, most-viewed); agencia = VOA (estatal; ativa apos ordem judicial de 03/2026).
- Congresso em recesso ate a eleicao de 03/11: pautas vazias; reavaliar depois da eleicao.
- Regressao local: AR 7/7; BR 7/8 (Senado: timeout no TLS, antes da identificacao; passageiro,
  confirmado OK a partir do GitHub).
FIM-sprint-011

sprint-012: fix(robustez) - Itamaraty mudou o layout (sem article.tileItem): 0 notas, BR caiu para incompleto.
- Diagnostico: mesma pagina para as duas identificacoes (nao era bloqueio); nova pagina usa o modelo
  listagem-noticias do gov.br -> br-itamaraty passa a html-govbr (30/30 com data e numero da nota).
- LEITOR DE RESERVA: se o leitor HTML configurado achar 0 itens, tenta os outros e registra o usado;
  o coletor emite alerta "leitor de reserva X em uso (layout mudou?)". Evita fonte zerada em silencio.
- Cabecalho Accept (rss/atom/xml/html) em todas as requisicoes (diferenca entre o teste OK e a coleta
  403 do Department of War).
- Planalto voltou a publicar apos o 2o turno (27/10): confirma a restricao do periodo eleitoral.
FIM-sprint-012

sprint-013: feat(audio) - BOLETIM EM AUDIO (ouvir com a tela apagada).
- Leitura do navegador (speechSynthesis) para em 2o plano no Chrome Android -> audio gerado no servidor.
- Vozes escolhidas: pt_BR-faber-medium (usuario), es_AR-daniela-high e en_US-lessac-medium (padrao).
- coletor/fala.py: texto falado limpo (rodapes, frases cortadas, caixa alta, moedas, transcricoes,
  resumo sem letras); coletor/boletim.py: 30 noticias por pais, Piper como programa separado (GPL),
  Opus 32 kbps, capitulos com inicio/fim de cada noticia, assinatura: reaproveita o audio publicado
  quando nada mudou. Audio NAO entra no Git (.gitignore no ramo dados); fica so no site.
- Workflow: preparar voz + cache dos modelos + gerar boletins, todos podem falhar sem afetar a coleta.
- Amostras (workflow manual amostra-voz.yml): 8 vozes OK, 5x a 27x tempo real.
FIM-sprint-013

sprint-014: feat(app) - PLAYER DO BOLETIM EM AUDIO no app.
- Botoes "Ouvir boletim" (pais aberto) e "Ouvir tudo" (todos em sequencia a partir do aberto),
  com noticias, duracao e horario do boletim; barra fixa: titulo, progresso, anterior/tocar/proxima,
  velocidade 1x-2x, fechar.
- Capitulos (boletim.json): notícia atual pelo tempo; anterior volta ao inicio ou a noticia anterior.
- Media Session: titulo/fonte/pais/icone na tela de bloqueio e fones; play/pause/anterior/proxima/
  avancar/voltar 10 s; posicao atualizada. Audio continua com a tela apagada.
- Cartao da noticia atual destacado e centralizado com a tela ligada.
- Service worker v2: arquivos .ogg vao direto a rede (requisicoes parciais 206 nao cabem no cache).
- Correcao: resumo so aparece se tiver letras (o "-" solto do Planalto).
FIM-sprint-014

sprint-015: perf(audio) - AUDIO POR NOTICIA: so as noticias novas sao narradas.
- Cache por noticia (audio-cache/<pais>/<sha1(voz+texto)>.ogg, Opus 48 kbps): reaproveitado e
  emendado; itens fora do boletim sao apagados (~10 MB). actions/cache com chave por execucao.
- Ambiente do Piper em cache (/tmp/piper); reinstala sozinho se deixar de funcionar (ex.: Ubuntu 26).
- Assinatura v2 forca uma regeneracao completa para encher o cache.
FIM-sprint-015

sprint-016: feat(app) - BOLETIM OFFLINE.
- Ao tocar, o app guarda uma copia completa do boletim (cache gin-audio-v1; so a versao mais recente
  de cada pais). Service worker v3: audio pela rede; sem internet, entrega a copia guardada e
  atende requisicoes parciais (206, Content-Range) para pular noticias offline.
- Info do boletim mostra "offline ✓" quando a versao atual esta guardada.
- Pendente de verificacao: cache por noticia com "N novas, M do cache" (aguarda noticia nova).
FIM-sprint-016

sprint-017: fix(datas) - FUSO HORARIO para paises a leste do Brasil.
- Fuso por nome IANA em fontes/<pais>.json ("fuso"), com horario de verao (zoneinfo); reserva:
  fuso_horas fixo (Termux nao tem a base de fusos; o GitHub tem).
- Noticias so com o dia ganham data_local (dia no fuso de origem); o app mostra esse dia sem
  converter (antes: nota de Israel "05/11" apareceria "04/11" em Brasilia). Historico antigo
  recebe data_local automaticamente.
- TESTE local: data 01/11/2026 em Asia/Jerusalem -> publicado 2026-10-31T22:00:00Z, data_local
  2026-11-01. (1o teste usou data futura e caiu, corretamente, na protecao de data suspeita.)
- Pendente: validar no celular o boletim offline (sprint-016) e o "N novas, M do cache" (sprint-015).
FIM-sprint-017

sprint-018: feat(traducao) - TRADUCAO AUTOMATICA para portugues + boletins AR/US em portugues.
- Modelos do Argos Translate via CTranslate2 + SentencePiece (sem PyTorch); es->pt direto, en->pt;
  remontagem padrao do SentencePiece ("▁" -> espaco); trocas pt-PT -> pt-BR (ex.: "dos Negocios
  Estrangeiros" -> "das Relacoes Exteriores"). Teste real: traducao legivel e util.
- coletor/traduzir.py grava titulo_pt/resumo_pt (ate 80 por execucao, mais recentes primeiro);
  coletar.py: gravar_paginas compartilhada; traducao descartada se a fonte mudar o titulo.
- boletim.py: idioma_audio por pais (AR/US = pt): voz faber, so noticias traduzidas, abertura avisa
  "Noticias traduzidas automaticamente". Workflow: passo de traducao com cache de chave fixa.
FIM-sprint-018

sprint-019: feat(app) - TRADUCAO NA TELA: cartoes de paises traduzidos mostram titulo/resumo em
portugues, selo "traducao automatica" e botao "Ver original"/"Ver traducao"; link leva a fonte
original. Publicado (sprint-018): AR e US com boletim na voz faber, 30 noticias, titulo_pt gravado.
FIM-sprint-019

sprint-020: fix(audio) - noticias traduzidas lidas "so com o titulo" (relato do usuario: EUA).
- Diagnostico no boletim publicado: 5/30 so titulo. Causas: resumo cortado numa frase unica
  (descartado inteiro), rodape traduzido junto ("[...] O Memorando pos-"), transcricoes.
- fala.py: sem frase completa, aproveita o trecho ate a ultima virgula/palavra, sem conectores
  soltos, e fecha com ponto (frase >= 15 caracteres, trecho >= 25). 4 casos reais testados.
- traduzir.py: limpa ANTES de traduzir; transcricao vira "Transcricao completa disponivel na
  fonte oficial."; versao de traducao 2 refaz as traducoes antigas (ate 80 por execucao).
- Interrupcao no meio da escuta (defeito latente): boletim anterior fica publicado por mais uma
  execucao; service worker toca a copia guardada se o site responder 404.
FIM-sprint-020

sprint-021: feat(reino-unido) - REINO UNIDO, 4o pais (ingles; 1o pais a leste do Brasil: Europe/London).
- governo/chancelaria/defesa: feeds Atom de "news and communications" do gov.uk filtrados por orgao
  (10 Downing Street, FCDO, Ministry of Defence); agencia: BBC News (Politics e UK), uso em sites
  incentivado com atribuicao "BBC News" e sem logotipo.
- parlamento: House of Commons Library e House of Lords Library (feeds oficiais). parliament.uk/news
  recusa acesso automatizado (403) e bills.parliament.uk nao tem feed: nao contornado.
- Traducao para portugues e boletim narrado em portugues (idioma_audio pt).
FIM-sprint-021

sprint-022: feat(alemanha) - ALEMANHA, 5o pais (alemao; Europe/Berlin).
- governo: Bundesregierung Pressemitteilungen; chancelaria: Auswaertiges Amt "Pressemitteilungen und
  Reden" (/static/includes/rss/Presse-RSS-Feed.xml, achado na pagina oficial de RSS); defesa: BMVg;
  parlamento: Bundestag hib + Pressemitteilungen; agencia: tagesschau (ARD).
- leitores.py: descompactacao GZIP automatica (cabecalho ou assinatura \x1f\x8b): o BMVg compacta sem
  ser pedido e o XML falhava na 1a posicao. Vale para todas as fontes.
FIM-sprint-022

sprint-023: feat(franca) - FRANCA, 6o pais (frances; Europe/Paris).
- governo: Elysee (feed); chancelaria: diplomatie.gouv.fr (feed SPIP; 403 a partir do celular, teste
  no GitHub); defesa: defense.gouv.fr/actualites (pagina + data na noticia); parlamento: Assemblee
  nationale e Senat (comunicados); agencia: France 24.
- leitores.py: data_do_artigo prefere metadados (article:published_time, datePublished, time datetime,
  com hora); meses por extenso em es/pt/fr/en/de; fuso sem dois-pontos (+0100). 8/8 testes (4 novos e
  4 antigos). Defesa francesa: 13/13 com precisao hora.
FIM-sprint-023

sprint-023 (cont.): LACUNA chancelaria FR. diplomatie.gouv.fr recusa acesso automatizado: HTTP 403 com
identificacao padrao e simples, do celular e do GitHub (4 combinacoes). Decisao do site respeitada (sem
disfarcar o coletor). Fonte removida; politica externa coberta por Elysee e France 24. Reavaliar no futuro.
FIM-sprint-023

sprint-024: fix(coletor) - "ultima publicacao" por fonte usa o HISTORICO quando a leitura nao traz data.
- Fontes com data_no_artigo (ex.: Defesa FR) nao reabrem noticias ja conhecidas; sem data na leitura,
  "ultima" virava "-" e, apos 7 dias, geraria falso alerta de fonte quieta. Agora usa a data do item no
  historico. Teste: fr-defense "ultima 2026-11-02" sem nenhuma busca.
- fr-senat: "Network is unreachable" numa execucao do GitHub foi passageiro (OK no celular em seguida).
FIM-sprint-024

sprint-025: feat(coletor) - TOLERANCIA DE 48 H para falhas passageiras de fonte.
- Motivo: hoje 3 falhas passageiras derrubaram paises inteiros (Cancilleria AR timeout, Senado FR
  "network unreachable", BMVg DE "HTTP 444" = nginx descarta pedidos apos 5 coletas em 1h30).
- Cada fonte guarda ultimo_ok; se falhar mas funcionou ha menos de 48 h, a categoria fica coberta com
  "falha_temporaria" e o pais segue completo. A fonte continua como ERRO no painel (transparencia).
  Mais de 48 h: o pais vira incompleto.
- Teste com falha simulada do BMVg: defesa fontes_ok 0, falha_temporaria 1, completo True.
- Bundeswehr avaliada como 2a fonte de defesa: pagina montada por JavaScript, sem feed (descartada).
FIM-sprint-025

sprint-026: feat(israel) - ISRAEL, 7o pais (fontes em ingles; Asia/Jerusalem) + LEITOR DE TELEGRAM.
- Sites oficiais bloqueiam coletores: gov.il (PMO e MFA) com Cloudflare 403; Knesset e IDF com desafio
  anti-robo (o IDF e a Kan abrem so a partir do GitHub). Nada foi contornado.
- Novo tipo de fonte "telegram": previa publica t.me/s/<canal> (sem conta), so canais oficiais
  verificados; titulo = 1a linha, data exata, sem emojis, anexos e links soltos. Aprovado pelo usuario.
- governo: canal verificado do Estado de Israel; defesa: canal oficial do IDF; agencia: Kan Reka
  (ingles, pagina + data na noticia). Lacunas documentadas: chancelaria e parlamento.
- Ferramenta: workflow explorar.yml (mapear/descobrir/coletar pela rede do GitHub).
FIM-sprint-026

sprint-027: feat(palestina) - PALESTINA, 8o pais (fontes em ingles; Asia/Hebron) + LINHA DE DATA DE AGENCIA.
- agencia: WAFA (english.wafa.ps, pagina + data na noticia; ate 25 por coleta). 42 lidas, 25 datadas.
- leitores.py: data_do_artigo reconhece a linha de data de agencia "CIDADE, November 3, 2026 (WAFA)"
  (so a data de publicacao, nunca uma data citada no texto) e o formato americano "Mes dia, ano".
  Testes: WAFA 3/11 local; Defesa FR e Camara AR inalteradas.
- Lacunas: governo (president.ps 403; palestinecabinet.gov.ps sem resposta), chancelaria (mofa.pna.ps e
  mfae.gov.ps sem resposta/DNS), defesa (AP sem forcas armadas), parlamento (CLP dissolvido em 2018).
  Testado do celular e do GitHub. A WAFA publica na integra as declaracoes oficiais.
FIM-sprint-027

sprint-028: fix(app) - PAISES ESCONDIDOS na tela (relato do usuario: so apareciam BR, AR e US).
- Os 8 paises estavam no app, mas a fileira de botoes rolava para o lado (overflow-x:auto) com a barra
  de rolagem escondida (scrollbar-width:none): alem de "Estados Unidos", tudo ficava fora da tela, sem
  indicio visual. Dados nao eram a causa (no-cache + service worker rede primeiro).
- .chips agora quebra em linhas (flex-wrap: wrap): todos os paises e filtros visiveis. CACHE_APP v4.
- Licao: conferir o app NA TELA ao incluir cada pais, nao so o paises.json publicado.
FIM-sprint-028

sprint-029: feat(china) - CHINA, 9o pais (fontes oficiais em ingles; Asia/Shanghai).
- governo: Conselho de Estado; chancelaria: MFA (notícias principais + atividades do ministro); defesa:
  Ministerio da Defesa Nacional; parlamento: APN (so por http://: o https recusa a criptografia do
  Python; acessivel so pelo GitHub); agencia: Xinhua. Todos os orgaos sao do Estado/Partido.
- leitores.py: DATA NO ENDERECO (Xinhua /AAAAMMDD/, gov.cn /AAAAMM/DD/, fmprc tAAAAMMDD_, /AAAA/MM/DD/,
  APN /AAAA-MM/DD/), validada, so quando o texto do link nao traz data (5/5 testes); DATA PELO ROTULO
  "Time： 2026-11-02 20:06:20" (dois-pontos de largura total; evita datas soltas de outro conteudo).
FIM-sprint-029

sprint-030: feat(el-salvador) - EL SALVADOR, 10o pais (espanhol; America/El_Salvador) + CERTIFICADOS.
- governo: Presidencia (feed; publica pouco no site: ultima 16/10, alerta de fonte quieta correto);
  parlamento: Asamblea Legislativa (pagina /node/ + data na noticia); agencia: Diario El Salvador
  (jornal estatal, feed). Lacunas: chancelaria (rree.gob.sv com Cloudflare 403, celular e GitHub) e
  defesa (faes.gob.sv nao existe mais no DNS).
- leitores.py: CONTEXTO SSL com intermediarios em coletor/certificados/ (verificacao COMPLETA mantida).
  A Asamblea nao envia o intermediario Sectigo OV R36; baixado do endereco oficial (AIA) e verificado
  com openssl contra a raiz Sectigo R46 (OK). Termux nao tem /tmp: usar $TMPDIR.
- Ferramentas descobrir/mapear fazem downloads proprios (sem o contexto SSL); testar pelo coletor.
FIM-sprint-030

sprint-031: fix(traducao) - modelos BAIXADOS DE NOVO a cada pais novo + download cortado no meio.
- Causa: chave do cache = hash de fontes/*.json -> todo pais novo invalidava o cache e rebaixava
  centenas de MB; numa dessas, IncompleteRead (82 de 150 MB) deixou 1 noticia sem traducao (DE e SV).
- traduzir.py: download em arquivo, em blocos, confere o tamanho, ate 4 tentativas; marca NOVO.
- coletar.yml: cache restaurado pela versao mais recente (restore-keys) e salvo SO quando um modelo
  novo foi baixado ou o ambiente foi reinstalado (actions/cache/restore + save condicional).
FIM-sprint-031

sprint-032: pesquisa(kuwait) - KUWAIT ADIADO: fontes oficiais inacessiveis (celular e GitHub, 02/11/2026).
- KUNA (kuna.net.kw, agencia oficial): tempo esgotado nas duas redes; sem canal oficial verificado no
  Telegram. MOFA (mofa.gov.kw) e Diwan Amiri (da.gov.kw): HTTP 403. MOD (mod.gov.kw): conexao encerrada
  sem resposta. Conselho de Ministros (cmgs.gov.kw): abre pelo GitHub, mas em arabe e com pouco conteudo.
- Parlamento: Assembleia Nacional suspensa desde 10/05/2024 por ate 4 anos (Emir e Conselho de Ministros
  assumiram o legislativo; IPU: sem parlamento em funcionamento) -> lacuna estrutural quando o pais entrar.
- Decisao: nao publicar com 1 fonte e 4 lacunas; reavaliar a KUNA mais tarde.
FIM-sprint-032

sprint-033: pesquisa(haiti) - HAITI ADIADO: sem fonte oficial ATUAL acessivel (celular e GitHub, 02/11/2026).
- Governo: Conselho Presidencial de Transicao dissolvido em 07/02/2026; PM Alix Didier Fils-Aime exerce o
  Executivo. Primature: feed parado em 10/02/2025 e "eventos" de dez/2024 (site abandonado).
- MAE (mae.gouv.ht): erro de conexao segura (servidor encerra) nas duas redes. Defesa (defense.gouv.ht)
  e RTNH (rtnh.ht): nomes inexistentes no DNS.
- Parlamento: sem eleicoes desde 2016; 1o turno das gerais marcado para 13/12/2026 (2o turno 21/02/2027).
- Decisao: nao publicar com conteudo de 2024-2025; reavaliar apos as eleicoes de dezembro.
FIM-sprint-033

sprint-034: perf(coleta) - COLETA EM PARALELO para escalar a ~195 paises.
- Medido: coleta ~10 s/pais em sequencia -> 195 paises = ~32 min so na coleta (limite era 30 min).
- Workflow: coleta 10 paises em paralelo (espera de rede; sites diferentes, pausa educada por site
  mantida), traducao 2 e boletins 3 em paralelo (CPU de 4 nucleos); logs por pais exibidos em ordem;
  limite do trabalho 50 min.
- Condicoes de corrida eliminadas: cada pais grava so dados/<pais>/resumo.json e juntar_paises.py
  monta paises.json no final (mantem a ordem dos botoes; preserva pais cuja coleta falhar);
  download de modelo de traducao com trava de arquivo (flock).
FIM-sprint-034

sprint-035: feat(america-do-sul) - CHILE, URUGUAI e PARAGUAI (1a leva com sondar_pais.py) + datas.
- Ferramenta sondar_pais.py (feeds, pastas e datas num relatorio, pelo coletor; opcao sondar no
  explorar.yml). Bloqueios conferidos no celular E no GitHub: 403 geral (gob.cl, minrel, senado.cl,
  camara.cl, mre.gov.py) -> lacunas; senado.gov.py so barra a nuvem -> Camara dos Deputados.
- leitores.py: busca no texto escolhe a 1a data PLAUSIVEL (posicao no texto, ano 2000..ano atual,
  nunca futura): corrigiu "Av. 8 de Octubre 2628" e data de evento futuro (gub.uy). Rotulos em
  espanhol ("Publicado el: 2026-11-02", Camara PY). Regressao WAFA/FR/AR/CN inalterada.
- Radio Uruguay: certificado de outro dominio (*.tnu.com.uy) -> recusado com razao -> lacuna.
FIM-sprint-035

sprint-036: feat(america-do-sul) - PERU, EQUADOR, COLOMBIA, BOLIVIA e VENEZUELA (2 sondagens).
- PE: gob.pe (Presidencia, RREE, MINDEF; data com hora na noticia) + Andina; lacuna parlamento.
- EC: 4 feeds (Presidencia, Cancilleria, Defensa, Asamblea); lacuna agencia (elciudadano.gob.ec fora do DNS).
- CO: Camara (feed) + Senado + Radio Nacional (RTVC); lacunas governo (pagina vazia/JS), chancelaria (403),
  defesa (404). BO: Presidencia + Cancilleria. VE: MPPRE + MINDEFENSA. Lacunas com motivo verificado.
- sondar_pais.py: agrupa enderecos planos (/agencia/noticia-titulo-123.aspx). Comandos resistentes as quedas
  da rede movel: disparo com novas tentativas e so aceita execucao criada DEPOIS do disparo.
FIM-sprint-036

sprint-037: feat(americas) - GUIANA, SURINAME e CANADA + TRADUCAO POR IDIOMA DA FONTE.
- GY: Office of the President, GDF, DPI (feeds). SR: portal gov.sr (holandes; reune os ministerios).
  CA: PM (feed), servico oficial de noticias api.io.canada.ca (dept=departmentofforeignaffairstradeand
  development; parametro publishedDate), Camara dos Comuns, Radio-Canada (frances).
- traduzir.py: cada fonte pode declarar "idioma" (paises multilingues; "pt" nao traduz).
- sondar_pais.py testa o proprio endereco como feed. Mexico adiado para leva propria (gob.mx por
  JavaScript, Senado 403, Camara com certificado invalido, IMER parado em 2023).
FIM-sprint-037

sprint-038: feat(america-central) - GUATEMALA (AGN) e PANAMA; 5 paises ADIADOS.
- GT: AGN (agencia estatal, 50 itens/dia); 4 lacunas (403, sem resposta, congresso sem noticias legiveis).
- PA: Presidencia (pagina + data) e MIRE (feed); defesa = lacuna estrutural (forcas armadas abolidas em
  1990, proibidas pela Constituicao desde 1994); Assembleia com certificado nao verificavel; SERTV sem resposta.
- ADIADOS (sondados pelo GitHub em 03/11/2026): Honduras (so Defesa acessivel), Costa Rica (Presidencia e
  SINART abrem mas sem noticias legiveis; RREE 403; Assembleia sem resposta; defesa estrutural: exercito
  abolido em 1948), Nicaragua (403/DNS), Belize (sem resposta), Mexico (gob.mx por JavaScript; Senado 403).
- Estrategia: seguir para a EUROPA (feeds oficiais mais regulares); casos dificeis em fase posterior.
FIM-sprint-038

sprint-039: feat(europa) - PORTUGAL, ESPANHA, ITALIA, PAISES BAIXOS e BELGICA (1a leva europeia).
- PT sem traducao (portugues original): governo + RTP (pais, politica). ES: Moncloa (7 feeds oficiais) +
  RTVE (data no endereco). IT: governo (feed) + RAI (feed). NL: Tweede Kamer + NOS; rijksoverheid.nl
  testado na hora (feeds.government.nl e feeds.rijksoverheid.nl foram desativados). BE: diplomatie (fr),
  mil.be (nl) e RTBF (fr), com traducao pelo idioma de cada fonte.
- Lacunas com motivo (403, anti-robo perfdrive, sem noticias legiveis, conexao recusada). EFE: HTTP 429.
FIM-sprint-039

sprint-040: feat(europa) - IRLANDA, SUICA, AUSTRIA, DINAMARCA, SUECIA, NORUEGA e FINLANDIA.
- Emissoras publicas em todos (RTE, Swissinfo/SRG, ORF, DR, SVT, NRK, Yle), feeds ou paginas com data.
- IE: Oireachtas (feed). CH: admin.ch e Swissinfo em ingles (pais quadrilingue). AT: Bundeskanzleramt.
  DK: Statsministeriet + Forsvarsministeriet. SE: Regeringen + Riksdagen. NO: Forsvaret + Stortinget.
  FI: so Yle (valtioneuvosto, um.fi e defmin.fi com 403). Idiomas novos: da, sv, nb, fi.
FIM-sprint-040

sprint-041: fix(traducao) - pacotes Argos de DINAMARQUES e FINLANDES com outro formato.
- StopIteration ao carregar (41 falhas: da 30, fi 11): o tokenizador nao se chama sentencepiece.model.
- traduzir.py aceita source.spm, *.spm e *.model; se faltar algo, o erro lista os arquivos do pacote.
FIM-sprint-041

sprint-041 (cont.): pacotes Argos 1.9 de da/fi usam bpe.model (subword-nmt + Moses), nao SentencePiece
("could not parse ModelProto"). traduzir.py ganhou dois separadores (_TokSP e _TokBPE, este como o
BPETokenizer do Argos); ambiente do tradutor com sacremoses e subword-nmt (MIT, Python puro).
FIM-sprint-041

sprint-042: feat(europa-leste) - TCHEQUIA, ESLOVAQUIA, GRECIA, BULGARIA e ROMENIA + DATAS COM PONTOS.
- leitores.py: datas numericas com pontos (02.11.2026, "2. 11. 2026", 2026.11.02.); 6/6 testes, sem regressao.
  Destravou governo e MZV tchecos, governo, MVR e BTA bulgaros.
- CZ: Vlada, MZV, MO (feed), CT24. SK: Vlada (feed), MOSR (feed), STVR (100 itens). GR: PM (feed), ERT.
  BG: governo, MVR, Parlamento (feed), BTA. RO: Agerpres (politica e comunicados; data no endereco).
- ADIADOS: Polonia (gov.pl redireciona, Sejm 403, PAP sem feed, Polskie Radio so podcasts) e Hungria
  (kormany.hu por JavaScript, feed da Defesa sem data legivel, hirado.hu responde HTTP 606).
FIM-sprint-042

sprint-042 (cont.): gr-pm deu 403 na coleta: o primeiroministro.gr so aceita a identificacao "simples"
(a sondagem mostrava "identificacao simples", mas a configuracao ficou com a padrao). Corrigido.
Regra: quando a sondagem indicar "identificacao simples", registrar "identificacao": "simples" na fonte.
Pendente: bg-mfa sem data encontrada nas noticias (15 buscadas).
FIM-sprint-042

sprint-043: feat(europa) - BALTICOS, ISLANDIA, LUXEMBURGO e CHIPRE (fontes incertas testadas na hora).
- Fontes com data na noticia so entram se a 1a noticia tiver data dos ultimos 60 dias; senao, lacuna.
- LV: Saeima + LSM English (+ governo/MFA se recentes). LT: LRT English. EE: Riigikogu. IS: government.is
  (defesa: sem forcas armadas, OTAN). LU: Camara (sessoes). CY: CNA se tiver data. Malta ADIADO (nada utilizavel).
FIM-sprint-043

sprint-044: feat(balcas) - CROACIA, ESLOVENIA, SERVIA, BOSNIA, MONTENEGRO, KOSOVO (+ Macedonia se houver fonte).
- Emissoras publicas: HRT (feed), RTS, RTCG ("03. 11. 2026", gracas as datas com pontos). gov.si (100/dia).
- Fontes incertas testadas na hora (data dos ultimos 60 dias). Albania ADIADA (ATA 403; governo e
  parlamento sem noticias legiveis). Kosovo incluido (governo proprio; reconhecimento internacional parcial).
FIM-sprint-044

sprint-045: manutencao(06/11/2026) - 3 dias depois: 50 paises, 2 incompletos (GB e CL), 20 alertas.
- GB: o Parlamento passou a bloquear coletores em todos os dominios (bibliotecas, comissoes, Hansard: 403).
  Bibliotecas trocadas pelo POST (post.parliament.uk/feed, oficial, publica com menos frequencia).
- CL: prensa.presidencia.cl migrou para presidencia.gob.cl (pagina vazia, JavaScript) -> lacuna governo.
- NO: forsvaret.no sem noticias recentes legiveis (a fonte so via noticias antigas: "401 dias") -> lacuna defesa.
- US: feeds de pauta do Congresso vazios em recesso pos-eleicao (03/11); mantidos, voltam nas sessoes.
- Alertas de 8 a 39 dias: fontes que publicam pouco no proprio site (informacao correta, nao defeito).
FIM-sprint-045

sprint-046: feat(leste-caucaso) - UCRANIA, RUSSIA, BELARUS, MOLDAVIA, TURQUIA, ARMENIA e AZERBAIJAO.
- Fontes oficiais em ingles quando existem (KMU, Rada, Kremlin, TASS, BelTA, MFA turco, Anadolu, PM armenio).
  MID russo com idioma ru. Fontes incertas testadas na hora (60 dias). Georgia ADIADA (tudo 403/sem resposta).
- Os dois lados da guerra (Russia e Ucrania) e de Armenia/Azerbaijao, com as mesmas regras de fonte oficial.
FIM-sprint-046

sprint-047: perf(workflow) - coleta a 48,7 de 50 min: "Preparar voz" levava 35,3 min.
- Causa: o runner nao tem ffmpeg; o apt baixava 71 MB a cada hora (dependencias de video, drivers Intel,
  pocketsphinx...) e o espelho Azure estava a 33,9 kB/s (pocketsphinx sozinho travou 10,7 min).
- ffmpeg estatico do GitHub (BtbN/FFmpeg-Builds) + cache de /tmp/ffmpeg-estatico e /tmp/piper (baixados 1 vez);
  reserva: apt com --no-install-recommends. Medicao: coleta 3,9 min, traducao 1,6 min, boletins 6,8 min.
FIM-sprint-047

sprint-047 (cont.): voz em 0,2 min (era 35,3). Publicacao cancelada apos 10 min em "syncing_files"
(sem concorrencia; tempo-limite padrao da deploy-pages). Site: 114,8 -> 119,9 -> 132 MB em 3 coletas.
deploy-pages com timeout de 20 min; passo "Medir o tamanho do site" (audio x json) antes do envio.
FIM-sprint-047

sprint-048: fix(leitores) - feeds com XML defeituoso (TASS: "undefined entity"; MID: "invalid token").
- _xml_tolerante: XML estrito primeiro (caminho de sempre); so se falhar, converte entidades HTML (&nbsp;
  &mdash;...), escapa & solto e remove caracteres de controle, e tenta de novo. Testado com TASS e MID reais.
- Coleta: 48,7 min -> 6,8 min (ffmpeg estatico em cache). Site: 96 MB (audio 84,6 MB em 58 boletins; json 9,3).
FIM-sprint-048

sprint-048 (cont.): mid.ru/rss devolve pagina de bloqueio do firewall ("Request Rejected"), nao XML;
na sondagem pelo GitHub respondeu (bloqueio intermitente). ru-mid -> lacuna chancelaria.
- _xml_tolerante identifica pagina HTML no lugar do feed e informa o titulo (diagnostico de bloqueios).
- Licao: no comando anterior o teste reprovou mas o envio ocorreu (linha seguinte nao encadeada com &&).
  Regra: teste e envio sempre encadeados com &&.
FIM-sprint-048

sprint-049: fix(china) - Xinhua com 0 itens: a pagina inicial english.news.cn passou a carregar as manchetes
por JavaScript (CN incompleto). Agora: english.news.cn/world/ (ingles, data no endereco /AAAAMMDD/) e
www.news.cn/politics/ (chines, idioma zh, politica interna). Feed RSS antigo parado em 2017.
FIM-sprint-049

sprint-050: feat(asia) - JAPAO, COREIA, INDIA, INDONESIA, VIETNA, TAILANDIA, MALASIA e SINGAPURA (os que tiverem fonte).
- Teste na hora cobre feeds (>=3 itens e algum dos ultimos 60 dias) e paginas; pais sem fonte e adiado sozinho.
- Fontes em ingles: Kantei (ATENCAO: endereco "/105/" = gabinete atual; muda com novo gabinete), Setkab,
  Antara, VietnamPlus, Bernama, MFA Singapura. Malasia: PMO em malaio (ms). Filipinas ADIADA (tudo 403).
FIM-sprint-050

sprint-051: fix(workflow) - publicacao cancelada de novo aos 10 min: a deploy-pages tem TETO FIXO de 10 min
(confirmado no log: valor acima vira o maximo; o timeout de 20 min da sprint-047 nao tinha efeito).
- 1a tentativa com continue-on-error; se nao tiver sucesso (failure OU cancelled), espera 90 s e tenta de novo.
- environment url usa a tentativa que der certo. Dados ficam no ramo dados: publicacao perdida nao perde noticias.
- Pendente: croata e servio sem modelo no Argos (160 falhas sr, 80 hr): Balcas sem traducao desde 03/11.
- Pendente: India adiada (feed do PIB com 20 itens sem data reconhecida).
FIM-sprint-051

sprint-052: feat(app) - GLOBO 3D. globe.gl 2.46.2 (MIT, inclui three.js) + NASA Blue Marble + Natural Earth
1:110m, hospedados em app/vendor (a CSP so permite 'self'; funciona offline; sem dependencia externa).
- app/globo.js independente: paises cobertos em azul, atual em ambar; toque abre o pais (location.hash);
  voa ate o pais do boletim (1 linha em tocarPais); gira sozinho e retoma 45 s apos a ultima mudanca;
  pausa fora da tela/em segundo plano; sem WebGL ou com erro, a area some e o app segue igual.
- Natural Earth marca FR e NO com ISO_A2 = -99: tabela de excecoes por ADM0_A3. Singapura vira marcador.
- Centro do pais por media esferica do contorno principal (vale para quem cruza a linha de data).
- CSP: img-src e worker-src com blob: (three.js). Service worker gin-app-v5 com globo.js.
FIM-sprint-052

sprint-053: feat(app) - SELETOR DE PAIS COM BUSCA. Com 64 paises, os botoes no cabecalho fixo cobriam a tela
inteira (e escondiam o globo e as noticias). Cabecalho em 1 linha: GIN + botao com o pais atual ("Brasil ▾");
categorias numa linha com rolagem lateral. <dialog> nativo com busca sem acento e paises em ordem alfabetica;
mesmo id="paises" (codigo de ativo e de toque inalterado). Service worker gin-app-v6.
FIM-sprint-053

sprint-054: fix(globo) - o pais aberto por padrao (sem escolha) nao ficava em ambar: o globo so focava ao vir
de hash. abrirPais agora avisa o globo (cobre abertura, seletor, toque no globo e Ouvir tudo). GLOBO APROVADO
pelo usuario ("Sensacional") em 08/11/2026. Service worker gin-app-v7.
FIM-sprint-054

sprint-055: feat(traducao) - CROATA, SERVIO, BOSNIO e MACEDONIO pelo OPUS-MT (Helsinki-NLP, opus-mt-sla-en).
- Argos nao tem hr/sr (240 falhas por coleta; Balcas sem traducao desde 03/11).
- Workflow converter-modelo.yml (uso unico): modelo oficial -> CTranslate2 int8 (76 MB; 63 MB compactado),
  publicado na release "modelos-traducao" do repositorio. Conversor atual exige transformers >=4.56 (dtype).
- Marian exige o marcador </s> no fim da frase: sem ele, repeticoes ("Foreign Foreign Minister..."). Com ele,
  4/4 traducoes corretas (croata, servio cirilico, bosnio, montenegrino).
- traduzir.py: pasta_opus (so quando nao ha pacote Argos; download com 4 tentativas, trava e marca NOVO para
  salvar o cache) e _TokOpus (acrescenta </s>). Caminho: hr/sr -> en (OPUS-MT) -> pt (Argos).
FIM-sprint-055

sprint-056: fix(coletor) - a busca de data dentro da noticia ignorava a identificacao da fonte (sempre "padrao").
data_do_artigo(link, ua=None) e o coletor repassa IDENTIDADES[fonte.identificacao]. Sem o parametro, igual a antes.
- leitores.py: meses abreviados em ingles (jan..dec, sept); a pagina do PIB traz "07 NOV 2026 7:24PM by PIB Delhi"
  (rotulo em hindi). ler_data ja usava minusculas. 7/7 formatos (novos e antigos) + PIB real.
- INDIA: Press Information Bureau (feed em hindi; o parametro Lang e ignorado), identificacao simples, data
  buscada na noticia. Lacunas: MEA 403; defesa pelo PIB; parlamento e All India Radio sem noticias legiveis.
FIM-sprint-056
