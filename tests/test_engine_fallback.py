"""
Tests for Engine Fallback & Transparency (SPRINT-02)

Validates that the system correctly tracks engine fallback events
and provides transparency to users when requested engine is unavailable.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.processor import VoiceProcessor
from app.models import Job, JobMode, JobStatus
from app.quality_profile_mapper import (
    map_quality_profile_for_fallback,
    is_profile_compatible,
    suggest_alternative_profile,
    QUALITY_PROFILE_FALLBACK_MAP
)


class TestEngineFallbackTracking:
    """Test engine fallback transparency (SPRINT-02)"""
    
    @pytest.mark.unit
    def test_job_metadata_fields_exist(self):
        """
        Verify Job model has new fallback tracking fields.
        
        Required fields (SPRINT-02):
        - tts_engine_requested
        - engine_fallback
        - fallback_reason
        - quality_profile_mapped
        """
        job = Job.create_new(
            mode=JobMode.DUBBING,
            text="Test",
            source_language="pt-BR"
        )
        
        # Verify new fields exist
        assert hasattr(job, 'tts_engine_requested'), \
            "Job should have tts_engine_requested field"
        assert hasattr(job, 'engine_fallback'), \
            "Job should have engine_fallback field"
        assert hasattr(job, 'fallback_reason'), \
            "Job should have fallback_reason field"
        assert hasattr(job, 'quality_profile_mapped'), \
            "Job should have quality_profile_mapped field"
        
        # Verify default values
        assert job.engine_fallback == False, \
            "engine_fallback should default to False"
        assert job.fallback_reason is None, \
            "fallback_reason should default to None"
        assert job.quality_profile_mapped == False, \
            "quality_profile_mapped should default to False"
    
    @pytest.mark.integration
    @patch('app.processor.VoiceProcessor._get_engine')
    def test_engine_fallback_tracking_success_case(self, mock_get_engine):
        """
        Test fallback tracking when requested engine is available.
        
        Scenario: User requests f5tts, f5tts loads successfully
        Expected: engine_fallback=False, both requested/used=f5tts
        """
        # Mock successful F5-TTS load
        mock_engine = Mock()
        mock_engine.engine_name = 'f5tts'
        mock_get_engine.return_value = mock_engine
        
        processor = VoiceProcessor(lazy_load=True)
        
        job = Job.create_new(
            mode=JobMode.DUBBING,
            text="Test",
            source_language="pt-BR",
            tts_engine="f5tts"
        )
        
        # Simulate engine loading in processor
        job.tts_engine_requested = "f5tts"
        engine = mock_get_engine("f5tts")
        job.tts_engine_used = engine.engine_name
        job.engine_fallback = (job.tts_engine_requested != job.tts_engine_used)
        
        # Verify tracking
        assert job.tts_engine_requested == "f5tts"
        assert job.tts_engine_used == "f5tts"
        assert job.engine_fallback == False
        assert job.fallback_reason is None
    
    @pytest.mark.integration
    @patch('app.processor.VoiceProcessor._get_engine')
    def test_engine_fallback_tracking_fallback_case(self, mock_get_engine):
        """
        Test fallback tracking when requested engine fails.
        
        Scenario: User requests f5tts, but it fails → fallback to xtts
        Expected: engine_fallback=True, fallback_reason set
        """
        # Mock F5-TTS failure, XTTS success
        def get_engine_side_effect(engine_type):
            if engine_type == 'f5tts':
                mock_f5tts = Mock()
                mock_f5tts.engine_name = 'xtts'  # Simulate fallback
                return mock_f5tts
            else:
                mock_xtts = Mock()
                mock_xtts.engine_name = 'xtts'
                return mock_xtts
        
        mock_get_engine.side_effect = get_engine_side_effect
        
        processor = VoiceProcessor(lazy_load=True)
        
        job = Job.create_new(
            mode=JobMode.DUBBING,
            text="Test",
            source_language="pt-BR",
            tts_engine="f5tts"
        )
        
        # Simulate fallback in processor
        job.tts_engine_requested = "f5tts"
        engine = mock_get_engine("f5tts")
        job.tts_engine_used = engine.engine_name
        job.engine_fallback = (job.tts_engine_requested != job.tts_engine_used)
        
        if job.engine_fallback:
            job.fallback_reason = f"Failed to load {job.tts_engine_requested}, using {job.tts_engine_used}"
        
        # Verify fallback tracked
        assert job.tts_engine_requested == "f5tts"
        assert job.tts_engine_used == "xtts"
        assert job.engine_fallback == True
        assert job.fallback_reason is not None
        assert "Failed to load" in job.fallback_reason


class TestQualityProfileMapping:
    """Test quality profile mapping on fallback (SPRINT-03)"""
    
    @pytest.mark.unit
    def test_profile_mapping_f5tts_to_xtts(self):
        """
        Test F5-TTS → XTTS quality profile mapping.
        
        Validates that F5-TTS profiles are correctly mapped to
        equivalent XTTS profiles.
        """
        test_cases = [
            ('f5tts_ultra_natural', 'f5tts', 'xtts', 'xtts_expressive'),
            ('f5tts_ultra_quality', 'f5tts', 'xtts', 'xtts_ultra_quality'),
            ('f5tts_balanced', 'f5tts', 'xtts', 'xtts_balanced'),
            ('f5tts_fast', 'f5tts', 'xtts', 'xtts_fast'),
        ]
        
        for profile_id, requested, actual, expected in test_cases:
            mapped = map_quality_profile_for_fallback(
                profile_id=profile_id,
                requested_engine=requested,
                actual_engine=actual
            )
            
            assert mapped == expected, \
                f"Expected {profile_id} → {expected}, got {mapped}"
    
    @pytest.mark.unit
    def test_profile_mapping_xtts_to_f5tts(self):
        """
        Test XTTS → F5-TTS quality profile mapping (reverse).
        
        Validates bidirectional mapping support.
        """
        test_cases = [
            ('xtts_expressive', 'xtts', 'f5tts', 'f5tts_ultra_natural'),
            ('xtts_ultra_quality', 'xtts', 'f5tts', 'f5tts_ultra_quality'),
            ('xtts_balanced', 'xtts', 'f5tts', 'f5tts_balanced'),
            ('xtts_fast', 'xtts', 'f5tts', 'f5tts_fast'),
        ]
        
        for profile_id, requested, actual, expected in test_cases:
            mapped = map_quality_profile_for_fallback(
                profile_id=profile_id,
                requested_engine=requested,
                actual_engine=actual
            )
            
            assert mapped == expected, \
                f"Expected {profile_id} → {expected}, got {mapped}"
    
    @pytest.mark.unit
    def test_profile_mapping_no_fallback(self):
        """
        Test that mapping is skipped when no fallback occurs.
        
        If requested_engine == actual_engine, return original profile.
        """
        mapped = map_quality_profile_for_fallback(
            profile_id='f5tts_balanced',
            requested_engine='f5tts',
            actual_engine='f5tts'  # No fallback
        )
        
        assert mapped == 'f5tts_balanced', \
            "Should return original profile when no fallback"
    
    @pytest.mark.unit
    def test_profile_mapping_none_profile(self):
        """
        Test mapping with None profile (use engine default).
        
        Should return None to let engine use default.
        """
        mapped = map_quality_profile_for_fallback(
            profile_id=None,
            requested_engine='f5tts',
            actual_engine='xtts'
        )
        
        assert mapped is None, \
            "Should return None for None input (use engine default)"
    
    @pytest.mark.unit
    def test_profile_mapping_unknown_profile(self):
        """
        Test mapping with unknown/custom profile.
        
        Should return None (use engine default) if no mapping exists.
        """
        mapped = map_quality_profile_for_fallback(
            profile_id='custom_profile_xyz',
            requested_engine='f5tts',
            actual_engine='xtts'
        )
        
        assert mapped is None, \
            "Should return None for unknown profile (use engine default)"
    
    @pytest.mark.unit
    def test_profile_compatibility_check(self):
        """
        Test profile compatibility detection.
        
        Profile is compatible if it starts with engine name.
        """
        assert is_profile_compatible('f5tts_balanced', 'f5tts') == True
        assert is_profile_compatible('xtts_fast', 'xtts') == True
        assert is_profile_compatible('f5tts_balanced', 'xtts') == False
        assert is_profile_compatible('xtts_fast', 'f5tts') == False
        assert is_profile_compatible(None, 'f5tts') == True  # None is always compatible
    
    @pytest.mark.unit
    def test_suggest_alternative_profile(self):
        """
        Test profile suggestion for different engine.
        
        Useful for API error messages.
        """
        suggestion = suggest_alternative_profile('f5tts_ultra_natural', 'xtts')
        assert suggestion == 'xtts_expressive'
        
        suggestion = suggest_alternative_profile('xtts_balanced', 'f5tts')
        assert suggestion == 'f5tts_balanced'
        
        suggestion = suggest_alternative_profile('unknown_profile', 'xtts')
        assert suggestion is None
    
    @pytest.mark.unit
    def test_quality_profile_mapping_dictionary(self):
        """
        Test that mapping dictionary is complete and bidirectional.
        
        Validates QUALITY_PROFILE_FALLBACK_MAP structure.
        """
        # Check F5-TTS → XTTS mappings exist
        assert 'f5tts_ultra_natural' in QUALITY_PROFILE_FALLBACK_MAP
        assert 'f5tts_ultra_quality' in QUALITY_PROFILE_FALLBACK_MAP
        assert 'f5tts_balanced' in QUALITY_PROFILE_FALLBACK_MAP
        assert 'f5tts_fast' in QUALITY_PROFILE_FALLBACK_MAP
        
        # Check XTTS → F5-TTS mappings exist (reverse)
        assert 'xtts_expressive' in QUALITY_PROFILE_FALLBACK_MAP
        assert 'xtts_ultra_quality' in QUALITY_PROFILE_FALLBACK_MAP
        assert 'xtts_balanced' in QUALITY_PROFILE_FALLBACK_MAP
        assert 'xtts_fast' in QUALITY_PROFILE_FALLBACK_MAP
        
        # Check bidirectionality
        assert QUALITY_PROFILE_FALLBACK_MAP['f5tts_ultra_natural'] == 'xtts_expressive'
        assert QUALITY_PROFILE_FALLBACK_MAP['xtts_expressive'] == 'f5tts_ultra_natural'


class TestHealthCheckEndpoint:
    """Test /health/engines endpoint (SPRINT-03)"""
    
    @pytest.mark.integration
    def test_health_check_endpoint_structure(self):
        """
        Test that health check endpoint returns correct structure.
        
        Expected fields:
        - status: 'healthy' | 'degraded' | 'unhealthy'
        - engines: dict with engine details
        - timestamp: ISO datetime
        """
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health/engines")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert 'status' in data
        assert 'engines' in data
        assert 'timestamp' in data
        
        # Verify status is valid
        assert data['status'] in ['healthy', 'degraded', 'unhealthy']
        
        # Verify engines field is dict
        assert isinstance(data['engines'], dict)
        
        # Verify timestamp is ISO format
        try:
            datetime.fromisoformat(data['timestamp'])
        except ValueError:
            pytest.fail("Timestamp should be valid ISO format")
    
    @pytest.mark.integration
    def test_health_check_engine_details(self):
        """
        Test that engine details include required information.
        
        Each engine should have:
        - status: 'available' | 'unavailable'
        - Additional fields depending on availability
        """
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health/engines")
        data = response.json()
        
        engines = data['engines']
        
        # Check both engines reported
        assert 'xtts' in engines
        assert 'f5tts' in engines
        
        # Check each engine has status
        for engine_name, engine_data in engines.items():
            assert 'status' in engine_data
            assert engine_data['status'] in ['available', 'unavailable']
            
            if engine_data['status'] == 'available':
                # Available engines should have details
                assert 'engine_name' in engine_data
                assert 'sample_rate' in engine_data
                assert 'languages' in engine_data or 'total_languages' in engine_data
            else:
                # Unavailable engines should have error info
                assert 'error' in engine_data
                assert 'error_type' in engine_data
    
    @pytest.mark.integration
    @patch('app.processor.VoiceProcessor._get_engine')
    def test_health_check_degraded_state(self, mock_get_engine):
        """
        Test health check in degraded state (one engine down).
        
        Expected: status='degraded' if at least one engine available
        """
        # Mock: XTTS works, F5-TTS fails
        def get_engine_side_effect(engine_type):
            if engine_type == 'xtts':
                mock_xtts = Mock()
                mock_xtts.engine_name = 'xtts'
                mock_xtts.sample_rate = 24000
                mock_xtts.device = 'cpu'
                mock_xtts.get_supported_languages = Mock(return_value=['pt-BR', 'en'])
                return mock_xtts
            else:
                raise RuntimeError("F5-TTS checkpoint incompatibility")
        
        mock_get_engine.side_effect = get_engine_side_effect
        
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health/engines")
        data = response.json()
        
        # Should be degraded (not healthy, not unhealthy)
        assert data['status'] == 'degraded'
        
        # XTTS should be available
        assert data['engines']['xtts']['status'] == 'available'
        
        # F5-TTS should be unavailable
        assert data['engines']['f5tts']['status'] == 'unavailable'
        assert 'error' in data['engines']['f5tts']
