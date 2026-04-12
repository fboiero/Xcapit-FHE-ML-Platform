# Success Metrics — Design Partner Pilot

> Cómo medimos si un pilot de 90 días fue exitoso. Aplica para Xcapit y para el partner.

---

## Filosofía de medición

**Si no se puede medir, no se hace.**

Antes de arrancar el pilot, las dos partes firman las métricas en el `PILOT_AGREEMENT`. Sin métricas firmadas, no hay pilot.

Las métricas se agrupan en **3 capas**:

1. **Producto** — ¿la plataforma resuelve el problema técnico?
2. **Negocio** — ¿hay ROI para el partner?
3. **Relación** — ¿la relación de trabajo funciona y escala?

---

## Capa 1 — Métricas de producto

### Performance técnica

| Métrica | Threshold mínimo | Threshold ideal |
|---------|------------------|------------------|
| Modelo accuracy / F1 / AUC vs baseline | Igual o mejor | +10% relativo |
| Latencia de predicción (p95) con FHE | < 2s | < 500ms |
| Throughput (predicciones/segundo) | > 100 / nodo | > 1,000 / nodo |
| Uptime durante el pilot | 99.0% | 99.9% |
| Errores críticos en producción | 0 | 0 |

### Cobertura funcional

| Métrica | Threshold mínimo | Threshold ideal |
|---------|------------------|------------------|
| % de funcionalidad requerida implementada | 80% | 100% |
| Custom integrations completadas | Las críticas | Todas las planteadas |
| Documentación de implementación entregada | Sí | Sí, con runbook operacional |

### Seguridad y compliance

| Métrica | Threshold mínimo | Threshold ideal |
|---------|------------------|------------------|
| Hallazgos críticos de seguridad | 0 | 0 |
| Hallazgos altos de seguridad | < 3 | 0 |
| Compliance audit del pilot (si aplica) | Pasa | Pasa con observaciones menores |
| Crypto audit external referenciable | Disponible | Auditoría completada y publicada |

---

## Capa 2 — Métricas de negocio (las que paga el sponsor ejecutivo)

### Para Banking — Fraud Detection

| Métrica | Cómo medir | Threshold mínimo | Threshold ideal |
|---------|------------|------------------|------------------|
| Fraud detection rate (recall) | A/B test contra modelo actual durante 30 días | +15% relativo | +30% |
| False positive rate | Mismo A/B | -10% relativo | -25% |
| $ recuperados (incremental) | Track de casos detectados solo por consorcio | $X / mes | $X * 3 / mes |
| Tiempo de detección | Median time-to-flag | -20% relativo | -50% |

### Para Healthcare

| Métrica | Cómo medir | Threshold mínimo | Threshold ideal |
|---------|------------|------------------|------------------|
| Modelo accuracy vs single-site | Validación clínica blind | +5% absoluto | +15% absoluto |
| Time-to-diagnosis | Median time | -15% relativo | -40% relativo |
| Cantidad de hospitales en consorcio | Conteo | 2 | ≥ 4 |
| Compliance findings (HIPAA audit) | Audit externa | 0 críticos | 0 totales |

### Para Insurance

| Métrica | Cómo medir | Threshold mínimo | Threshold ideal |
|---------|------------|------------------|------------------|
| Claims fraud cross-aseguradora detectados | Conteo de matches con investigación validada | > 10 / mes | > 100 / mes |
| $ evitados | Sum de claims no pagados validados | $X / mes | $X * 5 / mes |
| Reducción de tiempo de investigación | Median investigation time | -25% relativo | -60% |

### Métricas universales de negocio

| Métrica | Cómo medir |
|---------|------------|
| **ROI proyectado año 1** | $ evitados o ganados / $ invertidos |
| **Payback period** | Meses para recuperar inversión |
| **NPS interno del equipo del partner** | Survey al equipo técnico (escala 0-10) |
| **NPS del sponsor ejecutivo** | Survey directo al sponsor |

---

## Capa 3 — Métricas de relación

### Salud de la relación operativa

| Métrica | Cómo medir | Threshold mínimo | Threshold ideal |
|---------|------------|------------------|------------------|
| Reuniones semanales con asistencia completa | % de syncs sin no-shows | > 80% | 100% |
| Response time en Slack (lado Xcapit) | Median response time | < 4h hábiles | < 1h hábiles |
| Bloqueadores resueltos en < 48h | % | > 70% | > 90% |
| Tickets de soporte / bugs encontrados | Conteo + tiempo de resolución | 100% resueltos | < 24h resolution |

### Disposición a continuar

| Pregunta del survey final | Threshold mínimo | Threshold ideal |
|---------------------------|------------------|------------------|
| ¿Recomendarías Xcapit a un par de tu industria? (NPS) | > 7 | > 9 |
| ¿Continuarías como cliente pago? | "Probable" | "Sí, definitivamente" |
| ¿Aceptarías ser case study público con tu nombre? | "Discutible" | "Sí" |
| ¿Aceptarías hacer una intro warm a 3 pares? | "Maybe" | "Sí, ya tengo nombres" |

---

## Outcome final del pilot

Al **Día 90**, evaluamos las 3 capas:

| Resultado de las 3 capas | Decisión |
|--------------------------|----------|
| ✅ Producto + ✅ Negocio + ✅ Relación | **Conversión a cliente pago** — firma contrato anual con pricing privilegiado |
| ✅ Producto + ✅ Negocio + ⚠️ Relación | Conversión + ajuste de delivery model |
| ✅ Producto + ⚠️ Negocio | Extender pilot 60 días con scope ajustado para validar ROI |
| ⚠️ Producto + ✅ Negocio | Roadmap conjunto + extensión 60 días para cerrar gaps técnicos |
| ❌ Producto / ❌ Negocio | Cierre limpio con retrospectiva + documentar learnings |

---

## Cosas que NO medimos (y está bien que no las midamos)

- ❌ Cantidad de líneas de código integradas
- ❌ Cantidad de features usadas (vanity metric)
- ❌ Tiempo total que pasaron en la plataforma
- ❌ Activity en el dashboard (logins, clicks)
- ❌ Cantidad de modelos entrenados

**Por qué no**: estas métricas miden esfuerzo, no valor. Un partner que usó 1 sola feature pero recuperó $10M es un éxito rotundo. Uno que usó 50 features sin valor concreto es un fracaso.

---

## Reporte de cierre del pilot

**Día 90**: documento entregable de ~10 páginas con:

1. Resumen ejecutivo (1 página)
2. Métricas conseguidas vs targets firmados (2 páginas)
3. Casos concretos resueltos (2 páginas con datos reales o anonimizados)
4. Lo que faltó / gaps identificados (1 página — honesto)
5. Roadmap conjunto post-pilot (2 páginas)
6. Recomendación: continuar / extender / cerrar (1 página)
7. Anexos técnicos (sin límite)

Este reporte:
- Lo firma el sponsor ejecutivo del partner + founder de Xcapit
- Se vuelve la base del case study público (con o sin nombre del partner)
- Se vuelve input para el roadmap del producto
