#!/usr/bin/env python3
"""
Script consolidado de treinamento F5-TTS com todas as funcionalidades:
- Configuração unificada via config system (base_config.yaml + .env + CLI)
- Early stopping automático
- TensorBoard em background
- Geração de samples a cada N updates (configurável)
- Organização completa em train/
- Auto-resume de checkpoints

Uso:
    python3 -m train.run_training [--lr 2e-4] [--batch-size 4] [--epochs 500]
"""
import argparse
import logging
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
TRAIN_ROOT = PROJECT_ROOT / "train"
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

# Carregar config unificado
from train.config.loader import load_config


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


class F5TTSTrainer:
    """Treinador F5-TTS completo com todas as funcionalidades"""

    def __init__(self, cli_overrides=None):
        # Carregar config unificado (base + .env + CLI)
        self.config_obj = load_config(cli_overrides=cli_overrides)

        # Para compatibilidade com código legado, criar dict de acesso rápido
        self.config = self._build_legacy_config_dict()

        self.train_root = TRAIN_ROOT
        # Usar paths do config
        self.runs_dir = PROJECT_ROOT / self.config_obj.paths.tensorboard_dir
        self.output_dir = PROJECT_ROOT / self.config_obj.paths.output_dir
        self.data_dir = PROJECT_ROOT / Path(self.config_obj.paths.dataset_path).parent

        # Ajustar workers baseado no sistema
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()
        max_workers = max(1, cpu_count - 4)  # Deixa 4 cores livres
        actual_workers = self.config_obj.hardware.dataloader_workers
        if actual_workers > max_workers:
            logger.warning(f"⚠️  Ajustando workers: {actual_workers} → {max_workers}")
            # Note: config é imutável, mas podemos ajustar no dict legado
            self.config["dataloader_workers"] = max_workers

        self.pretrained_dir = self.train_root / "pretrained"
        self.tensorboard_process = None

        # 🔒 Garantia: se nada foi configurado, baixa e usa o F5-TTS-pt-br como base
        if (
            not self.config_obj.model.custom_checkpoint
            and self.config_obj.model.auto_download_pretrained
        ):
            logger.info(
                f"Auto-download habilitado para modelo base: {self.config_obj.model.base_model}"
            )

    def _build_legacy_config_dict(self):
        """
        Constrói dict de config no formato legado para compatibilidade.
        Mapeia F5TTSConfig (Pydantic) → dict flat.
        """
        cfg = self.config_obj

        return {
            # Training
            "epochs": cfg.training.epochs,
            "batch_size": cfg.training.batch_size_per_gpu,
            "batch_size_type": cfg.training.batch_size_type,
            "max_samples": cfg.training.max_samples,
            "learning_rate": cfg.training.learning_rate,
            "grad_accumulation_steps": cfg.training.grad_accumulation_steps,
            "max_grad_norm": cfg.training.max_grad_norm,
            "num_warmup_updates": cfg.training.num_warmup_updates,
            "warmup_start_lr": cfg.training.warmup_start_lr,
            "warmup_end_lr": cfg.training.warmup_end_lr,
            "early_stop_patience": cfg.training.early_stop_patience,
            "early_stop_min_delta": cfg.training.early_stop_min_delta,
            "exp_name": cfg.training.exp_name,
            "train_dataset_name": cfg.training.dataset_name,
            # Model
            "base_model": cfg.model.base_model,
            "custom_checkpoint": cfg.model.custom_checkpoint,
            "auto_download_pretrained": cfg.model.auto_download_pretrained,
            "model_filename": cfg.model.model_filename,
            "pretrained_model_path": cfg.paths.pretrained_model_path,
            "model_type": cfg.model.model_type,
            "dim": cfg.model.dim,
            "depth": cfg.model.depth,
            "heads": cfg.model.heads,
            "ff_mult": cfg.model.ff_mult,
            "text_dim": cfg.model.text_dim,
            "conv_layers": cfg.model.conv_layers,
            # EMA
            "use_ema": cfg.model.use_ema,
            "ema_decay": cfg.model.ema_decay,
            "ema_update_every": cfg.model.ema_update_every,
            "ema_update_after_step": cfg.model.ema_update_after_step,
            # Optimizer
            "optimizer_type": cfg.optimizer.type,
            "betas": cfg.optimizer.betas,
            "weight_decay": cfg.optimizer.weight_decay,
            "eps": cfg.optimizer.eps,
            "use_8bit_adam": cfg.optimizer.use_8bit_adam,
            # Mel Spec
            "target_sample_rate": cfg.mel_spec.target_sample_rate,
            "n_mel_channels": cfg.mel_spec.n_mel_channels,
            "hop_length": cfg.mel_spec.hop_length,
            "win_length": cfg.mel_spec.win_length,
            "n_fft": cfg.mel_spec.n_fft,
            "mel_spec_type": cfg.mel_spec.mel_spec_type,
            # Vocoder
            "vocoder_name": cfg.vocoder.name,
            "is_local": cfg.vocoder.is_local,
            "local_path": cfg.vocoder.local_path,
            # Checkpoints
            "save_per_updates": cfg.checkpoints.save_per_updates,
            "save_per_epochs": cfg.checkpoints.save_per_epochs,
            "keep_last_n_checkpoints": cfg.checkpoints.keep_last_n_checkpoints,
            "last_per_updates": cfg.checkpoints.last_per_updates,
            "resume_from_checkpoint": cfg.checkpoints.resume_from_checkpoint,
            "log_samples": cfg.checkpoints.log_samples,
            "log_samples_per_updates": cfg.checkpoints.log_samples_per_updates,
            "log_samples_per_epochs": cfg.checkpoints.log_samples_per_epochs,
            # Logging
            "logger": cfg.logging.logger,
            "log_every_n_steps": cfg.logging.log_every_n_steps,
            "wandb_enabled": cfg.logging.wandb.enabled,
            "wandb_project": cfg.logging.wandb.project,
            "wandb_entity": cfg.logging.wandb.entity,
            "wandb_run_name": cfg.logging.wandb.run_name,
            "tensorboard_port": cfg.logging.tensorboard_port,
            # Hardware
            "device": cfg.hardware.device,
            "num_gpus": cfg.hardware.num_gpus,
            "num_workers": cfg.hardware.num_workers,
            "dataloader_workers": cfg.hardware.dataloader_workers,
            "pin_memory": cfg.hardware.pin_memory,
            "persistent_workers": cfg.hardware.persistent_workers,
            # Mixed Precision
            "mixed_precision": cfg.mixed_precision.enabled,
            "mixed_precision_dtype": cfg.mixed_precision.dtype,
            # Validation
            "validation_enabled": cfg.validation.enabled,
            "val_dataset_path": cfg.validation.val_dataset_path,
            "val_every_n_updates": cfg.validation.val_every_n_updates,
            "num_val_samples": cfg.validation.num_val_samples,
            # Advanced
            "gradient_checkpointing": cfg.advanced.gradient_checkpointing,
            "seed": cfg.advanced.seed,
            "compile_model": cfg.advanced.compile_model,
            "f5tts_base_dir": cfg.advanced.f5tts_base_dir,
            "f5tts_ckpts_dir": cfg.advanced.f5tts_ckpts_dir,
            # Paths
            "dataset_path": cfg.paths.dataset_path,
            "output_dir": cfg.paths.output_dir,
            "tensorboard_dir": cfg.paths.tensorboard_dir,
            "vocab_file": cfg.paths.vocab_file,
        }

    def download_pretrained_model(self):
        """Baixa modelo pré-treinado do HuggingFace se necessário"""
        if not self.config.get("pretrained_model_path"):
            return None

        pretrained_path = Path(self.config["pretrained_model_path"])

        # Se caminho relativo, converter para absoluto
        if not pretrained_path.is_absolute():
            pretrained_path = PROJECT_ROOT / pretrained_path

        # Se o arquivo já existe, retorna o caminho
        if pretrained_path.exists():
            logger.info(f"✅ Modelo pré-treinado encontrado: {pretrained_path}")
            return str(pretrained_path.absolute())

        # Verificar se deve baixar automaticamente
        if not self.config.get("auto_download_pretrained", False):
            logger.warning(f"⚠️  Modelo não encontrado: {pretrained_path}")
            logger.warning(
                "   Configure AUTO_DOWNLOAD_PRETRAINED=true no .env para baixar automaticamente"
            )
            return None

        # Baixar modelo do HuggingFace
        base_model = self.config.get("base_model", "firstpixel/F5-TTS-pt-br")
        logger.info(f"📥 Baixando modelo pré-treinado: {base_model}")

        try:
            from huggingface_hub import hf_hub_download

            # Criar diretório
            self.pretrained_dir.mkdir(parents=True, exist_ok=True)
            model_dir = self.pretrained_dir / base_model.split("/")[-1]
            model_dir.mkdir(parents=True, exist_ok=True)

            # Baixar arquivo do modelo (configurável via MODEL_FILENAME no .env)
            model_filename = self.config.get("model_filename", "pt-br/model_200000.pt")
            logger.info(f"   Baixando {model_filename}...")
            downloaded_file = hf_hub_download(
                repo_id=base_model,
                filename=model_filename,
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
            )

            logger.info(f"✅ Modelo baixado: {downloaded_file}")
            return downloaded_file

        except Exception as e:
            logger.error(f"❌ Erro ao baixar modelo: {e}")
            logger.info("   Você pode baixar manualmente de:")
            logger.info(f"   https://huggingface.co/{base_model}")
            return None

    def setup_checkpoints_symlink(self):
        """
        Cria symlinks automáticos para F5-TTS:
        1. ckpts/f5_dataset -> train/output/F5TTS_Base (checkpoints)
        2. data -> train/data (dataset)
        3. runs -> train/runs (TensorBoard logs)
        """
        # 1. Symlink de checkpoints
        f5_ckpts_base = self.config.get("f5tts_ckpts_dir")
        
        # Se null/None, usar default
        if not f5_ckpts_base:
            f5_ckpts_base = "/root/.local/lib/python3.11/ckpts"
            
        f5_ckpt_dir = Path(f5_ckpts_base) / self.config["train_dataset_name"]
        target_dir = self.output_dir

        # Garantir que target existe
        target_dir.mkdir(parents=True, exist_ok=True)

        if f5_ckpt_dir.exists() and f5_ckpt_dir.is_symlink():
            # Já é symlink - verificar se aponta para lugar certo
            current_target = f5_ckpt_dir.resolve()
            if current_target != target_dir:
                logger.warning(f"⚠️  Symlink aponta para: {current_target}")
                logger.warning(f"   Redirecionando para: {target_dir}")
                f5_ckpt_dir.unlink()
                f5_ckpt_dir.symlink_to(target_dir)
            else:
                logger.info(
                    f"✅ Symlink de checkpoints OK: ckpts/{self.config['train_dataset_name']} -> {target_dir.relative_to(PROJECT_ROOT)}"
                )
        elif f5_ckpt_dir.exists():
            # Diretório real existe - mover conteúdo
            logger.info(
                f"📦 Movendo checkpoints existentes para {target_dir.relative_to(PROJECT_ROOT)}/"
            )
            import shutil

            for item in f5_ckpt_dir.iterdir():
                dest = target_dir / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))
                    logger.info(f"   ✅ {item.name}")

            # Remover diretório vazio e criar symlink
            try:
                f5_ckpt_dir.rmdir()
            except:
                import shutil

                shutil.rmtree(f5_ckpt_dir)

            f5_ckpt_dir.symlink_to(target_dir)
            logger.info(
                f"✅ Symlink criado: ckpts/{self.config['train_dataset_name']} -> {target_dir.relative_to(PROJECT_ROOT)}"
            )
        else:
            # Não existe - criar symlink
            f5_ckpt_dir.parent.mkdir(parents=True, exist_ok=True)
            f5_ckpt_dir.symlink_to(target_dir)
            logger.info(
                f"✅ Symlink criado: ckpts/{self.config['train_dataset_name']} -> {target_dir.relative_to(PROJECT_ROOT)}"
            )

        # 2. Symlink de data (automático)
        f5_base_dir = self.config.get("f5tts_base_dir")
        
        # Se null/None, usar default
        if not f5_base_dir:
            f5_base_dir = "/root/.local/lib/python3.11"
            
        data_link = Path(f5_base_dir) / "data"
        if not data_link.exists():
            data_link.symlink_to(self.data_dir.absolute(), target_is_directory=True)
            logger.info(f"✅ Symlink criado: data -> {self.data_dir.relative_to(PROJECT_ROOT)}")
        elif data_link.is_symlink() and data_link.resolve() == self.data_dir:
            logger.info("✅ Symlink de data OK")

        # 3. Symlink f5_dataset_pinyin -> f5_dataset (automático)
        dataset_dir = self.data_dir / self.config["train_dataset_name"]
        pinyin_link = self.data_dir / f"{self.config['train_dataset_name']}_pinyin"
        if not pinyin_link.exists() and dataset_dir.exists():
            pinyin_link.symlink_to(dataset_dir, target_is_directory=True)
            logger.info(f"✅ Symlink criado: {pinyin_link.name} -> {dataset_dir.name}")

        # 4. Symlink runs/ -> train/runs/ (para TensorBoard logs)
        # F5-TTS cria runs/ na raiz do workspace automaticamente
        # Precisamos redirecionar ANTES do treinamento começar
        root_runs = PROJECT_ROOT / "runs"
        if not root_runs.exists():
            # Ainda não foi criado - criar symlink preventivamente
            root_runs.symlink_to(self.runs_dir.absolute(), target_is_directory=True)
            logger.info(f"✅ Symlink criado: /runs -> {self.runs_dir.relative_to(PROJECT_ROOT)}")
        elif root_runs.is_symlink():
            # Já é symlink - verificar se aponta para o lugar certo
            if root_runs.resolve() != self.runs_dir.absolute():
                logger.warning(f"⚠️  Symlink /runs aponta para {root_runs.resolve()}")
                logger.warning(f"   Redirecionando para {self.runs_dir.absolute()}")
                root_runs.unlink()
                root_runs.symlink_to(self.runs_dir.absolute(), target_is_directory=True)
            else:
                logger.info("✅ Symlink /runs OK")

    def validate_checkpoint(self, checkpoint_path: str) -> bool:
        """
        Valida se um checkpoint pode ser carregado

        Returns:
            True se válido, False se corrompido
        """
        try:
            import torch

            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

            # Verificar se tem as keys esperadas
            if not isinstance(checkpoint, dict):
                logger.error(f"❌ Checkpoint não é um dict: {checkpoint_path}")
                return False

            # Verificar tamanho do arquivo (checkpoints válidos têm ~5GB)
            file_size_gb = Path(checkpoint_path).stat().st_size / (1024**3)
            if file_size_gb < 1.0:
                logger.error(
                    f"❌ Checkpoint muito pequeno ({file_size_gb:.1f}GB): {checkpoint_path}"
                )
                return False

            logger.info(
                f"✅ Checkpoint válido ({file_size_gb:.1f}GB): {Path(checkpoint_path).name}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Checkpoint corrompido: {checkpoint_path}")
            logger.error(f"   Erro: {e}")
            return False

    def check_disk_space(self, required_gb: float = 10.0) -> bool:
        """
        Verifica se há espaço em disco suficiente

        Args:
            required_gb: Espaço mínimo necessário em GB

        Returns:
            True se há espaço suficiente
        """

        stat = shutil.disk_usage(str(self.output_dir))
        available_gb = stat.free / (1024**3)

        if available_gb < required_gb:
            logger.warning(
                f"⚠️  Espaço em disco baixo: {available_gb:.1f}GB disponível (mínimo: {required_gb}GB)"
            )
            return False

        return True

    def cleanup_old_checkpoints(self, keep_last_n: int = None):
        """
        Remove checkpoints antigos mantendo apenas os últimos N

        Args:
            keep_last_n: Número de checkpoints a manter (usa config se None)
        """
        if keep_last_n is None:
            keep_last_n = self.config.get("keep_last_n_checkpoints", 10)

        # Listar checkpoints numerados (model_*.pt, exceto model_last.pt)
        checkpoints = sorted(
            [f for f in self.output_dir.glob("model_*.pt") if f.name != "model_last.pt"],
            key=lambda x: int(x.stem.split("_")[1]) if x.stem.split("_")[1].isdigit() else 0,
        )

        if len(checkpoints) <= keep_last_n:
            return

        # Remover os mais antigos
        to_remove = checkpoints[:-keep_last_n]
        freed_space_gb = 0

        for ckpt in to_remove:
            size_gb = ckpt.stat().st_size / (1024**3)
            ckpt.unlink()
            freed_space_gb += size_gb
            logger.info(f"🗑️  Removido checkpoint antigo: {ckpt.name} ({size_gb:.1f}GB)")

        if freed_space_gb > 0:
            logger.info(f"✅ Espaço liberado: {freed_space_gb:.1f}GB")

    def setup_environment(self):
        """Configura ambiente e diretórios"""
        logger.info("=" * 80)
        logger.info("🚀 F5-TTS TRAINING PIPELINE v3.0")
        logger.info("=" * 80)

        # Criar diretórios
        for dir_path in [self.runs_dir, self.output_dir, self.data_dir, self.pretrained_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Setup symlinks automáticos (checkpoints, data, pinyin)
        self.setup_checkpoints_symlink()

        # Baixar modelo pré-treinado se necessário
        pretrained_path = self.download_pretrained_model()
        if pretrained_path:
            self.config["pretrained_model_path"] = pretrained_path

        # Mover runs/ e data/ se existirem fora de train/
        # NÃO PRECISA MAIS - O symlink já redireciona tudo
        # self._organize_directories()

        logger.info("")
        logger.info("📋 CONFIGURAÇÃO (via .env)")
        logger.info("-" * 80)
        logger.info(f"Epochs: {self.config['epochs']}")
        logger.info(f"Batch size: {self.config['batch_size']}")
        logger.info(f"Gradient accumulation: {self.config['grad_accumulation_steps']}")
        logger.info(f"Learning rate: {self.config['learning_rate']}")
        logger.info(
            f"Early stopping: {self.config['early_stop_patience']} epochs (min_delta={self.config['early_stop_min_delta']})"
        )
        logger.info(f"Save checkpoints: cada {self.config['save_per_updates']} updates")
        logger.info(f"Generate samples: cada {self.config['log_samples_per_updates']} updates")
        logger.info(f"Keep last N checkpoints: {self.config['keep_last_n_checkpoints']}")
        logger.info("")
        logger.info("📁 ESTRUTURA")
        logger.info("-" * 80)
        logger.info(f"Dataset: {self.data_dir.relative_to(PROJECT_ROOT)}/f5_dataset/")
        logger.info(f"Checkpoints: {self.output_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(f"TensorBoard: {self.runs_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(
            f"Samples: {self.output_dir.relative_to(PROJECT_ROOT)}/samples/ (a cada {self.config['log_samples_per_updates']} updates)"
        )
        logger.info("=" * 80)
        logger.info("")

        # Verificar espaço em disco

        stat = shutil.disk_usage(str(self.output_dir))
        available_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_gb = stat.used / (1024**3)

        logger.info("💾 ESPAÇO EM DISCO")
        logger.info("-" * 80)
        logger.info(f"Total: {total_gb:.1f}GB")
        logger.info(f"Usado: {used_gb:.1f}GB ({used_gb/total_gb*100:.1f}%)")
        logger.info(f"Disponível: {available_gb:.1f}GB")

        # Limpar checkpoints antigos se espaço < 30GB
        if available_gb < 30.0:
            logger.warning("⚠️  Espaço baixo! Limpando checkpoints antigos...")
            self.cleanup_old_checkpoints(keep_last_n=3)  # Manter apenas 3

            # Re-verificar
            stat = shutil.disk_usage(str(self.output_dir))
            available_gb = stat.free / (1024**3)
            logger.info(f"✅ Espaço disponível após limpeza: {available_gb:.1f}GB")

        if available_gb < 15.0:
            logger.error(f"❌ ERRO: Espaço insuficiente ({available_gb:.1f}GB)")
            logger.error("   Necessário pelo menos 15GB para continuar treinamento")
            logger.error("   Libere espaço ou reduza keep_last_n_checkpoints no .env")
            sys.exit(1)

        logger.info("=" * 80)
        logger.info("")

        # Iniciar TensorBoard automaticamente
        self.start_tensorboard()

    def _organize_directories(self):
        """Move runs/ da raiz para train/runs se necessário"""
        root_runs = PROJECT_ROOT / "runs"

        if root_runs.exists() and root_runs != self.runs_dir:
            logger.info("📦 Movendo /runs/ -> /train/runs/")
            if self.runs_dir.exists():
                import shutil

                shutil.rmtree(self.runs_dir)
            import shutil

            shutil.move(str(root_runs), str(self.runs_dir))
            logger.info("   ✅ Movido")

    def start_tensorboard(self):
        """Inicia TensorBoard em background"""
        port = self.config.get("tensorboard_port", 6006)

        # Verificar se já está rodando
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result == 0:
                logger.info(f"📊 TensorBoard já rodando em http://localhost:{port}")
                return
        except:
            pass

        # Iniciar TensorBoard
        try:
            # Tentar encontrar tensorboard no PATH ou em locais comuns
            tensorboard_cmd = None
            for cmd in ["/root/.local/bin/tensorboard", "tensorboard"]:
                try:
                    result = subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
                    tensorboard_cmd = cmd
                    break
                except:
                    continue

            if not tensorboard_cmd:
                raise FileNotFoundError("tensorboard não encontrado")

            self.tensorboard_process = subprocess.Popen(
                [
                    tensorboard_cmd,
                    "--logdir",
                    str(self.runs_dir),
                    "--port",
                    str(port),
                    "--bind_all",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.info(f"📊 TensorBoard iniciado em http://localhost:{port}")
            logger.info(f"   Logdir: {self.runs_dir.relative_to(PROJECT_ROOT)}/")
            logger.info("")
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível iniciar TensorBoard: {e}")
            logger.info("")

    def run_training(self):
        """Executa treinamento F5-TTS com auto-resume inteligente"""
        from pathlib import Path
        import sys

        # Use intelligent checkpoint resolution
        resume_checkpoint = None
        pretrained_model = None

        try:
            from train.utils.checkpoint import resolve_checkpoint_path

            logger.info("🔍 Using intelligent checkpoint resolution...")

            # Try to resolve existing checkpoint
            resolved = resolve_checkpoint_path(
                self.config_obj,
                checkpoint_name=None,
                auto_download=False,  # Don't auto-download, we'll handle pretrained separately
                verbose=True,
            )

            if resolved:
                # Check if this is a training checkpoint or pretrained model
                resolved_path = Path(resolved)
                if str(self.output_dir) in str(resolved_path):
                    # It's from our training output - resume
                    resume_checkpoint = resolved
                    logger.info(f"✅ Auto-resume from: {resolved_path.name}")
                else:
                    # It's a pretrained model - use for fine-tuning
                    pretrained_model = resolved
                    logger.info(f"✅ Fine-tune from: {resolved_path.name}")

        except ImportError:
            logger.debug("Checkpoint utilities not available, using legacy detection")
        except Exception as e:
            logger.warning(f"Checkpoint resolution failed: {e}, using legacy detection")

        # Fallback to legacy checkpoint detection if intelligent resolution didn't find anything
        if not resume_checkpoint and not pretrained_model:
            logger.info("📂 Using legacy checkpoint detection...")

            # Priority 1: Check training output directory for existing checkpoints
            local_output_dir = self.output_dir

            if local_output_dir.exists():
                # Look for model_last.pt first (most recent)
                last_ckpt = local_output_dir / "model_last.pt"
                if last_ckpt.exists() and self.validate_checkpoint(str(last_ckpt)):
                    resume_checkpoint = str(last_ckpt.absolute())
                    logger.info(f"📂 Checkpoint válido encontrado: {last_ckpt.name}")
                else:
                    if last_ckpt.exists():
                        logger.warning(f"⚠️  Checkpoint corrompido, ignorando: {last_ckpt.name}")
                        # Renomear checkpoint corrompido
                        corrupted_name = last_ckpt.with_suffix(".pt.corrupted")
                        last_ckpt.rename(corrupted_name)
                        logger.info(f"   Renomeado para: {corrupted_name.name}")

                    # Look for numbered checkpoints
                    checkpoints = sorted(
                        local_output_dir.glob("model_*.pt"),
                        key=lambda x: (
                            int(x.stem.split("_")[1]) if x.stem.split("_")[1].isdigit() else 0
                        ),
                    )
                    for ckpt in reversed(checkpoints):  # Mais recente primeiro
                        if self.validate_checkpoint(str(ckpt)):
                            resume_checkpoint = str(ckpt.absolute())
                            logger.info(f"📂 Checkpoint válido encontrado: {ckpt.name}")
                            break
                        else:
                            logger.warning(f"⚠️  Checkpoint corrompido, pulando: {ckpt.name}")
                            # Renomear checkpoint corrompido
                            corrupted_name = ckpt.with_suffix(".pt.corrupted")
                            ckpt.rename(corrupted_name)

            # Priority 2: Check F5-TTS ckpts directory
            if not resume_checkpoint:
                # Usar F5TTS_CKPTS_DIR do .env ou path padrão
                f5tts_base = self.config.get("f5tts_ckpts_dir", "/root/.local/lib/python3.11/ckpts")
                checkpoint_dir = Path(f"{f5tts_base}/{self.config['train_dataset_name']}")
                if checkpoint_dir.exists():
                    last_ckpt = checkpoint_dir / "model_last.pt"
                    if last_ckpt.exists() and self.validate_checkpoint(str(last_ckpt)):
                        resume_checkpoint = str(last_ckpt.absolute())
                        logger.info(f"📂 Checkpoint válido encontrado em ckpts/: {last_ckpt.name}")

            # Priority 3: Use local pretrained model from models/f5tts/pt-br/
            if not resume_checkpoint:
                # Usar LOCAL_PRETRAINED_PATH do .env ou path padrão
                local_pretrained_path = self.config.get(
                    "local_pretrained_path", "models/f5tts/pt-br/model_last.pt"
                )
                local_pretrained = PROJECT_ROOT / local_pretrained_path
                if local_pretrained.exists() and self.validate_checkpoint(str(local_pretrained)):
                    pretrained_model = str(local_pretrained.absolute())
                    logger.info(
                        f"📥 Modelo pré-treinado válido: {local_pretrained.relative_to(PROJECT_ROOT)}"
                    )
                elif local_pretrained.exists():
                    logger.warning(
                        f"⚠️  Modelo pré-treinado corrompido: {local_pretrained.relative_to(PROJECT_ROOT)}"
                    )

            # Priority 4: Use pretrained model from .env configuration
            if not resume_checkpoint and not pretrained_model:
                pretrained_path_env = self.config.get("pretrained_model_path")
                if pretrained_path_env and pretrained_path_env.strip():  # Só se não estiver vazio
                    # Caminhos podem ser:
                    # 1. Absolutos: /root/.local/lib/python3.11/ckpts/f5_dataset/model_last.pt
                    # 2. Relativos ao F5-TTS: ckpts/f5_dataset/model_last.pt
                    # 3. Relativos ao workspace: train/pretrained/model.pt

                    pretrained_path = Path(pretrained_path_env)

                    if pretrained_path.is_absolute() and pretrained_path.exists():
                        # Caminho absoluto
                        pretrained_model = str(pretrained_path.absolute())
                        logger.info(
                            f"📥 Usando modelo pré-treinado (absoluto): {pretrained_path.name}"
                        )
                    elif pretrained_path_env.startswith("ckpts/"):
                        # Caminho relativo ao F5-TTS (ckpts/f5_dataset/model_last.pt)
                        f5tts_base_dir = self.config.get(
                            "f5tts_base_dir", "/root/.local/lib/python3.11"
                        )
                        f5tts_base = Path(f5tts_base_dir)
                        pretrained_full = f5tts_base / pretrained_path_env
                        if pretrained_full.exists():
                            pretrained_model = str(pretrained_full.absolute())
                            logger.info(
                                f"📥 Usando modelo pré-treinado (F5-TTS): {pretrained_full.name}"
                            )
                        else:
                            logger.warning(f"⚠️  Modelo não encontrado: {pretrained_full}")
                    else:
                        # Caminho relativo ao workspace
                        pretrained_full = self.train_root / pretrained_path_env.replace(
                            "train/", ""
                        )
                        if pretrained_full.exists():
                            pretrained_model = str(pretrained_full.absolute())
                            logger.info(
                                f"📥 Usando modelo pré-treinado (workspace): {pretrained_full.name}"
                            )
                        else:
                            logger.warning(f"⚠️  Modelo não encontrado: {pretrained_full}")

        # Preparar argumentos para finetune_cli
        args = [
            "--exp_name",
            self.config.get("exp_name", "F5TTS_Base"),
            "--dataset_name",
            self.config["train_dataset_name"],
            "--learning_rate",
            str(self.config["learning_rate"]),
            "--batch_size_per_gpu",
            str(self.config["batch_size"]),
            "--batch_size_type",
            self.config["batch_size_type"],
            "--max_samples",
            str(self.config.get("max_samples", 32)),
            "--grad_accumulation_steps",
            str(self.config["grad_accumulation_steps"]),
            "--max_grad_norm",
            str(self.config.get("max_grad_norm", 1.0)),
            "--epochs",
            str(self.config["epochs"]),
            "--num_warmup_updates",
            str(self.config["num_warmup_updates"]),
            "--save_per_updates",
            str(self.config["save_per_updates"]),
            "--last_per_updates",
            str(self.config["last_per_updates"]),
            "--keep_last_n_checkpoints",
            str(self.config["keep_last_n_checkpoints"]),
            "--logger",
            self.config.get("logger", "tensorboard"),
        ]

        # Add finetune flag only if we have a pretrained model
        # (finetune mode requires a checkpoint to continue from)
        has_pretrained = resume_checkpoint or pretrained_model
        if has_pretrained:
            args.append("--finetune")

        # Add log_samples flag if enabled
        if self.config.get("log_samples", True):
            args.append("--log_samples")

        # Add pretrained model path
        if resume_checkpoint:
            # Continue from existing checkpoint
            args.extend(["--pretrain", resume_checkpoint])
            logger.info("🔄 Modo: Continuar treinamento do checkpoint")
        elif pretrained_model:
            # Start from local pretrained model
            args.extend(["--pretrain", pretrained_model])
            logger.info("🎯 Modo: Fine-tuning do modelo pré-treinado local")
        else:
            logger.info("🆕 Modo: Treinamento do zero (sem modelo pré-treinado)")

        logger.info("")
        logger.info("🚀 Iniciando treinamento F5-TTS...")
        logger.info(f"   Argumentos completos: {args}")
        logger.info("")

        # Start checkpoint metadata monitor in background
        import threading

        metadata_thread = threading.Thread(
            target=self.monitor_checkpoints_and_add_metadata, daemon=True
        )
        metadata_thread.start()
        logger.info("📊 Checkpoint metadata monitor started")

        try:
            # Executar via CLI
            original_argv = sys.argv.copy()
            sys.argv = ["finetune_cli"] + args

            from f5_tts.train.finetune_cli import main as finetune_main

            finetune_main()

            sys.argv = original_argv

        except KeyboardInterrupt:
            logger.info("")
            logger.info("⚠️  Treinamento interrompido pelo usuário")
            self.cleanup()
            sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Erro durante treinamento: {e}")
            import traceback

            traceback.print_exc()
            self.cleanup()
            sys.exit(1)

    def monitor_checkpoints_and_add_metadata(self):
        """
        Monitor checkpoint directory and add metadata to new checkpoints.

        This runs in background during training to automatically add metadata
        to model_last.pt whenever it's updated.
        """
        from datetime import datetime
        import hashlib
        import json

        logger.info("📊 Starting checkpoint metadata monitor...")

        seen_checkpoints = set()
        last_metadata_update = {}

        while True:
            try:
                time.sleep(10)  # Check every 10 seconds

                # Find all checkpoints in output dir
                if not self.output_dir.exists():
                    continue

                checkpoints = list(self.output_dir.glob("model_*.pt"))

                for ckpt_path in checkpoints:
                    # Skip if already processed and not modified
                    ckpt_mtime = ckpt_path.stat().st_mtime

                    if str(ckpt_path) in last_metadata_update:
                        if last_metadata_update[str(ckpt_path)] >= ckpt_mtime:
                            continue

                    # Add metadata
                    try:
                        # Calculate checkpoint hash (first 1MB for speed)
                        hasher = hashlib.sha256()
                        with open(ckpt_path, "rb") as f:
                            hasher.update(f.read(1024 * 1024))
                        ckpt_hash = hasher.hexdigest()[:16]

                        # Build metadata
                        metadata = {
                            "checkpoint_name": ckpt_path.name,
                            "created_at": datetime.fromtimestamp(ckpt_mtime).isoformat(),
                            "size_bytes": ckpt_path.stat().st_size,
                            "size_gb": round(ckpt_path.stat().st_size / (1024**3), 2),
                            "hash_partial": ckpt_hash,
                            "config": {
                                "exp_name": self.config.get("exp_name"),
                                "dataset_name": self.config.get("train_dataset_name"),
                                "learning_rate": self.config.get("learning_rate"),
                                "batch_size": self.config.get("batch_size"),
                                "epochs": self.config.get("epochs"),
                            },
                            "training": {
                                "num_warmup_updates": self.config.get("num_warmup_updates"),
                                "max_grad_norm": self.config.get("max_grad_norm"),
                                "grad_accumulation_steps": self.config.get(
                                    "grad_accumulation_steps"
                                ),
                            },
                            "metadata_version": "1.0",
                        }

                        # Save metadata JSON
                        metadata_path = ckpt_path.parent / f"{ckpt_path.stem}.metadata.json"
                        with open(metadata_path, "w") as f:
                            json.dump(metadata, f, indent=2)

                        logger.info(f"💾 Added metadata: {metadata_path.name}")
                        last_metadata_update[str(ckpt_path)] = ckpt_mtime

                    except Exception as e:
                        logger.warning(f"Failed to add metadata to {ckpt_path.name}: {e}")

            except KeyboardInterrupt:
                logger.info("🛑 Checkpoint monitor stopped")
                break
            except Exception as e:
                logger.warning(f"Checkpoint monitor error: {e}")
                time.sleep(5)

    def cleanup(self):
        """Limpa processos em background"""
        if self.tensorboard_process:
            try:
                os.killpg(os.getpgid(self.tensorboard_process.pid), signal.SIGTERM)
                logger.info("🛑 TensorBoard encerrado")
            except:
                pass

    def run(self):
        """Pipeline completo"""
        try:
            self.setup_environment()
            self.start_tensorboard()
            self.run_training()

        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            import traceback

            traceback.print_exc()
            self.cleanup()
            sys.exit(1)


def main():
    """Entry point with CLI argument support"""

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="F5-TTS Training with Unified Config System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic training with defaults
  python -m train.run_training
  
  # Override learning rate and batch size
  python -m train.run_training --lr 2e-4 --batch-size 4
  
  # Full custom experiment
  python -m train.run_training --lr 3e-4 --batch-size 8 --epochs 500 --exp-name my_exp
  
  # Resume from specific checkpoint
  python -m train.run_training --resume train/output/model_100000.pt
        """,
    )

    # Training hyperparameters
    parser.add_argument(
        "--lr",
        "--learning-rate",
        type=float,
        dest="learning_rate",
        help="Learning rate (default: from config)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        dest="batch_size",
        help="Batch size per GPU (default: from config)",
    )
    parser.add_argument("--epochs", type=int, help="Number of epochs (default: from config)")
    parser.add_argument(
        "--grad-accum",
        type=int,
        dest="grad_accumulation_steps",
        help="Gradient accumulation steps (default: from config)",
    )

    # Experiment
    parser.add_argument(
        "--exp-name", type=str, dest="exp_name", help="Experiment name (default: from config)"
    )
    parser.add_argument(
        "--output-dir", type=str, dest="output_dir", help="Output directory (default: from config)"
    )

    # Hardware
    parser.add_argument(
        "--device", type=str, choices=["cuda", "cpu", "auto"], help="Device (default: from config)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        dest="dataloader_workers",
        help="DataLoader workers (default: from config)",
    )

    # Checkpoints
    parser.add_argument(
        "--resume", type=str, dest="resume_from_checkpoint", help="Resume from checkpoint path"
    )
    parser.add_argument(
        "--save-every",
        type=int,
        dest="save_per_updates",
        help="Save checkpoint every N updates (default: from config)",
    )

    # Logging
    parser.add_argument(
        "--wandb", action="store_true", dest="wandb_enabled", help="Enable W&B logging"
    )
    parser.add_argument("--wandb-project", type=str, dest="wandb_project", help="W&B project name")

    # Advanced
    parser.add_argument("--seed", type=int, help="Random seed (default: from config)")
    parser.add_argument(
        "--no-tensorboard", action="store_true", help="Disable TensorBoard (use logger=null)"
    )

    args = parser.parse_args()

    # Convert CLI args to config overrides
    cli_overrides = {}

    # Training overrides
    training_overrides = {}
    if args.learning_rate is not None:
        training_overrides["learning_rate"] = args.learning_rate
    if args.batch_size is not None:
        training_overrides["batch_size_per_gpu"] = args.batch_size
    if args.epochs is not None:
        training_overrides["epochs"] = args.epochs
    if args.grad_accumulation_steps is not None:
        training_overrides["grad_accumulation_steps"] = args.grad_accumulation_steps
    if args.exp_name is not None:
        training_overrides["exp_name"] = args.exp_name

    if training_overrides:
        cli_overrides["training"] = training_overrides

    # Hardware overrides
    hardware_overrides = {}
    if args.device is not None:
        hardware_overrides["device"] = args.device
    if args.dataloader_workers is not None:
        hardware_overrides["dataloader_workers"] = args.dataloader_workers

    if hardware_overrides:
        cli_overrides["hardware"] = hardware_overrides

    # Paths overrides
    paths_overrides = {}
    if args.output_dir is not None:
        paths_overrides["output_dir"] = args.output_dir

    if paths_overrides:
        cli_overrides["paths"] = paths_overrides

    # Checkpoints overrides
    checkpoints_overrides = {}
    if args.resume_from_checkpoint is not None:
        checkpoints_overrides["resume_from_checkpoint"] = args.resume_from_checkpoint
    if args.save_per_updates is not None:
        checkpoints_overrides["save_per_updates"] = args.save_per_updates

    if checkpoints_overrides:
        cli_overrides["checkpoints"] = checkpoints_overrides

    # Logging overrides
    logging_overrides = {}
    if args.wandb_enabled:
        logging_overrides.setdefault("wandb", {})["enabled"] = True
    if args.wandb_project is not None:
        logging_overrides.setdefault("wandb", {})["project"] = args.wandb_project
    if args.no_tensorboard:
        logging_overrides["logger"] = "null"

    if logging_overrides:
        cli_overrides["logging"] = logging_overrides

    # Advanced overrides
    advanced_overrides = {}
    if args.seed is not None:
        advanced_overrides["seed"] = args.seed

    if advanced_overrides:
        cli_overrides["advanced"] = advanced_overrides

    # Create trainer with CLI overrides
    trainer = F5TTSTrainer(cli_overrides=cli_overrides if cli_overrides else None)

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("")
        logger.info("⚠️  Recebido sinal de interrupção")
        trainer.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run
    trainer.run()


if __name__ == "__main__":
    main()
