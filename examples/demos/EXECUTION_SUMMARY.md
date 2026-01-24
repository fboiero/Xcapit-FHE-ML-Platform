# Xcapit FHE-ML Platform - Resumen de Ejecucion de Demos

**Fecha de ejecucion**: 2026-01-24

## 1. Fintech: Deteccion de Fraude

### Configuracion
- **Transacciones**: 10,000
- **Tasa de fraude**: 2.55%
- **Bancos participantes**: 3 (Argentina, Chile, Mexico)

### Resultados
| Metrica | Valor |
|---------|-------|
| Accuracy | 99.20% |
| AUC-ROC | 0.9997 |
| Precision (Fraude) | 0.76 |
| Recall (Fraude) | 1.00 |

### Predicciones en Tiempo Real
| TX | Monto | Hora | Distancia | Riesgo | Resultado |
|----|-------|------|-----------|--------|-----------|
| TX-001 | $45.99 | 14h | 2.5km | 0.0% | Legitima |
| TX-002 | $2,500 | 3h | 450km | 100.0% | **FRAUDE** |
| TX-003 | $89.50 | 10h | 0km | 0.0% | Legitima |
| TX-004 | $8,500 | 2h | 800km | 100.0% | **FRAUDE** |
| TX-005 | $12.99 | 18h | 5km | 0.0% | Legitima |
| TX-006 | $3,200 | 23h | 350km | 100.0% | **FRAUDE** |

---

## 2. Healthcare: Prediccion de Diabetes T2

### Configuracion
- **Pacientes**: 5,000
- **Tasa de diabetes**: 15.46%
- **Hospitales participantes**: 3 (Buenos Aires, Mendoza, Cordoba)
- **Cumplimiento**: HIPAA, GDPR, Ley 25.326

### Resultados
| Metrica | Valor |
|---------|-------|
| Accuracy | 99.30% |
| AUC-ROC | 0.9995 |
| Precision (Diabetes) | 0.96 |
| Recall (Diabetes) | 0.99 |

### Feature Importance (Top 5)
1. physical_activity (0.3577)
2. hba1c (0.2915)
3. glucose_fasting (0.1294)
4. cholesterol_hdl (0.0755)
5. bp_systolic (0.0355)

### Evaluacion de Nuevos Pacientes
| ID | Edad | BMI | Glucosa | HbA1c | Riesgo | Nivel |
|----|------|-----|---------|-------|--------|-------|
| PAT-NEW001 | 45 | 24.5 | 95 | 5.4 | 0.1% | Bajo |
| PAT-NEW002 | 62 | 32.1 | 142 | 7.2 | 86.4% | **Muy Alto** |
| PAT-NEW003 | 38 | 22.0 | 88 | 5.0 | 0.0% | Bajo |
| PAT-NEW004 | 55 | 35.5 | 185 | 9.1 | 99.6% | **Muy Alto** |
| PAT-NEW005 | 70 | 28.0 | 110 | 6.0 | 15.0% | Bajo |

---

## 3. Government: Asignacion de Recursos

### Configuracion
- **Ciudadanos**: 20,000
- **Provincias participantes**: 3 (Buenos Aires, Cordoba, Santa Fe)
- **Presupuesto total**: $1,000M
- **Cumplimiento**: Ley 25.326, ISO 27001, NIST

### Resultados
| Metrica | Valor |
|---------|-------|
| R2 Score | 0.9579 (95.8%) |
| MAE | 0.2675 |
| Silhouette (K-Means) | 0.1811 |
| Segmentos identificados | 5 |

### Segmentacion de Poblacion
| Segmento | Nombre | Tamano | Vulnerabilidad | Asistencia |
|----------|--------|--------|----------------|------------|
| 0 | Familias vulnerables | 13.7% | 0.318 | 12.3% |
| 1 | Jovenes estudiantes | 18.3% | 0.320 | 20.0% |
| 2 | Adultos mayores | 32.8% | 0.250 | 3.7% |
| 3 | Clase media trabajadora | 20.1% | 0.546 | 48.1% |
| 4 | Hogares estables | 15.1% | 0.278 | 7.5% |

### Asignacion de Recursos por Provincia
| Provincia | Presupuesto | Necesidad | Cobertura | Salud | Educacion | Social | Vivienda |
|-----------|-------------|-----------|-----------|-------|-----------|--------|----------|
| Buenos Aires | $500M | $29.3M | 100% | 17.3% | 47.8% | 12.0% | 22.9% |
| Cordoba | $250M | $14.6M | 100% | 17.5% | 47.5% | 11.7% | 23.2% |
| Santa Fe | $250M | $14.2M | 100% | 17.8% | 45.2% | 12.0% | 25.0% |

---

## Garantias de Privacidad (Todos los Demos)

- Datos NUNCA compartidos en plaintext
- Encriptacion FHE con CKKS (128-bit)
- Votacion commit-reveal para gobernanza
- Solo estadisticas agregadas compartidas
- Audit trail inmutable en Arbitrum blockchain
- Cumplimiento normativo (HIPAA, GDPR, Ley 25.326)

## Smart Contracts Desplegados (Arbitrum Sepolia)

| Contrato | Direccion |
|----------|-----------|
| Governance | 0xda52326d106A91A1F22A0c41Be2dc1F531C01F11 |
| Model Registry | 0x1296cCeF7803Bff51FB690afCFc586E7012417b8 |
| Computation Verifier | 0xa5f04E0aefe55173C91b949Aa2385f0228dd2921 |

**Explorer**: https://sepolia.arbiscan.io
