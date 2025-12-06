#!/usr/bin/env python3
"""
Auto-Trainer F5-TTS
Script completo de automação que:
1. Baixa modelo pt-BR se não existir
2. Valida e corrige compatibilidade
3. Valida dataset
4. Executa treinamento automaticamente
"""
import os
from pathlib import Path
import subprocess
import sys


# Cores para output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_step(step_num, msg):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}[PASSO {step_num}]{Colors.ENDC} {msg}")


def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")


def print_warning(msg):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")


def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ️  {msg}{Colors.ENDC}")


class AutoTrainer:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.train_root = (
            self.script_dir.parent if self.script_dir.name == "scripts" else self.script_dir
        )
        self.project_root = self.train_root.parent

        self.pretrained_dir = self.train_root / "pretrained" / "F5-TTS-pt-br" / "pt-br"
        self.dataset_dir = self.train_root / "data" / "f5_dataset"
        self.output_dir = self.train_root / "output" / "ptbr_finetuned"

        # Modelo esperado
        self.model_original = self.pretrained_dir / "model_200000.pt"
        self.model_fixed = self.pretrained_dir / "model_200000_fixed.pt"

        # Carregar configuração do .env
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Carrega configuração do .env"""
        env_file = self.train_root / ".env"
        config = {}

        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip().lower()] = value.strip()

        return config

    def run(self):
        """Executa pipeline completo"""
        print_header("🚀 AUTO-TRAINER F5-TTS - Pipeline Automático")

        try:
            # Verificar se deve usar modelo pré-treinado
            pretrain_path = self.config.get("pretrained_model_path", "")
            use_pretrained = bool(pretrain_path and pretrain_path.strip())

            if use_pretrained:
                # Passo 1: Verificar/Baixar modelo
                print_step(1, "Verificando modelo pt-BR...")
                self.ensure_model()

                # Passo 2: Validar e corrigir compatibilidade
                print_step(2, "Validando compatibilidade do modelo...")
                self.validate_and_fix_model()
            else:
                print_info("\n🔧 Treinamento do ZERO (sem modelo pré-treinado)")
                print_info("   PRETRAIN_MODEL_PATH está vazio no .env\n")

            # Passo 3: Validar dataset
            print_step(3, "Validando dataset...")
            self.validate_dataset()

            # Passo 4: Validar configuração
            print_step(4, "Validando configuração de treinamento...")
            self.validate_config()

            # Passo 5: Iniciar treinamento
            print_step(5, "Iniciando treinamento...")
            self.start_training()

        except KeyboardInterrupt:
            print_warning("\n\nProcesso interrompido pelo usuário")
            sys.exit(1)
        except Exception as e:
            print_error(f"Erro no pipeline: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    def ensure_model(self) -> None:
        """Garante que o modelo pt-BR existe"""
        # Verificar se já existe (original ou fixed)
        if self.model_fixed.exists():
            print_success(f"Modelo corrigido encontrado: {self.model_fixed.name}")
            return

        if self.model_original.exists():
            print_success(f"Modelo original encontrado: {self.model_original.name}")
            return

        # Modelo não existe, baixar
        print_warning("Modelo pt-BR não encontrado localmente")
        print_info("Iniciando download do HuggingFace...")

        self.download_model()

    def download_model(self) -> None:
        """Baixa modelo do HuggingFace"""
        try:
            from huggingface_hub import hf_hub_download

            # Criar diretório
            self.pretrained_dir.mkdir(parents=True, exist_ok=True)

            repo_id = "firstpixel/F5-TTS-pt-br"
            filename = "pt-br/model_200000.pt"

            print_info(f"Baixando de: {repo_id}/{filename}")
            print_info("Isso pode levar alguns minutos (arquivo ~5GB)...")

            # Download
            downloaded_file = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.pretrained_dir.parent),
                local_dir_use_symlinks=False,
                resume_download=True,
            )

            print_success(f"Modelo baixado: {downloaded_file}")

        except ImportError:
            print_error("huggingface_hub não instalado!")
            print_info("Instalando automaticamente...")
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
            # Tentar novamente
            self.download_model()

        except Exception as e:
            print_error(f"Erro ao baixar modelo: {e}")
            print_info("Alternativa: Baixe manualmente de:")
            print_info("https://huggingface.co/firstpixel/F5-TTS-pt-br/tree/main/pt-br")
            print_info(f"E salve em: {self.pretrained_dir}/")
            sys.exit(1)

    def validate_and_fix_model(self) -> None:
        """Valida compatibilidade e corrige se necessário"""
        # Se já existe modelo corrigido, usar
        if self.model_fixed.exists():
            print_success("Modelo corrigido já existe")
            self.verify_model_structure(self.model_fixed)
            return

        # Verificar modelo original
        if not self.model_original.exists():
            print_error("Modelo original não encontrado!")
            sys.exit(1)

        print_info("Verificando estrutura do modelo original...")
        is_compatible = self.check_model_compatibility(self.model_original)

        if is_compatible:
            print_success("Modelo original é compatível!")
            # Criar symlink ou copiar
            if not self.model_fixed.exists():
                print_info("Criando link para modelo corrigido...")
                import shutil

                shutil.copy2(self.model_original, self.model_fixed)
                print_success("Modelo preparado")
        else:
            print_warning("Modelo precisa de correção de estrutura")
            self.fix_model_structure(self.model_original, self.model_fixed)

    def check_model_compatibility(self, model_path: Path) -> bool:
        """Verifica se modelo é compatível"""
        try:
            import torch

            print_info(f"Carregando: {model_path.name}")
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

            if not isinstance(checkpoint, dict):
                return False

            # F5-TTS espera 'model' ou 'model_state_dict'
            has_model = "model" in checkpoint or "model_state_dict" in checkpoint

            if not has_model:
                print_warning("Faltando chave 'model' ou 'model_state_dict'")
                return False

            print_success("Estrutura básica OK")
            return True

        except Exception as e:
            print_error(f"Erro ao verificar modelo: {e}")
            return False

    def fix_model_structure(self, input_path: Path, output_path: Path) -> None:
        """Corrige estrutura do modelo"""
        print_info("Corrigindo estrutura do modelo...")

        try:
            import torch

            # Carregar
            checkpoint = torch.load(input_path, map_location="cpu", weights_only=False)

            # Extrair state_dict
            if "model" in checkpoint:
                model_state = checkpoint["model"]
            elif "model_state_dict" in checkpoint:
                model_state = checkpoint["model_state_dict"]
            else:
                # Checkpoint pode ser direto o state_dict
                model_state = checkpoint

            # Criar nova estrutura
            new_checkpoint = {
                "model": model_state,
                "iteration": checkpoint.get("iteration", checkpoint.get("step", 200000)),
            }

            # Copiar EMA se existir
            if "ema_model_state_dict" in checkpoint:
                new_checkpoint["ema_model_state_dict"] = checkpoint["ema_model_state_dict"]
                print_success("EMA copiado")

            # Copiar optimizer/scheduler se existir
            for key in ["optimizer", "optimizer_state_dict", "scheduler", "scheduler_state_dict"]:
                if key in checkpoint:
                    new_key = key.replace("_state_dict", "")
                    new_checkpoint[new_key] = checkpoint[key]

            # Salvar
            print_info(f"Salvando modelo corrigido em: {output_path.name}")
            torch.save(new_checkpoint, output_path)

            print_success("Modelo corrigido com sucesso!")

            # Verificar
            self.verify_model_structure(output_path)

        except Exception as e:
            print_error(f"Erro ao corrigir modelo: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    def verify_model_structure(self, model_path: Path) -> None:
        """Verifica estrutura final do modelo"""
        try:
            import torch

            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

            checks = []
            checks.append(("model" in checkpoint, "Model state_dict"))
            checks.append(("ema_model_state_dict" in checkpoint, "EMA (opcional)"))
            checks.append(("iteration" in checkpoint or "step" in checkpoint, "Iteration/Step"))

            print_info("Estrutura do modelo:")
            for passed, name in checks:
                status = "✅" if passed else "⚠️ "
                print(f"  {status} {name}")

            if "model" in checkpoint:
                num_params = len(checkpoint["model"])
                print_info(f"Parâmetros no modelo: {num_params}")

        except Exception as e:
            print_warning(f"Não foi possível verificar estrutura: {e}")

    def validate_dataset(self) -> None:
        """Valida dataset"""
        print_info(f"Dataset: {self.dataset_dir}")

        # Verificar diretório
        if not self.dataset_dir.exists():
            print_error(f"Dataset não encontrado: {self.dataset_dir}")
            print_info("Crie o dataset em train/data/f5_dataset/")
            sys.exit(1)

        # Criar symlink f5_dataset_pinyin -> f5_dataset
        # F5-TTS procura por {dataset_name}_{tokenizer}/vocab.txt
        # Como usamos tokenizer "pinyin", ele procura f5_dataset_pinyin/vocab.txt
        pinyin_link = self.dataset_dir.parent / "f5_dataset_pinyin"
        if pinyin_link.is_symlink():
            pinyin_link.unlink()
        elif pinyin_link.exists() and pinyin_link.is_dir():
            # Se existir como diretório real, não mexer
            pass

        if not pinyin_link.exists():
            pinyin_link.symlink_to(self.dataset_dir, target_is_directory=True)
            print_success("Symlink criado: f5_dataset_pinyin -> f5_dataset")

        # Verificar arquivos essenciais
        required_files = {
            "metadata.csv": self.dataset_dir / "metadata.csv",
            "duration.json": self.dataset_dir / "duration.json",
            "vocab.txt": self.dataset_dir / "vocab.txt",
        }

        all_ok = True
        for name, path in required_files.items():
            if path.exists():
                print_success(f"{name} encontrado")
            else:
                print_error(f"{name} não encontrado!")
                all_ok = False

        # Verificar wavs
        wavs_dir = self.dataset_dir / "wavs"
        if wavs_dir.exists():
            wav_files = list(wavs_dir.glob("*.wav"))
            if wav_files:
                print_success(f"{len(wav_files)} arquivos .wav encontrados")
            else:
                print_error("Nenhum arquivo .wav encontrado!")
                all_ok = False
        else:
            print_error("Diretório wavs/ não encontrado!")
            all_ok = False

        if not all_ok:
            print_error("Dataset incompleto!")
            print_info("Prepare o dataset antes de treinar")
            sys.exit(1)

        print_success("Dataset válido!")

    def validate_config(self) -> None:
        """Valida configuração"""
        env_file = self.train_root / ".env"

        if not env_file.exists():
            print_warning(".env não encontrado, usando padrões")
            return

        print_success("Configuração encontrada")

        # Verificar se modelo corrigido está configurado
        from dotenv import load_dotenv

        load_dotenv(env_file)

        pretrain_path = os.getenv("PRETRAIN_MODEL_PATH", "")
        if "model_200000_fixed.pt" not in pretrain_path:
            print_warning("Atualizando .env para usar modelo corrigido...")
            self.update_env_file(env_file)

    def update_env_file(self, env_file: Path) -> None:
        """Atualiza .env para usar modelo corrigido"""
        lines = []
        with open(env_file) as f:
            for line in f:
                if line.startswith("PRETRAIN_MODEL_PATH="):
                    lines.append(
                        "PRETRAIN_MODEL_PATH=train/pretrained/F5-TTS-pt-br/pt-br/model_200000_fixed.pt\n"
                    )
                elif line.startswith("AUTO_DOWNLOAD_PRETRAINED="):
                    lines.append("AUTO_DOWNLOAD_PRETRAINED=false\n")
                else:
                    lines.append(line)

        with open(env_file, "w") as f:
            f.writelines(lines)

        print_success(".env atualizado")

    def start_training(self) -> None:
        """Inicia treinamento"""
        print_header("🎯 Iniciando Treinamento F5-TTS")

        print_info("Modo: Verboso, primeiro plano")
        print_info(f"Modelo: {self.model_fixed.name}")
        print_info(f"Dataset: {self.dataset_dir.name}")
        print_info(f"Output: {self.output_dir}")

        print("\n" + "=" * 80)
        print("Executando run_training.py...")
        print("=" * 80 + "\n")

        # Executar no foreground
        os.chdir(self.project_root)

        try:
            # Executar diretamente, não em background
            result = subprocess.run(
                [sys.executable, "-m", "train.run_training"],
                cwd=str(self.project_root),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},  # Output em tempo real
            )

            if result.returncode == 0:
                print_success("\n✅ Treinamento concluído com sucesso!")
            else:
                print_error(f"\n❌ Treinamento terminou com código: {result.returncode}")
                sys.exit(result.returncode)

        except KeyboardInterrupt:
            print_warning("\n\n⚠️  Treinamento interrompido pelo usuário")
            sys.exit(1)


def main():
    trainer = AutoTrainer()
    trainer.run()


if __name__ == "__main__":
    main()
