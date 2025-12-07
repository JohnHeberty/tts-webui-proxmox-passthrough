"""
Tests for Training API Endpoints

Coverage:
- Dataset management (download, segment, transcribe, stats)
- Training control (start, stop, status)
- Checkpoint management
- Inference testing
"""
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ==================== DATASET MANAGEMENT TESTS ====================

def test_dataset_stats_empty():
    """Test dataset stats with no data"""
    response = client.get("/training/dataset/stats?folder=datasets/nonexistent")
    
    assert response.status_code == 200
    data = response.json()
    assert data["files"] == 0
    assert data["total_hours"] == 0
    assert data["transcribed_percent"] == 0


@patch("app.training_api.Path")
def test_dataset_stats_with_files(mock_path):
    """Test dataset stats with existing files"""
    # Mock file system
    mock_segments_dir = MagicMock()
    mock_segments_dir.exists.return_value = True
    
    # Mock 10 audio files
    mock_files = [MagicMock(name=f"segment_{i}.wav") for i in range(10)]
    mock_segments_dir.glob.return_value = mock_files
    
    # Mock metadata file
    mock_metadata = MagicMock()
    mock_metadata.exists.return_value = True
    
    mock_path.return_value.__truediv__.side_effect = lambda x: mock_segments_dir if x == "segments" else mock_metadata
    
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.__iter__.return_value = ["header"] + ["line"] * 8
        
        response = client.get("/training/dataset/stats?folder=datasets/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["files"] == 10
        assert data["total_hours"] > 0


def test_dataset_download_request():
    """Test dataset download endpoint"""
    request_data = {
        "urls": [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2"
        ],
        "folder": "datasets/test_voice"
    }
    
    with patch("app.training_api.Path") as mock_path:
        mock_dir = MagicMock()
        mock_dir.mkdir = MagicMock()
        mock_path.return_value.__truediv__.return_value = mock_dir
        
        response = client.post("/training/dataset/download", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["videos"] == 2


def test_dataset_segment_request():
    """Test dataset segmentation endpoint"""
    request_data = {
        "folder": "datasets/test_voice",
        "min_duration": 7.0,
        "max_duration": 12.0,
        "vad_threshold": -40.0
    }
    
    with patch("app.training_api.Path") as mock_path:
        # Mock raw directory exists
        mock_raw_dir = MagicMock()
        mock_raw_dir.exists.return_value = True
        
        mock_segments_dir = MagicMock()
        mock_segments_dir.mkdir = MagicMock()
        
        mock_path.return_value.__truediv__.side_effect = [mock_raw_dir, mock_segments_dir]
        
        response = client.post("/training/dataset/segment", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"


def test_dataset_segment_folder_not_found():
    """Test segmentation with nonexistent folder"""
    request_data = {
        "folder": "datasets/nonexistent",
        "min_duration": 7.0,
        "max_duration": 12.0,
        "vad_threshold": -40.0
    }
    
    response = client.post("/training/dataset/segment", json=request_data)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_dataset_transcribe_request():
    """Test dataset transcription endpoint"""
    request_data = {
        "folder": "datasets/test_voice"
    }
    
    with patch("app.training_api.Path") as mock_path:
        mock_segments_dir = MagicMock()
        mock_segments_dir.exists.return_value = True
        
        mock_path.return_value.__truediv__.return_value = mock_segments_dir
        
        response = client.post("/training/dataset/transcribe", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"


def test_list_dataset_files():
    """Test listing dataset files"""
    with patch("app.training_api.Path") as mock_path:
        mock_segments_dir = MagicMock()
        mock_segments_dir.exists.return_value = True
        
        # Mock files
        mock_files = []
        for i in range(5):
            mock_file = MagicMock()
            mock_file.name = f"segment_{i}.wav"
            mock_file.stat.return_value.st_size = 1024 * 100  # 100KB
            mock_files.append(mock_file)
        
        mock_segments_dir.glob.return_value = mock_files
        mock_path.return_value.__truediv__.return_value = mock_segments_dir
        
        response = client.get("/training/dataset/files?folder=datasets/test")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 5


# ==================== TRAINING CONTROL TESTS ====================

def test_training_start():
    """Test starting training"""
    request_data = {
        "model_name": "test_model",
        "dataset_folder": "datasets/test_voice",
        "epochs": 100,
        "batch_size": 4,
        "learning_rate": 0.0001,
        "use_deepspeed": False
    }
    
    with patch("app.training_api.Path") as mock_path:
        # Mock dataset exists
        mock_dataset_dir = MagicMock()
        mock_dataset_dir.exists.return_value = True
        
        mock_output_dir = MagicMock()
        mock_output_dir.mkdir = MagicMock()
        
        mock_path.return_value.__truediv__.side_effect = [
            mock_dataset_dir,  # dataset_folder/segments
            mock_output_dir,   # train/output/model_name
        ]
        
        response = client.post("/training/start", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["model_name"] == "test_model"


def test_training_start_dataset_not_found():
    """Test starting training with missing dataset"""
    request_data = {
        "model_name": "test_model",
        "dataset_folder": "datasets/nonexistent",
        "epochs": 100,
        "batch_size": 4,
        "learning_rate": 0.0001,
        "use_deepspeed": False
    }
    
    response = client.post("/training/start", json=request_data)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_training_status():
    """Test getting training status"""
    response = client.get("/training/status")
    
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "epoch" in data
    assert "progress" in data


def test_training_logs():
    """Test getting training logs"""
    response = client.get("/training/logs")
    
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data


@patch("app.training_api.training_state")
def test_training_stop_when_running(mock_state):
    """Test stopping running training"""
    mock_process = MagicMock()
    mock_state.__getitem__.side_effect = lambda x: {
        "is_running": True,
        "process": mock_process,
        "status": {"state": "running", "logs": ""}
    }[x]
    
    response = client.post("/training/stop")
    
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"


def test_training_stop_when_not_running():
    """Test stopping when no training running"""
    response = client.post("/training/stop")
    
    assert response.status_code == 400
    assert "no training" in response.json()["detail"].lower()


# ==================== CHECKPOINT MANAGEMENT TESTS ====================

def test_list_checkpoints_empty():
    """Test listing checkpoints with no models"""
    with patch("app.training_api.Path") as mock_path:
        mock_output_root = MagicMock()
        mock_output_root.exists.return_value = False
        
        mock_path.return_value = mock_output_root
        
        response = client.get("/training/checkpoints")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


def test_list_checkpoints_with_model():
    """Test listing checkpoints for specific model"""
    with patch("app.training_api.Path") as mock_path:
        mock_checkpoint_dir = MagicMock()
        mock_checkpoint_dir.exists.return_value = True
        
        # Mock checkpoint files
        mock_ckpt1 = MagicMock()
        mock_ckpt1.stem = "checkpoint_epoch_100"
        mock_ckpt1.stat.return_value.st_mtime = 1700000000
        mock_ckpt1.stat.return_value.st_size = 1024 * 1024 * 100  # 100MB
        mock_ckpt1.__str__.return_value = "train/output/test/checkpoints/checkpoint_epoch_100.pth"
        
        mock_checkpoint_dir.glob.return_value = [mock_ckpt1]
        
        mock_path.return_value.__truediv__.return_value = mock_checkpoint_dir
        
        response = client.get("/training/checkpoints?model_name=test_model")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


def test_load_checkpoint_success():
    """Test loading existing checkpoint"""
    with patch("app.training_api.Path") as mock_path:
        mock_ckpt = MagicMock()
        mock_ckpt.exists.return_value = True
        
        mock_path.return_value = mock_ckpt
        
        response = client.post(
            "/training/checkpoints/load",
            params={"checkpoint_path": "train/output/test/checkpoints/epoch_100.pth"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "loaded"


def test_load_checkpoint_not_found():
    """Test loading nonexistent checkpoint"""
    response = client.post(
        "/training/checkpoints/load",
        params={"checkpoint_path": "train/output/nonexistent.pth"}
    )
    
    assert response.status_code == 404


# ==================== INFERENCE TESTS ====================

@patch("app.training_api.subprocess")
@patch("app.training_api.Path")
def test_inference_synthesize_success(mock_path, mock_subprocess):
    """Test successful inference synthesis"""
    # Mock checkpoint exists
    mock_ckpt = MagicMock()
    mock_ckpt.exists.return_value = True
    
    # Mock output directory
    mock_output_dir = MagicMock()
    mock_output_dir.mkdir = MagicMock()
    
    mock_output_file = MagicMock()
    mock_output_file.name = "inference_20231201_120000.wav"
    
    def path_side_effect(arg):
        if "checkpoint" in str(arg):
            return mock_ckpt
        elif "temp/inference" in str(arg):
            return mock_output_dir
        return mock_output_file
    
    mock_path.side_effect = path_side_effect
    
    # Mock subprocess success
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_subprocess.run.return_value = mock_result
    
    request_data = {
        "checkpoint": "train/output/test/epoch_100.pth",
        "text": "Teste de síntese",
        "temperature": 0.7,
        "speed": 1.0
    }
    
    response = client.post("/training/inference/synthesize", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "audio_url" in data


def test_inference_synthesize_checkpoint_not_found():
    """Test inference with missing checkpoint"""
    request_data = {
        "checkpoint": "train/output/nonexistent.pth",
        "text": "Test",
        "temperature": 0.7,
        "speed": 1.0
    }
    
    response = client.post("/training/inference/synthesize", json=request_data)
    
    assert response.status_code == 404


@patch("app.training_api.subprocess")
@patch("app.training_api.Path")
def test_ab_test_success(mock_path, mock_subprocess):
    """Test A/B comparison"""
    # Mock checkpoint exists
    mock_ckpt = MagicMock()
    mock_ckpt.exists.return_value = True
    
    mock_output_dir = MagicMock()
    mock_output_dir.mkdir = MagicMock()
    
    mock_base_file = MagicMock()
    mock_base_file.name = "base_20231201.wav"
    
    mock_ft_file = MagicMock()
    mock_ft_file.name = "finetuned_20231201.wav"
    
    def path_side_effect(arg):
        if "checkpoint" in str(arg):
            return mock_ckpt
        elif "temp/ab_test" in str(arg):
            return mock_output_dir
        elif "base_" in str(arg):
            return mock_base_file
        elif "finetuned_" in str(arg):
            return mock_ft_file
        return MagicMock()
    
    mock_path.side_effect = path_side_effect
    
    # Mock subprocess success
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_subprocess.run.return_value = mock_result
    
    request_data = {
        "checkpoint": "train/output/test/epoch_100.pth",
        "text": "Test comparison"
    }
    
    response = client.post("/training/inference/ab-test", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "base_audio" in data
    assert "finetuned_audio" in data
    assert "similarity" in data
    assert "mfcc_score" in data


# ==================== VALIDATION TESTS ====================

def test_dataset_segment_validation():
    """Test request validation for segmentation"""
    # Invalid min_duration (too low)
    request_data = {
        "folder": "datasets/test",
        "min_duration": 2.0,  # Should be >= 3.0
        "max_duration": 12.0,
        "vad_threshold": -40.0
    }
    
    response = client.post("/training/dataset/segment", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_training_start_validation():
    """Test request validation for training start"""
    # Invalid learning rate (too high)
    request_data = {
        "model_name": "test",
        "dataset_folder": "datasets/test",
        "epochs": 100,
        "batch_size": 4,
        "learning_rate": 0.5,  # Should be <= 0.01
        "use_deepspeed": False
    }
    
    response = client.post("/training/start", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_inference_synthesize_validation():
    """Test request validation for inference"""
    # Invalid temperature
    request_data = {
        "checkpoint": "test.pth",
        "text": "Test",
        "temperature": 2.0,  # Should be <= 1.5
        "speed": 1.0
    }
    
    response = client.post("/training/inference/synthesize", json=request_data)
    
    assert response.status_code == 422  # Validation error


# ==================== INTEGRATION TESTS ====================

@pytest.mark.integration
def test_full_training_workflow():
    """Test complete training workflow (mocked)"""
    # 1. Download dataset
    # 2. Segment audio
    # 3. Transcribe
    # 4. Start training
    # 5. Check status
    # 6. List checkpoints
    # 7. Run inference
    
    # This test would require full mocking of the workflow
    # or actual integration testing with real files
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
