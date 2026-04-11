# Xcapit FHE-ML Platform — Centro de Documentacion

**Version**: 1.0.0-rc1 | **Ultima actualizacion**: Marzo 2026

---

## Documentacion Principal

| Documento | Descripcion |
|-----------|-------------|
| [Manual de Usuario](USER_MANUAL.md) | Manual completo para usuarios de la plataforma |
| [Release Notes RC1](RELEASE_NOTES_RC1.md) | Notas de version del Release Candidate 1 |
| [Arquitectura Tecnica](TECHNICAL_ARCHITECTURE.md) | Descripcion de la arquitectura del sistema |
| [Referencia API](API_REFERENCE.md) | Documentacion de endpoints REST |
| [OpenAPI Spec](openapi.yaml) | Especificacion OpenAPI 3.0 |
| [Auditoria de Seguridad](SECURITY_AUDIT_REPORT.md) | Reporte de auditoria de seguridad |
| [Guia de Implementacion](IMPLEMENTATION_GUIDE.md) | Patrones de implementacion |
| [Walkthrough de la Plataforma](PLATFORM_WALKTHROUGH.md) | Tour completo de la plataforma |

## Inicio Rapido

| Documento | Descripcion |
|-----------|-------------|
| [Getting Started](getting-started.md) | Guia de inicio rapido |
| [Onboarding Paso a Paso](ONBOARDING_PASO_A_PASO.md) | Tutorial de onboarding |
| [Glosario](glossary.md) | Terminos y definiciones |

## Teoria FHE

| Capitulo | Tema |
|----------|------|
| [01 — Cifrado Homomorfico](theory/01-homomorphic-encryption.md) | Fundamentos de FHE |
| [02 — Esquema CKKS](theory/02-ckks-scheme.md) | Detalles matematicos de CKKS |
| [03 — ML sobre Datos Cifrados](theory/03-ml-on-encrypted-data.md) | Modelos ML con FHE |
| [04 — Aproximaciones Polinomiales](theory/04-polynomial-approximations.md) | Tecnicas polinomiales para FHE |

## Guias de Arquitectura

| Guia | Tema |
|------|------|
| [01 — Arquitectura General](guides/01-architecture.md) | Vision general del sistema |
| [02 — Capa de Cifrado](guides/02-encryption-layer.md) | Detalles de la capa FHE |
| [03 — Modelos ML](guides/03-ml-models.md) | Documentacion de modelos |
| [04 — Integracion Blockchain](guides/04-blockchain-integration.md) | Smart contracts y Arbitrum |
| [05 — Inicio Rapido](guides/05-quickstart.md) | Tutorial paso a paso |

## SDK

| Documento | Descripcion |
|-----------|-------------|
| [Arquitectura SDK](sdk/ARCHITECTURE.md) | Arquitectura interna del SDK |
| [Troubleshooting](sdk/TROUBLESHOOTING.md) | Problemas comunes y soluciones |
| [Tutoriales](sdk/TUTORIALS.md) | Tutoriales del SDK |

## Cumplimiento y Seguridad

| Documento | Descripcion |
|-----------|-------------|
| [ISO 27001](compliance/ISO27001_2022_SaaS_Compliance.md) | Documentacion ISO 27001 |
| [Auditoria de Seguridad API](API_SECURITY_AUDIT.md) | Auditoria de seguridad de la API |
| [Smart Contract Audit](SMART_CONTRACT_AUDIT.md) | Auditoria de smart contracts |
| [Security Reviews](security-reviews/) | Reportes de revision de seguridad |

## Architecture Decision Records (ADR)

| ADR | Decision |
|-----|----------|
| [001 — JSONField](adr/001-jsonfield-usage.md) | Uso de JSONField en modelos |
| [002 — Service Layer](adr/002-service-layer-pattern.md) | Patron de capa de servicio |
| [003 — Blockchain Resilience](adr/003-blockchain-resilience.md) | Estrategia de resiliencia blockchain |
| [004 — Observability](adr/004-observability-stack.md) | Stack de monitoreo y logging |

## Trazabilidad

| Documento | Descripcion |
|-----------|-------------|
| [Requisitos](traceability/REQUIREMENTS.md) | Requisitos funcionales y no funcionales |
| [User Stories](traceability/USER_STORIES.md) | Historias de usuario |
| [Matriz de Trazabilidad](traceability/TRACEABILITY_MATRIX.csv) | Trazabilidad requisitos → tests |
| [Evidencia de Tests](traceability/TEST_EVIDENCE.md) | Evidencia de pruebas |
| [Plan de Sprint](traceability/SPRINT_PLAN.md) | Planificacion de sprints |

## Operaciones y Deployment

| Documento | Descripcion |
|-----------|-------------|
| [Deployment](DEPLOYMENT.md) | Procedimientos de despliegue |
| [Runbook de Operaciones](OPERATIONS_RUNBOOK.md) | Procedimientos operativos |
| [Production Readiness](PRODUCTION_READINESS_PLAN.md) | Checklist de produccion |
| [Release Checklist](RELEASE_CHECKLIST.md) | Procedimientos de release |

## Recursos

| Recurso | Descripcion |
|---------|-------------|
| [Diagramas](diagrams/) | 21 diagramas SVG de arquitectura |
| [Evidencia](evidence/) | Reportes de evidencia y demos |
| [Demos](demos/) | Demos interactivas y video comercial |
| [Ejemplos](../examples/) | 7 Jupyter notebooks |
| [Soporte FHE](FHE_SUPPORT_MATRIX.md) | Matriz de soporte de modelos FHE |
| [Schemas](MODEL_SCHEMAS.md) | Schemas de datos |
| [Roadmap](../PLATFORM_ROADMAP.md) | Hoja de ruta del proyecto |
| [Casos de Uso](USE_CASES.md) | Documentacion de casos de uso |

## Audiencia

Esta documentacion esta disenada para:

- **Usuarios de la plataforma** — [Manual de Usuario](USER_MANUAL.md)
- **Desarrolladores** — [Guia de Implementacion](IMPLEMENTATION_GUIDE.md), [SDK Docs](sdk/)
- **Cientificos de datos** — [Modelos ML](guides/03-ml-models.md), [Teoria FHE](theory/)
- **Oficiales de cumplimiento** — [ISO 27001](compliance/), [Auditoria](SECURITY_AUDIT_REPORT.md)
- **DevOps** — [Deployment](DEPLOYMENT.md), [Runbook](OPERATIONS_RUNBOOK.md)
- **Blockchain developers** — [Blockchain Guide](guides/04-blockchain-integration.md), [Contract Audit](SMART_CONTRACT_AUDIT.md)

---

*Xcapit FHE-ML Platform v1.0.0-rc1 — [Xcapit](https://xcapit.com) / [QuarkID](https://quarkid.org)*
