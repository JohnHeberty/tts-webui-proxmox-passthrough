/**
 * Voice Profiles Service
 * Sprint 7 Task 7.3: Domain service for voice profile management
 */

class VoiceProfilesService {
    constructor(apiClient) {
        this.api = apiClient;
    }

    async getProfiles() {
        return this.api.get('/voices');
    }

    async getProfile(profileId) {
        return this.api.get(\`/voices/\${profileId}\`);
    }

    async createProfile(profileData) {
        return this.api.post('/voices', {
            name: profileData.name,
            description: profileData.description || '',
            language: profileData.language || 'pt'
        });
    }

    async updateProfile(profileId, updates) {
        return this.api.put(\`/voices/\${profileId}\`, updates);
    }

    async deleteProfile(profileId) {
        return this.api.delete(\`/voices/\${profileId}\`);
    }

    async uploadAudio(file, metadata = {}) {
        return this.api.uploadFile('/voices/upload', file, metadata);
    }

    validateAudioFile(file) {
        const errors = [];
        const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3'];
        if (!validTypes.includes(file.type)) {
            errors.push('Formato inválido. Use WAV ou MP3.');
        }
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            errors.push('Arquivo muito grande. Máximo 10MB.');
        }
        return { valid: errors.length === 0, errors };
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VoiceProfilesService };
} else {
    window.VoiceProfilesService = VoiceProfilesService;
}
