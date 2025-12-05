#!/bin/bash
# Test script for job creation with correct parameter names
# Updated: 2024-12-05 - Fixed parameter names (removed _str suffix)

echo "🧪 Testing POST /jobs with F5-TTS engine"
echo "=========================================="

curl -X 'POST' \
  'http://localhost:8005/jobs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'text=Esse e um teste de clonagem de voz, eai como ficou porra!' \
  -d 'source_language=pt-BR' \
  -d 'mode=dubbing_with_clone' \
  -d 'voice_id=2caa74ef-5037-4f0a-8ba1-0d3818637155' \
  -d 'tts_engine=f5tts' \
  -d 'enable_rvc=false' \
  -d 'rvc_pitch=0' \
  -d 'rvc_index_rate=0.75' \
  -d 'rvc_filter_radius=3' \
  -d 'rvc_rms_mix_rate=0.25' \
  -d 'rvc_protect=0.33' \
  -d 'rvc_f0_method=rmvpe' \
  | jq '.'

echo ""
echo "=========================================="
echo "✅ If you see a job_id, the request was successful!"
echo "⚠️  If you see 'Field required', check parameter names"
