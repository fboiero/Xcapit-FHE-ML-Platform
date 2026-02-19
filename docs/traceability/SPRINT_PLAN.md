# Plan de Sprints — Xcapit FHE-ML Platform

## Resumen

| Sprint | Período | Foco | HU | Stories |
|--------|---------|------|----|---------|
| 1 | Dec 1-14, 2025 | Foundation | HU-01 a HU-04 | 4 |
| 2 | Dec 15-28, 2025 | Platform | HU-05 a HU-07 | 3 |
| 3 | Dec 29 - Jan 11, 2026 | Backend Migration | HU-08 a HU-11 | 4 |
| 4 | Jan 12-25, 2026 | Advanced Features | HU-12 a HU-15 | 4 |
| 5 | Jan 26 - Feb 8, 2026 | Hardening | HU-16 a HU-18 | 3 |
| 6 | Feb 9-23, 2026 | Quality & Docs | HU-19 a HU-20 | 2 |

**Total**: 20 historias, 40 commits (20 impl + 20 test), 6 sprints

## Equipo

| Miembro | Rol | Email | Stories |
|---------|-----|-------|---------|
| Franco Schillage (Tipo) | Developer | tipo@xcapit.com | HU-01, 03, 05, 07, 09, 11, 13, 15, 17, 19 |
| Fernando Boiero | Developer | fer@xcapit.com | HU-02, 04, 06, 08, 10, 12, 14, 16, 18, 20 |
| Maria Eugenia Cáceres (Rukia) | QA | euge@xcapit.com | Tests de todas las HU |

---

## Sprint 1: Foundation (Dec 1-14, 2025)

**Objetivo**: Establecer la base de cifrado FHE, modelos ML, blockchain y SDK.

| HU | Título | Dev | Impl Date | Test Date |
|----|--------|-----|-----------|-----------|
| HU-01 | Core FHE Encryption (CKKS) | Tipo | Dec 3, 10:30 | Dec 4, 14:00 |
| HU-02 | FHE ML Models (4 algoritmos) | Fernando | Dec 5, 09:00 | Dec 8, 10:30 |
| HU-03 | Blockchain & Smart Contracts | Tipo | Dec 9, 09:30 | Dec 10, 11:00 |
| HU-04 | SDK CLI & API Layer | Fernando | Dec 11, 10:00 | Dec 12, 14:30 |

**Entregables**: SDK con cifrado CKKS, 4 modelos ML, contratos Solidity deployados en Arbitrum Sepolia, CLI funcional.

---

## Sprint 2: Platform (Dec 15-28, 2025)

**Objetivo**: Construir la interfaz web (dashboard React) y landing pages por vertical.

| HU | Título | Dev | Impl Date | Test Date |
|----|--------|-----|-----------|-----------|
| HU-05 | React Dashboard Core | Tipo | Dec 15, 09:00 | Dec 16, 15:00 |
| HU-06 | Dashboard Feature Pages | Fernando | Dec 17, 10:00 | Dec 18, 11:30 |
| HU-07 | Landing Pages (Verticals) | Tipo | Dec 22, 09:30 | Dec 23, 10:00 |

**Entregables**: Dashboard con auth, 15+ páginas funcionales, 5 landing pages con i18n, Vercel deploy.

---

## Sprint 3: Backend Migration (Dec 29 - Jan 11, 2026)

**Objetivo**: Migrar de FastAPI a Django 5.2 LTS con todos los apps core.

| HU | Título | Dev | Impl Date | Test Date |
|----|--------|-----|-----------|-----------|
| HU-08 | Django Core & Auth (JWT) | Fernando | Dec 29, 09:00 | Dec 30, 14:00 |
| HU-09 | Consortiums & Governance | Tipo | Jan 2, 10:00 | Jan 3, 11:00 |
| HU-10 | Compliance, Marketplace, Sandbox | Fernando | Jan 5, 09:30 | Jan 6, 15:00 |
| HU-11 | SDK Route Tests (Legacy) | Tipo | Jan 7, 10:00 | Jan 8, 14:00 |

**Entregables**: Backend Django con 7 apps, JWT auth, service layer, ~620 SDK tests.

---

## Sprint 4: Advanced Features (Jan 12-25, 2026)

**Objetivo**: Implementar apps avanzadas y modelos ML sofisticados.

| HU | Título | Dev | Impl Date | Test Date |
|----|--------|-----|-----------|-----------|
| HU-12 | Federated Learning & ML Models | Fernando | Jan 12, 09:00 | Jan 13, 11:00 |
| HU-13 | Data Quality, Explainability, Ensemble | Tipo | Jan 14, 10:30 | Jan 15, 14:00 |
| HU-14 | Blockchain Backend & Secrets | Fernando | Jan 19, 09:00 | Jan 20, 15:30 |
| HU-15 | SDK Advanced Models (NN, RF, GBM) | Tipo | Jan 21, 10:00 | Jan 22, 14:00 |

**Entregables**: 13 Django apps completas, modelos avanzados en SDK, Vault integration.

---

## Sprint 5: Hardening (Jan 26 - Feb 8, 2026)

**Objetivo**: Containerización, CI/CD y security hardening.

| HU | Título | Dev | Impl Date | Test Date |
|----|--------|-----|-----------|-----------|
| HU-16 | Docker & Deployment | Fernando | Jan 26, 09:00 | Jan 27, 10:30 |
| HU-17 | CI/CD Pipelines (GH+GL) | Tipo | Jan 28, 10:00 | Jan 29, 14:00 |
| HU-18 | Security Hardening | Fernando | Feb 3, 09:00 | Feb 4, 11:00 |

**Entregables**: Docker multi-stage, CI green en ambas plataformas, security headers, bug fixes.

---

## Sprint 6: Quality & Documentation (Feb 9-23, 2026)

**Objetivo**: Coverage 95%+, tests E2E y documentación completa.

| HU | Título | Dev | Impl Date | Test Date |
|----|--------|-----|-----------|-----------|
| HU-19 | Test Coverage 95%+ | Tipo/Rukia | Feb 10, 09:00 | Feb 11, 10:00 |
| HU-20 | E2E Tests & Documentation | Fernando | Feb 19, 09:30 | Feb 20, 14:00 |

**Entregables**: 1,442+ Django tests, 95.12% coverage, 5 E2E flows, docs completas, skills architecture.
