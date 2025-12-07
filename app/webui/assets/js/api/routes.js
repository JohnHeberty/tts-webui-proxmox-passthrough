/**
 * API Routes Constants
 * Sprint 7 Task 7.2: Centralize all API endpoints
 * 
 * Benefits:
 * - Single source of truth for URLs
 * - Easy to update endpoints
 * - Type-safe route parameters
 * - No hardcoded URLs in code
 */

export const ROUTES = {
    // Training endpoints
    training: {
        checkpoints: '/training/checkpoints',
        datasets: '/training/datasets',
        datasetStats: '/training/dataset/stats',
        datasetDownload: '/training/dataset/download',
        datasetSegment: '/training/dataset/segment',
        datasetTranscribe: '/training/dataset/transcribe',
        inference: '/training/inference/synthesize',
        start: '/training/start',
        stop: '/training/stop',
        status: '/training/status',
        logs: '/training/logs',
        samples: '/training/samples',
        checkpoint: (epoch) => `/training/checkpoints/epoch_${epoch}`,
    },

    // Voice profiles endpoints
    voices: {
        list: '/voices',
        create: '/voices',
        get: (id) => `/voices/${id}`,
        update: (id) => `/voices/${id}`,
        delete: (id) => `/voices/${id}`,
        upload: '/voices/upload',
    },

    // Jobs endpoints
    jobs: {
        list: '/jobs',
        create: '/jobs/clone',
        get: (id) => `/jobs/${id}`,
        delete: (id) => `/jobs/${id}`,
        status: (id) => `/jobs/${id}/status`,
        download: (id) => `/jobs/${id}/download`,
    },

    // Settings endpoints
    settings: {
        get: '/settings',
        update: '/settings',
        qualityProfiles: '/settings/quality-profiles',
    },

    // Downloads endpoints
    downloads: {
        list: '/downloads',
        get: (id) => `/downloads/${id}`,
        create: '/downloads',
        status: (id) => `/downloads/${id}/status`,
    },

    // System endpoints
    system: {
        health: '/health',
        status: '/status',
        metrics: '/metrics',
        gpu: '/gpu/status',
    },
};

// Helper to build URLs with query parameters
export function buildUrl(path, params = {}) {
    const url = new URL(path, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            url.searchParams.append(key, value);
        }
    });
    return url.pathname + url.search;
}

// Export for module systems or attach to window
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ROUTES, buildUrl };
} else {
    window.APIRoutes = { ROUTES, buildUrl };
}
