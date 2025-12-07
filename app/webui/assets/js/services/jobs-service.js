/**
 * Jobs Service
 * Sprint 7 Task 7.3: Domain service for synthesis jobs
 */

class JobsService {
    constructor(apiClient) {
        this.api = apiClient;
    }

    async getJobs(filters = {}) {
        let url = '/jobs';
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.limit) params.append('limit', filters.limit);
        if (params.toString()) url += '?' + params.toString();
        return this.api.get(url);
    }

    async getJob(jobId) {
        return this.api.get(\`/jobs/\${jobId}\`);
    }

    async createJob(jobData) {
        return this.api.post('/jobs/clone', {
            text: jobData.text,
            source_language: jobData.sourceLanguage || 'pt',
            voice_profile_id: jobData.voiceProfileId,
            quality_profile: jobData.qualityProfile || 'balanced',
            mode: jobData.mode || 'tts'
        });
    }

    async deleteJob(jobId) {
        return this.api.delete(\`/jobs/\${jobId}\`);
    }

    async pollJobStatus(jobId, onUpdate, interval = 2000, timeout = 300000) {
        const startTime = Date.now();
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    if (Date.now() - startTime > timeout) {
                        reject(new Error('Job polling timeout'));
                        return;
                    }
                    const status = await this.api.get(\`/jobs/\${jobId}/status\`);
                    if (onUpdate) onUpdate(status);
                    if (status.status === 'completed') {
                        resolve(status);
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Job failed'));
                    } else {
                        setTimeout(poll, interval);
                    }
                } catch (error) {
                    reject(error);
                }
            };
            poll();
        });
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { JobsService };
} else {
    window.JobsService = JobsService;
}
