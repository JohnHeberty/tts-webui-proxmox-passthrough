# WebUI – Relatório de Problemas e Melhorias

**Data da Análise:** 2025-12-07  
**Analista:** Tech Lead - Auditoria Completa da WebUI  
**Escopo:** Tela de Training, Inferência, Integração com Backend, Arquitetura JS

---

## 1. Erros / Bugs Encontrados

### 1.1. Bugs de Inferência / Síntese ⚠️ **CRÍTICO**

#### **[CRÍTICO] `this.api is not a function` - Causa Raiz Identificada**

**Arquivo:** `app/webui/assets/js/app.js`  
**Linhas afetadas:** 2895, 2922, 2941, 2990, 3034, 3067, 3100, **3150** (runInference)

**Descrição detalhada:**
- **Sintoma:** Ao clicar em "Sintetizar" na tela de Training → Inferência, erro no console:
  ```
  TypeError: this.api is not a function
  at Object.runInference (app.js:3150:41)
  ```

- **Causa Raiz:**
  1. O objeto `app` possui o método `fetchJson()` na linha 511, mas **NÃO possui método `api()`**
  2. Há **8 chamadas** a `this.api()` no código:
     - `runInference()` - linha 3150 ✅ **PONTO DE FALHA REPORTADO**
     - `segmentAudio()` - linha 2895
     - `transcribeAudio()` - linha 2922
     - `stopTraining()` - linha 2941
     - `runABTest()` - linha 2990
     - `downloadVideos()` - linha 3034
     - `startTraining()` - linha 3067
     - `checkTrainingStatus()` - linha 3100
  3. Todas essas funções deveriam chamar `this.fetchJson()` em vez de `this.api()`

- **Contexto Histórico:**
  - Aparentemente houve uma refatoração onde `api()` foi renomeado para `fetchJson()`
  - As 3 funções do training tab (loadDatasetStats, loadCheckpoints, loadTrainingSamples) foram corrigidas recentemente (linhas 2700, 2772, 2840) mas as outras 8 funções foram esquecidas
  - Isso indica **refatoração incompleta** e falta de testes

**Impacto:**
- ❌ Inferência completamente quebrada (botão "Sintetizar")
- ❌ Todas as operações de dataset (download, segment, transcribe)
- ❌ Iniciar/parar treinamento
- ❌ A/B testing
- **Severidade:** P0 - Bloqueador total da funcionalidade de training

**Solução:**
Substituir todas as 8 chamadas de `this.api()` por `this.fetchJson()`

---

#### **[ALTO] Event Listener com contexto incorreto**

**Arquivo:** `app/webui/assets/js/app.js`  
**Linha:** 363

```javascript
document.getElementById('form-inference-test')?.addEventListener('submit', (e) => {
    e.preventDefault();
    this.runInference();  // ⚠️ Arrow function preserva 'this', MAS...
});
```

**Problema:**
- Mesmo após corrigir `this.api → this.fetchJson`, o `this` dentro do arrow function está correto
- PORÉM, não há validação se `runInference` existe antes de chamar
- Se houver erro de sintaxe no `app.js`, `window.app` pode estar incompleto

**Solução:**
Adicionar validação e logging:
```javascript
document.getElementById('form-inference-test')?.addEventListener('submit', (e) => {
    e.preventDefault();
    if (typeof this.runInference === 'function') {
        this.runInference();
    } else {
        console.error('❌ runInference não está disponível');
    }
});
```

---

### 1.2. Bugs de Integração com Backend

#### **[MÉDIO] Endpoint `/training/inference/synthesize` pode não existir**

**Arquivo:** `app/webui/assets/js/app.js`  
**Linha:** 3150

**Problema:**
- WebUI chama `POST /training/inference/synthesize` mas não há evidência de que este endpoint existe no backend
- Não encontrado em `app/training_api.py` (verificar se foi implementado)

**Validação necessária:**
```bash
curl -X POST http://localhost:8005/training/inference/synthesize \
  -H "Content-Type: application/json" \
  -d '{"checkpoint":"test.pt","text":"teste"}'
```

Se retornar 404, o endpoint precisa ser implementado no backend.

---

#### **[MÉDIO] Falta tratamento de timeouts**

**Arquivo:** `app/webui/assets/js/app.js`  
**Linha:** 511 (fetchJson)

**Problema:**
- `fetchJson()` não possui timeout configurado
- Inferência pode demorar minutos (carregamento de checkpoint + síntese)
- Usuário não vê progresso, apenas espera indefinidamente

**Solução:**
Adicionar timeout e feedback de progresso:
```javascript
async fetchJson(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000); // 60s
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: { ...options.headers }
        });
        clearTimeout(timeout);
        // ... resto do código
    } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout - operação muito lenta');
        }
        throw error;
    }
}
```

---

### 1.3. Bugs de Caminhos / Arquivos (checkpoints, samples, etc.)

#### **[BAIXO] Path de checkpoint pode estar incorreto**

**Arquivo:** `app/webui/assets/js/app.js`  
**Linha:** 3150

```javascript
const checkpoint = document.getElementById('inference-checkpoint').value;
// Envia direto para API: "train/output/checkpoints/best_model.pt"
```

**Problema:**
- O path é relativo (`train/output/...`)
- Se o backend não estiver configurado para resolver paths relativos à raiz do projeto, falhará
- Depende de volume Docker estar montado corretamente

**Validação:**
Verificar se backend resolve `train/output/checkpoints/best_model.pt` corretamente ou precisa de path absoluto

---

### 1.4. Bugs de UI/UX (mensagens erradas, feedback ruim, etc.)

#### **[MÉDIO] Mensagem de erro genérica**

**Arquivo:** `app/webui/assets/js/app.js`  
**Linha:** 3168

```javascript
} catch (error) {
    console.error('❌ Error running inference:', error);
    this.showToast('Erro ao sintetizar', 'danger');  // ⚠️ Muito genérico
}
```

**Problema:**
- Usuário vê apenas "Erro ao sintetizar"
- Não sabe se foi:
  - Checkpoint inválido?
  - Timeout?
  - Erro 500 no backend?
  - Falta de VRAM?

**Solução:**
```javascript
} catch (error) {
    console.error('❌ Error running inference:', error);
    const userMessage = error.message || 'Erro desconhecido ao sintetizar';
    this.showToast(`Erro: ${userMessage}`, 'danger');
}
```

---

#### **[BAIXO] Falta indicador de progresso**

**Arquivo:** `app/webui/index.html`  
**Linha:** 951-1010 (form de inferência)

**Problema:**
- Não há spinner ou indicador de "carregando"
- Inferência pode levar 30-60s (carregar checkpoint de 5GB + sintetizar)
- Usuário não sabe se clicou corretamente

**Solução:**
Adicionar spinner e desabilitar botão durante processamento

---

## 2. Problemas de Arquitetura / Organização

### 2.1. Dependências mal injetadas (ex: this.api)

#### **[CRÍTICO] Falta de padrão unificado para chamadas HTTP**

**Problema:**
- Existe `fetchJson()` mas código ainda usa `this.api()`
- Não há classe `ApiClient` isolada
- Toda lógica HTTP está misturada com lógica de UI no objeto `app`

**Impacto:**
- Dificulta testes (não dá para mockar HTTP sem mockar todo objeto `app`)
- Refatorações quebram código (como aconteceu com `api → fetchJson`)
- Violação do Single Responsibility Principle

**Solução Recomendada:**
Extrair para `ApiClient`:
```javascript
class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async get(path) { /* ... */ }
    async post(path, body) { /* ... */ }
    async fetchJson(path, options) { /* ... */ }
}

const api = new ApiClient(API_BASE);
const app = {
    api: api,  // Injeção de dependência
    // ... resto
};
```

---

### 2.2. Estado Global Confuso / Duplicado

#### **[ALTO] Módulos ES6 não utilizados**

**Arquivos:**
- `app/webui/assets/js/modules/training.js` (414 linhas) - **NÃO USADO**
- `app/webui/assets/js/modules/utils.js` (227 linhas) - **NÃO USADO**

**Problema:**
- Existe uma tentativa de modularização ES6 com `TrainingManager` class
- **MAS** o HTML carrega apenas `app.js` (monolito)
- Código duplicado entre `modules/training.js` e funções inline no `app.js`
- `modules/training.js` tem classe com injeção correta de `api` no construtor:
  ```javascript
  constructor(api, showToast) {
      this.api = api;  // ✅ Injeção correta!
  }
  ```
- Mas isso nunca é usado porque `app.js` não importa os módulos

**Evidência:**
```html
<!-- index.html linha 21 -->
<script defer src="/webui/assets/js/app.js?v=3.5"></script>
<!-- ❌ Não há import de modules/training.js -->
```

**Impacto:**
- Manutenção duplicada (bug corrigido em um lugar, persiste no outro)
- Confusão sobre qual código é "verdadeiro"
- ~600 linhas de código morto

**Decisão Necessária:**
1. **Opção A:** Remover `modules/` e manter tudo em `app.js` (+ simples)
2. **Opção B:** Migrar completamente para módulos ES6 e usar bundler (+ profissional)

---

### 2.3. Acoplamento excessivo com backend

#### **[MÉDIO] URLs hardcoded espalhados**

**Problema:**
- Endpoints espalhados por todo `app.js`:
  - `/training/checkpoints`
  - `/training/dataset/stats`
  - `/training/inference/synthesize`
  - `/training/start`
  - etc.
- Se mudar estrutura de rotas no backend, precisa editar dezenas de linhas

**Solução:**
Centralizar em objeto de rotas:
```javascript
const ROUTES = {
    training: {
        checkpoints: '/training/checkpoints',
        datasets: '/training/datasets',
        inference: '/training/inference/synthesize',
        start: '/training/start',
        stop: '/training/stop',
        status: '/training/status'
    },
    // ...
};
```

---

## 3. Pontos de Melhoria / Refatoração

### 3.1. Organização de Código (front-end)

#### **Proposta: Migrar para Arquitetura em Camadas**

```
app/webui/assets/js/
├── api/
│   ├── client.js        # ApiClient class
│   ├── routes.js        # ROUTES object
│   └── interceptors.js  # Error handling, logging
├── services/
│   ├── training.js      # TrainingService (usa ApiClient)
│   ├── voices.js        # VoiceService
│   └── jobs.js          # JobService
├── ui/
│   ├── toast.js         # Toast notifications
│   ├── forms.js         # Form helpers
│   └── validators.js    # Input validation
└── app.js               # Main app (orquestra tudo)
```

**Benefícios:**
- Testabilidade (cada camada isolada)
- Reutilização (ApiClient usado por todos services)
- Clareza (desenvolvedor sabe onde procurar código)

---

### 3.2. Observabilidade e Debug

#### **[ALTO] Adicionar logging estruturado**

**Problema atual:**
```javascript
console.log('🎓 Loading training section');
console.error('❌ Error loading dataset stats:', error);
```

**Melhoria:**
```javascript
class Logger {
    constructor(context) {
        this.context = context;
    }
    
    info(message, data = {}) {
        console.log(`[${this.context}] ${message}`, data);
    }
    
    error(message, error, data = {}) {
        console.error(`[${this.context}] ${message}`, {
            error: error.message,
            stack: error.stack,
            ...data
        });
    }
}

const trainingLogger = new Logger('Training');
trainingLogger.info('Loading checkpoints', { count: 3 });
```

---

#### **[MÉDIO] Expor métricas de performance**

**Adicionar:**
```javascript
async runInference() {
    const startTime = performance.now();
    try {
        // ... síntese
        const duration = performance.now() - startTime;
        console.log(`✅ Inferência concluída em ${duration.toFixed(0)}ms`);
    } catch (error) {
        const duration = performance.now() - startTime;
        console.error(`❌ Inferência falhou após ${duration.toFixed(0)}ms`, error);
    }
}
```

---

### 3.3. UX de Treinamento

#### **[ALTO] Dashboard de Training precisa mostrar:**

**Faltando atualmente:**
1. ❌ Link para TensorBoard (não há botão/link visível)
2. ❌ Status em tempo real do treinamento (epoch atual, loss)
3. ❌ Último sample gerado (player de áudio direto)
4. ❌ Estimativa de tempo restante
5. ❌ Uso de VRAM/GPU

**Proposta:**
Adicionar card no topo da tela de Training:
```html
<div class="card bg-primary text-white mb-3">
    <div class="card-body">
        <h5>Treinamento em Andamento</h5>
        <div class="row">
            <div class="col-md-3">
                <strong>Época:</strong> 45/100
            </div>
            <div class="col-md-3">
                <strong>Loss:</strong> 0.234
            </div>
            <div class="col-md-3">
                <strong>VRAM:</strong> 18.2GB / 24GB
            </div>
            <div class="col-md-3">
                <a href="/tensorboard" target="_blank" class="btn btn-light btn-sm">
                    📊 TensorBoard
                </a>
            </div>
        </div>
    </div>
</div>
```

---

#### **[MÉDIO] Melhorar seleção de checkpoint**

**Problema atual:**
- Dropdown simples `<select>`
- Não mostra tamanho do arquivo, data de criação, métricas

**Proposta:**
Radio buttons com cards detalhados:
```html
<div class="checkpoint-selector">
    <div class="form-check card mb-2">
        <div class="card-body">
            <input type="radio" name="checkpoint" value="best_model.pt" id="cp1">
            <label for="cp1">
                <strong>best_model.pt</strong>
                <br>
                <small>Epoch 87 • Loss 0.156 • 1.8GB • 2025-12-07 17:13</small>
            </label>
        </div>
    </div>
</div>
```

---

## 4. Resumo das Causas Raiz (Root Causes)

### 🔴 Causa Raiz #1: Refatoração Incompleta
- **O que:** Método `api()` renomeado para `fetchJson()` mas 8 chamadas não foram atualizadas
- **Por que:** Falta de busca global (find/replace) ou testes automatizados
- **Como evitar:** Linter (ESLint) com regra para detectar métodos inexistentes

### 🔴 Causa Raiz #2: Arquitetura Inconsistente
- **O que:** Código em `modules/` (ES6 classes) vs código inline em `app.js` (objeto literal)
- **Por que:** Tentativa de refatoração abandonada no meio
- **Como evitar:** Decidir arquitetura e seguir 100%

### 🔴 Causa Raiz #3: Falta de Testes
- **O que:** Nenhum teste unitário ou E2E
- **Por que:** Bugs básicos (método não existe) passam despercebidos
- **Como evitar:** Jest + Playwright para testes mínimos

### 🟡 Causa Raiz #4: Falta de Validação na Build
- **O que:** `app.js` carregado sem minificação/validação
- **Por que:** Erros de sintaxe só aparecem no navegador
- **Como evitar:** Bundler (Vite/Webpack) com TypeScript ou JSDoc

### 🟡 Causa Raiz #5: Estado Global Monolítico
- **O que:** Objeto `app` com 3000+ linhas misturando UI, API, estado
- **Por que:** Crescimento orgânico sem refatoração contínua
- **Como evitar:** Extrair serviços, aplicar SRP

---

## 5. Recomendações de Alto Nível

### **Imediato (Sprint 1 - P0):**
1. ✅ Corrigir `this.api → this.fetchJson` nas 8 funções (1h)
2. ✅ Implementar endpoint `/training/inference/synthesize` no backend se não existir (2h)
3. ✅ Adicionar mensagens de erro detalhadas (30min)
4. ✅ Adicionar spinner de loading na inferência (30min)

### **Curto Prazo (Sprint 2-3 - P1):**
1. 🔄 Decidir: usar módulos ES6 ou remover `modules/`? (decisão arquitetural)
2. 🔄 Extrair `ApiClient` do objeto `app` (4h)
3. 🔄 Adicionar timeout em requests (1h)
4. 🔄 Melhorar UX da tela de Training (dashboard de status) (6h)

### **Médio Prazo (Sprint 4-5 - P2):**
1. 📋 Implementar testes E2E com Playwright (8h)
2. 📋 Migrar para TypeScript ou adicionar JSDoc completo (16h)
3. 📋 Adicionar bundler (Vite) com hot reload (4h)
4. 📋 Centralizar rotas em objeto `ROUTES` (2h)

### **Longo Prazo (P3):**
1. 🚀 Refatorar para SPA framework (React/Vue) - **apenas se necessário**
2. 🚀 Adicionar state management (Zustand/Pinia)
3. 🚀 Implementar service workers para cache

---

## 6. Métricas de Qualidade (Baseline)

### **Antes das Correções:**
- ❌ **Bugs Críticos:** 1 (inferência quebrada)
- ⚠️ **Bugs Altos:** 3 (módulos não usados, timeout, erro genérico)
- 📝 **Bugs Médios:** 4
- 📊 **Cobertura de Testes:** 0%
- 🏗️ **Arquitetura:** Monolito de 3269 linhas
- 📦 **Build Pipeline:** Nenhum (JS direto sem validação)

### **Meta Após Sprint 1:**
- ✅ **Bugs Críticos:** 0
- ✅ **Inferência Funcional:** 100%
- ✅ **Mensagens de Erro:** Contextuais
- ✅ **Feedback de Loading:** Implementado

### **Meta Após Sprint 2-3:**
- ✅ **Arquitetura:** Modular (ApiClient separado)
- ✅ **Cobertura de Testes:** >50% (funções críticas)
- ✅ **Build Pipeline:** Validação automática (linter)

---

## Apêndice A: Checklist de Validação Pós-Correção

Após implementar Sprint 1, validar:

- [ ] ✅ Botão "Sintetizar" funciona sem erro no console
- [ ] ✅ Mensagem de erro mostra detalhes (não apenas "Erro ao sintetizar")
- [ ] ✅ Spinner aparece durante síntese
- [ ] ✅ Áudio é reproduzido após conclusão
- [ ] ✅ Download do áudio funciona
- [ ] ✅ Timeout de 60s está configurado
- [ ] ✅ Console mostra logs estruturados (não apenas emojis)
- [ ] ✅ Checkpoints são carregados corretamente
- [ ] ✅ Samples de treinamento aparecem na lista

---

**Fim do Relatório**

_Nota: Este documento deve ser atualizado após cada sprint para refletir o progresso das correções._
