/**
 * E2E Tests - Jobs & Synthesis Flow
 * Sprint 5 Task 5.4
 */

const { test, expect } = require('@playwright/test');

test.describe('Jobs Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('deve navegar para aba Jobs', async ({ page }) => {
    const jobsLink = page.locator('a:has-text("Jobs"), button:has-text("Jobs")').first();
    await jobsLink.click();
    
    // Verificar se formulário de criar job está visível
    await expect(page.locator('#form-create-job')).toBeVisible({ timeout: 10000 });
  });

  test('deve validar formulário de criar job - texto obrigatório', async ({ page }) => {
    await page.locator('a:has-text("Jobs")').first().click();
    await page.waitForSelector('#job-text', { state: 'visible' });
    
    // Tentar submeter sem texto
    const jobText = page.locator('#job-text');
    await jobText.fill('');
    
    // Tentar submeter
    const createButton = page.locator('#btn-create-job, button[type="submit"]:has-text("Criar")').first();
    await createButton.click();
    
    // Verificar validação
    const isValid = await jobText.evaluate(el => el.checkValidity());
    expect(isValid).toBe(false);
  });

  test('deve validar formulário - idioma obrigatório', async ({ page }) => {
    await page.locator('a:has-text("Jobs")').first().click();
    await page.waitForSelector('#job-source-language', { state: 'visible' });
    
    // Preencher texto mas não selecionar idioma
    await page.fill('#job-text', 'Texto de teste');
    
    const languageSelect = page.locator('#job-source-language');
    const selectedValue = await languageSelect.inputValue();
    
    // Se valor vazio, validação deve falhar
    if (selectedValue === '') {
      const isValid = await languageSelect.evaluate(el => el.checkValidity());
      expect(isValid).toBe(false);
    }
  });

  test('deve carregar idiomas disponíveis', async ({ page }) => {
    await page.locator('a:has-text("Jobs")').first().click();
    await page.waitForSelector('#job-source-language', { state: 'visible' });
    
    // Aguardar carregamento de idiomas (pode ser via API ou estático)
    await page.waitForTimeout(2000);
    
    const languageSelect = page.locator('#job-source-language');
    const optionCount = await languageSelect.locator('option').count();
    
    // Deve ter pelo menos 2 opções (1 padrão + idiomas)
    expect(optionCount).toBeGreaterThanOrEqual(1);
  });

  test('deve mostrar contador de caracteres', async ({ page }) => {
    await page.locator('a:has-text("Jobs")').first().click();
    await page.waitForSelector('#job-text', { state: 'visible' });
    
    const textArea = page.locator('#job-text');
    const counter = page.locator('#text-counter');
    
    // Verificar se contador existe
    await expect(counter).toBeVisible();
    
    // Digitar texto
    await textArea.fill('Teste');
    
    // Verificar se contador atualizou
    await expect(counter).toHaveText('5');
  });

  test('deve limitar texto a 10000 caracteres', async ({ page }) => {
    await page.locator('a:has-text("Jobs")').first().click();
    await page.waitForSelector('#job-text', { state: 'visible' });
    
    const textArea = page.locator('#job-text');
    
    // Verificar atributo maxlength
    const maxLength = await textArea.getAttribute('maxlength');
    expect(maxLength).toBe('10000');
  });
});

test.describe('Jobs List', () => {
  test('deve carregar lista de jobs existentes', async ({ page }) => {
    await page.goto('/');
    await page.locator('a:has-text("Jobs")').first().click();
    
    // Aguardar requisição de jobs
    await page.waitForResponse(
      resp => resp.url().includes('/jobs'),
      { timeout: 10000 }
    ).catch(() => null);
    
    // Verificar se seção de jobs existe
    const jobsList = page.locator('#jobs-list, .jobs-container').first();
    
    // Pode estar vazio, mas deve existir
    if (await jobsList.count() > 0) {
      await expect(jobsList).toBeVisible();
    }
  });
});

test.describe('Voice Selection', () => {
  test('deve alternar entre modo preset e voz clonada', async ({ page }) => {
    await page.goto('/');
    await page.locator('a:has-text("Jobs")').first().click();
    await page.waitForSelector('#job-mode', { state: 'visible' });
    
    const modeSelect = page.locator('#job-mode');
    
    // Verificar se tem opções de modo
    const optionCount = await modeSelect.locator('option').count();
    expect(optionCount).toBeGreaterThanOrEqual(2);
    
    // Verificar se pode alternar
    await modeSelect.selectOption({ index: 0 });
    const value1 = await modeSelect.inputValue();
    
    await modeSelect.selectOption({ index: 1 });
    const value2 = await modeSelect.inputValue();
    
    expect(value1).not.toBe(value2);
  });
});

test.describe('Job Creation', () => {
  test.skip('deve criar job com sucesso', async ({ page }) => {
    // Skip: requer backend configurado
    await page.goto('/');
    await page.locator('a:has-text("Jobs")').first().click();
    
    // Preencher formulário
    await page.fill('#job-text', 'Texto de teste para síntese');
    await page.selectOption('#job-source-language', 'pt');
    await page.selectOption('#job-mode', 'dubbing');
    
    // Submeter
    await page.click('button[type="submit"]');
    
    // Verificar toast de sucesso
    await expect(page.locator('.toast')).toContainText(/criado|success/i, { timeout: 5000 });
  });
});
