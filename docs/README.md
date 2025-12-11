# 📚 Documentação - Índice Geral

Documentação completa do **Audio Voice Service** atualizada em **10 de Dezembro de 2025**.

**Versão:** v2.0.1

---

## 🎯 Guias de Início Rápido

### Para Iniciantes

1. **[README.md](../README.md)** - Porta de entrada do projeto
   - Visão geral do projeto
   - Funcionalidades principais
   - Instalação rápida (5 minutos)
   - Exemplos de uso básico
   - Links para documentação detalhada

2. **[getting-started.md](getting-started.md)** - Setup completo passo a passo
   - Pré-requisitos detalhados (hardware + software)
   - Instalação do Docker e NVIDIA toolkit
   - Configuração de variáveis de ambiente
   - Primeiros testes (WebUI + API)
   - Troubleshooting comum

### Para Desenvolvedores

3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitetura do sistema
   - Estrutura do projeto (diretórios e módulos)
   - Stack tecnológica completa
   - Componentes principais (FastAPI, Celery, Redis, TTS Engines, RVC)
   - Fluxos de dados e comunicação
   - Padrões de design (Factory, Singleton, Repository)

4. **[api-reference.md](api-reference.md)** - Referência completa da API
   - 42 endpoints REST documentados
   - Exemplos de request/response para cada endpoint
   - Códigos de status HTTP
   - Workflows completos (clone voz → TTS → RVC → download)
   - Exemplos em cURL e PowerShell

---

## 🎛️ Guias de Configuração

5. **[QUALITY_PROFILES.md](QUALITY_PROFILES.md)** - Sistema de perfis de qualidade
   - 8 perfis pré-configurados (3 XTTS + 5 F5-TTS)
   - Parâmetros detalhados de cada perfil
   - Como criar perfis customizados
   - Casos de uso recomendados
   - API de gerenciamento de perfis

6. **[LOW_VRAM.md](LOW_VRAM.md)** - Otimizações para GPU com pouca VRAM
   - Modo LOW_VRAM (carregamento/descarregamento automático)
   - Configurações para GPUs com 4GB, 6GB, 8GB
   - Monitoramento de uso de VRAM
   - Troubleshooting de Out of Memory

---

## 🚀 Deploy e Operações

7. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy em produção
   - Arquitetura de produção recomendada
   - Docker Compose vs Kubernetes
   - Configuração de reverse proxy (nginx)
   - SSL/TLS e segurança
   - Backup e disaster recovery
   - Monitoramento e logs

8. **[INFRASTRUCTURE_SETUP.md](INFRASTRUCTURE_SETUP.md)** - Setup de infraestrutura
   - Proxmox GPU passthrough
   - NVIDIA Container Toolkit
   - Configuração de rede
   - Storage e volumes persistentes
   - Scripts de automação

---

## 📝 Histórico e Manutenção

9. **[CHANGELOG.md](CHANGELOG.md)** - Histórico de versões
   - Versões lançadas com datas
   - Features adicionadas
   - Bugs corrigidos
   - Breaking changes
   - Roadmap futuro

---

## 🗂️ Estrutura da Documentação

```
docs/
├── README.md                    # Este arquivo (índice geral)
├── getting-started.md           # Setup inicial (COMECE AQUI!)
├── ARCHITECTURE.md              # Arquitetura técnica
├── api-reference.md             # API REST completa
├── QUALITY_PROFILES.md          # Perfis de qualidade
├── LOW_VRAM.md                  # Otimizações GPU
├── DEPLOYMENT.md                # Deploy produção
├── INFRASTRUCTURE_SETUP.md      # Setup infraestrutura
└── CHANGELOG.md                 # Histórico de versões
```

---

## 🎓 Fluxo de Leitura Recomendado

### Primeiro Uso (Desenvolvimento Local)

1. [README.md](../README.md) - Entender o projeto
2. [getting-started.md](getting-started.md) - Instalar e rodar
3. [api-reference.md](api-reference.md) - Explorar API
4. [QUALITY_PROFILES.md](QUALITY_PROFILES.md) - Otimizar qualidade

### Deploy em Produção

1. [ARCHITECTURE.md](ARCHITECTURE.md) - Entender arquitetura
2. [DEPLOYMENT.md](DEPLOYMENT.md) - Planejar deploy
3. [INFRASTRUCTURE_SETUP.md](INFRASTRUCTURE_SETUP.md) - Setup infraestrutura
4. [LOW_VRAM.md](LOW_VRAM.md) - Otimizar recursos (se aplicável)

### Desenvolvimento e Contribuição

1. [ARCHITECTURE.md](ARCHITECTURE.md) - Entender código
2. [api-reference.md](api-reference.md) - Conhecer API
3. [README.md](../README.md#-contribuindo) - Diretrizes de contribuição
4. [CHANGELOG.md](CHANGELOG.md) - Ver histórico

---

## 🔗 Links Externos Úteis

### Tecnologias Utilizadas

- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**
- **[Celery Documentation](https://docs.celeryq.dev/)**
- **[Redis Documentation](https://redis.io/docs/)**
- **[Docker Documentation](https://docs.docker.com/)**
- **[PyTorch Documentation](https://pytorch.org/docs/)**

### TTS Engines

- **[Coqui TTS (XTTS v2)](https://github.com/coqui-ai/TTS)**
- **[F5-TTS](https://github.com/SWivid/F5-TTS)**
- **[F5-TTS Paper](https://arxiv.org/abs/2410.06885)**

### RVC Voice Conversion

- **[RVC Project](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)**
- **[RVC Documentation](https://docs.ai-hub.wtf/rvc/)**

### GPU e CUDA

- **[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)**
- **[CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)**
- **[Proxmox GPU Passthrough Guide](https://pve.proxmox.com/wiki/PCI_Passthrough)**

---

## 🆘 Suporte

### Documentação Interativa

- **Swagger UI:** http://localhost:8005/docs
- **ReDoc:** http://localhost:8005/redoc
- **WebUI:** http://localhost:8005/webui

### Comunidade

- **Issues:** [GitHub Issues](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/issues)
- **Discussions:** [GitHub Discussions](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/discussions)

### FAQ Rápido

**Q: Qual arquivo ler primeiro?**  
A: [getting-started.md](getting-started.md) para setup inicial, depois [README.md](../README.md) para visão geral.

**Q: Como ver todos os endpoints da API?**  
A: [api-reference.md](api-reference.md) ou http://localhost:8005/docs (Swagger UI).

**Q: Meu GPU tem pouca VRAM, o que fazer?**  
A: Veja [LOW_VRAM.md](LOW_VRAM.md) e ative `LOW_VRAM=true` no `.env`.

**Q: Como fazer deploy em produção?**  
A: Siga [DEPLOYMENT.md](DEPLOYMENT.md) + [INFRASTRUCTURE_SETUP.md](INFRASTRUCTURE_SETUP.md).

**Q: Onde ver mudanças recentes?**  
A: [CHANGELOG.md](CHANGELOG.md).

---

## 📊 Status da Documentação

✅ **Completa e atualizada** (Dezembro 2025)

- README.md: ✅ Reescrito com boas práticas GitHub
- getting-started.md: ✅ Criado (guia passo a passo)
- ARCHITECTURE.md: ✅ Atualizado (baseado no código real)
- api-reference.md: ✅ Criado (42 endpoints documentados)
- QUALITY_PROFILES.md: ✅ Existente e válido
- LOW_VRAM.md: ✅ Existente e válido
- DEPLOYMENT.md: ✅ Existente e válido
- INFRASTRUCTURE_SETUP.md: ✅ Existente e válido
- CHANGELOG.md: ✅ Existente e válido

**Última verificação:** Dezembro 2025  
**Fonte de verdade:** Código do projeto (não documentos antigos)

---

<p align="center">
  <strong>📖 Documentação mantida com ❤️ pela comunidade</strong>
</p>

<p align="center">
  <a href="../README.md">← Voltar ao README principal</a>
</p>
