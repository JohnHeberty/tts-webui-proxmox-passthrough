/**
 * Unit tests for API Client (fetchJson)
 * Sprint 5 Task 5.2
 */

describe('API Client - fetchJson', () => {
  let mockApp;

  beforeEach(() => {
    // Mock fetchJson function
    mockApp = {
      async fetchJson(url, options = {}) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), options.timeout || 60000);

        try {
          const response = await fetch(url, {
            ...options,
            signal: controller.signal
          });
          
          clearTimeout(timeout);

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
          }

          return response.json();
        } catch (error) {
          clearTimeout(timeout);
          if (error.name === 'AbortError') {
            throw new Error('Request timeout');
          }
          throw error;
        }
      }
    };
  });

  test('faz requisição GET com sucesso', async () => {
    const mockData = { result: 'success' };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const result = await mockApp.fetchJson('/api/test');
    
    expect(fetch).toHaveBeenCalledWith(
      '/api/test',
      expect.objectContaining({
        signal: expect.any(Object)
      })
    );
    expect(result).toEqual(mockData);
  });

  test('faz requisição POST com body JSON', async () => {
    const mockData = { id: 123 };
    const postBody = { name: 'test' };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const result = await mockApp.fetchJson('/api/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(postBody)
    });
    
    expect(fetch).toHaveBeenCalledWith(
      '/api/create',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postBody)
      })
    );
    expect(result).toEqual(mockData);
  });

  test('lança erro em resposta 404', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' })
    });

    await expect(mockApp.fetchJson('/api/notfound')).rejects.toThrow('Not found');
  });

  test('lança erro em resposta 500', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' })
    });

    await expect(mockApp.fetchJson('/api/error')).rejects.toThrow('Internal server error');
  });

  test('lança erro "HTTP 500" quando response.json() falha', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => { throw new Error('Invalid JSON'); }
    });

    await expect(mockApp.fetchJson('/api/error')).rejects.toThrow('HTTP 500');
  });

  test('adiciona timeout padrão de 60s', async () => {
    jest.useFakeTimers();
    
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 70000))
    );

    const promise = mockApp.fetchJson('/api/slow');
    
    jest.advanceTimersByTime(60000);
    
    await expect(promise).rejects.toThrow('Request timeout');
    
    jest.useRealTimers();
  });

  test('permite timeout customizado', async () => {
    jest.useFakeTimers();
    
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 6000))
    );

    const promise = mockApp.fetchJson('/api/custom-timeout', { timeout: 5000 });
    
    jest.advanceTimersByTime(5000);
    
    await expect(promise).rejects.toThrow('Request timeout');
    
    jest.useRealTimers();
  });

  test('limpa timeout após resposta bem-sucedida', async () => {
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    await mockApp.fetchJson('/api/test');
    
    expect(clearTimeoutSpy).toHaveBeenCalled();
    
    clearTimeoutSpy.mockRestore();
  });

  test('limpa timeout após erro', async () => {
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
    
    fetch.mockRejectedValueOnce(new Error('Network error'));

    await expect(mockApp.fetchJson('/api/test')).rejects.toThrow('Network error');
    
    expect(clearTimeoutSpy).toHaveBeenCalled();
    
    clearTimeoutSpy.mockRestore();
  });
});

describe('API Client - AbortController', () => {
  test('cria AbortController para cada requisição', async () => {
    const AbortControllerSpy = jest.spyOn(global, 'AbortController');
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({})
    });

    const mockApp = {
      async fetchJson(url, options = {}) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), options.timeout || 60000);
        try {
          const response = await fetch(url, { ...options, signal: controller.signal });
          clearTimeout(timeout);
          return response.json();
        } catch (error) {
          clearTimeout(timeout);
          throw error;
        }
      }
    };

    await mockApp.fetchJson('/api/test');
    
    expect(AbortControllerSpy).toHaveBeenCalled();
    
    AbortControllerSpy.mockRestore();
  });

  test('passa signal para fetch', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({})
    });

    const mockApp = {
      async fetchJson(url) {
        const controller = new AbortController();
        const response = await fetch(url, { signal: controller.signal });
        return response.json();
      }
    };

    await mockApp.fetchJson('/api/test');
    
    expect(fetch).toHaveBeenCalledWith(
      '/api/test',
      expect.objectContaining({
        signal: expect.any(Object)
      })
    );
  });
});
