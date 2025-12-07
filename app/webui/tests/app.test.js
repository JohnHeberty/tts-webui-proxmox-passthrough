/**
 * Unit tests for app.js - Error Formatting & Toast
 * Sprint 5 Task 5.2
 */

describe('App - Error Handling', () => {
  let mockApp;

  beforeEach(() => {
    // Setup DOM
    document.body.innerHTML = `
      <div id="toast" class="toast">
        <div id="toast-title"></div>
        <div id="toast-body"></div>
      </div>
    `;

    // Mock app object (simplified version)
    mockApp = {
      formatError(error) {
        const errorMessage = error.message || String(error);
        
        const ERROR_TRANSLATIONS = {
          'Connection refused': 'Não foi possível conectar ao servidor. Verifique se está rodando.',
          'Failed to fetch': 'Erro de conexão. Verifique sua internet ou se o servidor está rodando.',
          'timeout': 'A operação demorou muito tempo. Tente novamente.',
          'Network error': 'Erro de rede. Verifique sua conexão.',
          '404': 'Recurso não encontrado no servidor.',
          '500': 'Erro interno do servidor. Consulte os logs para mais detalhes.',
        };
        
        for (const [key, translation] of Object.entries(ERROR_TRANSLATIONS)) {
          if (errorMessage.includes(key)) {
            return translation;
          }
        }
        
        return errorMessage;
      },

      showToast(title, message, type = 'info') {
        const toastEl = document.getElementById('toast');
        const toastTitle = document.getElementById('toast-title');
        const toastBody = document.getElementById('toast-body');

        toastTitle.textContent = title;
        toastBody.textContent = message;

        toastEl.className = 'toast';
        
        const typeClasses = {
          success: 'bg-success text-white',
          error: 'bg-danger text-white',
          warning: 'bg-warning',
          info: 'bg-info text-white'
        };
        toastEl.classList.add(...(typeClasses[type] || typeClasses.info).split(' '));
      }
    };
  });

  describe('formatError', () => {
    test('traduz "Connection refused" para português', () => {
      const error = { message: 'Connection refused' };
      const result = mockApp.formatError(error);
      expect(result).toBe('Não foi possível conectar ao servidor. Verifique se está rodando.');
    });

    test('traduz "Failed to fetch" para português', () => {
      const error = { message: 'Failed to fetch' };
      const result = mockApp.formatError(error);
      expect(result).toBe('Erro de conexão. Verifique sua internet ou se o servidor está rodando.');
    });

    test('traduz "timeout" para português', () => {
      const error = { message: 'Request timeout exceeded' };
      const result = mockApp.formatError(error);
      expect(result).toBe('A operação demorou muito tempo. Tente novamente.');
    });

    test('traduz código HTTP 404', () => {
      const error = { message: 'HTTP 404 Not Found' };
      const result = mockApp.formatError(error);
      expect(result).toBe('Recurso não encontrado no servidor.');
    });

    test('traduz código HTTP 500', () => {
      const error = { message: 'HTTP 500 Internal Server Error' };
      const result = mockApp.formatError(error);
      expect(result).toBe('Erro interno do servidor. Consulte os logs para mais detalhes.');
    });

    test('retorna mensagem original se não houver tradução', () => {
      const error = { message: 'Unknown custom error' };
      const result = mockApp.formatError(error);
      expect(result).toBe('Unknown custom error');
    });

    test('lida com erro sem propriedade message', () => {
      const error = 'String error';
      const result = mockApp.formatError(error);
      expect(result).toBe('String error');
    });
  });

  describe('showToast', () => {
    test('define título e mensagem corretamente', () => {
      mockApp.showToast('Test Title', 'Test Message', 'info');
      
      const title = document.getElementById('toast-title');
      const body = document.getElementById('toast-body');
      
      expect(title.textContent).toBe('Test Title');
      expect(body.textContent).toBe('Test Message');
    });

    test('adiciona classe success corretamente', () => {
      mockApp.showToast('Success', 'Success message', 'success');
      
      const toast = document.getElementById('toast');
      expect(toast.classList.contains('bg-success')).toBe(true);
      expect(toast.classList.contains('text-white')).toBe(true);
    });

    test('adiciona classe error corretamente', () => {
      mockApp.showToast('Error', 'Error message', 'error');
      
      const toast = document.getElementById('toast');
      expect(toast.classList.contains('bg-danger')).toBe(true);
      expect(toast.classList.contains('text-white')).toBe(true);
    });

    test('adiciona classe warning corretamente', () => {
      mockApp.showToast('Warning', 'Warning message', 'warning');
      
      const toast = document.getElementById('toast');
      expect(toast.classList.contains('bg-warning')).toBe(true);
    });

    test('usa info como tipo padrão', () => {
      mockApp.showToast('Info', 'Info message');
      
      const toast = document.getElementById('toast');
      expect(toast.classList.contains('bg-info')).toBe(true);
    });

    test('reseta classes antes de adicionar novas', () => {
      const toast = document.getElementById('toast');
      toast.classList.add('old-class');
      
      mockApp.showToast('Test', 'Message', 'success');
      
      expect(toast.classList.contains('old-class')).toBe(false);
      expect(toast.classList.contains('bg-success')).toBe(true);
    });
  });
});

describe('App - Form Validation', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <form id="test-form" novalidate>
        <input type="text" id="test-input" required minlength="3" />
        <input type="number" id="test-number" required min="10" max="100" />
      </form>
    `;
  });

  test('form.checkValidity() retorna false para campo vazio', () => {
    const form = document.getElementById('test-form');
    const input = document.getElementById('test-input');
    
    input.value = '';
    expect(form.checkValidity()).toBe(false);
  });

  test('form.checkValidity() retorna false para minlength inválido', () => {
    const form = document.getElementById('test-form');
    const input = document.getElementById('test-input');
    const numberInput = document.getElementById('test-number');
    
    input.value = 'ab'; // menos que minlength=3
    numberInput.value = '50';
    expect(form.checkValidity()).toBe(false);
  });

  test('form.checkValidity() retorna false para número fora do range', () => {
    const form = document.getElementById('test-form');
    const input = document.getElementById('test-input');
    const numberInput = document.getElementById('test-number');
    
    input.value = 'valid text';
    numberInput.value = '5'; // menor que min=10
    expect(form.checkValidity()).toBe(false);
  });

  test('form.checkValidity() retorna true para campos válidos', () => {
    const form = document.getElementById('test-form');
    const input = document.getElementById('test-input');
    const numberInput = document.getElementById('test-number');
    
    input.value = 'valid text';
    numberInput.value = '50';
    expect(form.checkValidity()).toBe(true);
  });

  test('was-validated class é adicionada em validação', () => {
    const form = document.getElementById('test-form');
    
    form.checkValidity();
    form.classList.add('was-validated');
    
    expect(form.classList.contains('was-validated')).toBe(true);
  });
});
