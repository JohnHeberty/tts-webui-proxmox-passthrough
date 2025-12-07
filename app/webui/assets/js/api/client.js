/**
 * API Client for TTS WebUI
 * Sprint 7 Task 7.1: Extracted from app.js monolith
 * 
 * Handles all HTTP communication with the backend API
 * Features:
 * - Automatic timeout (60s default)
 * - AbortController support
 * - Error handling and translation
 * - JSON parsing
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.defaultTimeout = 60000; // 60 seconds
    }

    /**
     * Make an HTTP request with timeout support
     * 
     * @param {string} path - API endpoint path
     * @param {Object} options - Fetch options
     * @param {number} options.timeout - Request timeout in ms (default: 60000)
     * @returns {Promise<any>} Parsed JSON response
     * @throws {Error} Network, timeout, or HTTP errors
     */
    async request(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const timeout = options.timeout || this.defaultTimeout;
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            clearTimeout(timeoutId);

            // Handle HTTP errors
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage;
                
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || errorJson.message || errorText;
                } catch {
                    errorMessage = errorText || `HTTP ${response.status}`;
                }
                
                throw new Error(errorMessage);
            }

            // Parse JSON response
            const data = await response.json();
            return data;

        } catch (error) {
            clearTimeout(timeoutId);
            
            // Handle abort/timeout
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout (>${timeout / 1000}s)`);
            }
            
            // Re-throw other errors
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(path, options = {}) {
        return this.request(path, {
            ...options,
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(path, body, options = {}) {
        return this.request(path, {
            ...options,
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    /**
     * PUT request
     */
    async put(path, body, options = {}) {
        return this.request(path, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }

    /**
     * DELETE request
     */
    async delete(path, options = {}) {
        return this.request(path, {
            ...options,
            method: 'DELETE'
        });
    }

    /**
     * Upload file with multipart/form-data
     */
    async uploadFile(path, file, additionalData = {}, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add additional fields
        Object.entries(additionalData).forEach(([key, value]) => {
            formData.append(key, value);
        });

        const url = `${this.baseUrl}${path}`;
        const timeout = options.timeout || this.defaultTimeout;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                signal: controller.signal,
                // Don't set Content-Type - browser will set it with boundary
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || `HTTP ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error(`Upload timeout (>${timeout / 1000}s)`);
            }
            
            throw error;
        }
    }
}

// Export for module systems or attach to window for legacy
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
} else {
    window.ApiClient = ApiClient;
}
