/**
 * Error Formatter Utility
 * Sprint 7: Extracted from app.js
 * 
 * Translates technical errors to user-friendly Portuguese messages
 */

const ERROR_TRANSLATIONS = {
    // Network errors
    'Failed to fetch': 'Não foi possível conectar ao servidor. Verifique se está rodando.',
    'Connection refused': 'Servidor offline ou inacessível',
    'Network error': 'Erro de rede. Verifique sua conexão.',
    'NetworkError': 'Erro de rede. Verifique sua conexão.',
    
    // Timeout errors
    'timeout': 'A operação demorou muito. Tente novamente.',
    'Request timeout': 'A requisição demorou muito tempo',
    'AbortError': 'Operação cancelada ou timeout',
    
    // HTTP errors
    'HTTP 400': 'Requisição inválida',
    'HTTP 401': 'Não autorizado. Faça login novamente.',
    'HTTP 403': 'Acesso negado',
    'HTTP 404': 'Recurso não encontrado',
    'HTTP 500': 'Erro interno do servidor. Consulte os logs.',
    'HTTP 502': 'Gateway inválido',
    'HTTP 503': 'Serviço temporariamente indisponível',
    
    // Application-specific errors
    'CUDA out of memory': 'VRAM insuficiente. Reduza o batch size ou feche outras aplicações.',
    'No CUDA': 'GPU não disponível. Usando CPU (mais lento).',
    'Checkpoint not found': 'Checkpoint não encontrado. Verifique o caminho.',
    'Dataset not found': 'Dataset não encontrado. Verifique a configuração.',
    'Invalid audio format': 'Formato de áudio inválido. Use WAV ou MP3.',
    'Audio too short': 'Áudio muito curto. Mínimo 3 segundos.',
    'Audio too long': 'Áudio muito longo. Máximo 30 segundos.',
    
    // Training errors
    'Training already running': 'Já existe um treinamento em execução',
    'No dataset configured': 'Nenhum dataset configurado',
    'Insufficient samples': 'Amostras insuficientes para treinar',
    
    // File upload errors
    'File too large': 'Arquivo muito grande',
    'Invalid file type': 'Tipo de arquivo inválido',
    'Upload failed': 'Falha no upload. Tente novamente.',
};

/**
 * Format error message to user-friendly Portuguese
 * 
 * @param {Error|string} error - Error object or message
 * @returns {string} Formatted error message in Portuguese
 */
function formatError(error) {
    // Handle Error objects
    const errorMessage = typeof error === 'string' ? error : (error.message || String(error));
    
    // Check for exact matches first
    if (ERROR_TRANSLATIONS[errorMessage]) {
        return ERROR_TRANSLATIONS[errorMessage];
    }
    
    // Check for partial matches
    for (const [key, translation] of Object.entries(ERROR_TRANSLATIONS)) {
        if (errorMessage.includes(key)) {
            return translation;
        }
    }
    
    // Fallback to original message (already user-friendly or unknown error)
    return errorMessage;
}

/**
 * Get severity level for error
 * 
 * @param {Error|string} error - Error object or message
 * @returns {string} Severity: 'danger', 'warning', or 'info'
 */
function getErrorSeverity(error) {
    const errorMessage = typeof error === 'string' ? error : (error.message || String(error));
    
    // Critical errors
    if (errorMessage.includes('500') || 
        errorMessage.includes('CUDA out of memory') ||
        errorMessage.includes('Failed to fetch')) {
        return 'danger';
    }
    
    // Warnings
    if (errorMessage.includes('timeout') ||
        errorMessage.includes('No CUDA') ||
        errorMessage.includes('404')) {
        return 'warning';
    }
    
    // Default
    return 'danger';
}

// Export for module systems or attach to window
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { formatError, getErrorSeverity, ERROR_TRANSLATIONS };
} else {
    window.ErrorFormatter = { formatError, getErrorSeverity, ERROR_TRANSLATIONS };
}
