# ⚙️ Configuração via .env

## 📋 Setup Inicial

```bash
# 1. Copiar arquivo de exemplo
cp train/.env.example train/.env

# 2. Editar configurações
vim train/.env
```

## 🎯 Principais Configurações

### Training Parameters

```bash
# Treina até 1000 epochs OU até parar de evoluir
EPOCHS=1000

# Tamanho do batch (ajuste conforme VRAM)
BATCH_SIZE=4

# Learning rate
LEARNING_RATE=0.0001
```

### Early Stopping

```bash
# Para se não evoluir por 5 epochs
EARLY_STOP_PATIENCE=5

# Melhora mínima de 0.1%
EARLY_STOP_MIN_DELTA=0.001
```

### Checkpoints

```bash
# Salvar a cada 500 updates
SAVE_PER_UPDATES=500

# Salvar model_last.pt a cada 50 updates
LAST_PER_UPDATES=50

# Manter 10 últimos checkpoints
KEEP_LAST_N_CHECKPOINTS=10
```

## 🔧 Como Usar

### Opção 1: Valores Padrão (.env)
```bash
# Usa configurações do .env
python3 -m train.run_supervised_training
```

### Opção 2: Testar Configuração
```bash
# Ver valores carregados
python3 -m train.utils.env_loader
```

## 📊 Exemplo de Configuração Otimizada

### Para RTX 3090 (24GB VRAM)
```bash
EPOCHS=1000
BATCH_SIZE=4
GRAD_ACCUMULATION_STEPS=4
EARLY_STOP_PATIENCE=5
MIXED_PRECISION=fp16
```

### Para GPU com menos VRAM (16GB)
```bash
EPOCHS=1000
BATCH_SIZE=2
GRAD_ACCUMULATION_STEPS=8
EARLY_STOP_PATIENCE=5
MIXED_PRECISION=fp16
```

### Para GPU com pouca VRAM (8GB)
```bash
EPOCHS=1000
BATCH_SIZE=1
GRAD_ACCUMULATION_STEPS=16
EARLY_STOP_PATIENCE=5
MIXED_PRECISION=fp16
```

## ⚡ Dicas de Performance

### Early Stopping Agressivo
```bash
# Para mais cedo se não melhorar
EARLY_STOP_PATIENCE=3
EARLY_STOP_MIN_DELTA=0.002  # 0.2%
```

### Early Stopping Conservador
```bash
# Treina por mais tempo antes de parar
EARLY_STOP_PATIENCE=10
EARLY_STOP_MIN_DELTA=0.0005  # 0.05%
```

### Salvar Mais Checkpoints
```bash
# Útil para comparar modelos
SAVE_PER_UPDATES=250
KEEP_LAST_N_CHECKPOINTS=20
```

## 🎯 Configuração Atual (Padrão)

**Objetivo**: Treinar até convergir (máximo 1000 epochs)

```bash
EPOCHS=1000                    # Limite máximo
EARLY_STOP_PATIENCE=5          # Para se 5 epochs sem melhora
EARLY_STOP_MIN_DELTA=0.001     # Melhora mínima 0.1%
```

**Resultado esperado**: 
- Treina por 20-100 epochs (típico)
- Para automaticamente quando convergir
- Economiza tempo e recursos
