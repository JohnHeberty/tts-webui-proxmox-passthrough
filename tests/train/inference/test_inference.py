"""
Tests for train.inference module

Tests F5TTSInference API and service layer.
"""
import pytest

from train.inference.service import F5TTSInferenceService, get_inference_service


def test_service_singleton():
    """Test that service follows singleton pattern."""
    service1 = get_inference_service()
    service2 = get_inference_service()
    service3 = F5TTSInferenceService.get_instance()

    assert service1 is service2
    assert service1 is service3


def test_service_initial_state():
    """Test service initial state."""
    service = get_inference_service()

    assert not service.is_loaded()
    # May be configured or not depending on previous tests
    # assert not service.is_configured()


def test_service_configure():
    """Test service configuration."""
    service = get_inference_service()

    service.configure(
        checkpoint_path="/fake/model.pt",
        vocab_file="/fake/vocab.txt",
        device="cpu",
    )

    assert service.is_configured()
    assert service.config["checkpoint_path"] == "/fake/model.pt"
    assert service.config["device"] == "cpu"


def test_service_repr():
    """Test service string representation."""
    service = get_inference_service()
    repr_str = repr(service)

    assert "F5TTSInferenceService" in repr_str
    assert "configured" in repr_str or "not configured" in repr_str


@pytest.mark.slow
def test_inference_api_creation(tmp_path):
    """Test F5TTSInference can be created (requires model files)."""
    # This test requires actual model files
    # Skip if files not available
    pytest.skip("Requires actual model checkpoint and vocab files")


@pytest.mark.slow
def test_inference_generate(tmp_path, sample_audio_path):
    """Test inference generation (requires model)."""
    # This test requires actual model
    # Skip if model not available
    pytest.skip("Requires actual model checkpoint")
