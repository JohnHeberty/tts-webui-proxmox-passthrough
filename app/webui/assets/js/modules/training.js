/**
 * Training Module - Manages dataset, training, and inference operations
 * Extracted from app.js for better maintainability
 */

export class TrainingManager {
    constructor(api, showToast) {
        this.api = api;
        this.showToast = showToast;
        this.trainingPollInterval = null;
    }

    /**
     * Initialize training section
     */
    async loadTrainingSection() {
        console.log('🎓 Loading training section');
        await this.loadDatasetStats();
        await this.loadCheckpoints();
    }

    /**
     * Load dataset statistics
     */
    async loadDatasetStats() {
        try {
            const response = await this.api('/training/dataset/stats');
            const stats = await response.json();
            
            const statsContainer = document.getElementById('dataset-stats');
            if (!stats.files || stats.files === 0) {
                statsContainer.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="bi bi-folder-x" style="font-size: 3rem;"></i>
                        <p class="mt-2">Nenhum dataset carregado</p>
                    </div>
                `;
                return;
            }

            statsContainer.innerHTML = `
                <div class="row text-center">
                    <div class="col-6 mb-3">
                        <h3 class="mb-0">${stats.files}</h3>
                        <small class="text-muted">Arquivos</small>
                    </div>
                    <div class="col-6 mb-3">
                        <h3 class="mb-0">${Math.round(stats.total_hours * 10) / 10}h</h3>
                        <small class="text-muted">Duração Total</small>
                    </div>
                    <div class="col-12">
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-success" style="width: ${stats.transcribed_percent}%">
                                ${stats.transcribed_percent}% Transcrito
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('❌ Error loading dataset stats:', error);
        }
    }

    /**
     * Load checkpoints list
     */
    async loadCheckpoints() {
        try {
            const response = await this.api('/training/checkpoints');
            const checkpoints = await response.json();
            
            const checkpointList = document.getElementById('checkpoint-list');
            const inferenceSelect = document.getElementById('inference-checkpoint');
            
            if (!checkpoints || checkpoints.length === 0) {
                checkpointList.innerHTML = '<p class="p-3 text-muted mb-0">Nenhum checkpoint disponível</p>';
                inferenceSelect.innerHTML = '<option value="">Selecione um checkpoint...</option>';
                return;
            }

            // Update checkpoint list
            checkpointList.innerHTML = checkpoints.map(cp => `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${cp.name}</strong>
                            <br>
                            <small class="text-muted">Epoch ${cp.epoch} • ${cp.date}</small>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="app.training.loadCheckpoint('${cp.path}')">
                            <i class="bi bi-box-arrow-in-down"></i>
                        </button>
                    </div>
                </div>
            `).join('');

            // Update inference select
            inferenceSelect.innerHTML = '<option value="">Selecione um checkpoint...</option>' +
                checkpoints.map(cp => `<option value="${cp.path}">${cp.name} (Epoch ${cp.epoch})</option>`).join('');

        } catch (error) {
            console.error('❌ Error loading checkpoints:', error);
        }
    }

    /**
     * Download videos from YouTube URLs
     */
    async downloadVideos() {
        const urls = document.getElementById('youtube-urls').value.split('\n').filter(u => u.trim());
        const folder = document.getElementById('dataset-folder').value;

        if (urls.length === 0) {
            this.showToast('Insira pelo menos uma URL', 'warning');
            return;
        }

        try {
            const progressDiv = document.getElementById('download-progress');
            progressDiv.style.display = 'block';

            const response = await this.api('/training/dataset/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({urls, folder})
            });

            const result = await response.json();
            
            // Update progress bar
            const progressBar = document.getElementById('download-progress-bar');
            progressBar.style.width = '100%';
            document.getElementById('download-status').textContent = `${result.downloaded} vídeos baixados`;

            this.showToast('Download concluído', 'success');
            await this.loadDatasetStats();
        } catch (error) {
            console.error('❌ Error downloading videos:', error);
            this.showToast('Erro ao baixar vídeos', 'danger');
        }
    }

    /**
     * Segment audio files using VAD
     */
    async segmentAudio() {
        const folder = document.getElementById('dataset-folder').value;
        const minDuration = document.getElementById('segment-min-duration').value;
        const maxDuration = document.getElementById('segment-max-duration').value;
        const vadThreshold = document.getElementById('vad-threshold').value;

        try {
            const response = await this.api('/training/dataset/segment', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    folder,
                    min_duration: parseFloat(minDuration),
                    max_duration: parseFloat(maxDuration),
                    vad_threshold: parseFloat(vadThreshold)
                })
            });

            const result = await response.json();
            this.showToast('Segmentação iniciada', 'success');
            await this.loadDatasetStats();
        } catch (error) {
            console.error('❌ Error segmenting audio:', error);
            this.showToast('Erro ao segmentar áudio', 'danger');
        }
    }

    /**
     * Transcribe dataset using Whisper
     */
    async transcribeDataset() {
        const folder = document.getElementById('dataset-folder').value;

        try {
            const response = await this.api('/training/dataset/transcribe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({folder})
            });

            const result = await response.json();
            this.showToast('Transcrição iniciada', 'success');
        } catch (error) {
            console.error('❌ Error transcribing dataset:', error);
            this.showToast('Erro ao transcrever dataset', 'danger');
        }
    }

    /**
     * Start training process
     */
    async startTraining() {
        const modelName = document.getElementById('model-name').value;
        const datasetFolder = document.getElementById('training-dataset-folder').value;
        const epochs = document.getElementById('training-epochs').value;
        const batchSize = document.getElementById('training-batch-size').value;
        const learningRate = document.getElementById('training-lr').value;
        const useDeepspeed = document.getElementById('training-use-deepspeed').checked;

        try {
            const response = await this.api('/training/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    model_name: modelName,
                    dataset_folder: datasetFolder,
                    epochs: parseInt(epochs),
                    batch_size: parseInt(batchSize),
                    learning_rate: parseFloat(learningRate),
                    use_deepspeed: useDeepspeed
                })
            });

            const result = await response.json();
            
            this.showToast('Treinamento iniciado', 'success');
            document.getElementById('btn-start-training').style.display = 'none';
            document.getElementById('btn-stop-training').style.display = 'block';

            // Start polling training status
            this.startPollingStatus();
        } catch (error) {
            console.error('❌ Error starting training:', error);
            this.showToast('Erro ao iniciar treinamento', 'danger');
        }
    }

    /**
     * Stop training process
     */
    async stopTraining() {
        try {
            await this.api('/training/stop', {method: 'POST'});
            this.showToast('Treinamento interrompido', 'warning');
            document.getElementById('btn-start-training').style.display = 'block';
            document.getElementById('btn-stop-training').style.display = 'none';
            this.stopPollingStatus();
        } catch (error) {
            console.error('❌ Error stopping training:', error);
        }
    }

    /**
     * Start polling training status
     */
    startPollingStatus() {
        this.trainingPollInterval = setInterval(async () => {
            await this.pollTrainingStatus();
        }, 5000); // Poll every 5 seconds
    }

    /**
     * Stop polling training status
     */
    stopPollingStatus() {
        if (this.trainingPollInterval) {
            clearInterval(this.trainingPollInterval);
            this.trainingPollInterval = null;
        }
    }

    /**
     * Poll training status
     */
    async pollTrainingStatus() {
        try {
            const response = await this.api('/training/status');
            const status = await response.json();

            if (status.state === 'completed' || status.state === 'failed') {
                this.stopPollingStatus();
                document.getElementById('btn-start-training').style.display = 'block';
                document.getElementById('btn-stop-training').style.display = 'none';
            }

            // Update status display
            const statusDiv = document.getElementById('training-status');
            statusDiv.innerHTML = `
                <p><strong>Estado:</strong> ${status.state}</p>
                <p><strong>Epoch:</strong> ${status.epoch}/${status.total_epochs}</p>
                <p><strong>Loss:</strong> ${status.loss?.toFixed(4) || 'N/A'}</p>
                <div class="progress">
                    <div class="progress-bar" style="width: ${status.progress}%">${status.progress}%</div>
                </div>
            `;

            // Update logs
            if (status.logs) {
                document.getElementById('training-logs').textContent = status.logs;
            }

            // Reload checkpoints if new ones are available
            await this.loadCheckpoints();

        } catch (error) {
            console.error('❌ Error polling training status:', error);
            this.stopPollingStatus();
        }
    }

    /**
     * Run inference with selected checkpoint
     */
    async runInference() {
        const checkpoint = document.getElementById('inference-checkpoint').value;
        const text = document.getElementById('inference-text').value;
        const temperature = document.getElementById('inference-temperature').value;
        const speed = document.getElementById('inference-speed').value;

        if (!checkpoint || !text) {
            this.showToast('Selecione um checkpoint e insira texto', 'warning');
            return;
        }

        try {
            const response = await this.api('/training/inference/synthesize', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    checkpoint,
                    text,
                    temperature: parseFloat(temperature),
                    speed: parseFloat(speed)
                })
            });

            const result = await response.json();
            
            const resultDiv = document.getElementById('inference-result');
            resultDiv.style.display = 'block';
            document.getElementById('inference-audio').src = result.audio_url;

            this.showToast('Síntese concluída', 'success');
        } catch (error) {
            console.error('❌ Error running inference:', error);
            this.showToast('Erro ao sintetizar', 'danger');
        }
    }

    /**
     * Generate A/B comparison between base and finetuned model
     */
    async generateABComparison() {
        const checkpoint = document.getElementById('inference-checkpoint').value;
        const text = document.getElementById('inference-text').value;

        if (!checkpoint || !text) {
            this.showToast('Selecione um checkpoint e insira texto', 'warning');
            return;
        }

        try {
            const response = await this.api('/training/inference/ab-test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({checkpoint, text})
            });

            const result = await response.json();
            
            document.getElementById('ab-audio-base').src = result.base_audio;
            document.getElementById('ab-audio-finetuned').src = result.finetuned_audio;
            
            const metricsDiv = document.getElementById('quality-metrics');
            metricsDiv.innerHTML = `
                <div class="mb-2">
                    <strong>Similaridade:</strong> ${result.similarity}%
                </div>
                <div class="mb-2">
                    <strong>MFCC Score:</strong> ${result.mfcc_score}%
                </div>
            `;

            this.showToast('Comparação A/B gerada', 'success');
        } catch (error) {
            console.error('❌ Error generating A/B comparison:', error);
            this.showToast('Erro ao gerar comparação A/B', 'danger');
        }
    }

    /**
     * Load checkpoint for inference
     */
    async loadCheckpoint(path) {
        console.log('Loading checkpoint:', path);
        document.getElementById('inference-checkpoint').value = path;
        this.showToast('Checkpoint selecionado', 'success');
    }

    /**
     * Clear training logs
     */
    clearTrainingLogs() {
        document.getElementById('training-logs').textContent = 'Logs limpos...';
    }

    /**
     * Download inference audio result
     */
    downloadInferenceAudio() {
        const audio = document.getElementById('inference-audio');
        const link = document.createElement('a');
        link.href = audio.src;
        link.download = 'inference_result.wav';
        link.click();
    }
}
