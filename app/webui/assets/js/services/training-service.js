/**
 * Training Service
 * Sprint 7 Task 7.3: Domain service for training operations
 * 
 * Encapsulates all training-related API calls and business logic
 */

class TrainingService {
    constructor(apiClient) {
        this.api = apiClient;
    }

    async getCheckpoints() {
        return this.api.get('/training/checkpoints');
    }

    async getDatasets() {
        return this.api.get('/training/datasets');
    }

    async getDatasetStats(datasetPath) {
        return this.api.post('/training/dataset/stats', { dataset_path: datasetPath });
    }

    async downloadVideos(urls, folder) {
        return this.api.post('/training/dataset/download', { urls, folder });
    }

    async segmentAudio(datasetPath) {
        return this.api.post('/training/dataset/segment', { dataset_path: datasetPath });
    }

    async transcribeDataset(datasetPath, language = 'pt') {
        return this.api.post('/training/dataset/transcribe', {
            dataset_path: datasetPath,
            language
        });
    }

    async startTraining(config) {
        const payload = {
            model_name: config.modelName,
            dataset_path: config.datasetPath,
            epochs: parseInt(config.epochs),
            batch_size: parseInt(config.batchSize),
            learning_rate: parseFloat(config.learningRate),
            use_deepspeed: config.useDeepspeed || false,
        };
        return this.api.post('/training/start', payload);
    }

    async stopTraining() {
        return this.api.post('/training/stop');
    }

    async getStatus() {
        return this.api.get('/training/status');
    }

    async getLogs(lines = 100) {
        return this.api.get(\`/training/logs?lines=\${lines}\`);
    }

    async synthesize(checkpoint, text, options = {}) {
        return this.api.post('/training/inference/synthesize', {
            checkpoint,
            text,
            temperature: options.temperature || 0.7,
            speed: options.speed || 1.0,
            language: options.language || 'pt'
        });
    }

    async getSamples() {
        return this.api.get('/training/samples');
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TrainingService };
} else {
    window.TrainingService = TrainingService;
}
