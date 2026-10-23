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
