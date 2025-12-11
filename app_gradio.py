"""
Audio Voice Service - Pure Gradio Application
TTS & Voice Cloning sem FastAPI, sem RVC
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import uuid

import gradio as gr
from pydub import AudioSegment

# Imports do projeto
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.processor import VoiceProcessor
from app.redis_store import RedisJobStore
from app.config import get_settings, get_voice_presets, get_supported_languages
from app.quality_profile_manager import quality_profile_manager
from app.models import Job, JobStatus, DubbingRequest, VoiceCloneRequest, VoiceProfile
from app.logging_config import setup_logging, get_logger

# Setup
settings = get_settings()
setup_logging("audio-voice-gradio", settings['log_level'])
logger = get_logger(__name__)

# Initialize components
processor = VoiceProcessor(lazy_load=True)
redis_store = RedisJobStore(redis_url=settings.get('redis_url', 'redis://localhost:6379/4'))

# ========================= HELPER FUNCTIONS =========================

def get_presets() -> List[str]:
    """Get voice presets"""
    try:
        presets = get_voice_presets()
        return [p['id'] for p in presets]
    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        return []


def get_languages() -> List[Tuple[str, str]]:
    """Get supported languages"""
    try:
        langs = get_supported_languages()
        return [(lang['name'], lang['code']) for lang in langs]
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        return [("Português (Brasil)", "pt")]


def get_voices() -> List[Tuple[str, str]]:
    """Get cloned voices"""
    try:
        voices = redis_store.list_voices()
        return [(v.voice_name, v.voice_id) for v in voices]
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return []


def get_quality_profiles(engine: Optional[str] = None) -> List[Tuple[str, str]]:
    """Get quality profiles"""
    try:
        profiles = quality_profile_manager.list_profiles(engine_type=engine)
        return [(p.name, p.id) for p in profiles]
    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        return []


# ========================= TTS GENERATION =========================

async def generate_tts_async(
    text: str,
    engine: str,
    quality_profile_id: str,
    mode: str,
    voice_preset: Optional[str] = None,
    voice_id: Optional[str] = None,
    source_lang: str = "pt",
    target_lang: str = "pt"
) -> Tuple[Optional[str], str]:
    """
    Generate TTS audio
    Returns: (audio_file_path, status_message)
    """
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
            engine=engine,
            quality_profile_id=quality_profile_id,
            mode=mode,
            voice_preset=voice_preset if mode == "dubbing" else None,
            voice_id=voice_id if mode == "dubbing_with_clone" else None,
            status=JobStatus.QUEUED,
            created_at=datetime.now()
        )
        
        # Store in Redis
        redis_store.save_job(job)
        
        # Process directly (no Celery queue)
        job.status = JobStatus.PROCESSING
        redis_store.save_job(job)
        
        logger.info(f"Processing job {job.job_id} with engine {engine}")
        
        # Process job
        result_job = await processor.process_dubbing_job(job)
        
        if result_job.status == JobStatus.COMPLETED:
            audio_path = result_job.output_audio_path
            if audio_path and Path(audio_path).exists():
                return audio_path, f"✅ TTS gerado com sucesso! Job ID: {job.job_id}"
            else:
                return None, "❌ Erro: Arquivo de áudio não encontrado"
        else:
            error = result_job.error_message or "Erro desconhecido"
            return None, f"❌ Falha na geração: {error}"
    
    except Exception as e:
        logger.error(f"Error generating TTS: {e}", exc_info=True)
        return None, f"❌ Erro: {str(e)}"


def generate_tts_sync(*args, **kwargs):
    """Sync wrapper for Gradio"""
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
    language: str,
    engine: str
) -> Tuple[str, Optional[str]]:
    """
    Clone voice
    Returns: (status_message, voice_id)
    """
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
        
        # Copy audio to voice profiles directory
        voice_dir = Path("voice_profiles")
        voice_dir.mkdir(exist_ok=True)
        
        audio_dest = voice_dir / f"{voice_id}.wav"
        audio.export(audio_dest, format="wav")
        
        # Create voice profile
        profile = VoiceProfile(
            voice_id=voice_id,
            voice_name=voice_name.strip(),
            description=description.strip() if description else "",
            audio_path=str(audio_dest),
            language=language,
            engine=engine,
            duration_seconds=duration_seconds,
            created_at=datetime.now()
        )
        
        # Store in Redis
        redis_store.save_voice(profile)
        
        logger.info(f"Voice cloned successfully: {voice_name} (ID: {voice_id})")
        
        return f"✅ Voz clonada com sucesso! ID: {voice_id}", voice_id
    
    except Exception as e:
        logger.error(f"Error cloning voice: {e}", exc_info=True)
        return f"❌ Erro: {str(e)}", None


def clone_voice_sync(*args, **kwargs):
    """Sync wrapper for Gradio"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(clone_voice_async(*args, **kwargs))
        return result
    finally:
        loop.close()


# ========================= JOBS MANAGEMENT =========================

def list_jobs(limit: int = 20) -> str:
    """List recent jobs as HTML table"""
    try:
        jobs = redis_store.list_jobs(limit=limit)
        
        if not jobs:
            return "<p>Nenhum job encontrado.</p>"
        
        # Build HTML table
        html = '<table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif;">'
        html += '<thead><tr style="background: #4A90E2; color: white; border-bottom: 2px solid #357ABD;">'
        html += '<th style="padding: 12px; text-align: left;">Job ID</th>'
        html += '<th style="padding: 12px; text-align: left;">Status</th>'
        html += '<th style="padding: 12px; text-align: left;">Engine</th>'
        html += '<th style="padding: 12px; text-align: left;">Modo</th>'
        html += '<th style="padding: 12px; text-align: left;">Texto</th>'
        html += '</tr></thead><tbody>'
        
        for job in jobs:
            status_colors = {
                "completed": "#28a745",
                "failed": "#dc3545",
                "processing": "#ffc107",
                "queued": "#17a2b8"
            }
            status_color = status_colors.get(job.status.value, "#6c757d")
            
            html += f'<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 10px; font-family: monospace; font-size: 11px;">{job.job_id[:16]}...</td>'
            html += f'<td style="padding: 10px; color: {status_color}; font-weight: bold;">{job.status.value}</td>'
            html += f'<td style="padding: 10px;">{job.engine}</td>'
            html += f'<td style="padding: 10px;">{job.mode.value}</td>'
            html += f'<td style="padding: 10px; max-width: 300px; overflow: hidden; text-overflow: ellipsis;">{job.text[:60]}...</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        return f"<p style='color: red;'>❌ Erro ao carregar jobs: {str(e)}</p>"


def get_job_audio(job_id: str) -> Tuple[Optional[str], str]:
    """Get job audio by ID"""
    try:
        if not job_id:
            return None, "❌ Erro: Job ID é obrigatório"
        
        job = redis_store.get_job(job_id)
        if not job:
            return None, "❌ Job não encontrado"
        
        if job.status != JobStatus.COMPLETED:
            return None, f"❌ Job não está completo. Status: {job.status.value}"
        
        if not job.output_audio_path or not Path(job.output_audio_path).exists():
            return None, "❌ Arquivo de áudio não encontrado"
        
        return job.output_audio_path, f"✅ Áudio carregado! Job: {job_id[:16]}..."
    
    except Exception as e:
        logger.error(f"Error getting job audio: {e}", exc_info=True)
        return None, f"❌ Erro: {str(e)}"


def list_voices_html() -> str:
    """List cloned voices as HTML table"""
    try:
        voices = redis_store.list_voices()
        
        if not voices:
            return "<p>Nenhuma voz clonada encontrada.</p>"
        
        html = '<table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif;">'
        html += '<thead><tr style="background: #E27B4A; color: white; border-bottom: 2px solid #BD5A35;">'
        html += '<th style="padding: 12px; text-align: left;">Nome</th>'
        html += '<th style="padding: 12px; text-align: left;">Voice ID</th>'
        html += '<th style="padding: 12px; text-align: left;">Engine</th>'
        html += '<th style="padding: 12px; text-align: left;">Idioma</th>'
        html += '<th style="padding: 12px; text-align: left;">Duração</th>'
        html += '</tr></thead><tbody>'
        
        for voice in voices:
            html += f'<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 10px; font-weight: bold;">{voice.voice_name}</td>'
            html += f'<td style="padding: 10px; font-family: monospace; font-size: 11px;">{voice.voice_id[:16]}...</td>'
            html += f'<td style="padding: 10px;">{voice.engine}</td>'
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
    
    with gr.Blocks(title="Audio Voice Service - TTS & Voice Cloning") as app:
        
        gr.Markdown(
            """
            # 🎙️ Audio Voice Service
            
            **Text-to-Speech e Voice Cloning com XTTS v2**
            """
        )
        
        with gr.Tabs():
            # ==================== TTS GENERATION ====================
            with gr.Tab("🎤 Geração TTS"):
                gr.Markdown("## Conversão de Texto em Voz")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        text_input = gr.Textbox(
                            label="Texto para sintetizar",
                            placeholder="Digite o texto que deseja converter em áudio...",
                            lines=6,
                            max_lines=15
                        )
                        
                        with gr.Row():
                            engine_select = gr.Dropdown(
                                choices=["xtts"],
                                value="xtts",
                                label="Engine TTS",
                                info="XTTS v2: Multilingual (16 idiomas)"
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
                                choices=[],
                                label="Voice Preset",
                                visible=True
                            )
                            voice_clone_select = gr.Dropdown(
                                choices=[],
                                label="Voz Clonada",
                                visible=False
                            )
                        
                        quality_profile_select = gr.Dropdown(
                            choices=[],
                            label="Perfil de Qualidade"
                        )
                        
                        with gr.Row():
                            source_lang = gr.Dropdown(
                                choices=[],
                                value="pt",
                                label="Idioma de Origem"
                            )
                            target_lang = gr.Dropdown(
                                choices=[],
                                value="pt",
                                label="Idioma de Destino"
                            )
                        
                        generate_btn = gr.Button("🎵 Gerar TTS", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        status_output = gr.Textbox(label="Status", interactive=False, lines=3)
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
                    inputs=[
                        text_input, engine_select, quality_profile_select, mode_select,
                        voice_preset_select, voice_clone_select, source_lang, target_lang
                    ],
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
                        
                        with gr.Row():
                            language_select_clone = gr.Dropdown(
                                choices=[],
                                value="pt",
                                label="Idioma"
                            )
                            engine_select_clone = gr.Dropdown(
                                choices=["xtts"],
                                value="xtts",
                                label="Engine"
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
                    inputs=[audio_upload, voice_name_input, description_input, language_select_clone, engine_select_clone],
                    outputs=[clone_status, voice_id_output]
                )
                
                refresh_voices_btn.click(
                    fn=list_voices_html,
                    outputs=[voices_list]
                )
            
            # ==================== JOBS ====================
            with gr.Tab("📋 Jobs"):
                gr.Markdown("## Gerenciamento de Jobs TTS")
                
                with gr.Tabs():
                    with gr.Tab("📊 Listar Jobs"):
                        limit_slider = gr.Slider(10, 100, value=20, step=10, label="Limite de Jobs")
                        refresh_jobs_btn = gr.Button("🔄 Atualizar Lista", variant="secondary")
                        jobs_html = gr.HTML()
                        
                        refresh_jobs_btn.click(
                            fn=list_jobs,
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
            
            # ==================== TRAINING ====================
            with gr.Tab("🎓 Treinamento"):
                gr.Markdown("## Fine-tuning XTTS v2")
                gr.Markdown("""
                **Treine vozes customizadas com seus próprios dados**
                
                O treinamento XTTS permite criar modelos especializados em:
                - Vozes específicas (dubladores, narradores)
                - Sotaques regionais (português brasileiro, europeu)
                - Estilos de fala (formal, informal, emotivo)
                """)
                
                with gr.Accordion("📋 Pré-requisitos", open=False):
                    gr.Markdown("""
                    ### Requisitos
                    - **Áudio**: 10-30 minutos de áudio limpo da voz alvo
                    - **Transcrições**: Texto correspondente a cada áudio
                    - **GPU**: Recomendado 8GB+ VRAM
                    - **Tempo**: ~2-6 horas de treinamento
                    
                    ### Formato dos Dados
                    ```
                    data/
                      audio/
                        001.wav  (16kHz, mono)
                        002.wav
                      metadata.csv (path|transcription|speaker_name)
                    ```
                    """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📂 Configuração do Dataset")
                        
                        dataset_path = gr.Textbox(
                            label="Caminho do Dataset",
                            placeholder="Ex: ./train/data/processed",
                            value="./train/data/processed"
                        )
                        
                        speaker_name = gr.Textbox(
                            label="Nome do Speaker",
                            placeholder="Ex: narrator_male_br"
                        )
                        
                        language_train = gr.Dropdown(
                            choices=["pt", "en", "es", "fr", "de", "it", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu"],
                            value="pt",
                            label="Idioma do Dataset"
                        )
                        
                        gr.Markdown("### ⚙️ Hiperparâmetros")
                        
                        with gr.Row():
                            epochs = gr.Slider(10, 100, value=50, step=10, label="Epochs")
                            batch_size = gr.Slider(1, 16, value=4, step=1, label="Batch Size")
                        
                        with gr.Row():
                            learning_rate = gr.Number(value=0.0001, label="Learning Rate")
                            save_frequency = gr.Slider(5, 50, value=10, step=5, label="Save Every N Epochs")
                        
                        output_dir = gr.Textbox(
                            label="Diretório de Output",
                            placeholder="Ex: ./train/output/my_model",
                            value="./train/output/ptbr_custom"
                        )
                        
                        train_btn = gr.Button("🚀 Iniciar Treinamento", variant="primary", size="lg")
                    
                    with gr.Column():
                        train_status = gr.Textbox(
                            label="Status do Treinamento",
                            interactive=False,
                            lines=10
                        )
                        
                        train_progress = gr.HTML(
                            value="<p style='color: gray;'>Aguardando início do treinamento...</p>"
                        )
                
                gr.Markdown("---")
                gr.Markdown("""
                ### 📚 Recursos
                - **Documentação**: [train/README.md](train/README.md)
                - **Scripts**: Veja `/train/scripts/` para preparação de dados
                - **Configs**: Edite `train/config/train_config.yaml`
                
                ### ⚠️ Nota
                O treinamento é um processo pesado. Para datasets grandes (>1h de áudio):
                - Use GPU com 12GB+ VRAM
                - Monitore via TensorBoard: `tensorboard --logdir train/output`
                - Checkpoints salvos a cada N epochs
                """)
                
                def start_training(dataset, speaker, lang, ep, bs, lr, save_freq, output):
                    """Placeholder para iniciar treinamento"""
                    try:
                        # Validações
                        if not dataset or not Path(dataset).exists():
                            return "❌ Erro: Dataset não encontrado", "<p style='color: red;'>Dataset inválido</p>"
                        
                        if not speaker:
                            return "❌ Erro: Nome do speaker é obrigatório", "<p style='color: red;'>Speaker vazio</p>"
                        
                        # TODO: Implementar treinamento real
                        # Por enquanto, retorna mensagem informativa
                        status_msg = f"""✅ Configuração validada!

Dataset: {dataset}
Speaker: {speaker}
Idioma: {lang}
Epochs: {ep}
Batch Size: {bs}
Learning Rate: {lr}

⚠️ NOTA: Treinamento real ainda não implementado.
Para treinar, execute manualmente:

python -m train.run_training \\
    --dataset {dataset} \\
    --speaker {speaker} \\
    --language {lang} \\
    --epochs {ep} \\
    --batch-size {bs} \\
    --lr {lr} \\
    --output {output}

Veja train/README.md para mais detalhes.
"""
                        
                        progress_html = """
<div style="background: #f0f0f0; padding: 15px; border-radius: 5px;">
    <h4>🔧 Como Treinar (Manual)</h4>
    <ol>
        <li>Prepare seus dados de áudio + transcrições</li>
        <li>Execute os scripts em <code>/train/scripts/</code></li>
        <li>Configure <code>train/config/train_config.yaml</code></li>
        <li>Execute: <code>python -m train.run_training</code></li>
    </ol>
    <p><strong>Documentação completa:</strong> <code>train/README.md</code></p>
</div>
"""
                        
                        return status_msg, progress_html
                    
                    except Exception as e:
                        return f"❌ Erro: {str(e)}", "<p style='color: red;'>Falha na validação</p>"
                
                train_btn.click(
                    fn=start_training,
                    inputs=[dataset_path, speaker_name, language_train, epochs, batch_size, learning_rate, save_frequency, output_dir],
                    outputs=[train_status, train_progress]
                )
            
            # ==================== ABOUT ====================
            with gr.Tab("ℹ️ Sobre"):
                gr.Markdown(
                    """
                    ## Audio Voice Service
                    
                    **Versão:** 2.0.0 (Gradio Pure)  
                    **Engine:** XTTS v2 (Coqui TTS)  
                    **Features:** Text-to-Speech, Voice Cloning Zero-Shot, Training
                    
                    ### Características
                    - ✅ 100% Gradio (sem FastAPI)
                    - ✅ Sem RVC (simplificado)
                    - ✅ Processamento direto (sem Celery)
                    - ✅ XTTS v2 Multilingual (16 idiomas)
                    - ✅ Voice Cloning com áudio curto
                    - ✅ Fine-tuning XTTS customizado
                    - ✅ Quality Profiles configuráveis
                    
                    ### Como Usar
                    1. **TTS Generation**: Digite texto, escolha engine e voz
                    2. **Voice Cloning**: Upload áudio de 5-300s para clonar
                    3. **Jobs**: Veja histórico e baixe áudios gerados
                    
                    ### Suporte
                    - GitHub: [seu-repo]
                    - Documentação: [docs/]
                    """
                )
        
        # Load initial data
        def load_initial_data():
            try:
                presets = get_presets()
                voices = get_voices()
                profiles = get_quality_profiles()
                languages = get_languages()
                jobs_table = list_jobs(20)
                voices_table = list_voices_html()
                
                return (
                    gr.update(choices=presets, value=presets[0] if presets else None),
                    gr.update(choices=[v[1] for v in voices]),
                    gr.update(choices=[p[1] for p in profiles], value=profiles[0][1] if profiles else None),
                    gr.update(choices=[lang[1] for lang in languages], value="pt"),
                    gr.update(choices=[lang[1] for lang in languages], value="pt"),
                    gr.update(choices=[lang[1] for lang in languages], value="pt"),
                    jobs_table,
                    voices_table
                )
            except Exception as e:
                logger.error(f"Error loading initial data: {e}", exc_info=True)
                return tuple([gr.update() for _ in range(6)] + ["<p>Erro ao carregar</p>", "<p>Erro ao carregar</p>"])
        
        app.load(
            fn=load_initial_data,
            outputs=[
                voice_preset_select, voice_clone_select, quality_profile_select,
                source_lang, target_lang, language_select_clone,
                jobs_html, voices_list
            ]
        )
    
    return app


# ========================= MAIN =========================

if __name__ == "__main__":
    logger.info("🚀 Starting Audio Voice Service (Pure Gradio)")
    logger.info(f"📍 Access at: http://localhost:7860")
    
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
