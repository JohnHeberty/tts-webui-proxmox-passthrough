# 📚 API Reference - TTS WebUI Training System

**Version**: 2.0.1  
**Base URL**: `http://localhost:8000`  
**Last Updated**: 2025-12-10

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Dataset Management](#dataset-management)
4. [Training Control](#training-control)
5. [Checkpoint Management](#checkpoint-management)
6. [Inference & Testing](#inference--testing)
7. [Error Codes](#error-codes)
8. [Rate Limits](#rate-limits)

---

## 🎯 Overview

The TTS WebUI Training System provides a comprehensive REST API for managing XTTS-v2 fine-tuning workflows:

- **Dataset Management**: Download, segment, and transcribe audio datasets
- **Training Control**: Start, stop, and monitor training jobs
- **Checkpoint Management**: List and load model checkpoints
- **Inference Testing**: Synthesize audio and perform A/B comparisons

### Base Endpoints

```
/training/*          - Training management endpoints
/files/*             - Static file serving
/webui               - Web interface
```

---

## 🔐 Authentication

**Current Status**: No authentication required (development)

**Production**: Add JWT bearer token:
```http
Authorization: Bearer <token>
```

---

## 📦 Dataset Management

### Download YouTube Videos

**POST** `/training/dataset/download`

Download audio from YouTube videos and prepare for training.

**Request Body**:
```json
{
  "urls": [
    "https://youtube.com/watch?v=VIDEO_ID_1",
    "https://youtube.com/watch?v=VIDEO_ID_2"
  ],
  "folder": "datasets/my_voice"
}
```

**Response** (200 OK):
```json
{
  "status": "started",
  "videos": 2,
  "output_folder": "datasets/my_voice/raw"
}
```

**Errors**:
- `400`: Invalid URL format
- `500`: Download failed

**Notes**:
- Runs in background using BackgroundTasks
- Audio extracted at 22050Hz mono WAV
- Progress tracked via logs

---

### Segment Audio Files

**POST** `/training/dataset/segment`

Segment audio files using Voice Activity Detection (VAD).

**Request Body**:
```json
{
  "folder": "datasets/my_voice",
  "min_duration": 7.0,
  "max_duration": 12.0,
  "vad_threshold": -40.0
}
```

**Parameters**:
- `folder` (string, required): Dataset folder path
- `min_duration` (float, 3.0-15.0): Minimum segment duration in seconds
- `max_duration` (float, 5.0-20.0): Maximum segment duration in seconds
- `vad_threshold` (float, -60.0 to -20.0): VAD threshold in dB

**Response** (200 OK):
```json
{
  "status": "started",
  "input_folder": "datasets/my_voice/raw",
  "output_folder": "datasets/my_voice/segments"
}
```

**Errors**:
- `404`: Folder not found
- `422`: Invalid parameter values
- `500`: Segmentation failed

**Processing Details**:
- Uses RMS energy-based VAD
- Applies fade-in/fade-out (50ms)
- Normalizes to -20dB LUFS
- Outputs 22050Hz mono WAV

---

### Transcribe Dataset

**POST** `/training/dataset/transcribe`

Transcribe audio files using Whisper.

**Request Body**:
```json
{
  "folder": "datasets/my_voice"
}
```

**Response** (200 OK):
```json
{
  "status": "started",
  "folder": "datasets/my_voice/segments"
}
```

**Errors**:
- `404`: Folder not found
- `500`: Transcription failed

**Notes**:
- Uses Whisper `base` model by default
- Generates `metadata.csv` (LJSpeech format)
- Parallel processing across CPU cores
- Portuguese BR normalization applied

---

### Get Dataset Statistics

**GET** `/training/dataset/stats?folder=datasets/my_voice`

Get statistics about a dataset.

**Query Parameters**:
- `folder` (string): Dataset folder path (default: `datasets/my_voice`)

**Response** (200 OK):
```json
{
  "files": 4922,
  "total_hours": 15.3,
  "transcribed_percent": 100.0
}
```

**Response Fields**:
- `files` (int): Number of audio files
- `total_hours` (float): Total duration in hours
- `transcribed_percent` (float): Percentage of files transcribed (0-100)

---

### List Dataset Files

**GET** `/training/dataset/files?folder=datasets/my_voice&limit=100`

List files in a dataset.

**Query Parameters**:
- `folder` (string): Dataset folder path
- `limit` (int): Maximum files to return (default: 100)

**Response** (200 OK):
```json
{
  "files": [
    {
      "name": "segment_00001.wav",
      "size": 264600,
      "path": "datasets/my_voice/segments/segment_00001.wav"
    }
  ]
}
```

---

## 🎓 Training Control

### Start Training

**POST** `/training/start`

Start XTTS-v2 fine-tuning.

**Request Body**:
```json
{
  "model_name": "my_voice_model",
  "dataset_folder": "datasets/my_voice",
  "epochs": 100,
  "batch_size": 4,
  "learning_rate": 0.0001,
  "use_deepspeed": false
}
```

**Parameters**:
- `model_name` (string, required): Name for the trained model
- `dataset_folder` (string, required): Path to dataset
- `epochs` (int, 10-1000): Number of training epochs
- `batch_size` (int, 1-16): Batch size
- `learning_rate` (float, 0.00001-0.01): Learning rate
- `use_deepspeed` (bool): Enable DeepSpeed (multi-GPU)

**Response** (200 OK):
```json
{
  "status": "started",
  "model_name": "my_voice_model",
  "output_folder": "train/output/my_voice_model"
}
```

**Errors**:
- `400`: Training already running
- `404`: Dataset not found
- `422`: Invalid parameters
- `500`: Training initialization failed

**Notes**:
- Runs in background process
- Checkpoints saved every N epochs
- Logs streamed to `/training/logs`
- Status polled via `/training/status`

---

### Stop Training

**POST** `/training/stop`

Stop running training.

**Response** (200 OK):
```json
{
  "status": "stopped"
}
```

**Errors**:
- `400`: No training running

**Notes**:
- Gracefully terminates training process
- Last checkpoint preserved
- Logs available for review

---

### Get Training Status

**GET** `/training/status`

Get current training status and progress.

**Response** (200 OK):
```json
{
  "state": "running",
  "epoch": 45,
  "total_epochs": 100,
  "loss": 0.0234,
  "progress": 45,
  "logs": "Epoch 45/100 - Loss: 0.0234..."
}
```

**Response Fields**:
- `state` (string): `idle`, `running`, `completed`, `failed`, `stopped`
- `epoch` (int): Current epoch number
- `total_epochs` (int): Total epochs configured
- `loss` (float|null): Current loss value
- `progress` (int): Progress percentage (0-100)
- `logs` (string): Recent log lines (last 50)

**Polling Recommendation**: Poll every 5 seconds during training

---

### Get Training Logs

**GET** `/training/logs`

Get full training logs.

**Response** (200 OK):
```json
{
  "logs": "Full training log content..."
}
```

---

## 💾 Checkpoint Management

### List Checkpoints

**GET** `/training/checkpoints?model_name=my_voice_model`

List available model checkpoints.

**Query Parameters**:
- `model_name` (string, optional): Filter by model name (omit for all models)

**Response** (200 OK):
```json
[
  {
    "name": "checkpoint_epoch_100",
    "path": "train/output/my_voice_model/checkpoints/checkpoint_epoch_100.pth",
    "epoch": 100,
    "date": "2025-12-06 14:30",
    "size_mb": 235.67
  }
]
```

**Response Fields**:
- `name` (string): Checkpoint display name
- `path` (string): Full file path
- `epoch` (int): Training epoch number
- `date` (string): Creation timestamp
- `size_mb` (float): File size in megabytes

**Sorting**: Newest first by date

---

### Load Checkpoint

**POST** `/training/checkpoints/load?checkpoint_path=path/to/checkpoint.pth`

Load a checkpoint for inference.

**Query Parameters**:
- `checkpoint_path` (string, required): Path to checkpoint file

**Response** (200 OK):
```json
{
  "status": "loaded",
  "checkpoint": "train/output/my_voice_model/checkpoints/epoch_100.pth"
}
```

**Errors**:
- `404`: Checkpoint not found
- `500`: Loading failed

---

## 🎤 Inference & Testing

### Synthesize Audio

**POST** `/training/inference/synthesize`

Synthesize audio using a fine-tuned checkpoint.

**Request Body**:
```json
{
  "checkpoint": "train/output/my_voice_model/checkpoints/epoch_100.pth",
  "text": "Este é um teste de síntese de voz em português brasileiro.",
  "temperature": 0.7,
  "speed": 1.0
}
```

**Parameters**:
- `checkpoint` (string, required): Path to checkpoint
- `text` (string, required): Text to synthesize
- `temperature` (float, 0.1-1.5): Sampling temperature (higher = more variation)
- `speed` (float, 0.5-2.0): Speech speed multiplier

**Response** (200 OK):
```json
{
  "status": "success",
  "audio_url": "/files/inference/inference_20251206_143000.wav",
  "text": "Este é um teste..."
}
```

**Errors**:
- `404`: Checkpoint not found
- `422`: Invalid parameters
- `500`: Synthesis failed
- `504`: Timeout (>60s)

**Audio Format**: 22050Hz mono WAV

---

### A/B Comparison Test

**POST** `/training/inference/ab-test`

Generate A/B comparison between base and fine-tuned models.

**Request Body**:
```json
{
  "checkpoint": "train/output/my_voice_model/checkpoints/epoch_100.pth",
  "text": "Texto para comparação de qualidade."
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "base_audio": "/files/ab_test/base_20251206_143000.wav",
  "finetuned_audio": "/files/ab_test/finetuned_20251206_143000.wav",
  "similarity": 85.5,
  "mfcc_score": 92.3
}
```

**Response Fields**:
- `base_audio` (string): URL to base model output
- `finetuned_audio` (string): URL to fine-tuned output
- `similarity` (float): Similarity score (0-100)
- `mfcc_score` (float): MFCC coefficient score (0-100)

**Use Case**: Compare model quality after fine-tuning

---

## ⚠️ Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request (e.g., training already running) |
| 404 | Not Found | Resource not found (file, checkpoint, etc.) |
| 422 | Unprocessable Entity | Validation error (invalid parameters) |
| 500 | Internal Server Error | Server error during processing |
| 504 | Gateway Timeout | Request timeout (e.g., inference > 60s) |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## 🚦 Rate Limits

**Current Status**: No rate limits (development)

**Production Recommendations**:
- Training endpoints: 1 request/minute
- Inference endpoints: 10 requests/minute
- Dataset queries: 60 requests/minute

---

## 📝 Examples

### Complete Training Workflow

```bash
# 1. Download dataset
curl -X POST http://localhost:8000/training/dataset/download \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://youtube.com/watch?v=VIDEO_ID"],
    "folder": "datasets/my_voice"
  }'

# 2. Segment audio
curl -X POST http://localhost:8000/training/dataset/segment \
  -H "Content-Type: application/json" \
  -d '{
    "folder": "datasets/my_voice",
    "min_duration": 7.0,
    "max_duration": 12.0,
    "vad_threshold": -40.0
  }'

# 3. Transcribe
curl -X POST http://localhost:8000/training/dataset/transcribe \
  -H "Content-Type: application/json" \
  -d '{"folder": "datasets/my_voice"}'

# 4. Start training
curl -X POST http://localhost:8000/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "my_voice_model",
    "dataset_folder": "datasets/my_voice",
    "epochs": 100,
    "batch_size": 4,
    "learning_rate": 0.0001
  }'

# 5. Monitor status (poll every 5s)
curl http://localhost:8000/training/status

# 6. List checkpoints
curl http://localhost:8000/training/checkpoints?model_name=my_voice_model

# 7. Test inference
curl -X POST http://localhost:8000/training/inference/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "checkpoint": "train/output/my_voice_model/checkpoints/epoch_100.pth",
    "text": "Teste de voz",
    "temperature": 0.7,
    "speed": 1.0
  }'
```

---

## 🔧 Integration Scripts

### Python Client Example

```python
import requests
import time

class TTSTrainingClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def download_dataset(self, urls, folder):
        response = requests.post(
            f"{self.base_url}/training/dataset/download",
            json={"urls": urls, "folder": folder}
        )
        return response.json()
    
    def start_training(self, model_name, dataset_folder, **kwargs):
        response = requests.post(
            f"{self.base_url}/training/start",
            json={
                "model_name": model_name,
                "dataset_folder": dataset_folder,
                **kwargs
            }
        )
        return response.json()
    
    def poll_status(self, interval=5):
        while True:
            response = requests.get(f"{self.base_url}/training/status")
            status = response.json()
            print(f"Epoch {status['epoch']}/{status['total_epochs']} - {status['progress']}%")
            
            if status['state'] in ['completed', 'failed', 'stopped']:
                break
            
            time.sleep(interval)
        
        return status

# Usage
client = TTSTrainingClient()
client.start_training("my_model", "datasets/my_voice", epochs=100)
client.poll_status()
```

---

## 📚 Additional Resources

- **WebUI**: http://localhost:8000/webui
- **OpenAPI Docs**: http://localhost:8000/docs (FastAPI auto-generated)
- **Source Code**: `/app/training_api.py`
- **Tests**: `/tests/test_training_api.py`

---

## 🆘 Support

For issues or questions:
1. Check error logs: `GET /training/logs`
2. Review dataset stats: `GET /training/dataset/stats`
3. Verify checkpoint existence: `GET /training/checkpoints`

**Common Issues**:
- **Training won't start**: Check dataset exists and has transcriptions
- **Low quality output**: Increase epochs, verify dataset quality
- **Out of memory**: Reduce batch_size or use DeepSpeed
