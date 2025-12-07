# WebUI – Plano de Sprints COMPLETO (Baseado em Auditoria Profunda)

**Baseado em:** `MORE_WEBUI_COMPLETE.md` (Relatório de Auditoria 2025-12-07 v2.0)  
**Objetivo:** Transformar WebUI de estado quebrado para production-ready em 6-7 semanas  
**Atualizado:** 2025-12-07 (Sprint 1 Completo)

---

## ✅ SPRINT 1 - COMPLETO (2025-12-07)

**Status:** 100% Completo  
**Commits:** 5 (pushed to main)  
**Documentação:** Ver `SPRINT_1_COMPLETE.md`

**Tasks Completadas:**
- ✅ Task 1.1: RVC Legacy Removal (313 linhas removidas)
- ✅ Task 1.2: Settings Serialization Fix (10 instâncias corrigidas)
- ✅ Task 1.3: fetchJson Timeout (60s default)
- ✅ Task 1.4: Favicon 404 Fix

**Impacto:** 10 erros de console eliminados, -8% código, WebUI estável

---

## CONTEXTO GERAL

### Situação Atual (Análise Técnica)

**Problemas Críticos Encontrados:**

- [x] **Task 0.1:** Corrigir `this.api is not a function` (8 ocorrências) ✅ COMPLETO
  - **Arquivo:** `app/webui/assets/js/app.js`
  - **Linhas:** 2895, 2922, 2941, 2990, 3034, 3067, 3100, 3150
  - **Ação:** Substituir `this.api()` por `this.fetchJson()` em todas as 8 funções:
    ```javascript
    // ANTES:
    const response = await this.api('/training/inference/synthesize', {...});
    
    // DEPOIS:
    const result = await this.fetchJson('/training/inference/synthesize', {...});
    ```
  - **Tempo estimado:** 30 min
  - **Validação:** Clicar em "Sintetizar" não deve dar erro no console

- [ ] **Task 0.2:** Verificar se endpoint `/training/inference/synthesize` existe no backend
  - **Arquivo:** `app/training_api.py`
  - **Ação:** 
    ```bash
    grep -n "synthesize" app/training_api.py
    curl -X POST http://localhost:8005/training/inference/synthesize \
      -H "Content-Type: application/json" \
      -d '{"checkpoint":"train/output/checkpoints/best_model.pt","text":"teste"}'
    ```
  - **Se não existir:** Implementar endpoint que:
    1. Carrega checkpoint XTTS-v2 do path especificado
    2. Sintetiza áudio com o texto fornecido
    3. Retorna `{"audio_url": "/static/inference_output.wav"}`
  - **Tempo estimado:** 1-2h (se precisar implementar)
  - **Validação:** curl retorna 200 OK com JSON válido

- [ ] **Task 0.3:** Melhorar mensagem de erro
  - **Arquivo:** `app/webui/assets/js/app.js` linha 3168
  - **Ação:**
    ```javascript
    } catch (error) {
        console.error('❌ Error running inference:', error);
        const userMessage = error.message || 'Erro desconhecido';
        this.showToast(`Síntese falhou: ${userMessage}`, 'danger');
    }
    ```
  - **Tempo estimado:** 10 min
  - **Validação:** Erro mostra mensagem detalhada (ex: "HTTP 500", "Checkpoint not found")

- [ ] **Task 0.4:** Adicionar spinner de loading
  - **Arquivos:** `app/webui/index.html` + `app/webui/assets/js/app.js`
  - **Ação:**
    1. HTML: Adicionar spinner após botão "Sintetizar"
       ```html
       <button type="submit" class="btn btn-success" id="btn-synthesize">
           <i class="bi bi-play-fill"></i> Sintetizar
       </button>
       <div class="spinner-border spinner-border-sm ms-2" id="synthesis-spinner" style="display:none;"></div>
       ```
    2. JS: Mostrar/ocultar spinner
       ```javascript
       async runInference() {
           const spinner = document.getElementById('synthesis-spinner');
           const btn = document.getElementById('btn-synthesize');
           
           spinner.style.display = 'inline-block';
           btn.disabled = true;
           
           try {
               // ... síntese
           } finally {
               spinner.style.display = 'none';
               btn.disabled = false;
           }
       }
       ```
  - **Tempo estimado:** 20 min
  - **Validação:** Spinner aparece durante síntese e desaparece após

**Critério de Sucesso Sprint 0:**
✅ Usuário consegue sintetizar áudio sem erro  
✅ Feedback visual (spinner) durante processamento  
✅ Mensagens de erro são úteis (não genéricas)

---

## Sprint 1 – Correções Críticas de Infraestrutura ✅ COMPLETO
**Duração:** 2 horas (2025-12-07)  
**Meta:** Estabilizar integrações e resolver débitos técnicos críticos  
**Status:** 100% Completo - Ver `SPRINT_1_COMPLETE.md`

### Tasks Executadas:

- [x] **Task 1.1:** Remover código legado RVC ✅
  - Removido: Seção HTML (95 linhas) + Modal (18 linhas) + JS (200 linhas)
  - Eliminado: 8 erros 404 de endpoints `/rvc-models/*`
  - Commits: f94cf1f, 1176981

- [x] **Task 1.2:** Corrigir Settings object serialization ✅
  - Corrigido: 10 instâncias `settings['key']` → `settings.key`
  - Endpoints funcionando: `/admin/stats`, `/health`, `/admin/cleanup`
  - Commit: 607a9ff

- [x] **Task 1.3:** Adicionar timeout em requests HTTP ✅
  - Implementado: AbortController com 60s default
  - Proteção: 100% das chamadas `fetchJson()`
  - Commit: 2adc08c

- [x] **Task 1.4:** Corrigir favicon 404 ✅
  - Adicionado: `<link rel="icon" href="data:,">`
  - Eliminado: 1 erro 404 de `/favicon.ico`
  - Commit: 0a8081c

**Critério de Sucesso Sprint 1:**
✅ Código morto removido (RVC legacy eliminado)  
✅ Requests longos não travam a UI (timeout implementado)  
✅ Settings endpoint funcional (dict→attr fix)  
✅ Console limpo (10 erros eliminados)

---

## Sprint 1 (ORIGINAL - Descontinuado)
**NOTA:** O Sprint 1 original foi substituído pelo Sprint 1 executado acima.
Tasks originais movidas para Sprint 2-3 conforme necessário.

<details>
<summary>Ver tasks originais do Sprint 1 (arquivado)</summary>

- [ ] **Task 1.1 (ORIGINAL):** Decidir destino dos módulos ES6 não utilizados
  - **Arquivos:** `app/webui/assets/js/modules/training.js`, `modules/utils.js`
  - **Decisão necessária:** 
    - **Opção A:** Remover `modules/` (código morto) - **RECOMENDADO**
    - **Opção B:** Migrar `app.js` para usar módulos ES6 + bundler
  - **Se Opção A:**
    ```bash
    rm -rf app/webui/assets/js/modules/
    ```
  - **Se Opção B:**
    - Instalar Vite: `npm install vite`
    - Converter `app.js` para imports ES6
    - Atualizar `index.html` para carregar bundle
  - **Tempo estimado:** 1h (Opção A) ou 8h (Opção B)
  - **Validação:** Não há código duplicado/morto

- [ ] **Task 1.2:** Adicionar timeout em requests HTTP
  - **Arquivo:** `app/webui/assets/js/app.js` linha 511 (fetchJson)
  - **Ação:**
    ```javascript
    async fetchJson(url, options = {}) {
        const controller = new AbortController();
        const timeoutMs = options.timeout || 60000; // 60s default
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: { ...options.headers }
            });
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                // ... tratamento de erro existente
            }
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`Timeout: operação excedeu ${timeoutMs/1000}s`);
            }
            throw error;
        }
    }
    ```
  - **Tempo estimado:** 1h
  - **Validação:** Request lento (>60s) retorna erro de timeout

- [ ] **Task 1.3:** Validar paths de checkpoints
  - **Arquivo:** `app/webui/assets/js/app.js` linha 3139
  - **Problema:** Path relativo `train/output/checkpoints/best_model.pt` pode não resolver no backend
  - **Ação:** Testar e documentar se backend espera path relativo ou absoluto
  - **Validação no backend:**
    ```python
    # app/training_api.py - endpoint synthesize
    checkpoint_path = Path(request.checkpoint)
    if not checkpoint_path.is_absolute():
        checkpoint_path = Path.cwd() / checkpoint_path
    
    if not checkpoint_path.exists():
        raise HTTPException(404, f"Checkpoint não encontrado: {checkpoint_path}")
    ```
  - **Tempo estimado:** 1h
  - **Validação:** Inferência funciona com checkpoints em `/train/output/checkpoints/`

- [ ] **Task 1.4:** Adicionar handlers globais de erro
  - **Arquivo:** `app/webui/assets/js/app.js` (final do arquivo)
  - **Ação:**
    ```javascript
    window.addEventListener('unhandledrejection', (event) => {
        console.error('❌ Unhandled Promise Rejection:', event.reason);
        app.showToast('Erro inesperado: ' + (event.reason?.message || event.reason), 'danger');
        event.preventDefault(); // Evita log duplicado
    });
    
    window.addEventListener('error', (event) => {
        // Já existe filter para erros de extensão (INT-05)
        if (event.message.includes('Extension context')) return;
        
        console.error('❌ Unhandled Error:', event.error);
        app.showToast('Erro crítico: ' + event.message, 'danger');
    });
    ```
  - **Tempo estimado:** 30 min
  - **Validação:** Erros não tratados mostram toast em vez de apenas aparecer no console

**Critério de Sucesso Sprint 1:**
✅ Código morto removido ou módulos ES6 totalmente adotados  
✅ Requests longos não travam a UI (timeout)  
✅ Checkpoints carregam corretamente do `/train`  
✅ Erros inesperados são capturados e mostrados ao usuário

</details>

---

## Sprint 2 – Training Integration ✅ COMPLETO
**Duração:** 2 horas (2025-12-07)  
**Meta:** Garantir que WebUI enxerga tudo em `/train` via volume Docker  
**Status:** 100% Completo

**NOTA:** Melhorias de UX e Testes serão tratados em sprints dedicados (Sprint 4 e 5)

### Tasks:

- [x] **Task 2.1:** Validar volume Docker `/train` ✅
  - **Resultado:** Validado - 6 checkpoints encontrados (28GB total)
  - **Commit:** Parte do Sprint 2 (13927f0)

- [x] **Task 2.2:** Melhorar lista de checkpoints na WebUI ✅
  - **Resultado:** Já implementado - mostra epoch, data e tamanho
  - **Validação:** Interface funcional, nenhuma mudança necessária
  - **Commit:** Parte do Sprint 2 (13927f0)

- [x] **Task 2.3:** Implementar player de samples na WebUI ✅
  - **Resultado:** Já implementado - 4 samples reproduzíveis
  - **Validação:** Player funcional com controles HTML5
  - **Commit:** Parte do Sprint 2 (13927f0)

- [x] **Task 2.4:** Substituir input hardcoded por dropdown dinâmico ✅
  - **Arquivo:** `app/webui/index.html` linha 768, `app/webui/assets/js/app.js`
  - **Resultado:** Dropdown populado via `/training/datasets` endpoint
  - **Funcionalidade:** Mostra nome, arquivos e duração de cada dataset
  - **Commit:** 13927f0

**Critério de Sucesso Sprint 2:**
✅ WebUI enxerga checkpoints via volume Docker (6 encontrados)  
✅ Lista de checkpoints mostra métricas (tamanho, época, data)  
✅ Player de samples funcional (4 samples reproduzíveis)  
✅ Datasets selecionáveis via dropdown (elimina erros de digitação)

---

## Sprint 3 – Observability & Monitoring ✅ COMPLETO
**Duração:** 2 horas (2025-12-07)  
**Meta:** Dashboards em tempo real para status e progresso de treinamento  
**Status:** 100% Completo

### Tasks:

- [x] **Task 3.1:** Enhanced training status dashboard ✅
  - **Arquivo:** `app/webui/index.html` linhas 813-825
  - **Resultado:** Card dinâmico com color-coded headers
    - idle = secondary (cinza)
    - training = primary (azul)
    - completed = success (verde)
    - failed = danger (vermelho)
  - **Commit:** cb9ead0

- [x] **Task 3.2:** Real-time status polling mechanism ✅
  - **Arquivo:** `app/webui/assets/js/app.js`
  - **Resultado:** Polling a cada 5 segundos via `/training/status`
  - **Funcionalidades:**
    - Animated progress bar durante training
    - Badges com epoch/loss/progress
    - TensorBoard link button quando ativo
    - Auto-reload de checkpoints/samples ao completar
  - **Commit:** cb9ead0

- [x] **Task 3.3:** Training logs display ✅
  - **Resultado:** Já implementado anteriormente
  - **Localização:** Card "Training Logs" com terminal-style viewer
  - **Validação:** Logs atualizados via polling
  - **Commit:** cb9ead0

- [x] **Task 3.4:** Operation feedback improvements ✅
  - **Arquivo:** `app/webui/assets/js/app.js` - `startTraining()` e `stopTraining()`
  - **Resultado:**
    - Loading spinners nos botões Start/Stop
    - Disabled states durante operações
    - Enhanced toast messages com detalhes de erro
    - Restauração de estado em caso de erro
  - **Commit:** cb9ead0

**Critério de Sucesso Sprint 3:**
✅ Dashboard mostra status em tempo real (estado, epoch, loss, progress)  
✅ Link direto para TensorBoard quando treinamento ativo  
✅ Logs de treinamento visíveis e atualizados em tempo real  
✅ Feedback claro em todas as operações (spinners e mensagens)

---

## Sprint 3 – Observabilidade e UX de Treinamento (DESCONTINUADO)
**NOTA:** Esta seção foi substituída pelo Sprint 3 executado acima.
Tasks originais foram implementadas ou movidas para outros sprints.

<details>
<summary>Ver tasks originais (descontinuadas)</summary>

### Tasks:

- [ ] **Task 3.1:** Implementar dashboard de status de treinamento
  - **Arquivo:** `app/webui/index.html` (topo da aba Training)
  - **Ação:** Adicionar card de status
    ```html
    <div class="card bg-primary text-white mb-3" id="training-status-card" style="display:none;">
        <div class="card-body">
            <h5>
                <i class="bi bi-cpu"></i> Treinamento em Andamento
                <button class="btn btn-sm btn-light float-end" onclick="app.stopTraining()">
                    <i class="bi bi-stop-circle"></i> Parar
                </button>
            </h5>
            <div class="row mt-3">
                <div class="col-md-2">
                    <strong>Época:</strong>
                    <span id="training-epoch">-/-</span>
                </div>
                <div class="col-md-2">
                    <strong>Loss:</strong>
                    <span id="training-loss">-</span>
                </div>
                <div class="col-md-2">
                    <strong>VRAM:</strong>
                    <span id="training-vram">-</span>
                </div>
                <div class="col-md-3">
                    <strong>Tempo Decorrido:</strong>
                    <span id="training-time">-</span>
                </div>
                <div class="col-md-3">
                    <a href="http://localhost:6006" target="_blank" class="btn btn-light btn-sm w-100">
                        📊 Abrir TensorBoard
                    </a>
                </div>
            </div>
            <div class="progress mt-3" style="height: 25px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     id="training-progress" style="width: 0%">
                    0%
                </div>
            </div>
        </div>
    </div>
    ```
  - **Tempo estimado:** 3h
  - **Validação:** Card aparece quando treinamento está ativo

- [ ] **Task 3.2:** Implementar polling de status
  - **Arquivo:** `app/webui/assets/js/app.js`
  - **Ação:** Atualizar `checkTrainingStatus()` para atualizar UI
    ```javascript
    async checkTrainingStatus() {
        const status = await this.fetchJson('/training/status');
        
        const statusCard = document.getElementById('training-status-card');
        
        if (status.is_training) {
            statusCard.style.display = 'block';
            document.getElementById('training-epoch').textContent = 
                `${status.current_epoch}/${status.total_epochs}`;
            document.getElementById('training-loss').textContent = 
                status.current_loss?.toFixed(4) || '-';
            document.getElementById('training-vram').textContent = 
                `${status.vram_used_gb?.toFixed(1) || '-'} GB`;
            
            const progress = (status.current_epoch / status.total_epochs * 100);
            document.getElementById('training-progress').style.width = `${progress}%`;
            document.getElementById('training-progress').textContent = `${progress.toFixed(0)}%`;
        } else {
            statusCard.style.display = 'none';
        }
    }
    ```
  - **Polling:**
    ```javascript
    startTrainingStatusPolling() {
        this.trainingPollInterval = setInterval(() => {
            this.checkTrainingStatus();
        }, 5000); // A cada 5s
    }
    
    stopTrainingStatusPolling() {
        if (this.trainingPollInterval) {
            clearInterval(this.trainingPollInterval);
            this.trainingPollInterval = null;
        }
    }
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Status atualiza a cada 5s durante treinamento

- [ ] **Task 3.3:** Adicionar logs de treinamento na UI
  - **Arquivo:** `app/webui/index.html`
  - **Ação:** Adicionar terminal de logs
    ```html
    <div class="card mt-3">
        <div class="card-header bg-dark text-white">
            <i class="bi bi-terminal"></i> Logs de Treinamento
            <button class="btn btn-sm btn-outline-light float-end" onclick="app.clearTrainingLogs()">
                Limpar
            </button>
        </div>
        <div class="card-body p-0">
            <pre id="training-logs" class="bg-dark text-light p-3 m-0" 
                 style="max-height: 300px; overflow-y: auto; font-size: 0.85rem;">
                Aguardando início do treinamento...
            </pre>
        </div>
    </div>
    ```
  - **Backend:** Implementar endpoint `GET /training/logs` que retorna últimas 100 linhas
  - **Tempo estimado:** 3h
  - **Validação:** Logs aparecem em tempo real (via polling ou WebSocket)

- [ ] **Task 3.4:** Melhorar feedback de progresso
  - **Arquivos:** Todos os forms de training
  - **Ação:** Para cada operação assíncrona (download, segment, transcribe, train):
    1. Desabilitar botão durante execução
    2. Mostrar spinner
    3. Atualizar texto do botão (ex: "Baixando..." / "Segmentando..." / "Treinando...")
    4. Reabilitar botão após conclusão ou erro
  - **Tempo estimado:** 2h
  - **Validação:** Usuário sempre sabe o que está acontecendo

**Critério de Sucesso Sprint 3:**
✅ Dashboard mostra status em tempo real (época, loss, VRAM)  
✅ Link direto para TensorBoard (http://localhost:6006)  
✅ Logs de treinamento visíveis na UI  
✅ Feedback claro em todas as operações (loading states)

</details>

---

## Sprint 4 – Melhorias de UX (User Experience) 🎨
**Duração:** 1 semana  
**Meta:** Melhorar feedback visual e experiência do usuário em todas as operações

**NOTA:** Sprint focado exclusivamente em UX, conforme solicitado pelo usuário.

### Tasks:

- [ ] **Task 4.1:** Adicionar spinners em todas operações longas
  - **Arquivos afetados:**
    - `app/webui/assets/js/app.js` - todas as funções async
    - `app/webui/index.html` - adicionar estrutura de spinner aos botões
  - **Operações a melhorar:**
    - `synthesize()` ✅ - já tem spinner (Sprint 0)
    - `uploadAudio()` - adicionar spinner durante upload
    - `downloadYouTube()` - spinner + progress bar
    - `segmentAudio()` - spinner durante processamento
    - `transcribeAudio()` - spinner + tempo estimado
    - `createVoiceProfile()` - spinner + "Criando perfil..."
  - **Padrão de implementação:**
    ```javascript
    // HTML
    <button class="btn btn-primary">
        <span class="btn-icon"><i class="bi bi-play"></i></span>
        <span class="btn-text">Processar</span>
        <span class="spinner-border spinner-border-sm btn-spinner d-none"></span>
    </button>
    
    // JavaScript
    async myOperation() {
        const btn = document.getElementById('my-btn');
        const icon = btn.querySelector('.btn-icon');
        const text = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.btn-spinner');
        
        btn.disabled = true;
        icon.classList.add('d-none');
        spinner.classList.remove('d-none');
        text.textContent = 'Processando...';
        
        try {
            await this.doWork();
            this.showToast('Sucesso!', 'success');
        } catch (error) {
            this.showToast('Erro: ' + error.message, 'danger');
        } finally {
            btn.disabled = false;
            icon.classList.remove('d-none');
            spinner.classList.add('d-none');
            text.textContent = 'Processar';
        }
    }
    ```
  - **Tempo estimado:** 3h
  - **Validação:** Todos os botões mostram spinner durante operação

- [ ] **Task 4.2:** Melhorar mensagens de erro (user-friendly)
  - **Ação:** Traduzir e humanizar mensagens de erro do backend
  - **Exemplo de mapeamento:**
    ```javascript
    const ERROR_MESSAGES = {
        'Connection refused': 'Não foi possível conectar ao servidor. Verifique se está rodando.',
        'timeout': 'A operação demorou muito. Tente novamente.',
        '404': 'Recurso não encontrado',
        '500': 'Erro interno do servidor. Consulte os logs.',
        'Network error': 'Sem conexão com a internet',
    };
    
    formatError(error) {
        for (const [key, msg] of Object.entries(ERROR_MESSAGES)) {
            if (error.message.includes(key)) return msg;
        }
        return error.message; // fallback
    }
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Erros mostram mensagens compreensíveis para usuários

- [ ] **Task 4.3:** Adicionar progress bars (uploads/downloads)
  - **Operações:** Upload de áudio, download do YouTube
  - **Implementação:**
    ```html
    <div class="progress mt-2" id="upload-progress" style="display:none;">
        <div class="progress-bar progress-bar-striped progress-bar-animated" 
             role="progressbar" style="width: 0%"></div>
    </div>
    ```
    ```javascript
    async uploadAudio(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const xhr = new XMLHttpRequest();
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                this.updateProgress('upload-progress', percent);
            }
        };
        // ... resto da implementação
    }
    ```
  - **Tempo estimado:** 4h
  - **Validação:** Barra de progresso funcional em uploads

- [ ] **Task 4.4:** Toasts informativos (não só erros)
  - **Ação:** Adicionar toasts de sucesso para operações importantes
  - **Operações a adicionar toast:**
    - Áudio sintetizado com sucesso
    - Checkpoint carregado
    - Perfil de voz criado
    - Dataset validado
    - Configuração salva
  - **Exemplo:**
    ```javascript
    this.showToast('✅ Checkpoint carregado com sucesso', 'success');
    this.showToast('ℹ️ Processando... Aguarde', 'info');
    this.showToast('⚠️ VRAM baixa detectada', 'warning');
    ```
  - **Tempo estimado:** 1h
  - **Validação:** Usuário recebe feedback positivo das ações

- [ ] **Task 4.5:** Validação de formulários com feedback inline
  - **Ação:** Adicionar validação client-side antes de enviar ao backend
  - **Campos a validar:**
    - Training: Dataset obrigatório, epochs > 0
    - Voice Clone: Mínimo 3 áudios
    - Synthesis: Texto não vazio
  - **Implementação:**
    ```html
    <input type="number" class="form-control" id="training-epochs" required min="1">
    <div class="invalid-feedback">
        Número de épocas deve ser maior que zero
    </div>
    ```
    ```javascript
    validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return false;
        }
        return true;
    }
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Formulários mostram erros antes de submeter

**Critério de Sucesso Sprint 4:**
✅ Todas operações assíncronas têm spinner  
✅ Mensagens de erro são compreensíveis  
✅ Progress bars funcionam em uploads/downloads  
✅ Toasts mostram sucesso e não só erros  
✅ Validação inline previne erros de input

---

## Sprint 5 – Testes Automatizados 🧪 ✅ COMPLETO
**Duração:** 6 horas (2025-12-07)  
**Meta:** Garantir qualidade com testes automatizados  
**Status:** 100% Completo

**NOTA:** Sprint focado exclusivamente em testes, conforme solicitado pelo usuário.

### Tasks Executadas:

- [x] **Task 5.1:** Configurar Jest para testes unitários ✅
  - `package.json` com Jest 29.7.0
  - `jest.config.js` com threshold 70%
  - `tests/setup.js` com mocks Bootstrap/fetch
  - Commit: aa940fd

- [x] **Task 5.2:** Testes unitários (70%+ coverage) ✅
  - `tests/app.test.js`: 15 testes (formatError, showToast, validation)
  - `tests/api.test.js`: 11 testes (fetchJson, timeout, AbortController)
  - Total: 26 unit tests passing
  - Coverage: >70% nas funções críticas
  - Commit: aa940fd

- [x] **Task 5.3:** Configurar Playwright (E2E) ✅
  - `playwright.config.js` completo
  - Base URL configurada (localhost:8005)
  - Reporter HTML + artifacts
  - Commit: 051ccd3

- [x] **Task 5.4:** Testes E2E críticos ✅
  - `e2e/training.spec.js`: 7 testes (navigation, datasets, validation)
  - `e2e/jobs.spec.js`: 9 testes (form validation, character counter)
  - Total: 16 E2E tests
  - Commit: 051ccd3

- [x] **Task 5.5:** CI/CD com GitHub Actions ✅
  - `.github/workflows/test.yml` criado
  - 3 jobs: unit-tests, e2e-tests, lint
  - Codecov integration
  - Docker compose para E2E
  - Commit: 051ccd3

**Critério de Sucesso Sprint 5:**
✅ Jest configurado e rodando  
✅ Testes unitários com >70% coverage (26 tests)  
✅ Playwright configurado  
✅ Testes E2E cobrem fluxos críticos (16 tests)  
✅ CI/CD automático no GitHub Actions  
✅ Artifacts e reports configurados

---

## Sprint 5 – Testes Automatizados 🧪 (ORIGINAL - Substituído)

### Tasks:

- [ ] **Task 5.1:** Configurar Jest para testes unitários JavaScript
  - **Arquivos:**
    - `package.json` (adicionar dependências)
    - `jest.config.js` (configuração)
    - `.gitignore` (node_modules, coverage)
  - **Ação:**
    ```bash
    cd app/webui
    npm init -y
    npm install --save-dev jest @testing-library/dom @testing-library/jest-dom
    ```
  - **jest.config.js:**
    ```javascript
    module.exports = {
      testEnvironment: 'jsdom',
      collectCoverageFrom: [
        'assets/js/**/*.js',
        '!assets/js/vendor/**'
      ],
      coverageThreshold: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70
        }
      }
    };
    ```
  - **Tempo estimado:** 2h
  - **Validação:** `npm test` executa sem erros

- [ ] **Task 5.2:** Escrever testes unitários (70%+ coverage)
  - **Arquivos de teste:**
    - `app/webui/tests/app.test.js`
    - `app/webui/tests/api.test.js`
    - `app/webui/tests/utils.test.js`
  - **Casos de teste críticos:**
    ```javascript
    // tests/app.test.js
    describe('App Object', () => {
      test('formatError traduz erros corretamente', () => {
        expect(app.formatError({message: 'Connection refused'}))
          .toBe('Não foi possível conectar ao servidor...');
      });
      
      test('showToast adiciona classes corretas', () => {
        app.showToast('Test', 'Message', 'success');
        const toast = document.getElementById('toast');
        expect(toast.classList.contains('bg-success')).toBe(true);
      });
      
      test('validateForm retorna false para campos vazios', () => {
        // Mock form validation
      });
    });
    
    // tests/api.test.js
    describe('API Client', () => {
      test('fetchJson adiciona timeout', async () => {
        // Mock fetch with timeout
      });
      
      test('fetchJson lança erro em 404', async () => {
        // Mock 404 response
      });
    });
    ```
  - **Tempo estimado:** 8h
  - **Validação:** `npm run test:coverage` mostra >70%

- [ ] **Task 5.3:** Configurar Playwright para testes E2E
  - **Ação:**
    ```bash
    npm init playwright@latest
    ```
  - **playwright.config.js:**
    ```javascript
    module.exports = {
      testDir: './e2e',
      timeout: 30000,
      use: {
        baseURL: 'http://localhost:8005',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure'
      },
      projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
      ],
    };
    ```
  - **Tempo estimado:** 2h
  - **Validação:** `npx playwright test --list` mostra testes

- [ ] **Task 5.4:** Escrever testes E2E críticos
  - **Arquivos:**
    - `app/webui/e2e/training.spec.js`
    - `app/webui/e2e/synthesis.spec.js`
    - `app/webui/e2e/jobs.spec.js`
  - **Casos de teste:**
    ```javascript
    // e2e/training.spec.js
    test('deve carregar página de training', async ({ page }) => {
      await page.goto('/');
      await page.click('text=Training');
      await expect(page.locator('#training-dataset')).toBeVisible();
    });
    
    test('deve validar formulário de training', async ({ page }) => {
      await page.goto('/');
      await page.click('text=Training');
      await page.click('#btn-start-training');
      // Deve mostrar mensagem de validação
      await expect(page.locator('.invalid-feedback')).toBeVisible();
    });
    
    test('deve carregar checkpoints', async ({ page }) => {
      await page.goto('/');
      await page.click('text=Training');
      // Aguardar requisição
      await page.waitForResponse(resp => 
        resp.url().includes('/training/checkpoints') && resp.status() === 200
      );
      await expect(page.locator('#checkpoint-list')).not.toBeEmpty();
    });
    
    // e2e/synthesis.spec.js
    test('deve criar job de síntese', async ({ page }) => {
      await page.goto('/');
      await page.fill('#job-text', 'Teste de síntese');
      await page.selectOption('#job-source-language', 'pt');
      await page.click('#btn-create-job');
      await expect(page.locator('.toast')).toContainText('Job criado');
    });
    ```
  - **Tempo estimado:** 6h
  - **Validação:** Todos os testes E2E passam

- [ ] **Task 5.5:** Adicionar CI/CD com GitHub Actions
  - **Arquivo:** `.github/workflows/test.yml`
  - **Ação:**
    ```yaml
    name: Tests
    
    on: [push, pull_request]
    
    jobs:
      unit-tests:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: actions/setup-node@v3
            with:
              node-version: '18'
          - name: Install dependencies
            working-directory: app/webui
            run: npm ci
          - name: Run unit tests
            working-directory: app/webui
            run: npm test -- --coverage
          - name: Upload coverage
            uses: codecov/codecov-action@v3
            
      e2e-tests:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: actions/setup-node@v3
          - name: Install Playwright
            working-directory: app/webui
            run: npx playwright install --with-deps
          - name: Start server
            run: docker-compose up -d
          - name: Wait for server
            run: npx wait-on http://localhost:8005
          - name: Run E2E tests
            working-directory: app/webui
            run: npx playwright test
          - name: Upload test results
            if: always()
            uses: actions/upload-artifact@v3
            with:
              name: playwright-report
              path: app/webui/playwright-report/
    ```
  - **Tempo estimado:** 3h
  - **Validação:** CI passa em cada push

**Critério de Sucesso Sprint 5:**
✅ Jest configurado e rodando  
✅ Testes unitários com >70% coverage  
✅ Playwright configurado  
✅ Testes E2E cobrem fluxos críticos  
✅ CI/CD automático no GitHub Actions  
✅ Badge de coverage no README

---

## Sprint 6 – Bugs Críticos de Backend/Training 🐛
**Duração:** 1 semana  
**Meta:** Corrigir memory leaks e bugs críticos no sistema de treinamento  
**Prioridade:** ALTA (afeta estabilidade do sistema)

### 🚨 BUG CRÍTICO: Memory Leak no Training Loop

**Descoberto em:** 2025-12-07 18:01  
**Severidade:** CRÍTICA  
**Impacto:** Sistema consome toda RAM disponível e trava após ~5 épocas

**Sintomas:**
```
2025-12-07 18:01:03,435 - INFO - 💾 Checkpoint salvo: train/output/checkpoints/checkpoint_epoch_5.pt
2025-12-07 18:01:05,958 - INFO - 🧹 Liberando VRAM para geração de samples...
2025-12-07 18:01:06,552 - INFO -    ✅ Modelo de treinamento movido para CPU
2025-12-07 18:01:06,583 - INFO -    📝 Texto do metadata: 'ah, agora eu estou me ouvindo na tv, entendi. fica...'
2025-12-07 18:01:06,583 - INFO - 🎤 Gerando sample de áudio (subprocesso CPU)...
2025-12-07 18:01:06,583 - INFO -    Época: 5
2025-12-07 18:01:06,583 - INFO -    Referência: audio_00001.wav
2025-12-07 18:01:06,583 - INFO -    ⚠️  Host PyTorch 2.6 - usando CPU por causa do bug cuFFT
2025-12-07 18:01:06,583 - INFO -    🚀 Iniciando subprocesso CPU...
2025-12-07 18:03:53,977 - ERROR -    ❌ Timeout ao gerar sample (>120s)
2025-12-07 18:03:53,982 - INFO - 📥 Recarregando modelo de treinamento...
^C
Aborted!
```

**Hipóteses:**
1. **Memory Leak na geração de samples:**
   - Cada época carrega modelo na RAM para CPU inference
   - Modelo não é descarregado após geração do sample
   - Acúmulo progressivo consome toda RAM disponível
   
2. **Subprocesso CPU não libera recursos:**
   - Timeout de 120s indica processo travado
   - Subprocesso pode não estar sendo terminated corretamente
   - Memória do subprocesso não é liberada

3. **Bug cuFFT workaround problemático:**
   - Movimentação modelo GPU→CPU→GPU pode estar duplicando memória
   - `torch.cuda.empty_cache()` pode não estar sendo chamado

### Tasks:

- [ ] **Task 6.1:** Investigar e corrigir memory leak no training loop
  - **Arquivos afetados:**
    - `train/scripts/train_xtts.py` (training loop)
    - `app/engines/xtts_engine.py` (sample generation)
  - **Investigação necessária:**
    1. Adicionar logging de uso de RAM em cada epoch
    2. Verificar se `del model` + `gc.collect()` é chamado
    3. Confirmar se subprocesso é `terminate()` + `join()`
    4. Validar que `torch.cuda.empty_cache()` é executado
  - **Ações:**
    ```python
    # Adicionar monitoramento de memória
    import psutil
    process = psutil.Process()
    print(f"📊 RAM usada: {process.memory_info().rss / 1024**3:.2f}GB")
    
    # Garantir limpeza após sample generation
    try:
        sample_path = generate_sample(...)
    finally:
        # Forçar limpeza
        if 'model' in locals():
            del model
        gc.collect()
        torch.cuda.empty_cache()
        
        # Se usando subprocess, garantir cleanup
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
    ```
  - **Tempo estimado:** 8h (investigação + correção + testes)
  - **Validação:** 
    - Treinar por 10 épocas sem memory leak
    - RAM deve permanecer estável (~8-12GB)
    - Samples gerados em <30s (não 120s timeout)

- [ ] **Task 6.2:** Otimizar sample generation (evitar timeout)
  - **Problema:** Timeout de 120s é muito longo, indica ineficiência
  - **Meta:** Reduzir para <20s por sample
  - **Ações:**
    1. Mover sample generation de volta para GPU (se cuFFT bug foi resolvido)
    2. Usar modelo já carregado (não recarregar a cada época)
    3. Cache de embeddings de referência
    4. Batch processing se múltiplos samples
  - **Tempo estimado:** 4h
  - **Validação:** Sample gerado em <20s consistentemente

- [ ] **Task 6.3:** Adicionar circuit breaker para sample generation
  - **Ação:** Se sample falhar 3 vezes consecutivas, desabilitar auto
  - **Implementação:**
    ```python
    class SampleGenerationCircuitBreaker:
        def __init__(self, max_failures=3):
            self.failures = 0
            self.max_failures = max_failures
            self.disabled = False
            
        def execute(self, func):
            if self.disabled:
                logger.warning("⚠️  Sample generation desabilitada (circuit breaker)")
                return None
                
            try:
                result = func()
                self.failures = 0  # Reset on success
                return result
            except Exception as e:
                self.failures += 1
                logger.error(f"❌ Sample falhou ({self.failures}/{self.max_failures})")
                
                if self.failures >= self.max_failures:
                    self.disabled = True
                    logger.error("🚫 Circuit breaker ativado - samples desabilitados")
                raise
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Training continua mesmo se samples falharem

- [ ] **Task 6.4:** Melhorar logging de uso de recursos
  - **Adicionar métricas:**
    - RAM usada (host)
    - VRAM usada (GPU)
    - Tempo de cada operação (forward, backward, sample)
  - **Dashboard de recursos:**
    ```python
    def log_resource_usage(epoch):
        import psutil
        import torch
        
        ram_gb = psutil.virtual_memory().used / 1024**3
        vram_gb = torch.cuda.memory_allocated() / 1024**3
        
        logger.info(f"📊 Epoch {epoch} Resources:")
        logger.info(f"   💾 RAM: {ram_gb:.2f}GB / {psutil.virtual_memory().total / 1024**3:.2f}GB")
        logger.info(f"   🎮 VRAM: {vram_gb:.2f}GB / {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB")
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Logs mostram uso de recursos a cada época

**Critério de Sucesso Sprint 6:**
✅ Training roda por 20+ épocas sem memory leak  
✅ RAM permanece estável (<15GB usado)  
✅ Samples gerados em <30s (não timeout)  
✅ Circuit breaker previne crashes se samples falharem  
✅ Logs mostram métricas de recursos detalhadas

---

## Sprint 7 – Refatoração Arquitetural (Clean Code)
**Duração:** 2 semanas  
**Meta:** Modularizar código e eliminar débito técnico

### Tasks:

- [ ] **Task 7.1:** Extrair `ApiClient` do objeto `app`
  - **Novo arquivo:** `app/webui/assets/js/api/client.js`
  - **Ação:**
    ```javascript
    // api/client.js
    class ApiClient {
        constructor(baseUrl = '') {
            this.baseUrl = baseUrl;
        }
        
        async request(path, options = {}) {
            const url = `${this.baseUrl}${path}`;
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), options.timeout || 60000);
            
            try {
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });
                clearTimeout(timeout);
                
                if (!response.ok) {
                    const error = await this.parseError(response);
                    throw new Error(error);
                }
                
                return await response.json();
            } catch (error) {
                clearTimeout(timeout);
                if (error.name === 'AbortError') {
                    throw new Error('Request timeout');
                }
                throw error;
            }
        }
        
        async get(path, options = {}) {
            return this.request(path, { ...options, method: 'GET' });
        }
        
        async post(path, body, options = {}) {
            return this.request(path, {
                ...options,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                body: JSON.stringify(body)
            });
        }
        
        async delete(path, options = {}) {
            return this.request(path, { ...options, method: 'DELETE' });
        }
        
        async parseError(response) {
            try {
                const data = await response.json();
                return data.detail || `HTTP ${response.status}`;
            } catch {
                return `HTTP ${response.status}`;
            }
        }
    }
    
    export default ApiClient;
    ```
  - **Uso em app.js:**
    ```javascript
    import ApiClient from './api/client.js';
    
    const api = new ApiClient(API_BASE);
    
    const app = {
        api: api,
        
        async runInference() {
            const result = await this.api.post('/training/inference/synthesize', {
                checkpoint: '...',
                text: '...'
            });
        }
    };
    ```
  - **Tempo estimado:** 4h
  - **Validação:** Todas as chamadas HTTP usam `this.api.get/post/delete`

- [ ] **Task 4.2:** Centralizar rotas em objeto `ROUTES`
  - **Novo arquivo:** `app/webui/assets/js/api/routes.js`
  - **Ação:**
    ```javascript
    // api/routes.js
    export const ROUTES = {
        training: {
            checkpoints: '/training/checkpoints',
            datasets: '/training/datasets',
            datasetStats: '/training/dataset/stats',
            inference: '/training/inference/synthesize',
            start: '/training/start',
            stop: '/training/stop',
            status: '/training/status',
            logs: '/training/logs'
        },
        voices: {
            list: '/voices',
            create: '/voices',
            delete: (id) => `/voices/${id}`
        },
        jobs: {
            list: '/jobs',
            get: (id) => `/jobs/${id}`,
            create: '/jobs/clone'
        }
    };
    ```
  - **Uso:**
    ```javascript
    import { ROUTES } from './api/routes.js';
    
    // Antes:
    const checkpoints = await this.api.get('/training/checkpoints');
    
    // Depois:
    const checkpoints = await this.api.get(ROUTES.training.checkpoints);
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Nenhuma URL hardcoded no código (exceto em `ROUTES`)

- [ ] **Task 4.3:** Extrair serviços de domínio
  - **Novos arquivos:**
    - `app/webui/assets/js/services/training.js`
    - `app/webui/assets/js/services/voices.js`
    - `app/webui/assets/js/services/jobs.js`
  - **Exemplo: TrainingService**
    ```javascript
    // services/training.js
    import { ROUTES } from '../api/routes.js';
    
    export class TrainingService {
        constructor(apiClient) {
            this.api = apiClient;
        }
        
        async getCheckpoints() {
            return this.api.get(ROUTES.training.checkpoints);
        }
        
        async getDatasetStats() {
            return this.api.get(ROUTES.training.datasetStats);
        }
        
        async synthesize(checkpoint, text, options = {}) {
            return this.api.post(ROUTES.training.inference, {
                checkpoint,
                text,
                temperature: options.temperature || 0.7,
                speed: options.speed || 1.0
            });
        }
        
        async startTraining(config) {
            return this.api.post(ROUTES.training.start, config);
        }
        
        async stopTraining() {
            return this.api.post(ROUTES.training.stop);
        }
        
        async getStatus() {
            return this.api.get(ROUTES.training.status);
        }
    }
    ```
  - **Uso em app.js:**
    ```javascript
    import { TrainingService } from './services/training.js';
    
    const trainingService = new TrainingService(api);
    
    const app = {
        training: trainingService,
        
        async runInference() {
            const checkpoint = document.getElementById('inference-checkpoint').value;
            const text = document.getElementById('inference-text').value;
            
            const result = await this.training.synthesize(checkpoint, text, {
                temperature: 0.7,
                speed: 1.0
            });
        }
    };
    ```
  - **Tempo estimado:** 6h
  - **Validação:** Lógica de API separada da lógica de UI

- [ ] **Task 4.4:** Migrar para módulos ES6 + bundler (Vite)
  - **Pré-requisito:** Tasks 4.1-4.3 concluídas
  - **Ação:**
    1. Instalar Vite: `npm install vite`
    2. Criar `vite.config.js`:
       ```javascript
       import { defineConfig } from 'vite';
       
       export default defineConfig({
           root: 'app/webui',
           build: {
               outDir: 'dist',
               rollupOptions: {
                   input: {
                       main: 'app/webui/index.html'
                   }
               }
           },
           server: {
               port: 8080,
               proxy: {
                   '/api': 'http://localhost:8005'
               }
           }
       });
       ```
    3. Atualizar `index.html`:
       ```html
       <!-- Antes: -->
       <script defer src="/webui/assets/js/app.js?v=3.5"></script>
       
       <!-- Depois: -->
       <script type="module" src="/assets/js/main.js"></script>
       ```
    4. Criar `main.js` como entry point:
       ```javascript
       import ApiClient from './api/client.js';
       import { TrainingService } from './services/training.js';
       import { initApp } from './app.js';
       
       const api = new ApiClient(API_BASE);
       const training = new TrainingService(api);
       
       window.app = initApp({ api, training });
       ```
  - **Tempo estimado:** 4h
  - **Validação:** 
    - `npm run dev` inicia servidor com hot reload
    - `npm run build` gera bundle otimizado
    - Nenhum erro 404 ao carregar JS

**Critério de Sucesso Sprint 4:**
✅ Código modular (serviços separados)  
✅ ApiClient isolado e testável  
✅ Rotas centralizadas em ROUTES  
✅ Build pipeline configurado (Vite)  
✅ Zero código morto (modules/ removido ou integrado)

---

## Sprint 5 – Hardening e Resiliência
**Duração:** 1 semana  
**Meta:** Garantir que WebUI não quebra em cenários adversos

### Tasks:

- [ ] **Task 5.1:** Implementar testes E2E básicos (Playwright)
  - **Arquivo:** `tests/e2e/training.spec.js`
  - **Ação:**
    ```javascript
    import { test, expect } from '@playwright/test';
    
    test('should load training tab without errors', async ({ page }) => {
        await page.goto('http://localhost:8005/webui');
        
        // Clicar na aba Training
        await page.click('text=Treinamento');
        
        // Verificar que não há erros no console
        page.on('console', msg => {
            if (msg.type() === 'error') {
                throw new Error(`Console error: ${msg.text()}`);
            }
        });
        
        // Verificar elementos carregados
        await expect(page.locator('#dataset-stats')).toBeVisible();
        await expect(page.locator('#checkpoint-list')).toBeVisible();
    });
    
    test('should synthesize audio successfully', async ({ page }) => {
        await page.goto('http://localhost:8005/webui');
        await page.click('text=Treinamento');
        await page.click('text=Inferência');
        
        // Selecionar checkpoint
        await page.selectOption('#inference-checkpoint', 'train/output/checkpoints/best_model.pt');
        
        // Inserir texto
        await page.fill('#inference-text', 'Teste de síntese de voz');
        
        // Clicar em sintetizar
        await page.click('button:has-text("Sintetizar")');
        
        // Aguardar áudio aparecer (timeout 60s)
        await expect(page.locator('#inference-audio')).toBeVisible({ timeout: 60000 });
    });
    ```
  - **Tempo estimado:** 4h
  - **Validação:** `npx playwright test` passa sem erros

- [ ] **Task 5.2:** Adicionar retry automático em falhas de rede
  - **Arquivo:** `app/webui/assets/js/api/client.js`
  - **Ação:**
    ```javascript
    async requestWithRetry(path, options = {}, maxRetries = 3) {
        let lastError;
        
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                return await this.request(path, options);
            } catch (error) {
                lastError = error;
                
                // Não retenta em erros 4xx (client errors)
                if (error.message.includes('HTTP 4')) {
                    throw error;
                }
                
                // Aguarda antes de retentar (exponential backoff)
                if (attempt < maxRetries - 1) {
                    const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
                    await new Promise(resolve => setTimeout(resolve, delay));
                    console.log(`⚠️ Retry ${attempt + 1}/${maxRetries} for ${path}`);
                }
            }
        }
        
        throw lastError;
    }
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Falhas de rede temporárias são recuperadas automaticamente

- [ ] **Task 5.3:** Adicionar validação de formulários
  - **Arquivo:** `app/webui/assets/js/ui/validators.js` (novo)
  - **Ação:**
    ```javascript
    export class FormValidator {
        static validateInferenceForm(formData) {
            const errors = [];
            
            if (!formData.checkpoint) {
                errors.push('Selecione um checkpoint');
            }
            
            if (!formData.text || formData.text.trim().length === 0) {
                errors.push('Insira o texto para síntese');
            }
            
            if (formData.text.length > 1000) {
                errors.push('Texto muito longo (máximo 1000 caracteres)');
            }
            
            if (formData.temperature < 0.1 || formData.temperature > 2.0) {
                errors.push('Temperatura deve estar entre 0.1 e 2.0');
            }
            
            return errors;
        }
    }
    ```
  - **Uso:**
    ```javascript
    async runInference() {
        const formData = {
            checkpoint: document.getElementById('inference-checkpoint').value,
            text: document.getElementById('inference-text').value,
            temperature: parseFloat(document.getElementById('inference-temperature').value)
        };
        
        const errors = FormValidator.validateInferenceForm(formData);
        if (errors.length > 0) {
            this.showToast(errors.join('<br>'), 'warning');
            return;
        }
        
        // ... continua com síntese
    }
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Formulários inválidos mostram erros claros antes de enviar

- [ ] **Task 5.4:** Implementar logging estruturado
  - **Arquivo:** `app/webui/assets/js/utils/logger.js` (novo)
  - **Ação:**
    ```javascript
    export class Logger {
        constructor(context, level = 'info') {
            this.context = context;
            this.level = level;
            this.levels = { debug: 0, info: 1, warn: 2, error: 3 };
        }
        
        _log(level, message, data = {}) {
            if (this.levels[level] < this.levels[this.level]) {
                return; // Não loga se nível for menor que configurado
            }
            
            const timestamp = new Date().toISOString();
            const logData = {
                timestamp,
                level,
                context: this.context,
                message,
                ...data
            };
            
            const emoji = { debug: '🔍', info: 'ℹ️', warn: '⚠️', error: '❌' };
            const method = { debug: 'debug', info: 'log', warn: 'warn', error: 'error' };
            
            console[method[level]](`${emoji[level]} [${this.context}] ${message}`, logData);
        }
        
        debug(message, data) { this._log('debug', message, data); }
        info(message, data) { this._log('info', message, data); }
        warn(message, data) { this._log('warn', message, data); }
        error(message, error, data) {
            this._log('error', message, {
                error: error?.message,
                stack: error?.stack,
                ...data
            });
        }
    }
    ```
  - **Uso:**
    ```javascript
    import { Logger } from './utils/logger.js';
    
    const logger = new Logger('TrainingService');
    
    async synthesize(checkpoint, text) {
        logger.info('Starting synthesis', { checkpoint, textLength: text.length });
        
        try {
            const result = await this.api.post(...);
            logger.info('Synthesis completed', { duration: result.duration });
            return result;
        } catch (error) {
            logger.error('Synthesis failed', error, { checkpoint });
            throw error;
        }
    }
    ```
  - **Tempo estimado:** 2h
  - **Validação:** Logs estruturados facilitam debug

**Critério de Sucesso Sprint 5:**
✅ Testes E2E cobrem fluxos críticos (>3 testes)  
✅ Retry automático em falhas de rede  
✅ Validação de formulários antes de envio  
✅ Logging estruturado em toda aplicação  
✅ WebUI resiliente a falhas temporárias de backend

---

## Backlog / Melhorias Futuras (P3)

### Arquitetura:
- [ ] Migrar para framework SPA (React/Vue/Svelte)
- [ ] Implementar state management (Zustand/Pinia/Redux)
- [ ] Adicionar TypeScript completo
- [ ] Implementar service workers para cache offline

### Features:
- [ ] Comparação A/B de checkpoints (já existe endpoint, falta UI)
- [ ] Exportação de relatórios de treinamento (PDF/JSON)
- [ ] Notificações push quando treinamento terminar
- [ ] Histórico de treinamentos (banco de dados)
- [ ] Backup automático de checkpoints

### DevOps:
- [ ] CI/CD para testes E2E (GitHub Actions)
- [ ] Linting automático (ESLint + Prettier)
- [ ] Pre-commit hooks (Husky)
- [ ] Coverage reports (Jest + Istanbul)

---

## Métricas de Progresso

### Sprint 0 (Emergencial):
- **Tempo estimado:** 2-4h
- **Impacto:** 🔴 Crítico (bloqueador total)
- **Critério de sucesso:** Inferência funcional

### Sprint 1 (Infraestrutura):
- **Tempo estimado:** 1 semana
- **Impacto:** 🟡 Alto (estabilidade)
- **Critério de sucesso:** Zero código morto, timeout configurado

### Sprint 2 (Integração /train):
- **Tempo estimado:** 1 semana
- **Impacto:** 🟡 Alto (funcionalidade core)
- **Critério de sucesso:** WebUI enxerga tudo em /train

### Sprint 3 (Observabilidade):
- **Tempo estimado:** 1 semana
- **Impacto:** 🟢 Médio (UX)
- **Critério de sucesso:** Dashboard de status em tempo real

### Sprint 4 (Refatoração):
- **Tempo estimado:** 2 semanas
- **Impacto:** 🔵 Médio-Alto (manutenibilidade)
- **Critério de sucesso:** Código modular, testável

### Sprint 5 (Hardening):
- **Tempo estimado:** 1 semana
- **Impacto:** 🟢 Médio (qualidade)
- **Critério de sucesso:** Testes E2E, validações, retry

**Total:** 6-7 semanas para todas as sprints

---

## Como Usar Este Documento

1. **Começar pelo Sprint 0** (urgente!)
2. **Após cada sprint:**
   - Atualizar checkboxes `[x]`
   - Adicionar notas de implementação se necessário
   - Validar critérios de sucesso
3. **Ajustar estimativas** conforme realidade
4. **Mover tasks** entre sprints se prioridades mudarem

**Última Atualização:** 2025-12-07  
**Próxima Revisão:** Após conclusão do Sprint 0
