# Guiones para Videos Demo - Xcapit Privacy Platform

Este documento contiene los guiones detallados para grabar los videos demo de las funcionalidades de TIER 3 y TIER 4.

## Instrucciones Generales

1. **Iniciar el Dashboard:**
   ```bash
   cd dashboard && npm run dev
   ```
   El dashboard estara disponible en `http://localhost:5173`

2. **URLs de Demo (no requieren login):**
   - TIER 3: `/demo-compliance`, `/demo-quality`, `/demo-marketplace`, `/demo-sandbox`
   - TIER 4: `/demo-federated`, `/demo-explainability`, `/demo-competitive`, `/demo-ensemble`

3. **Resolucion recomendada:** 1920x1080 o 1280x720
4. **Duracion por video:** 60-90 segundos

---

## TIER 3: Enterprise Features

### Video 1: Compliance Dashboard
**URL:** `http://localhost:5173/demo-compliance`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar dashboard con el titulo "Compliance Dashboard"
   - Destacar las 4 cards de frameworks: GDPR, HIPAA, SOC2, PCI-DSS

2. **Metricas principales (10s)**
   - Mostrar el Compliance Score general (85%)
   - Destacar los badges de estado de cada framework
   - Senalar "Last Assessment" timestamp

3. **Detalle GDPR (15s)**
   - Click en la card GDPR para expandir
   - Mostrar los controles verificados:
     - Data encryption at rest
     - Consent management
     - Right to erasure
     - Data portability
   - Mostrar issues detectados y recomendaciones

4. **Verificacion en tiempo real (15s)**
   - Click en "Run Compliance Check"
   - Mostrar animacion de verificacion
   - Ver actualizacion del score
   - Destacar el log de auditoria generado

5. **Reportes (10s)**
   - Click en "Generate Report"
   - Mostrar preview del PDF exportable
   - Mencionar que es auditable por reguladores

6. **Cierre (5s)**
   - Volver a vista general
   - Mostrar todos los frameworks en verde/amarillo

**Puntos clave a mencionar:**
- Verificacion automatica sin acceso a datos reales
- Cumple GDPR, HIPAA, SOC2, PCI-DSS
- Reportes auditables para reguladores
- Actualizaciones en tiempo real

---

### Video 2: Data Quality Score
**URL:** `http://localhost:5173/demo-quality`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Data Quality Score" dashboard
   - Destacar score general (87/100)

2. **Dimensiones de calidad (15s)**
   - Mostrar las 5 dimensiones:
     - Completeness (92%)
     - Consistency (88%)
     - Accuracy (85%)
     - Timeliness (90%)
     - Uniqueness (95%)
   - Explicar que cada una se calcula sin ver datos

3. **Analisis por columna (15s)**
   - Expandir vista de columnas
   - Mostrar metricas por campo:
     - Null percentage
     - Distinct values
     - Distribution stats
   - Todo calculado sobre datos encriptados

4. **Alertas y recomendaciones (15s)**
   - Mostrar panel de alertas
   - Ver issues detectados automaticamente
   - Mostrar recomendaciones de mejora
   - Explicar impacto en modelo ML

5. **Historico (10s)**
   - Mostrar grafico de tendencia
   - Ver mejora/degradacion en el tiempo
   - Comparar con baseline

6. **Cierre (5s)**
   - Destacar que todo es privacy-preserving
   - Mostrar badge "FHE Verified"

**Puntos clave a mencionar:**
- Metricas calculadas sobre datos encriptados
- Sin acceso al contenido real
- Identifica problemas antes del training
- Mejora la calidad del modelo final

---

### Video 3: Model Marketplace
**URL:** `http://localhost:5173/demo-marketplace`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Model Marketplace"
   - Vista de cards de modelos disponibles

2. **Categorias por industria (10s)**
   - Mostrar filtros: Finance, Healthcare, Retail
   - Destacar modelos pre-entrenados:
     - Fraud Detection
     - Credit Scoring
     - Medical Diagnosis
     - Customer Churn

3. **Detalle de modelo (20s)**
   - Click en "Fraud Detection Model"
   - Mostrar metricas:
     - Accuracy: 94%
     - F1 Score: 0.91
     - Training samples: 1M+
   - Ver description y use cases
   - Mostrar reviews y rating (4.5 estrellas)

4. **Deploy a consorcio (15s)**
   - Click en "Deploy to Consortium"
   - Seleccionar consorcio destino
   - Ver configuracion de parametros
   - Mostrar confirmacion de deploy

5. **Modelos propios (10s)**
   - Click en "My Models"
   - Ver modelos publicados
   - Mostrar estadisticas de uso
   - Ver revenue generado

6. **Cierre (5s)**
   - Volver a marketplace
   - Destacar "Enterprise Ready" badge

**Puntos clave a mencionar:**
- Modelos pre-entrenados por industria
- Deploy en un click
- Monetizacion para creadores
- Privacy-preserving desde el dia 1

---

### Video 4: Sandbox Mode
**URL:** `http://localhost:5173/demo-sandbox`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Sandbox Mode"
   - Destacar "Safe Testing Environment"

2. **Crear sandbox (15s)**
   - Click en "Create Sandbox"
   - Seleccionar template: Finance, Healthcare, Retail
   - Ver configuracion:
     - Dataset size
     - Complexity level
     - Features to include
   - Click "Generate"

3. **Datos sinteticos (15s)**
   - Mostrar preview de datos generados
   - Destacar que son estadisticamente similares
   - Pero completamente sinteticos
   - Sin PII real

4. **Experimentos (20s)**
   - Ir a "Experiments"
   - Crear nuevo experimento
   - Seleccionar algoritmo (Linear Regression)
   - Configurar parametros
   - Run experiment
   - Ver resultados y metricas

5. **Comparar experimentos (10s)**
   - Mostrar tabla comparativa
   - Ver diferentes configuraciones
   - Identificar mejor approach
   - "Promote to Production"

6. **Cierre (5s)**
   - Mostrar resumen
   - Destacar "Zero Risk Testing"

**Puntos clave a mencionar:**
- Ambiente seguro de pruebas
- Datos sinteticos realistas
- Experimentacion sin riesgo
- Onboarding rapido de clientes

---

## TIER 4: Diferenciadores

### Video 5: Federated Inference
**URL:** `http://localhost:5173/demo-federated`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Federated Inference"
   - Destacar "Predictions Without Data Movement"

2. **Arquitectura (15s)**
   - Mostrar diagrama de edge nodes
   - Explicar que datos nunca salen de la empresa
   - Modelo viaja a los datos, no al reves
   - Destacar conexiones encriptadas

3. **Crear endpoint (15s)**
   - Click en "Create Inference Endpoint"
   - Seleccionar modelo base
   - Configurar:
     - Batch size
     - Latency requirements
     - Edge nodes
   - Deploy endpoint

4. **Hacer prediccion (15s)**
   - Input sample data
   - Click "Predict"
   - Mostrar resultado encriptado
   - Explicar que solo el owner puede desencriptar

5. **Monitoreo (10s)**
   - Ver dashboard de metricas
   - Latency, throughput, errors
   - Mostrar edge node status
   - Health checks

6. **Cierre (5s)**
   - Destacar "Data Never Leaves"
   - Mostrar compliance badges

**Puntos clave a mencionar:**
- Predicciones sin mover datos
- Modelo distribuido en edge
- Maxima privacidad
- Baja latencia

---

### Video 6: Model Explainability
**URL:** `http://localhost:5173/demo-explainability`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Model Explainability"
   - "Understand AI Decisions Privately"

2. **Overview (10s)**
   - Mostrar stats generales
   - Explicaciones generadas
   - Tipos disponibles
   - Privacy level

3. **Feature Importance (15s)**
   - Ir a tab "Feature Importance"
   - Mostrar grafico de barras
   - Destacar features mas relevantes
   - Explicar que se calcula sin ver datos originales

4. **Explicaciones individuales (20s)**
   - Ir a "Explanations"
   - Seleccionar una prediccion
   - Ver diferentes tipos:
     - SHAP values
     - Decision path
     - Counterfactual
   - Cada una privacy-preserving

5. **Model Insights (10s)**
   - Ir a "Insights"
   - Ver patrones detectados
   - Bias analysis
   - Fairness metrics

6. **Cierre (5s)**
   - Destacar "Explainable + Private"
   - Mostrar compliance badges

**Puntos clave a mencionar:**
- Explicaciones sin revelar training data
- Multiples tipos de explicacion
- Cumple requisitos regulatorios
- Deteccion de bias

---

### Video 7: Competitive Insights
**URL:** `http://localhost:5173/demo-competitive`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Competitive Insights"
   - "Anonymous Industry Benchmarks"

2. **Seleccionar industria (10s)**
   - Mostrar selector: Finance, Healthcare, Retail
   - Seleccionar "Finance"
   - Ver benchmarks disponibles

3. **Benchmarks (15s)**
   - Mostrar tabla de metricas:
     - Fraud detection rate
     - False positive rate
     - Processing time
   - Ver percentiles (25th, 50th, 75th, 90th)
   - Todo anonimizado

4. **Comparacion (20s)**
   - Click "Compare My Metrics"
   - Input valores propios
   - Ver posicion vs industria
   - Graficos de comparacion
   - Identificar areas de mejora

5. **Tendencias (10s)**
   - Ir a "Industry Trends"
   - Ver evolucion temporal
   - Predicciones futuras
   - Oportunidades detectadas

6. **Cierre (5s)**
   - Destacar "100% Anonymous"
   - Mostrar privacy guarantee

**Puntos clave a mencionar:**
- Benchmarks anonimos reales
- Saber posicion competitiva
- Sin revelar datos propios
- Identificar oportunidades

---

### Video 8: Multi-Model Ensemble
**URL:** `http://localhost:5173/demo-ensemble`
**Duracion:** 60-90 segundos

**Guion:**

1. **Apertura (5s)**
   - Mostrar "Multi-Model Ensemble"
   - "Combine Models for Better Predictions"

2. **Crear ensemble (15s)**
   - Click "Create Ensemble"
   - Nombrar: "Fraud Detection Ensemble"
   - Seleccionar tipo:
     - Voting
     - Averaging
     - Weighted
     - Stacking
   - Explicar diferencias brevemente

3. **Agregar modelos (15s)**
   - Click "Add Model"
   - Seleccionar modelos de diferentes consorcios
   - Asignar pesos
   - Ver preview de configuracion

4. **Activar y predecir (15s)**
   - Click "Activate Ensemble"
   - Ir a "Predict"
   - Input sample data
   - Ver prediccion combinada
   - Comparar con modelos individuales

5. **Performance (10s)**
   - Ver metricas del ensemble
   - Comparar accuracy vs individuales
   - Ver contribution de cada modelo
   - Ajustar pesos si necesario

6. **Cierre (5s)**
   - Destacar "Better Together"
   - Mostrar improvement percentage

**Puntos clave a mencionar:**
- Combinar conocimiento de multiples consorcios
- Mejor accuracy que modelos individuales
- Multiples estrategias de combinacion
- Colaboracion sin compartir datos

---

## Comandos Utiles

### Iniciar el ambiente completo
```bash
# Terminal 1: Backend
cd /Users/fboiero/Documents/GitHub/Xcapit-FHE-ML-Platform
source .venv/bin/activate
python -m sdk.api.server

# Terminal 2: Frontend
cd /Users/fboiero/Documents/GitHub/Xcapit-FHE-ML-Platform/dashboard
npm run dev
```

### Grabar pantalla (macOS)
```bash
# Usando QuickTime Player
# 1. Abrir QuickTime Player
# 2. File -> New Screen Recording
# 3. Seleccionar area
# 4. Grabar
```

### Exportar a GIF (opcional)
```bash
ffmpeg -i video.mp4 -vf "fps=10,scale=800:-1" output.gif
```

---

## Notas Finales

- Todos los demos funcionan con datos mock/simulados
- No se requiere backend activo para demos basicos
- Las URLs /demo-* no requieren autenticacion
- Ideal para presentaciones y pitch decks
