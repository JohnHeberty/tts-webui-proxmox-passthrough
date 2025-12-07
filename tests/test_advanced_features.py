"""
Tests for Advanced Features API
Sprint 7 - Batch Processing, Authentication, Monitoring
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.advanced_features import (
    create_jwt_token,
    verify_jwt_token,
    generate_api_key,
    hash_api_key,
    verify_api_key
)

client = TestClient(app)

# ==================== FIXTURES ====================

@pytest.fixture
def valid_token():
    """Generate valid JWT token"""
    return create_jwt_token("testuser")


@pytest.fixture
def api_key_file(tmp_path):
    """Create temporary API keys file"""
    api_keys_file = tmp_path / "api_keys.txt"
    return api_keys_file


# ==================== AUTHENTICATION TESTS ====================

def test_create_jwt_token():
    """Test JWT token creation"""
    token = create_jwt_token("testuser")
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_jwt_token():
    """Test verifying valid JWT token"""
    token = create_jwt_token("testuser")
    payload = verify_jwt_token(token)
    
    assert payload["sub"] == "testuser"
    assert "exp" in payload
    assert "iat" in payload


def test_verify_invalid_jwt_token():
    """Test verifying invalid JWT token"""
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token("invalid.token.here")
    
    assert exc_info.value.status_code == 401


def test_generate_api_key():
    """Test API key generation"""
    key1 = generate_api_key()
    key2 = generate_api_key()
    
    assert isinstance(key1, str)
    assert len(key1) > 20
    assert key1 != key2  # Should be unique


def test_hash_api_key():
    """Test API key hashing"""
    key = "test_api_key_123"
    hash1 = hash_api_key(key)
    hash2 = hash_api_key(key)
    
    assert hash1 == hash2  # Same key = same hash
    assert len(hash1) == 64  # SHA256 hex = 64 chars


def test_login_endpoint():
    """Test login endpoint returns JWT token"""
    response = client.post(
        "/api/v1/advanced/auth/token",
        json={"username": "testuser", "password": "testpass"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_invalid_credentials():
    """Test login with empty credentials"""
    response = client.post(
        "/api/v1/advanced/auth/token",
        json={"username": "", "password": ""}
    )
    
    assert response.status_code == 401


def test_create_api_key_requires_auth():
    """Test that creating API key requires authentication"""
    response = client.post(
        "/api/v1/advanced/auth/api-key",
        json={"name": "Test Key", "expires_days": 30}
    )
    
    assert response.status_code == 401


def test_create_api_key_with_auth(valid_token):
    """Test creating API key with valid auth"""
    with patch('app.advanced_features.save_api_key'):
        response = client.post(
            "/api/v1/advanced/auth/api-key",
            json={"name": "Test Key", "expires_days": 30},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["name"] == "Test Key"
        assert "expires_at" in data


# ==================== BATCH TTS TESTS ====================

def test_batch_tts_requires_auth():
    """Test that batch TTS requires authentication"""
    response = client.post(
        "/api/v1/advanced/batch-tts",
        json={
            "texts": ["Hello", "World"],
            "voice_id": "test_voice",
            "language": "en"
        }
    )
    
    assert response.status_code == 401


def test_batch_tts_validation():
    """Test batch TTS request validation"""
    from app.advanced_features import BatchTTSRequest
    
    # Valid request
    request = BatchTTSRequest(
        texts=["Hello", "World"],
        voice_id="test_voice",
        language="en"
    )
    assert len(request.texts) == 2
    
    # Test max items validation
    with pytest.raises(ValueError):
        BatchTTSRequest(
            texts=[],  # Empty list
            voice_id="test_voice"
        )


def test_batch_tts_text_length_validation():
    """Test that texts over 5000 chars are rejected"""
    from app.advanced_features import BatchTTSRequest
    import pydantic
    
    long_text = "a" * 6000
    
    with pytest.raises((ValueError, pydantic.ValidationError)):
        BatchTTSRequest(
            texts=[long_text],
            voice_id="test_voice"
        )


@patch('app.advanced_features.create_clone_voice_job')
def test_batch_tts_with_auth(mock_create_job, valid_token):
    """Test batch TTS with valid authentication"""
    mock_create_job.return_value = {"job_id": "test_job_123"}
    
    response = client.post(
        "/api/v1/advanced/batch-tts",
        json={
            "texts": ["Hello", "World"],
            "voice_id": "test_voice",
            "language": "en",
            "tts_engine": "xtts"
        },
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["total_jobs"] == 2
    assert "estimated_time" in data
    assert "status_url" in data


def test_batch_status_not_found(valid_token):
    """Test getting status of non-existent batch"""
    response = client.get(
        "/api/v1/advanced/batch-tts/nonexistent_batch/status",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    
    assert response.status_code == 404


@patch('app.advanced_features.Path.exists')
@patch('builtins.open', create=True)
def test_batch_status_success(mock_open, mock_exists, valid_token):
    """Test getting status of existing batch"""
    mock_exists.return_value = True
    
    batch_metadata = {
        "batch_id": "test_batch",
        "job_ids": ["job1", "job2", "job3"],
        "total_jobs": 3,
        "created_at": datetime.utcnow().isoformat()
    }
    
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = json.dumps(batch_metadata)
    mock_open.return_value = mock_file
    
    with patch('app.advanced_features.get_job', return_value={"status": "completed"}):
        response = client.get(
            "/api/v1/advanced/batch-tts/test_batch/status",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "progress" in data


# ==================== VOICE MORPHING TESTS ====================

def test_voice_morphing_not_implemented(valid_token):
    """Test that voice morphing returns 501"""
    response = client.post(
        "/api/v1/advanced/voice-morphing",
        json={
            "voice_ids": ["voice1", "voice2"],
            "weights": [0.5, 0.5],
            "text": "Hello",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    
    assert response.status_code == 501


def test_voice_morphing_weights_validation():
    """Test voice morphing weights validation"""
    from app.advanced_features import VoiceMorphingRequest
    import pydantic
    
    # Weights must sum to 1.0
    with pytest.raises((ValueError, pydantic.ValidationError)):
        VoiceMorphingRequest(
            voice_ids=["v1", "v2"],
            weights=[0.3, 0.3],  # Sum = 0.6, not 1.0
            text="Hello"
        )
    
    # Number of weights must match voice_ids
    with pytest.raises((ValueError, pydantic.ValidationError)):
        VoiceMorphingRequest(
            voice_ids=["v1", "v2"],
            weights=[1.0],  # Only one weight
            text="Hello"
        )


# ==================== CSV BATCH TESTS ====================

def test_batch_csv_requires_csv_file(valid_token):
    """Test that non-CSV files are rejected"""
    response = client.post(
        "/api/v1/advanced/batch-csv",
        files={"file": ("test.txt", b"content", "text/plain")},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


@patch('app.advanced_features.create_clone_voice_job')
def test_batch_csv_success(mock_create_job, valid_token):
    """Test successful CSV batch processing"""
    mock_create_job.return_value = {"job_id": "test_job_123"}
    
    csv_content = b"text,voice_id,language\nHello,voice1,en\nWorld,voice1,en"
    
    response = client.post(
        "/api/v1/advanced/batch-csv",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


# ==================== HEALTH CHECK TESTS ====================

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/advanced/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


# ==================== METRICS TESTS ====================

def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert b"http_requests_total" in response.content
    assert response.headers["content-type"].startswith("text/plain")


def test_health_monitoring():
    """Test health endpoint for monitoring"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@patch('torch.cuda.is_available', return_value=True)
@patch('app.metrics.redis_client.ping')
def test_readiness_all_checks_pass(mock_ping, mock_cuda):
    """Test readiness when all checks pass"""
    response = client.get("/ready")
    
    # Should return tuple (dict, status_code)
    data = response.json()
    assert data["ready"] is True
    assert data["checks"]["gpu"] is True


@patch('torch.cuda.is_available', return_value=False)
def test_readiness_gpu_not_available(mock_cuda):
    """Test readiness when GPU is not available"""
    response = client.get("/ready")
    
    data = response.json()
    assert data["ready"] is False
    assert data["checks"]["gpu"] is False


# ==================== INTEGRATION TESTS ====================

def test_full_auth_flow():
    """Test complete authentication flow"""
    # 1. Login
    login_response = client.post(
        "/api/v1/advanced/auth/token",
        json={"username": "testuser", "password": "testpass"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 2. Use token to create API key
    with patch('app.advanced_features.save_api_key'):
        api_key_response = client.post(
            "/api/v1/advanced/auth/api-key",
            json={"name": "Test Key", "expires_days": 30},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert api_key_response.status_code == 200
        api_key = api_key_response.json()["api_key"]
        assert len(api_key) > 20


@patch('app.advanced_features.create_clone_voice_job')
def test_batch_processing_workflow(mock_create_job, valid_token):
    """Test complete batch processing workflow"""
    mock_create_job.return_value = {"job_id": "test_job_123"}
    
    # 1. Submit batch
    batch_response = client.post(
        "/api/v1/advanced/batch-tts",
        json={
            "texts": ["Text 1", "Text 2", "Text 3"],
            "voice_id": "test_voice",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert batch_response.status_code == 200
    batch_id = batch_response.json()["job_id"]
    
    # 2. Check status (mocked)
    with patch('app.advanced_features.Path.exists', return_value=True):
        with patch('builtins.open', create=True) as mock_open:
            batch_metadata = {
                "batch_id": batch_id,
                "job_ids": ["job1", "job2", "job3"],
                "total_jobs": 3
            }
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = json.dumps(batch_metadata)
            mock_open.return_value = mock_file
            
            with patch('app.advanced_features.get_job', return_value={"status": "completed"}):
                status_response = client.get(
                    f"/api/v1/advanced/batch-tts/{batch_id}/status",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
                assert status_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
