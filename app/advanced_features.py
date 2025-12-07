"""
Advanced Features API - Batch Processing, Authentication, and More
Sprint 7 implementation
"""

import os
import asyncio
import zipfile
import io
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
import jwt

from app.logging_config import get_logger

logger = get_logger(__name__)

# ==================== CONFIGURATION ====================

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

API_KEYS_FILE = Path("data/api_keys.txt")
API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/v1/advanced", tags=["advanced"])

# ==================== MODELS ====================

class BatchTTSRequest(BaseModel):
    """Batch TTS request model"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to synthesize")
    voice_id: str = Field(..., description="Voice ID to use for all texts")
    language: str = Field(default="pt", description="Language code")
    tts_engine: str = Field(default="xtts", description="TTS engine to use")
    quality_profile: Optional[str] = Field(None, description="Quality profile")
    
    @validator('texts')
    def validate_texts(cls, v):
        for text in v:
            if len(text) > 5000:
                raise ValueError("Each text must be less than 5000 characters")
        return v


class BatchTTSResponse(BaseModel):
    """Batch TTS response model"""
    job_id: str
    total_jobs: int
    estimated_time: int  # seconds
    status_url: str


class VoiceMorphingRequest(BaseModel):
    """Voice morphing request - blend multiple voices"""
    voice_ids: List[str] = Field(..., min_items=2, max_items=5, description="Voice IDs to blend")
    weights: List[float] = Field(..., description="Weights for each voice (must sum to 1.0)")
    text: str = Field(..., max_length=5000)
    language: str = Field(default="pt")
    
    @validator('weights')
    def validate_weights(cls, v, values):
        if 'voice_ids' in values and len(v) != len(values['voice_ids']):
            raise ValueError("Number of weights must match number of voice_ids")
        if abs(sum(v) - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")
        return v


class APIKeyCreate(BaseModel):
    """API key creation request"""
    name: str = Field(..., description="Friendly name for the API key")
    expires_days: int = Field(default=365, ge=1, le=3650, description="Days until expiration")


class APIKeyResponse(BaseModel):
    """API key response"""
    api_key: str
    name: str
    expires_at: datetime
    warning: str = "Store this key securely - it won't be shown again!"


class TokenRequest(BaseModel):
    """JWT token request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ==================== AUTHENTICATION ====================

def create_jwt_token(username: str) -> str:
    """Create JWT token"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": username,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def save_api_key(api_key: str, name: str, expires_at: datetime):
    """Save API key to file"""
    hashed = hash_api_key(api_key)
    with open(API_KEYS_FILE, "a") as f:
        f.write(f"{hashed}|{name}|{expires_at.isoformat()}\n")


def verify_api_key(api_key: str) -> bool:
    """Verify API key"""
    if not API_KEYS_FILE.exists():
        return False
    
    hashed = hash_api_key(api_key)
    with open(API_KEYS_FILE, "r") as f:
        for line in f:
            stored_hash, name, expires_str = line.strip().split("|")
            expires_at = datetime.fromisoformat(expires_str)
            
            if stored_hash == hashed and datetime.utcnow() < expires_at:
                return True
    
    return False


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> str:
    """Verify authentication via JWT or API key"""
    # Try API key first
    if x_api_key:
        if verify_api_key(x_api_key):
            return "api_key_user"
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    
    # Try JWT token
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization.split(" ")[1]
        payload = verify_jwt_token(token)
        return payload["sub"]
    
    raise HTTPException(status_code=401, detail="Authentication required")


# ==================== ENDPOINTS ====================

@router.post("/auth/token", response_model=TokenResponse)
async def login(credentials: TokenRequest):
    """
    Authenticate and get JWT token
    
    For demo purposes, accepts any username/password.
    In production, verify against database.
    """
    # TODO: Verify credentials against database
    # For now, accept any non-empty credentials
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(credentials.username)
    
    return TokenResponse(
        access_token=token,
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )


@router.post("/auth/api-key", response_model=APIKeyResponse, dependencies=[Depends(get_current_user)])
async def create_api_key(request: APIKeyCreate):
    """
    Create new API key
    
    Requires JWT authentication.
    """
    api_key = generate_api_key()
    expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
    
    save_api_key(api_key, request.name, expires_at)
    
    logger.info(f"Created API key: {request.name}, expires: {expires_at}")
    
    return APIKeyResponse(
        api_key=api_key,
        name=request.name,
        expires_at=expires_at
    )


@router.post("/batch-tts", response_model=BatchTTSResponse, dependencies=[Depends(get_current_user)])
async def batch_text_to_speech(
    request: BatchTTSRequest,
    background_tasks: BackgroundTasks
):
    """
    Batch text-to-speech processing
    
    Creates multiple TTS jobs and returns a ZIP file with all audio files.
    """
    from app.celery_tasks import create_clone_voice_job
    
    job_id = f"batch_{secrets.token_hex(8)}"
    job_ids = []
    
    logger.info(f"Creating batch TTS job {job_id} with {len(request.texts)} texts")
    
    # Create individual jobs
    for idx, text in enumerate(request.texts):
        try:
            # Create job using existing Celery task
            result = create_clone_voice_job(
                text=text,
                voice_id=request.voice_id,
                source_language=request.language,
                target_language=request.language,
                tts_engine=request.tts_engine,
                quality_profile=request.quality_profile or "balanced"
            )
            job_ids.append(result["job_id"])
        except Exception as e:
            logger.error(f"Error creating batch job {idx}: {e}")
    
    # Estimate time: ~5 seconds per text
    estimated_time = len(request.texts) * 5
    
    # Store batch job metadata
    batch_metadata = {
        "batch_id": job_id,
        "job_ids": job_ids,
        "total_jobs": len(job_ids),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Save metadata to file
    batch_file = Path(f"temp/batch_{job_id}.json")
    batch_file.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(batch_file, "w") as f:
        json.dump(batch_metadata, f)
    
    return BatchTTSResponse(
        job_id=job_id,
        total_jobs=len(job_ids),
        estimated_time=estimated_time,
        status_url=f"/api/v1/advanced/batch-tts/{job_id}/status"
    )


@router.get("/batch-tts/{batch_id}/status", dependencies=[Depends(get_current_user)])
async def get_batch_status(batch_id: str):
    """
    Get status of batch TTS job
    """
    from app.redis_store import get_job
    import json
    
    batch_file = Path(f"temp/batch_{batch_id}.json")
    if not batch_file.exists():
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    with open(batch_file, "r") as f:
        metadata = json.load(f)
    
    # Check status of all jobs
    statuses = []
    for job_id in metadata["job_ids"]:
        job = get_job(job_id)
        if job:
            statuses.append(job.get("status", "unknown"))
        else:
            statuses.append("not_found")
    
    completed = statuses.count("completed")
    failed = statuses.count("failed")
    pending = len(statuses) - completed - failed
    
    return {
        "batch_id": batch_id,
        "total_jobs": metadata["total_jobs"],
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "progress": int((completed / metadata["total_jobs"]) * 100),
        "status": "completed" if completed == metadata["total_jobs"] else "processing"
    }


@router.get("/batch-tts/{batch_id}/download", dependencies=[Depends(get_current_user)])
async def download_batch_results(batch_id: str):
    """
    Download all completed audio files as ZIP
    """
    from app.redis_store import get_job
    import json
    
    batch_file = Path(f"temp/batch_{batch_id}.json")
    if not batch_file.exists():
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    with open(batch_file, "r") as f:
        metadata = json.load(f)
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, job_id in enumerate(metadata["job_ids"]):
            job = get_job(job_id)
            if job and job.get("status") == "completed":
                audio_path = job.get("output_path")
                if audio_path and Path(audio_path).exists():
                    zip_file.write(audio_path, f"audio_{idx+1:03d}.wav")
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.zip"}
    )


@router.post("/voice-morphing", dependencies=[Depends(get_current_user)])
async def voice_morphing(request: VoiceMorphingRequest):
    """
    Voice morphing - blend multiple voices
    
    This is a placeholder implementation.
    Real implementation would:
    1. Load embeddings of multiple voices
    2. Blend embeddings using weighted average
    3. Synthesize with blended embedding
    """
    logger.info(f"Voice morphing request: {len(request.voice_ids)} voices")
    
    # TODO: Implement actual voice blending
    raise HTTPException(
        status_code=501,
        detail="Voice morphing is not yet implemented. Coming soon!"
    )


@router.post("/batch-csv", dependencies=[Depends(get_current_user)])
async def batch_from_csv(file: UploadFile = File(...)):
    """
    Batch TTS from CSV file
    
    CSV format: text,voice_id,language
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV")
    
    content = await file.read()
    
    try:
        import csv
        import io
        
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        texts = []
        voice_ids = []
        languages = []
        
        for row in csv_reader:
            texts.append(row.get('text', ''))
            voice_ids.append(row.get('voice_id', ''))
            languages.append(row.get('language', 'pt'))
        
        if not texts:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # For now, use first voice_id for all (can be enhanced)
        batch_request = BatchTTSRequest(
            texts=texts,
            voice_id=voice_ids[0],
            language=languages[0]
        )
        
        return await batch_text_to_speech(batch_request, BackgroundTasks())
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")


@router.get("/health", tags=["monitoring"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
