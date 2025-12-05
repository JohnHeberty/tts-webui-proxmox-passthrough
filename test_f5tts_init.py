#!/usr/bin/env python3
"""Test F5-TTS engine initialization"""

import sys
sys.path.insert(0, '/app')

from app.engines.factory import create_engine
from app.config import get_settings

print("🔧 Testing F5-TTS engine initialization...")
print("=" * 60)

try:
    settings = get_settings()
    engine = create_engine('f5tts', settings)
    print(f"✅ Engine created: {engine.__class__.__name__}")
    print(f"   Device: {engine.device}")
    print(f"   Model: {engine.hf_model_name}")
    print(f"   Config: {engine.config_name}")
    
    # Check if model is loaded
    if hasattr(engine, 'tts') and engine.tts is not None:
        print(f"   TTS Model: LOADED")
    else:
        print(f"   TTS Model: NOT LOADED (lazy loading)")
    
    print("\n✅ F5-TTS engine initialized successfully!")
    
except Exception as e:
    print(f"\n❌ Failed to initialize F5-TTS: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
