"""
Audio Voice Service - Pure Gradio Application
TTS & Voice Cloning standalone com XTTS v2 apenas
Sem Redis, sem FastAPI, sem Celery, sem RVC, sem F5-TTS
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import uuid
import json

import gradio as gr
from pydub import AudioSegment

# Imports do projeto
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.processor import VoiceProcessor
from app.config import get_settings
from app.models import Job, JobStatus, VoiceProfile
from app.logging_config import setup_logging, get_logger

# Setup
settings = get_settings()
setup_logging("audio-voice-gradio", settings['log_level'])
logger = get_logger(__name__)

# Initialize processor
processor = VoiceProcessor(lazy_load=True)

# Storage simples em memória e disco
JOBS_DIR = Path("./storage/jobs")
VOICES_DIR = Path("./storage/voices")
JOBS_DIR.mkdir(parents=True, exist_ok=True)
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# Cache em memória
jobs_cache = {}
voices_cache = {}


# ========================= HELPER FUNCTIONS =========================

def save_job(job: Job):
    """Salvar job em arquivo JSON"""
    job_file = JOBS_DIR / f"{job.job_id}.json"
    with open(job_file, 'w', encoding='utf-8') as f:
        json.dump(job.model_dump(), f, default=str, ensure_ascii=False, indent=2)
    jobs_cache[job.job_id] = job


def get_job(job_id: str) -> Optional[Job]:
    """Recuperar job do cache ou disco"""
    if job_id in jobs_cache:
        return jobs_cache[job_id]
    
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        with open(job_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            job = Job(**data)
            jobs_cache[job_id] = job
            return job
    return None


def list_jobs(limit: int = 50) -> List[Job]:
    """Listar todos os jobs"""
    jobs = []
    for job_file in sorted(JOBS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(jobs) >= limit:
            break
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                jobs.append(Job(**data))
        except Exception as e:
            logger.error(f"Error loading job {job_file}: {e}")
    return jobs


def save_voice(voice: VoiceProfile):
    """Salvar voice profile"""
    voice_file = VOICES_DIR / f"{voice.voice_id}.json"
    with open(voice_file, 'w', encoding='utf-8') as f:
        json.dump(voice.model_dump(), f, default=str, ensure_ascii=False, indent=2)
    voices_cache[voice.voice_id] = voice


def get_voice(voice_id: str) -> Optional[VoiceProfile]:
    """Recuperar voice profile"""
    if voice_id in voices_cache:
        return voices_cache[voice_id]
    
    voice_file = VOICES_DIR / f"{voice_id}.json"
    if voice_file.exists():
        with open(voice_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            voice = VoiceProfile(**data)
            voices_cache[voice_id] = voice
            return voice
    return None


def list_voices() -> List[VoiceProfile]:
    """Listar todas as vozes"""
    voices = []
    for voice_file in sorted(VOICES_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(voice_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                voices.append(VoiceProfile(**data))
        except Exception as e:
            logger.error(f"Error loading voice {voice_file}: {e}")
    return voices


def get_presets() -> List[str]:
    """Get voice presets"""
    return ["female", "male"]  # Simplificado


def get_languages() -> List[Tuple[str, str]]:
    """Get supported languages"""
    return [
        ("Português (Brasil)", "pt"),
        ("English", "en"),
        ("Español", "es"),
        ("Français", "fr"),
        ("Deutsch", "de"),
        ("Italiano", "it"),
        ("Polski", "pl"),
        ("Türkçe", "tr"),
        ("Русский", "ru"),
        ("Nederlands", "nl"),
        ("Čeština", "cs"),
        ("العربية", "ar"),
        ("中文", "zh-cn"),
        ("日本語", "ja"),
        ("한국어", "ko"),
        ("Magyar", "hu")
    ]


# ========================= TTS GENERATION =========================

async def generate_tts_async(
    text: str,
    mode: str,
    voice_preset: Optional[str] = None,
    voice_id: Optional[str] = None,
    source_lang: str = "pt",
    target_lang: str = "pt"
) -> Tuple[Optional[str], str]:
    """Generate TTS audio"""
    try:
        # Validation
        if not text or len(text.strip()) == 0:
            return None, "❌ Erro: Texto não pode estar vazio"
        
        if mode == "dubbing" and not voice_preset:
            return None, "❌ Erro: Selecione um preset de voz"
        
        if mode == "dubbing_with_clone" and not voice_id:
            return None, "❌ Erro: Selecione uma voz clonada"
        
        # Create job
        job = Job(
            job_id=str(uuid.uuid4()),
            text=text.strip(),
            source_language=source_lang,
            target_language=target_lang,
            engine="xtts",  # Sempre XTTS
            mode=mode,
            voice_preset=voice_preset if mode == "dubbing" else None,
            voice_id=voice_id if mode == "dubbing_with_clone" else None,
            status=JobStatus.QUEUED,
            created_at=datetime.now()
        )
        
        # Save job
        save_job(job)
        
        # Process
        job.status = JobStatus.PROCESSING
        save_job(job)
        
        logger.info(f"Processing job {job.job_id}")
        
        # Process job
        result_job = await processor.process_dubbing_job(job)
        
        # Update job
        save_job(result_job)
        
        if result_job.status == JobStatus.COMPLETED:
            audio_path = result_job.output_audio_path
            if audio_path and Path(audio_path).exists():
                return audio_path, f"✅ TTS gerado com sucesso!\nJob ID: {job.job_id}\nDuração: {result_job.duration_seconds:.1f}s"
            else:
                return None, "❌ Erro: Arquivo de áudio não encontrado"
        else:
            error = result_job.error_message or "Erro desconhecido"
            return None, f"❌ Falha na geração: {error}"
    
    except Exception as e:
        logger.error(f"Error generating TTS: {e}", exc_info=True)
        return None, f"❌ Erro: {str(e)}"


def generate_tts_sync(*args, **kwargs):
    """Sync wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(generate_tts_async(*args, **kwargs))
        return result
    finally:
        loop.close()


# ========================= VOICE CLONING =========================

async def clone_voice_async(
    audio_file,
    voice_name: str,
    description: str,
    language: str
) -> Tuple[str, Optional[str]]:
    """Clone voice"""
    try:
        if not audio_file:
            return "❌ Erro: Selecione um arquivo de áudio", None
        
        if not voice_name or len(voice_name.strip()) == 0:
            return "❌ Erro: Nome da voz é obrigatório", None
        
        # Validate audio duration
        audio = AudioSegment.from_file(audio_file)
        duration_seconds = len(audio) / 1000.0
        
        if duration_seconds < 5:
            return "❌ Erro: Áudio muito curto (mínimo 5 segundos)", None
        if duration_seconds > 300:
            return "❌ Erro: Áudio muito longo (máximo 300 segundos)", None
        
        # Create voice profile
        voice_id = str(uuid.uuid4())
        
        # Copy audio to voices directory
        audio_dest = VOICES_DIR / f"{voice_id}.wav"
        audio.export(audio_dest, format="wav")
        
        # Create voice profile
        profile = VoiceProfile(
            voice_id=voice_id,
            voice_name=voice_name.strip(),
            description=description.strip() if description else "",
            audio_path=str(audio_dest),
            language=language,
            engine="xtts",
            duration_seconds=duration_seconds,
            created_at=datetime.now()
        )
        
        # Save
        save_voice(profile)
        
        logger.info(f"Voice cloned: {voice_name} (ID: {voice_id})")
        
        return f"✅ Voz clonada com sucesso!\n\nID: {voice_id}\nDuração: {duration_seconds:.1f}s", voice_id
    
    except Exception as e:
        logger.error(f"Error cloning voice: {e}", exc_info=True)
        return f"❌ Erro: {str(e)}", None


def clone_voice_sync(*args, **kwargs):
    """Sync wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(clone_voice_async(*args, **kwargs))
        return result
    finally:
        loop.close()


# ========================= JOBS MANAGEMENT =========================

def list_jobs_html(limit: int = 20) -> str:
    """List jobs as HTML"""
    try:
        jobs = list_jobs(limit=limit)
        
        if not jobs:
            return "<p>Nenhum job encontrado.</p>"
        
        html = '<table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif;">'
        html += '<thead><tr style="background: #4A90E2; color: white;">'
        html += '<th style="padding: 12px;">Job ID</th>'
        html += '<th style="padding: 12px;">Status</th>'
        html += '<th style="padding: 12px;">Texto</th>'
        html += '<th style="padding: 12px;">Duração</th>'
        html += '</tr></thead><tbody>'
        
        for job in jobs:
            status_colors = {
                "completed": "#28a745",
                "failed": "#dc3545",
                "processing": "#ffc107",
                "queued": "#17a2b8"
            }
            status_color = status_colors.get(job.status.value, "#6c757d")
            
            duration = f"{job.duration_seconds:.1f}s" if job.duration_seconds else "N/A"
            
            html += f'<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 10px; font-family: monospace; font-size: 11px;">{job.job_id[:16]}...</td>'
            html += f'<td style="padding: 10px; color: {status_color}; font-weight: bold;">{job.status.value}</td>'
            html += f'<td style="padding: 10px; max-width: 300px;">{job.text[:60]}...</td>'
            html += f'<td style="padding: 10px;">{duration}</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        return f"<p style='color: red;'>❌ Erro: {str(e)}</p>"


def get_job_audio(job_id: str) -> Tuple[Optional[str], str]:
    """Get job audio"""
    try:
        if not job_id:
            return None, "❌ Erro: Job ID é obrigatório"
        
        job = get_job(job_id)
        if not job:
            return None, "❌ Job não encontrado"
        
        if job.status != JobStatus.COMPLETED:
            return None, f"❌ Job não está completo. Status: {job.status.value}"
        
        if not job.output_audio_path or not Path(job.output_audio_path).exists():
            return None, "❌ Arquivo de áudio não encontrado"
        
        return job.output_audio_path, f"✅ Áudio carregado! Duração: {job.duration_seconds:.1f}s"
    
    except Exception as e:
        logger.error(f"Error getting job audio: {e}", exc_info=True)
        return None, f"❌ Erro: {str(e)}"


def list_voices_html() -> str:
    """List voices as HTML"""
    try:
        voices = list_voices()
        
        if not voices:
            return "<p>Nenhuma voz clonada encontrada.</p>"
        
        html = '<table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif;">'
        html += '<thead><tr style="background: #E27B4A; color: white;">'
        html += '<th style="padding: 12px;">Nome</th>'
        html += '<th style="padding: 12px;">Voice ID</th>'
        html += '<th style="padding: 12px;">Idioma</th>'
        html += '<th style="padding: 12px;">Duração</th>'
        html += '</tr></thead><tbody>'
        
        for voice in voices:
            html += f'<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 10px; font-weight: bold;">{voice.voice_name}</td>'
            html += f'<td style="padding: 10px; font-family: monospace; font-size: 11px;">{voice.voice_id[:16]}...</td>'
            html += f'<td style="padding: 10px;">{voice.language}</td>'
            html += f'<td style="padding: 10px;">{voice.duration_seconds:.1f}s</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    except Exception as e:
        logger.error(f"Error listing voices: {e}", exc_info=True)
        return f"<p style='color: red;'>❌ Erro: {str(e)}</p>"


# ========================= GRADIO UI =========================

def create_app():
    """Create Gradio application"""
    
    with gr.Blocks(title="Audio Voice Service - XTTS v2") as app:
        
        gr.Markdown(
            """
            # 🎙️ Audio Voice Service
            
            **Text-to-Speech e Voice Cloning com XTTS v2**
            """
        )
        
        with gr.Tabs():
            # ==================== TTS GENERATION ====================
            with gr.Tab("🎤 Geração TTS"):
                gr.Markdown("## Conversão de Texto em Voz (XTTS v2)")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        text_input = gr.Textbox(
                            label="Texto para sintetizar",
                            placeholder="Digite o texto que deseja converter em áudio...",
                            lines=6,
                            max_lines=15
                        )
                        
                        mode_select = gr.Radio(
                            choices=[
                                ("Voz Genérica (Preset)", "dubbing"),
                                ("Voz Clonada", "dubbing_with_clone")
                            ],
                            value="dubbing",
                            label="Modo de Voz"
                        )
                        
                        with gr.Row():
                            voice_preset_select = gr.Dropdown(
                                choices=get_presets(),
                                value="female",
                                label="Voice Preset",
                                visible=True
                            )
                            voice_clone_select = gr.Dropdown(
                                choices=[v.voice_id for v in list_voices()],
                                label="Voz Clonada",
                                visible=False
                            )
                        
                        with gr.Row():
                            source_lang = gr.Dropdown(
                                choices=[code for name, code in get_languages()],
                                value="pt",
                                label="Idioma de Origem"
                            )
                            target_lang = gr.Dropdown(
                                choices=[code for name, code in get_languages()],
                                value="pt",
                                label="Idioma de Destino"
                            )
                        
                        generate_btn = gr.Button("🎵 Gerar TTS", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        status_output = gr.Textbox(label="Status", interactive=False, lines=5)
                        audio_output = gr.Audio(label="Áudio Gerado", type="filepath")
                
                # Event handlers
                def update_voice_selectors(mode):
                    if mode == "dubbing":
                        return gr.update(visible=True), gr.update(visible=False)
                    else:
                        return gr.update(visible=False), gr.update(visible=True)
                
                mode_select.change(
                    fn=update_voice_selectors,
                    inputs=[mode_select],
                    outputs=[voice_preset_select, voice_clone_select]
                )
                
                generate_btn.click(
                    fn=generate_tts_sync,
                    inputs=[text_input, mode_select, voice_preset_select, voice_clone_select, source_lang, target_lang],
                    outputs=[audio_output, status_output]
                )
            
            # ==================== VOICE CLONING ====================
            with gr.Tab("🎙️ Clonagem de Voz"):
                gr.Markdown("## Clone Vozes com 5-300 segundos de áudio")
                
                with gr.Row():
                    with gr.Column():
                        audio_upload = gr.Audio(
                            label="Áudio de Referência (5-300s)",
                            type="filepath",
                            sources=["upload", "microphone"]
                        )
                        
                        voice_name_input = gr.Textbox(
                            label="Nome da Voz",
                            placeholder="Ex: João Silva - Narração"
                        )
                        
                        description_input = gr.Textbox(
                            label="Descrição (Opcional)",
                            placeholder="Ex: Voz masculina, tom profissional",
                            lines=2
                        )
                        
                        language_select_clone = gr.Dropdown(
                            choices=[code for name, code in get_languages()],
                            value="pt",
                            label="Idioma"
                        )
                        
                        clone_btn = gr.Button("🎤 Clonar Voz", variant="primary", size="lg")
                    
                    with gr.Column():
                        clone_status = gr.Textbox(label="Status", interactive=False, lines=5)
                        voice_id_output = gr.Textbox(label="Voice ID (copie para usar)", interactive=False)
                        
                        gr.Markdown("### 📋 Vozes Clonadas")
                        voices_list = gr.HTML()
                        refresh_voices_btn = gr.Button("🔄 Atualizar Lista", size="sm")
                
                clone_btn.click(
                    fn=clone_voice_sync,
                    inputs=[audio_upload, voice_name_input, description_input, language_select_clone],
                    outputs=[clone_status, voice_id_output]
                )
                
                refresh_voices_btn.click(
                    fn=list_voices_html,
                    outputs=[voices_list]
                )
            
            # ==================== JOBS ====================
            with gr.Tab("📋 Jobs"):
                gr.Markdown("## Histórico de Jobs TTS")
                
                with gr.Tabs():
                    with gr.Tab("📊 Listar Jobs"):
                        limit_slider = gr.Slider(10, 100, value=20, step=10, label="Limite de Jobs")
                        refresh_jobs_btn = gr.Button("🔄 Atualizar Lista", variant="secondary")
                        jobs_html = gr.HTML()
                        
                        refresh_jobs_btn.click(
                            fn=list_jobs_html,
                            inputs=[limit_slider],
                            outputs=[jobs_html]
                        )
                    
                    with gr.Tab("⬇️ Download Job"):
                        job_id_input = gr.Textbox(
                            label="Job ID",
                            placeholder="Cole o Job ID completo aqui"
                        )
                        download_btn = gr.Button("⬇️ Carregar Áudio", variant="primary")
                        
                        download_status = gr.Textbox(label="Status", interactive=False)
                        download_audio = gr.Audio(label="Áudio do Job", type="filepath")
                        
                        download_btn.click(
                            fn=get_job_audio,
                            inputs=[job_id_input],
                            outputs=[download_audio, download_status]
                        )
            
            # ==================== ABOUT ====================
            with gr.Tab("ℹ️ Sobre"):
                gr.Markdown(
                    """
                    ## Audio Voice Service
                    
                    **Versão:** 2.0.0 Standalone  
                    **Engine:** XTTS v2 (Coqui TTS)  
                    **Armazenamento:** Local (sem Redis)
                    
                    ### Características
                    - ✅ 100% Gradio (sem FastAPI)
                    - ✅ Standalone (sem Redis, sem Celery)
                    - ✅ XTTS v2 Multilingual (16 idiomas)
                    - ✅ Voice Cloning Zero-Shot
                    - ✅ Armazenamento local em `./storage/`
                    
                    ### Como Usar
                    1. **TTS Generation**: Digite texto, escolha preset ou voz clonada
                    2. **Voice Cloning**: Upload 5-300s de áudio limpo
                    3. **Jobs**: Veja histórico e baixe áudios
                    
                    ### Dados Armazenados
                    - **Jobs**: `./storage/jobs/*.json`
                    - **Vozes**: `./storage/voices/*.json` + áudios
                    - **Outputs**: `./processed/*.wav`
                    
                    ### Suporte
                    - Documentação: [README.md](README.md)
                    - Engine: XTTS v2 by Coqui AI
                    """
                )
        
        # Load initial data
        app.load(
            fn=lambda: (list_jobs_html(20), list_voices_html()),
            outputs=[jobs_html, voices_list]
        )
    
    return app


# ========================= MAIN =========================

if __name__ == "__main__":
    logger.info("🚀 Starting Audio Voice Service (Standalone)")
    logger.info(f"📍 Access at: http://localhost:7860")
    logger.info(f"💾 Storage: ./storage/")
    
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
