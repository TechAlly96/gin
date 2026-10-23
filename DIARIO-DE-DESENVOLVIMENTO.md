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
