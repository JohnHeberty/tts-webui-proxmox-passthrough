# F5-TTS Training Pipeline - Documentation Index

Índice completo da documentação do pipeline de treinamento F5-TTS.

---

## 📚 Começando

### Para Iniciantes
1. **[Tutorial Passo-a-Passo](TUTORIAL.md)** ⭐ **COMECE AQUI**
   - Setup completo do ambiente
   - Preparação de dataset
   - Configuração e execução de treino
   - Deploy em produção

2. **[Getting Started](../../docs/getting-started.md)**
   - Visão geral do projeto
   - Quickstart guide

---

## 🏗️ Arquitetura

### Documentação Técnica

1. **[Architecture Overview](../../docs/ARCHITECTURE.md)**
   - Arquitetura geral do sistema
   - Componentes principais
   - Fluxo de dados

2. **[Infrastructure Setup](../../docs/INFRASTRUCTURE_SETUP.md)**
   - Setup de infraestrutura
   - GPU/CUDA configuration
   - Docker deployment

3. **[Proxmox GPU Setup](../../docs/PROXMOX_GPU_SETUP.md)**
   - Configuração GPU passthrough
   - Troubleshooting Proxmox

---

## 🔧 Módulos

### Core Modules

1. **[Audio Processing](../audio/README.md)**
   - `io.py` - Load/save audio
   - `vad.py` - Voice activity detection
   - `segmentation.py` - Audio segmentation
   - `normalization.py` - Volume normalization
   - `effects.py` - Audio effects

2. **[Text Processing](../text/README.md)**
   - `normalizer.py` - Text normalization
   - `vocab.py` - Vocabulary management
   - `qa.py` - Quality assurance

3. **[I/O Utilities](../io/README.md)**
   - `youtube.py` - YouTube download
   - `subtitles.py` - Subtitle processing
   - `storage.py` - File management

4. **[Training Components](../training/README.md)**
   - `callbacks.py` - Training callbacks
   - Best model tracking
   - Audio sampling
   - Metrics logging

---

## 🎯 API Reference

### Inference API

1. **[Inference API Documentation](INFERENCE_API.md)** ⭐
   - `F5TTSInference` - Core API
   - `F5TTSInferenceService` - Service layer
   - CLI tool usage
   - Integration examples

2. **[API Parameters](../../docs/API_PARAMETERS.md)**
   - Quality parameters
   - Engine-specific settings

3. **[API Reference](../../docs/api-reference.md)**
   - REST API endpoints
   - Request/response formats

---

## ⚙️ Configuration

### Config Documentation

1. **[Configuration Schema](../config/README.md)**
   - `schemas.py` - Pydantic models
   - `loader.py` - Config loading
   - Environment variables
   - YAML structure

2. **[Quality Profiles](../../docs/QUALITY_PROFILES.md)**
   - Predefined quality settings
   - Custom profile creation
   - Profile management

---

## 🛠️ Scripts & Tools

### Utility Scripts

1. **[Scripts Reference](../scripts/README.md)**
   - `health_check.py` - Environment validation
   - `AgentF5TTSChunk.py` - Batch inference
   - `download_models.py` - Model downloader
   - Validation scripts

2. **[CLI Tools](../cli/README.md)**
   - `infer.py` - Inference CLI
   - Usage examples
   - Parameters reference

---

## 📊 Sprint Documentation

### Development Sprints

1. **[Sprint Plan](../../SPRINTS_PLAN.md)**
   - All 10 sprints detailed
   - Tasks and deliverables
   - Progress tracking

2. **Sprint Summaries:**
   - **Sprint 3:** [Dataset Consolidation](SPRINT_3_COMPLETE.md)
   - **Sprint 4:** [Reproducibility](SPRINT_4_COMPLETE.md)
   - **Sprint 5:** [Training Experience](SPRINT_5_COMPLETE.md)
   - **Sprint 6:** [Inference API](SPRINT_6_COMPLETE.md) - [Full docs](INFERENCE_API.md)
   - **Sprint 7:** [Quality & Testing](SPRINT_7_COMPLETE.md)

---

## 🧪 Testing

### Test Documentation

1. **[Test Guide](../../tests/README.md)**
   - Running tests
   - Test structure
   - Coverage reports

2. **Test Suites:**
   - Config tests: `tests/train/config/`
   - Inference tests: `tests/train/inference/`
   - Audio tests: `tests/train/audio/`

---

## 🚀 Deployment

### Production Deployment

1. **[Deployment Guide](../../docs/DEPLOYMENT.md)**
   - Production checklist
   - Scaling strategies
   - Monitoring

2. **[Docker Setup](../../docker-compose.yml)**
   - Docker configuration
   - GPU passthrough
   - Environment variables

---

## 🔧 Development

### For Contributors

1. **[Form Enum Pattern](../../docs/FORM_ENUM_PATTERN.md)**
   - Code patterns
   - Best practices

2. **[Changelog](../../docs/CHANGELOG.md)**
   - Version history
   - Breaking changes

---

## 🐛 Troubleshooting

### Common Issues

1. **[Error Patterns](../app/error_patterns.py)**
   - Common errors
   - Solutions

2. **GPU/CUDA Issues:**
   - [Proxmox Fix](../../docs/PROXMOX_FIX_RAPIDO.md)
   - [GPU Status](../../docs/STATUS_GPU_PROXMOX.md)
   - [Low VRAM Guide](../../docs/LOW_VRAM.md)

3. **[Symlink Fix](../../docs/SYMLINK_FIX.md)**
   - Model path issues

---

## 📈 Quality & Best Practices

### Code Quality

1. **Tools Configuration:**
   - `pyproject.toml` - Ruff, Black, Mypy, Pytest
   - `Makefile` - Quality commands

2. **Quality Commands:**
   ```bash
   make format      # Format code with black
   make lint        # Lint with ruff
   make typecheck   # Type check with mypy
   make test-unit   # Run unit tests
   make test-coverage  # Tests with coverage
   make check-all   # All quality checks
   ```

---

## 📖 Examples

### Code Examples

1. **[Example Usage](../config/example_usage.py)**
   - Config usage examples
   - Common patterns

2. **Quick Examples:**

   **Simple Inference:**
   ```python
   from train.inference.api import F5TTSInference
   
   inference = F5TTSInference(
       checkpoint_path="model.pt",
       vocab_file="vocab.txt",
       device="cuda"
   )
   
   audio = inference.generate(
       text="Olá, mundo!",
       ref_audio="ref.wav"
   )
   ```

   **Batch Processing:**
   ```python
   from train.inference.service import get_inference_service
   
   service = get_inference_service()
   service.configure(checkpoint_path="model.pt", vocab_file="vocab.txt")
   
   for text in texts:
       audio = service.generate(text=text, ref_audio="ref.wav")
       service.save_audio(audio, f"output_{i}.wav")
   ```

---

## 🔗 External Resources

### Official Documentation

1. **F5-TTS Library:**
   - [GitHub](https://github.com/SWivid/F5-TTS)
   - [Paper](https://arxiv.org/abs/2410.06885)

2. **PyTorch:**
   - [Docs](https://pytorch.org/docs/stable/index.html)
   - [Tutorials](https://pytorch.org/tutorials/)

3. **Pydantic:**
   - [Docs](https://docs.pydantic.dev/)
   - [Migration Guide](https://docs.pydantic.dev/latest/migration/)

---

## 📝 Quick Reference

### Most Used Commands

```bash
# Setup
make train-setup

# Health check
python train/scripts/health_check.py

# Training
python -m train.run_training --config train/config/config.yaml

# Inference CLI
python -m train.cli.infer \
    --checkpoint model.pt \
    --vocab vocab.txt \
    --text "Texto" \
    --ref-audio ref.wav \
    --output output.wav

# Tests
make test-unit

# Quality
make check-all
```

---

## 📞 Support

### Getting Help

1. **Documentation:** Search this index first
2. **GitHub Issues:** [Report bugs](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/issues)
3. **Logs:** Check `train/logs/` for detailed errors

---

## 🎯 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| Tutorial | ✅ Complete | 2025-12-06 |
| Inference API | ✅ Complete | 2025-12-06 |
| Audio README | ✅ Complete | 2025-12-06 |
| Text README | ✅ Complete | 2025-12-06 |
| Scripts README | ✅ Complete | 2025-12-06 |
| Config Schema | ✅ Complete | 2025-11-27 |
| Sprint Plan | ✅ Complete | 2025-11-25 |

---

**Last Updated:** 2025-12-06  
**Version:** 1.0  
**Maintainer:** F5-TTS Training Pipeline Team

---

## Navigation

- [⬆️ Back to Top](#f5-tts-training-pipeline---documentation-index)
- [📖 Tutorial](TUTORIAL.md)
- [🎯 Inference API](INFERENCE_API.md)
- [🏠 Main README](../../README.md)
