# Product Roadmap — FaceFusion Modernizado (Decoupled)

Este roadmap descreve as fases planejadas e executadas de modernização da arquitetura do FaceFusion, migrando de um monólito Gradio para um sistema desacoplado e distribuído.

**Status:** Concluído (10/10 tarefas concluídas)
**Fase Atual:** Fase 3: Ajustes, Higienização e Homologação Final

---

## Filosofia de Desenvolvimento

1. **Desacoplamento Limpo**: Isolamento de processos pesados em threads separadas, deixando a API REST livre para responder requisições e a UI React livre para renderizar.
2. **Offline-First Estrito**: Todo processamento de imagem/vídeo, banco SQLite e dependências devem funcionar localmente sem conexões de rede externas.
3. **Segurança de PII (Mascaramento)**: Higienizar dados sensíveis do host local (como caminhos de pasta pessoal de usuários `/home/user`) em qualquer arquivo exportável.
4. **Resiliência de Rede**: Detecção de porta de socket livre dinamicamente para hospedar o backend sem falhas se a porta padrão estiver ocupada.

---

## Phase 0: Base da Arquitetura & Uploads Dinâmicos

> **Objetivo:** Estabelecer a API FastAPI com escaneamento de portas, mapeamento de banco SQLite com ORM e mecanismo de upload temporário e uploads de mídias estruturados.

- [x] **TASK-001** — Detecção Dinâmica de Porta Livre & Configuração do Frontend
  * **Arquivos**: [run_api.py](file:///home/yurix/Documentos/my-facefusion/run_api.py), [main.py](file:///home/yurix/Documentos/my-facefusion/facefusion/api/main.py)
  * **Ação**: Implementar mecanismo que tenta ligar o Uvicorn na porta 8000. Em caso de ocupação, varre portas sequencialmente até achar uma livre. Grava a URL selecionada em `public/config.json` e `out/config.json`.
  * **Verificação**: Inicialização bem-sucedida da API sem conflito de portas.

- [x] **TASK-002** — Schema do Banco SQLite & Inicialização Lifespan
  * **Arquivos**: [database.py](file:///home/yurix/Documentos/my-facefusion/facefusion/api/database.py)
  * **Ação**: Criar schema `JobModel` contendo campos de status, progresso, caminhos de arquivos físicas e variáveis de processamento. Inicializar a criação de tabelas dinamicamente no hook `lifespan` do FastAPI.
  * **Verificação**: Arquivo `jobs.db` criado na pasta raiz temporária.

- [x] **TASK-003** — Endpoint de Upload e Resolução Segura de Arquivos
  * **Arquivos**: [routes.py](file:///home/yurix/Documentos/my-facefusion/facefusion/api/routes.py)
  * **Ação**: Desenvolver a rota `/api/media/upload` para receber mídias de entrada e salvá-las com nomes exclusivos em UUID na pasta `uploads` do `jobs_path`.
  * **Verificação**: Testar upload via insomnia/curl confirmando retorno de caminhos absolutos e caminhos relativos da URL.

---

## Phase 1: Fila de Tarefas & Worker Run-loop

> **Objetivo:** Implementar o loop de execução de jobs em segundo plano e a exportação higienizada de dados para diagnósticos.

- [x] **TASK-004** — Rota de Submissão de Jobs & Integração ao Core
  * **Arquivos**: [routes.py](file:///home/yurix/Documentos/my-facefusion/facefusion/api/routes.py)
  * **Ação**: Rota `POST /api/jobs` que recebe argumentos, resolve URLs em caminhos físicos do host, cria estrutura local do job em disco e persiste registro com status `queued` no SQLite.
  * **Verificação**: Requisição bem-sucedida retornando ID único e status na fila.

- [x] **TASK-005** — Background Thread Worker
  * **Arquivos**: [worker.py](file:///home/yurix/Documentos/my-facefusion/facefusion/api/worker.py)
  * **Ação**: Criar thread em background (`worker_loop`) acionada na inicialização da API. O worker consome sequencialmente jobs `queued` do SQLite, atualiza para `processing`, executa a engine nativa `job_runner.run_job()` e gerencia status de sucesso/falha.
  * **Verificação**: Recuperação automática de tarefas travadas em `processing` ao reiniciar o servidor, marcando-as como falhas.

- [x] **TASK-006** — Exportador de Diagnósticos com Mascaramento de PII
  * **Arquivos**: [routes.py](file:///home/yurix/Documentos/my-facefusion/facefusion/api/routes.py)
  * **Ação**: Implementar endpoint `/api/diagnostic/export` que reúne logs, dados de hardware e arquivo de configurações. Substituir expressões regulares que contenham caminhos contendo pastas de usuários locais por `/home/user` e `C:\Users\user` antes de compactar em ZIP.
  * **Verificação**: Descompactar ZIP gerado e confirmar anonimização de caminhos pessoais.

---

## Phase 2: Cockpit UI & Comparador Deslizante

> **Objetivo:** Desenvolver o cliente Next.js com painel de métricas da fila, sliders e comparador visual.

- [x] **TASK-007** — Dashboard Cockpit com Acompanhamento de Fila
  * **Arquivos**: [page.tsx](file:///home/yurix/Documentos/my-facefusion/frontend/src/app/page.tsx)
  * **Ação**: Aba dashboard exibindo fila de tarefas atuais em grid, com status atualizando a cada 2 segundos por meio de polling curto, mostrando progresso dinâmico e barra de cores correspondentes.
  * **Verificação**: Cards mudam de cor e tamanho de progresso conforme o worker avança na execução.

- [x] **TASK-008** — Configuração e Envio de Mídias
  * **Arquivos**: [page.tsx](file:///home/yurix/Documentos/my-facefusion/frontend/src/app/page.tsx)
  * **Ação**: Implementar drag and drop de arquivos de origem (Source) e destino (Target). Se for vídeo, permitir o operador reproduzir no player e congelar para envio com recorte (`trim_frame_start`).
  * **Verificação**: Valor de frame capturado no player é repassado no payload de submissão do job.

- [x] **TASK-009** — Comparador Antes/Depois
  * **Arquivos**: [page.tsx](file:///home/yurix/Documentos/my-facefusion/frontend/src/app/page.tsx)
  * **Ação**: Desenvolvimento de um slider interativo que sobrepõe o vídeo original e o resultado processado, permitindo arrastar uma barra divisora vertical de 0 a 100% que ajusta de forma síncrona a área visível de ambos.
  * **Verificação**: Arrastar a barra revela em tempo real os detalhes da sobreposição de faces sem dessincronização visual.

- [x] **TASK-010** — Console de Configurações do Estado & Downloader de Diagnóstico
  * **Arquivos**: [page.tsx](file:///home/yurix/Documentos/my-facefusion/frontend/src/app/page.tsx)
  * **Ação**: Desenvolver abas de configurações para alteração de limites de threads e buffers de processamento e botões para acionar o download do pacote diagnóstico de erros gerado pelo backend.
  * **Verificação**: Arquivo ZIP gerado pelo backend é baixado com sucesso diretamente pelo browser do operador.
