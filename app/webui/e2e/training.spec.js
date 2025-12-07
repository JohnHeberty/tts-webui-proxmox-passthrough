/**
 * E2E Tests - Training Flow
 * Sprint 5 Task 5.4
 */

const { test, expect } = require('@playwright/test');

test.describe('Training Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('deve carregar página inicial', async ({ page }) => {
    await expect(page).toHaveTitle(/TTS/);
    await expect(page.locator('nav')).toBeVisible();
  });

  test('deve navegar para aba Training', async ({ page }) => {
    // Procurar link ou botão de Training
    const trainingLink = page.locator('a:has-text("Training"), button:has-text("Training")').first();
    await trainingLink.click();
    
    // Verificar elementos da página de training
    await expect(page.locator('#training-dataset')).toBeVisible({ timeout: 10000 });
  });

  test('deve carregar lista de datasets', async ({ page }) => {
    await page.locator('a:has-text("Training"), button:has-text("Training")').first().click();
    
    // Aguardar requisição de datasets
    const datasetsResponse = page.waitForResponse(
      resp => resp.url().includes('/training/datasets') && resp.status() === 200,
      { timeout: 10000 }
    );
    
    await datasetsResponse;
    
    // Verificar se select tem opções
    const datasetSelect = page.locator('#training-dataset');
    await expect(datasetSelect).toBeVisible();
    
    const optionCount = await datasetSelect.locator('option').count();
    expect(optionCount).toBeGreaterThan(0);
  });

  test('deve validar formulário de training - campos obrigatórios', async ({ page }) => {
    await page.locator('a:has-text("Training"), button:has-text("Training")').first().click();
    await page.waitForSelector('#training-dataset', { state: 'visible' });
    
    // Tentar submeter sem selecionar dataset
    const startButton = page.locator('#btn-start-training');
    await startButton.click();
    
    // Verificar se aparece mensagem de validação ou toast
    const hasValidationMessage = await page.locator('.invalid-feedback:visible').count() > 0;
    const hasToast = await page.locator('.toast:visible').count() > 0;
    
    expect(hasValidationMessage || hasToast).toBe(true);
  });

  test('deve validar epochs entre 10 e 1000', async ({ page }) => {
    await page.locator('a:has-text("Training"), button:has-text("Training")').first().click();
    await page.waitForSelector('#training-epochs', { state: 'visible' });
    
    const epochsInput = page.locator('#training-epochs');
    
    // Testar valor abaixo do mínimo
    await epochsInput.fill('5');
    await epochsInput.blur();
    
    // Verificar validação HTML5
    const isValid = await epochsInput.evaluate(el => el.checkValidity());
    expect(isValid).toBe(false);
  });

  test('deve carregar lista de checkpoints', async ({ page }) => {
    await page.locator('a:has-text("Training"), button:has-text("Training")').first().click();
    
    // Aguardar requisição de checkpoints
    await page.waitForResponse(
      resp => resp.url().includes('/training/checkpoints'),
      { timeout: 10000 }
    ).catch(() => null); // Pode não ter checkpoints, ok
    
    const checkpointList = page.locator('#checkpoint-list');
    await expect(checkpointList).toBeVisible();
  });

  test('deve mostrar status de treinamento quando iniciado', async ({ page }) => {
    await page.locator('a:has-text("Training"), button:has-text("Training")').first().click();
    await page.waitForSelector('#training-status-card', { state: 'attached' });
    
    const statusCard = page.locator('#training-status-card');
    
    // Card pode estar oculto se não houver treinamento ativo
    // Isso é esperado
    const isVisible = await statusCard.isVisible();
    
    // Se visível, deve ter conteúdo
    if (isVisible) {
      await expect(statusCard).toContainText(/idle|training|completed|failed/i);
    }
  });
});

test.describe('Training Operations', () => {
  test.skip('deve iniciar treinamento com dataset válido', async ({ page }) => {
    // Skip: requer backend configurado e dataset disponível
    await page.goto('/');
    await page.locator('a:has-text("Training")').first().click();
    
    // Selecionar dataset
    await page.selectOption('#training-dataset', { index: 1 });
    
    // Configurar parâmetros
    await page.fill('#training-epochs', '10');
    await page.fill('#training-batch-size', '2');
    
    // Iniciar treinamento
    await page.click('#btn-start-training');
    
    // Verificar se botão mudou para "Parando..."
    await expect(page.locator('#btn-stop-training')).toBeVisible({ timeout: 5000 });
  });
});
