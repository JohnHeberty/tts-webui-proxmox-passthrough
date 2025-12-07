# Deprecated Documentation - v2.0

⚠️ **These documents contain outdated information for v2.0**

The following documents reference **RVC** and/or **F5-TTS**, which have been removed in v2.0.

---

## 📚 Partially Deprecated

These docs have some useful content but need updates:

| Document | Status | Action Needed |
|----------|--------|---------------|
| `LOW_VRAM.md` | ⚠️ Partially deprecated | Already marked with v2.0 warnings |
| `QUALITY_PROFILES.md` | ⚠️ Partially deprecated | Already updated for XTTS-only |
| `ADVANCED_FEATURES.md` | ⚠️ Contains RVC metrics | Needs update |
| `SPRINT_6.2_MODULARIZATION.md` | ⚠️ Old sprint plan | Historical reference only |

---

## 📖 Still Relevant

These docs remain valid for v2.0:

| Document | Status | Notes |
|----------|--------|-------|
| `ARCHITECTURE.md` | ✅ Valid | Core architecture unchanged |
| `DEPLOYMENT.md` | ✅ Valid | Deployment process same |
| `API_PARAMETERS.md` | ⚠️ Needs review | Remove RVC params |
| `api-reference.md` | ⚠️ Needs review | Remove RVC endpoints |
| `PROXMOX_GPU_SETUP.md` | ✅ Valid | GPU setup unchanged |
| `TRAINING_API.md` | ✅ Valid | Training still relevant |

---

## 🆕 New Documentation (v2.0)

| Document | Description |
|----------|-------------|
| `README.md` | Updated for v2.0 with migration guide |
| `CHANGELOG.md` | Complete v2.0 changelog |
| `MORE.md` | Technical analysis of RVC removal |
| `SPRINTS_RVC_REMOVAL.md` | Sprint plans for refactoring |

---

## ��️ Candidates for Removal

These docs can be safely archived/deleted:

- `SPRINT_6.2_MODULARIZATION.md` - Old sprint (completed)
- `FORM_ENUM_PATTERN.md` - Implementation detail (can be in wiki)

---

## ✅ Next Steps

1. [ ] Update `ADVANCED_FEATURES.md` - remove RVC metrics
2. [ ] Update `API_PARAMETERS.md` - remove RVC parameters
3. [ ] Update `api-reference.md` - remove RVC endpoints
4. [ ] Archive old sprints to `docs/archive/`
5. [ ] Create `docs/MIGRATION_V1_TO_V2.md` with detailed guide

**Last Updated:** 2025-12-07
**Version:** 2.0.0
