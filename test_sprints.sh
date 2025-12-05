#!/bin/bash
# Manual Test Script for SPRINT Implementation
# Tests all SPRINT fixes: checkpoint patching, fallback tracking, health check

set -e  # Exit on error

echo "=================================================="
echo "🧪 SPRINT IMPLEMENTATION MANUAL TESTS"
echo "=================================================="
echo ""

BASE_URL="http://localhost:8005"

echo "📋 Test Checklist:"
echo "  ✅ SPRINT-01: F5-TTS checkpoint patching"
echo "  ✅ SPRINT-02: Engine fallback tracking"
echo "  ✅ SPRINT-03: Quality profile mapping"
echo "  ✅ SPRINT-04: Health check endpoint"
echo ""

# Test 1: Health Check Endpoint
echo "=================================================="
echo "TEST 1: Health Check Endpoint (/health/engines)"
echo "=================================================="
echo ""

echo "Making request to $BASE_URL/health/engines..."
response=$(curl -s "$BASE_URL/health/engines")

echo "Response:"
echo "$response" | jq '.'

# Check if both engines are reported
xtts_status=$(echo "$response" | jq -r '.engines.xtts.status')
f5tts_status=$(echo "$response" | jq -r '.engines.f5tts.status')

echo ""
echo "Engine Status:"
echo "  XTTS:  $xtts_status"
echo "  F5-TTS: $f5tts_status"

if [ "$f5tts_status" == "available" ]; then
    echo "  ✅ F5-TTS is AVAILABLE (checkpoint patching worked!)"
elif [ "$f5tts_status" == "unavailable" ]; then
    echo "  ⚠️  F5-TTS is UNAVAILABLE (check error details above)"
    echo ""
    echo "Error details:"
    echo "$response" | jq '.engines.f5tts.error'
fi

echo ""
echo "Press ENTER to continue to next test..."
read

# Test 2: F5-TTS Job (Success Case)
echo "=================================================="
echo "TEST 2: F5-TTS Job Request (Success Case)"
echo "=================================================="
echo ""

echo "Creating job with tts_engine=f5tts..."
job_response=$(curl -s -X POST "$BASE_URL/jobs" \
  -d 'text=Olá, este é um teste do F5-TTS em português.' \
  -d 'source_language=pt-BR' \
  -d 'mode=dubbing' \
  -d 'voice_preset=female_generic' \
  -d 'tts_engine=f5tts')

echo "Job Response:"
echo "$job_response" | jq '.'

job_id=$(echo "$job_response" | jq -r '.id')

if [ "$job_id" != "null" ] && [ -n "$job_id" ]; then
    echo ""
    echo "Job created: $job_id"
    
    # Wait for job to process
    echo "Waiting 5 seconds for processing..."
    sleep 5
    
    # Check job status
    echo "Checking job status..."
    job_status=$(curl -s "$BASE_URL/jobs/$job_id")
    
    echo ""
    echo "Job Status:"
    echo "$job_status" | jq '.'
    
    # Check fallback tracking
    tts_requested=$(echo "$job_status" | jq -r '.tts_engine_requested')
    tts_used=$(echo "$job_status" | jq -r '.tts_engine_used')
    engine_fallback=$(echo "$job_status" | jq -r '.engine_fallback')
    
    echo ""
    echo "Fallback Tracking (SPRINT-02):"
    echo "  Requested Engine: $tts_requested"
    echo "  Used Engine:      $tts_used"
    echo "  Fallback:         $engine_fallback"
    
    if [ "$engine_fallback" == "false" ]; then
        echo "  ✅ No fallback occurred (F5-TTS worked!)"
    else
        fallback_reason=$(echo "$job_status" | jq -r '.fallback_reason')
        echo "  ⚠️  Fallback occurred: $fallback_reason"
    fi
fi

echo ""
echo "Press ENTER to continue to next test..."
read

# Test 3: F5-TTS with Quality Profile (Profile Mapping Test)
echo "=================================================="
echo "TEST 3: F5-TTS with Quality Profile Mapping"
echo "=================================================="
echo ""

echo "Creating job with f5tts_ultra_natural profile..."
job_response=$(curl -s -X POST "$BASE_URL/jobs" \
  -d 'text=Teste de qualidade ultra natural.' \
  -d 'source_language=pt-BR' \
  -d 'mode=dubbing' \
  -d 'voice_preset=female_generic' \
  -d 'tts_engine=f5tts' \
  -d 'quality_profile_id=f5tts_ultra_natural')

echo "Job Response:"
echo "$job_response" | jq '.'

job_id=$(echo "$job_response" | jq -r '.id')

if [ "$job_id" != "null" ] && [ -n "$job_id" ]; then
    echo ""
    echo "Job created: $job_id"
    
    # Wait for job to process
    echo "Waiting 5 seconds for processing..."
    sleep 5
    
    # Check job status
    echo "Checking job status..."
    job_status=$(curl -s "$BASE_URL/jobs/$job_id")
    
    # Check quality profile mapping
    quality_profile=$(echo "$job_status" | jq -r '.quality_profile')
    profile_mapped=$(echo "$job_status" | jq -r '.quality_profile_mapped')
    engine_fallback=$(echo "$job_status" | jq -r '.engine_fallback')
    
    echo ""
    echo "Quality Profile Mapping (SPRINT-03):"
    echo "  Final Profile:    $quality_profile"
    echo "  Profile Mapped:   $profile_mapped"
    echo "  Engine Fallback:  $engine_fallback"
    
    if [ "$engine_fallback" == "true" ] && [ "$profile_mapped" == "true" ]; then
        echo "  ✅ Quality profile was auto-mapped during fallback!"
        echo "     (f5tts_ultra_natural → xtts_expressive expected)"
    elif [ "$engine_fallback" == "false" ]; then
        echo "  ✅ No fallback, using original profile: $quality_profile"
    fi
fi

echo ""
echo "Press ENTER to continue to next test..."
read

# Test 4: Check Docker Logs for Checkpoint Patching
echo "=================================================="
echo "TEST 4: Check Docker Logs for Checkpoint Patching"
echo "=================================================="
echo ""

echo "Searching celery logs for checkpoint patching messages..."
echo ""

# Look for patching logs
docker compose logs audio-voice-celery --tail=100 | grep -E "(Patching|patched|ema_model)" || echo "No patching logs found (may already be cached)"

echo ""
echo "Search for F5-TTS loading success:"
docker compose logs audio-voice-celery --tail=100 | grep -E "(F5-TTS|f5tts)" | grep -i "loaded" || echo "No F5-TTS load logs found"

echo ""
echo "Press ENTER to continue to summary..."
read

# Summary
echo "=================================================="
echo "🎉 TEST SUMMARY"
echo "=================================================="
echo ""

echo "Tests Completed:"
echo "  1. ✅ Health check endpoint tested"
echo "  2. ✅ F5-TTS job creation tested"
echo "  3. ✅ Quality profile mapping tested"
echo "  4. ✅ Docker logs inspected"
echo ""

echo "Manual Validation Checklist:"
echo "  [ ] F5-TTS shows 'available' in /health/engines"
echo "  [ ] Job metadata includes tts_engine_requested/used"
echo "  [ ] engine_fallback is tracked correctly"
echo "  [ ] Quality profile is mapped on fallback"
echo "  [ ] Logs show checkpoint patching on first load"
echo "  [ ] Logs show cached checkpoint on subsequent loads"
echo ""

echo "To run automated tests:"
echo "  docker exec audio-voice-celery pytest tests/test_f5tts_loading.py -v"
echo "  docker exec audio-voice-celery pytest tests/test_engine_fallback.py -v"
echo ""

echo "=================================================="
echo "Testing complete! Review results above."
echo "=================================================="
