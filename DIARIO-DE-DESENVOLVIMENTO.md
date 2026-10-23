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
