# Pilot Scope — 90 Days

> Documento contractual base. Se adapta caso por caso pero los pilares no se negocian.

---

## Objetivo del pilot

**Validar que la plataforma resuelve un problema real, medible, y reproducible** en producción del partner — no un POC sintético.

Al final de los 90 días, ambas partes deben poder responder con datos:

1. ¿La plataforma resolvió el problema definido?
2. ¿El ROI proyectado se sostiene?
3. ¿Estamos listos para producción / escala?

---

## Estructura de fases (90 días)

### Fase 1 — Discovery & Setup (Días 1-15)

**Objetivo**: alinear equipos, definir scope técnico, levantar entorno.

- **Día 1**: Kick-off (4h workshop con ambos equipos)
- **Días 2-5**: Discovery técnico (entrevistas con stakeholders, revisión de datos disponibles, modelos actuales)
- **Días 6-10**: Setup de entorno (cuenta enterprise activada, accesos, deploy del SDK)
- **Días 11-15**: Definición final de success metrics + plan de pilot firmado

**Deliverables del partner**:
- Acceso a un dataset representativo (puede estar anonimizado)
- 1 lead técnico (~50% dedicación esta fase) + 1 data scientist (~30%)
- Sponsor ejecutivo con poder de decisión

**Deliverables de Xcapit**:
- Solutions engineer asignado (~50%)
- Cuenta enterprise + acceso a todos los tiers
- Documentación de arquitectura adaptada al caso de uso

---

### Fase 2 — Build & Iterate (Días 16-60)

**Objetivo**: implementar el caso de uso end-to-end, iterar sobre métricas.

- **Días 16-30**: Implementación inicial (modelo + integración con datos del partner)
- **Días 31-45**: Primera evaluación contra success metrics
- **Días 46-60**: Iteración (ajustes, optimización, agregar features)

**Cadencia**:
- Sync semanal técnico (1h, miércoles)
- Sync bi-semanal ejecutivo (30min, viernes alternados)
- Slack compartido para preguntas asincrónicas (response < 4h hábiles)

**Hitos medibles**:
- Día 30: primera predicción end-to-end con datos cifrados
- Día 45: comparación contra baseline existente
- Día 60: decisión go/no-go preliminar

---

### Fase 3 — Validate & Decide (Días 61-90)

**Objetivo**: validar en condiciones realistas, medir contra success metrics, decidir continuidad.

- **Días 61-75**: Pruebas a escala (volumen real de producción, latencia, costo)
- **Días 76-85**: Documentación de resultados (case study draft, technical report)
- **Días 86-90**: Reunión de cierre + decisión formal

**Decisión final** (Day 90 meeting):

| Outcome | Acciones |
|---------|----------|
| ✅ **Conversión a cliente** | Firma contrato anual, pricing privilegiado de Founding Partner, roadmap conjunto |
| ⏸️ **Extender pilot** | +60 días con scope ajustado (máximo una vez) |
| ❌ **No conversión** | Documentar learnings, liberar accesos, mantener relación para futuro |

---

## Success metrics — template

> A definir caso por caso en Fase 1. Estos son ejemplos típicos.

### Para Banking — Fraud Detection

| Métrica | Baseline actual | Target del pilot |
|---------|-----------------|------------------|
| Fraud detection rate (recall) | 65% | ≥ 78% (+20% relativo) |
| False positive rate | 8% | ≤ 5% |
| Latencia de scoring (p95) | 200ms | ≤ 500ms (con FHE overhead aceptable) |
| Casos detectados solo por consorcio (incrementales) | 0 | > 50/mes |

### Para Healthcare — Diagnóstico cross-hospital

| Métrica | Baseline actual | Target del pilot |
|---------|-----------------|------------------|
| Modelo accuracy (vs single-site) | X% | +10% absoluto |
| Time-to-diagnosis | Y horas | -30% relativo |
| Hospitales participantes | 1 | ≥ 3 |
| Compliance audit findings | N/A | 0 hallazgos críticos |

### Para Insurance — Claims fraud

| Métrica | Baseline actual | Target del pilot |
|---------|-----------------|------------------|
| Detección de claims duplicados (cross-aseguradora) | Manual | Automatizado, > 95% precisión |
| Costo evitado | $X anual | $X * 1.5 anual |
| Aseguradoras integradas | 1 | ≥ 3 |

---

## Lo que NO está incluido en el pilot

Para evitar scope creep, dejar explícito:

- ❌ Migración de modelos legacy del partner (eso es proyecto de implementación, fuera del pilot)
- ❌ Custom development que no esté en el roadmap (priorizable post-pilot)
- ❌ SLA de producción con uptime garantizado (eso es contrato post-pilot)
- ❌ Integración con sistemas internos no-cloud (fase 2 si aplica)
- ❌ Reentrenamiento continuo automatizado (fase 2)

---

## Pricing del pilot

**Default**: GRATIS durante los 90 días para los primeros 5 Design Partners.

**Por qué gratis**: el valor para Xcapit (caso de éxito documentable + roadmap input + warm intros futuras) excede el revenue del pilot.

**Excepciones que evaluamos cobrar**:
- Custom development fuera del roadmap (~$15-30K USD)
- Integraciones específicas con sistemas legacy (~$20-50K USD)
- Soporte 24x7 durante el pilot (~$5K USD/mes)

**Contrato post-pilot** (si convierte):
- Año 1: 50% off del pricing público
- Año 2: 25% off
- Año 3: lock-in del precio inicial sin aumentos
- A partir del año 4: pricing standard con opción de renovación

---

## Términos legales mínimos

Documento separado: `PILOT_AGREEMENT_TEMPLATE.md` (a redactar con asesoría legal).

Puntos no negociables:
- IP de la plataforma queda con Xcapit (open source no implica work-for-hire)
- IP del modelo entrenado puede ser conjunta o del partner (a definir)
- Datos del partner NUNCA se exportan ni almacenan en infraestructura de Xcapit (cifrados o no)
- Auditoría externa cripto disponible para inspección del partner (NDA si necesario)
- Salida limpia: Día 91, todos los accesos revocables sin retención de datos

---

## Roles y responsabilidades

| Rol | Lado partner | Lado Xcapit | Compromiso |
|-----|--------------|-------------|------------|
| **Sponsor ejecutivo** | C-level / VP | Founder / C-level | 1h / semana |
| **Lead técnico** | Senior engineer | Solutions engineer | 50% durante Fase 1, 30% Fases 2-3 |
| **Data scientist** | Senior DS | ML engineer | 30% durante todo el pilot |
| **Compliance / Legal** | CISO / DPO | Compliance officer | On-demand, ~5h total |
| **Project manager** | Optional | Customer success | Sync semanal |

**Total esfuerzo estimado por lado**: ~1.5 FTE durante 90 días.
