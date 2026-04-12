# Intake Form — Discovery Call

> Documento interno. Usar como guion de la primera llamada (30 min) y para calificar.

---

## Bloque 1 — Contexto (5 min)

### 1.1 Sobre la organización

- **Nombre y URL**: ___________________
- **Vertical principal**: Banking / Insurance / Healthcare / Government / Other
- **Tamaño**: empleados / facturación / clientes
- **Geografía operativa**: ___________________

### 1.2 Sobre la persona

- **Nombre y rol**: ___________________
- **Años en la organización**: ___________________
- **Reporta a**: ___________________
- **¿Tiene autoridad de decisión técnica?**: Sí / No / Comparte
- **¿Tiene autoridad de decisión presupuestaria?**: Sí / No / Comparte

---

## Bloque 2 — El problema (10 min)

### 2.1 Contexto del problema

> "Contame qué te trae a esta conversación. ¿Qué problema estás tratando de resolver?"

**Notas**:
___________________

### 2.2 Estado actual

- **¿Tienen un caso de uso de data sharing identificado?**: Sí / No / Exploratorio
- **Si sí, descripción en 1 frase**: ___________________
- **¿Con quiénes querrían compartir datos?**: ___________________
- **¿Por qué hoy no lo hacen?** (regulación / técnico / contractual / desconfianza): ___________________

### 2.3 Intentos previos

- **¿Han evaluado data clean rooms?**: Sí (cuál) / No
- **¿Han evaluado FHE / MPC / DP previamente?**: Sí (cuál) / No
- **¿Compraron alguna solución de privacy ML?**: Sí (cuál, cuándo) / No

> 🚩 **Anti-criterio**: si compraron Duality / TripleBlind / Enveil hace <12 meses, es difícil — no descartar pero ajustar expectativas.

### 2.4 Costo del problema (sin solución)

- **Si no resuelven esto en 12 meses, ¿qué pasa?**: ___________________
- **¿Pueden cuantificarlo?** ($ perdidos, % market share, riesgo regulatorio): ___________________

---

## Bloque 3 — La organización técnica (5 min)

### 3.1 Equipo

- **Tamaño del equipo de data science**: ___________________
- **Tamaño del equipo de ML eng / platform**: ___________________
- **¿Tienen security / cripto interno?**: Sí / No

### 3.2 Stack actual

- **Cloud principal**: AWS / GCP / Azure / On-premise / Hybrid
- **ML stack**: Python (sklearn / TF / PyTorch) / R / Other
- **Data warehouse**: Snowflake / BigQuery / Databricks / Other
- **Producción ML actual**: Sí, en producción / En POC / Solo notebooks

### 3.3 Compliance

- **Frameworks aplicables**: GDPR / HIPAA / PCI-DSS / SOC2 / ISO 27001 / Other
- **¿Han pasado auditoría externa en últimos 12 meses?**: Sí / No
- **¿Tienen DPO / CISO activo en proyectos técnicos?**: Sí / No

---

## Bloque 4 — El proceso de decisión (5 min)

### 4.1 Stakeholders

- **¿Quiénes deben aprobar un pilot de 90 días gratuito?**:
  - Técnico: ___________________
  - Compliance / Legal: ___________________
  - Procurement: ___________________
  - Ejecutivo: ___________________

### 4.2 Timing

- **¿Tienen presupuesto identificado para 2026 en privacy ML?**: Sí (cuánto) / No / TBD
- **¿En qué quarter podrían arrancar un pilot?**: Q2 / Q3 / Q4 2026 / 2027
- **¿Hay deadline regulatorio o de negocio que acelera?**: ___________________

### 4.3 Tiempo del equipo

- **¿Pueden asignar 1 lead técnico + 1 DS al 30-50% durante 90 días?**: Sí / Maybe / No
- **¿El sponsor ejecutivo puede dar 1h/semana?**: Sí / Maybe / No

---

## Bloque 5 — Cierre (5 min)

### 5.1 Próximo paso

- **¿Tienen interés en avanzar a un technical fit assessment (60 min con tu equipo técnico)?**: Sí / No / Necesito más info
- **Si sí, ¿quiénes participarían?**: ___________________
- **Fecha tentativa**: ___________________

### 5.2 Material adicional a enviar

- [ ] PROGRAM_OVERVIEW.md
- [ ] PILOT_SCOPE.md
- [ ] Demo del platform (link)
- [ ] Whitepaper técnico (cuando esté listo)
- [ ] Casos de uso por vertical aplicable
- [ ] Carta de intención de auditoría externa cripto

### 5.3 Notas para CRM

- **Score de calificación** (0-10): ___________________
- **Probabilidad de pilot** (low/med/high): ___________________
- **Próxima fecha de contacto**: ___________________
- **Owner Xcapit**: ___________________

---

## Sistema de scoring rápido

| Pregunta | Valor si "Sí fuerte" | Valor si "Tibio" | Valor si "No" |
|----------|----------------------|------------------|----------------|
| ¿Tiene caso de uso identificado? | 3 | 1 | 0 |
| ¿Sponsor ejecutivo identificado? | 3 | 1 | -2 (descalifica) |
| ¿Equipo DS dedicado mínimo 3? | 2 | 1 | 0 |
| ¿Presupuesto 2026 identificado? | 2 | 1 | 0 |
| ¿Cloud-native? | 1 | 0 | -1 |
| ¿Compliance activo? | 1 | 0 | 0 |
| ¿Pueden arrancar Q2-Q3 2026? | 2 | 1 | 0 |
| ¿Ya evaluaron competidores? | 1 (validación) | 0 | 0 |

**Score interpretación**:
- 12-15: Hot — agendar TFA en 1 semana
- 8-11: Warm — TFA en 2-3 semanas con material adicional
- 4-7: Cold — nurturing por email
- 0-3: Pase

> Cualquier "No" en sponsor ejecutivo o "No" rotundo en presupuesto → descalifica independientemente del score.
