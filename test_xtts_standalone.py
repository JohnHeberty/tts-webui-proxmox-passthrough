#!/usr/bin/env python3
"""
Test script para validar XTTSService sem Docker

Usage:
    python3 test_xtts_standalone.py
"""
import sys
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.xtts_service import XTTSService

def test_service_creation():
    """Test 1: Criar service"""
    print("✓ Test 1: Creating XTTSService...")
    service = XTTSService(device="cpu")
    print(f"  Device: {service.device}")
    print(f"  Model: {service.model_name}")
    print(f"  Ready: {service.is_ready}")
    assert not service.is_ready, "Service should not be ready before init"
    print("✅ PASSED\n")

def test_quality_profiles():
    """Test 2: Validar quality profiles"""
    print("✓ Test 2: Validating quality profiles...")
    service = XTTSService(device="cpu")
    
    for profile in ["fast", "balanced", "high_quality"]:
        params = service._get_profile_params(profile)
        print(f"  {profile}: temp={params['temperature']}, speed={params['speed']}")
        assert "temperature" in params
        assert "speed" in params
    
    print("✅ PASSED\n")

def test_language_normalization():
    """Test 3: Normalização de linguagens"""
    print("✓ Test 3: Language normalization...")
    service = XTTSService(device="cpu")
    
    tests = [
        ("pt-BR", "pt"),
        ("PT-BR", "pt"),
        ("en-US", "en"),
        ("fr", "fr"),
    ]
    
    for input_lang, expected in tests:
        result = service._normalize_language(input_lang)
        print(f"  {input_lang} → {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ PASSED\n")

def test_supported_languages():
    """Test 4: Linguagens suportadas"""
    print("✓ Test 4: Supported languages...")
    service = XTTSService(device="cpu")
    langs = service.get_supported_languages()
    
    print(f"  Total: {len(langs)} languages")
    print(f"  Languages: {', '.join(langs[:8])}...")
    
    assert 'pt' in langs
    assert 'en' in langs
    assert len(langs) >= 16
    
    print("✅ PASSED\n")

def test_status_before_init():
    """Test 5: Status antes de inicializar"""
    print("✓ Test 5: Status before initialization...")
    service = XTTSService(device="cpu")
    status = service.get_status()
    
    print(f"  Initialized: {status['initialized']}")
    print(f"  Ready: {status['ready']}")
    print(f"  Device: {status['device']}")
    
    assert not status['initialized']
    assert not status['ready']
    
    print("✅ PASSED\n")

def main():
    """Run all tests"""
    print("=" * 60)
    print("XTTSService Standalone Tests")
    print("=" * 60)
    print()
    
    try:
        test_service_creation()
        test_quality_profiles()
        test_language_normalization()
        test_supported_languages()
        test_status_before_init()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED (5/5)")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
