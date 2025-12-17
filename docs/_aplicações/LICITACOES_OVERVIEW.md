# Licitações Techdengue — Overview do Núcleo

> **Propósito do documento**  
> Este é o **Documento 01** (primeiro artefato do repositório) para guiar a construção do núcleo **“Licitações Techdengue”** dentro da **Agno Multi-Agent Platform**.  
> Ele define **visão, personas, fluxos, limites e critérios de sucesso**, servindo como “contrato” do que vamos construir antes de entrar em código.

---

## 1) Visão do produto

Construir um **workflow multiagente** (Agno) que monitora, interpreta e apoia a tomada de decisão sobre **licitações públicas** relacionadas ao ecossistema Techdengue/Aero Engenharia, com foco em:

- **Detecção e monitoramento** (novos editais + mudanças em licitações em andamento).
- **Triagem e priorização** (o que vale atenção, por quê, e qual o risco).
- **Análise técnica/jurídica assistida** (resumo do edital + pontos críticos + checklist de documentos + recomendações).
- **Ação operacional** (criar tarefas, gerar minuta de perguntas/impugnação, rascunhos de propostas, evidências).

O produto é **orientado a fluxo** (Flow Studio) e **auditável** (logs, fontes, rastreabilidade).

---

## 2) Escopo do MVP

### 2.1 O que entra (MVP)

1. **Monitor diário** (ou agendado) em fontes-alvo:
   - PNCP (prioritário), portais/diários definidos, e fontes adicionais plugáveis.
2. **Normalização** de itens de licitação para um schema único (ex.: `LicitacaoItem`).
3. **Triagem** por regras + modelo:
   - palavras-chave, região/órgão, modalidade, prazos, valor estimado, aderência ao portfólio Techdengue.
4. **Resumo e extração de requisitos**:
   - prazos, anexos, critérios de habilitação, exigências técnicas, penalidades, visitas técnicas etc.
5. **Geração de entregáveis**:
   - resumo executivo (1 página),
   - checklist de documentos,
   - lista de dúvidas/perguntas,
   - sinais de risco (com justificativa + evidências).

### 2.2 O que NÃO entra (por enquanto)

- Assinatura/entrega automática de proposta em portais.
- Automação de envio de e-mails/WhatsApp (pode entrar depois via integrações).
- “Scraping agressivo” sem governança (quando necessário, será **plugável e limitado**).

---

## 3) Personas e necessidades

### 3.1 CEO / Direção (decisão rápida)

- Quer saber: **o que apareceu**, **o que mudou**, **o que é prioritário**, **o risco**, **o valor** e **o prazo**.
- Saída ideal: **painel + resumo executivo**.

### 3.2 Comercial / Pré-vendas

- Quer saber: **como abordar**, **se vale entrar**, **qual estratégia**, **qual diferencial**.
- Saída ideal: **oportunidade + ângulo comercial + próximos passos**.

### 3.3 Jurídico / Contratos

- Quer saber: **regras de habilitação**, **cláusulas críticas**, **riscos**, **pontos impugnáveis**.
- Saída ideal: **checklist + matriz de risco + perguntas/impugnação**.

### 3.4 Operações / Delivery

- Quer saber: **escopo real**, **SLA**, **exigências técnicas**, **capacidade**.
- Saída ideal: **extração de requisitos + estimativa + riscos operacionais**.

---

## 4) Fluxos (end-to-end)

### Fluxo A — Monitoramento diário (P0)

1. Coletar itens (PNCP/portais) → normalizar.
2. Deduplicar (hash + fonte + número do processo).
3. Classificar prioridade (score) + risco.
4. Gerar “Digest do Dia”:
   - **Novas licitações** (top 10)
   - **Mudanças relevantes** (top 10)
   - **Alertas de prazo** (janela curta)
5. Registrar tudo com rastreabilidade:
   - fonte, url, data, evidências, decisão.

### Fluxo B — Investigação sob demanda (P0)

1. Usuário cola um edital/URL/PDF.
2. Agente extrai: requisitos, prazos, anexos, critérios.
3. Agente compara com base normativa e padrões internos.
4. Gera pacote:
   - resumo executivo
   - checklist de documentos
   - matriz de risco
   - perguntas e pontos de atenção

### Fluxo C — Preparação de resposta (P1)

1. Selecionar licitação priorizada.
2. Gerar minuta de:
   - e-mail para órgão
   - perguntas técnicas/jurídicas
   - rascunho de impugnação (se aplicável)
3. Criar tarefas (ClickUp/Jira/etc.) via integração.

---

## 5) Modelo mental de “Risco” e “Prioridade”

### 5.1 Prioridade (exemplo de score)

- Aderência ao portfólio (Techdengue / geotecnologia / drones / saúde)
- Região/órgão (estratégico ou recorrente)
- Valor estimado / lote / vigência
- Prazos (janela curta = sobe prioridade)
- Barreiras (exigências impeditivas = baixa prioridade, mas pode virar “risco alto”)

### 5.2 Risco (categorias sugeridas)

- **Jurídico**: cláusulas restritivas, exigências abusivas, prazos incoerentes
- **Operacional**: escopo inviável, SLA irreal, necessidade de equipe/hardware
- **Financeiro**: garantias, multas, pagamentos, reajustes, equilíbrio
- **Reputacional**: órgão conflituoso, histórico de questionamentos

> Importante: risco **não** é “não participar”. Risco é **conhecer e decidir** com base em evidência.

---

## 6) Arquitetura alvo (dentro da Agno)

### 6.1 Domínio

Criar um domínio dedicado (exemplo): `domains/licitacoes/` com:

- `models/` (Pydantic + schemas)
- `services/` (normalização, scoring, dedup, parsing)
- `agents/` (orquestração/roles)
- `tools/` (PNCP, fetch, parser, RAG)
- `flows/` (Flow Studio templates)

### 6.2 Agentes (MVP)

- **Watcher**: monitora fontes e detecta mudanças
- **Triage**: aplica score e define prioridade
- **Analyst**: extrai requisitos e produz entregáveis
- **Compliance**: aplica guardrails, checagens e políticas
- **Orchestrator**: controla o fluxo e registra auditoria

### 6.3 RAG jurídico

Base normativa inicial:

- Lei 14.133/2021 (contratações públicas)
- Regras e orientações internas (padrões de proposta, checklists)
- (Opcional) acórdãos/pareceres selecionados por confiabilidade

---

## 7) Critérios de sucesso (DoD do MVP)

O MVP está “pronto” quando:

1. Um job diário roda e gera um **Digest** consistente.
2. Um usuário consegue colar um edital/URL e receber **resumo + checklist + riscos**.
3. Existe rastreabilidade mínima:
   - fonte, data, evidências, decisão, logs.
4. Guardrails básicos estão ativos (PII, injection, jailbreak, moderação).
5. Há testes mínimos:
   - dedup funciona
   - normalização valida schema
   - scoring retorna categorias válidas

---

## 8) Limites e governança

- **Sem prometer “parecer jurídico”**: sempre “assistência”, com indicação de pontos e evidências.
- **Fontes**: registrar URL + timestamp + (quando possível) hash do documento.
- **Scraping**: só quando necessário e com backoff/limites; preferir APIs oficiais.
- **Segurança**: nunca persistir segredos em logs; integrar com secrets manager.

---

## 9) Como criar este documento no WindSurf (passo a passo)

1. Abra o repositório do Agno no **WindSurf**.
2. Crie a pasta `docs/` na raiz (se ainda não existir).
3. Crie o arquivo: `docs/LICITACOES_OVERVIEW.md`.
4. Cole o conteúdo deste documento.
5. Salve.
6. Rode no terminal (na raiz do repo):
   - `git status`
   - `pre-commit` (se existir) ou `make lint` / `npm run lint` / `ruff` (conforme seu setup)
7. Commit sugerido:
   - `docs(licitacoes): add product overview and MVP scope`

---

## 10) Próximo documento (Documento 02)

**Doc 02 — `docs/SCHEMAS_LICITACOES.md`**  
Vai detalhar os schemas Pydantic/JSON que serão a base do núcleo (itens de licitação, fonte, evidências, scoring e outputs).
