# WebUI Tests

Testes automatizados para a interface web do TTS Audio Voice Service.

## Sprint 5: Testes Automatizados 🧪

### Estrutura de Testes

```
app/webui/
├── tests/              # Testes unitários (Jest)
│   ├── setup.js       # Configuração global
│   ├── app.test.js    # Testes de lógica principal
│   └── api.test.js    # Testes de API client
├── e2e/               # Testes E2E (Playwright)
│   ├── training.spec.js
│   ├── synthesis.spec.js
│   └── jobs.spec.js
├── jest.config.js     # Configuração Jest
├── playwright.config.js
└── package.json
```

## Instalação

```bash
cd app/webui
npm install
```

## Executar Testes

### Testes Unitários (Jest)

```bash
# Executar todos os testes
npm test

# Executar com watch mode
npm run test:watch

# Gerar relatório de coverage
npm run test:coverage
```

### Testes E2E (Playwright)

```bash
# Instalar browsers
npx playwright install

# Executar testes E2E
npx playwright test

# Executar em modo UI
npx playwright test --ui

# Executar teste específico
npx playwright test e2e/training.spec.js
```

## Coverage Mínimo

- **Branches:** 70%
- **Functions:** 70%
- **Lines:** 70%
- **Statements:** 70%

## CI/CD

Testes são executados automaticamente no GitHub Actions em cada push/PR.

Ver `.github/workflows/test.yml` para configuração.

## Testes Implementados

### Unitários (Jest)

- ✅ `formatError()` - Tradução de mensagens de erro
- ✅ `showToast()` - Exibição de notificações
- ✅ Form validation - Validação de formulários
- ✅ `fetchJson()` - Cliente HTTP com timeout
- ✅ AbortController - Cancelamento de requisições

### E2E (Playwright)

- ⏳ Training flow - Fluxo completo de treinamento
- ⏳ Synthesis flow - Criação de jobs de síntese
- ⏳ Jobs management - Gestão de jobs
- ⏳ Voice cloning - Clonagem de vozes

## Status

**Sprint 5 Progress:** 40% (Task 5.1 ✅, Task 5.2 🔄)

- ✅ Task 5.1: Jest configurado
- 🔄 Task 5.2: Testes unitários (2/5 arquivos)
- ⏳ Task 5.3: Playwright setup
- ⏳ Task 5.4: Testes E2E
- ⏳ Task 5.5: CI/CD GitHub Actions
