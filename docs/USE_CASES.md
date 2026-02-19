# Xcapit FHE-ML Platform - Casos de Uso

## Resumen Ejecutivo

La plataforma Xcapit FHE-ML permite a múltiples organizaciones colaborar en Machine Learning **sin compartir datos sensibles**. Utiliza:

- **FHE (Fully Homomorphic Encryption)**: Procesar datos cifrados sin descifrarlos
- **Blockchain (Arbitrum)**: Gobernanza transparente y auditoría inmutable
- **Commit-Reveal Voting**: Votación privada que previene front-running

---

## Caso 1: Detección de Fraude Bancario (Consorcio LatAm)

### El Problema

Tres bancos en Latinoamérica quieren detectar fraude:
- 🇦🇷 **Bank Alpha (Argentina)**: 400 transacciones/día
- 🇨🇱 **Bank Beta (Chile)**: 300 transacciones/día
- 🇲🇽 **Bank Gamma (Mexico)**: 300 transacciones/día

**Desafíos:**
- Regulaciones locales prohíben compartir datos de clientes
- Cada banco tiene pocos casos de fraude para entrenar un modelo robusto
- Los defraudadores operan cross-border

### La Solución

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSORCIO DE FRAUDE LATAM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Bank Alpha          Bank Beta           Bank Gamma            │
│   (Argentina)         (Chile)             (Mexico)              │
│        │                  │                   │                  │
│        ▼                  ▼                   ▼                  │
│   ┌─────────┐        ┌─────────┐        ┌─────────┐            │
│   │ Encrypt │        │ Encrypt │        │ Encrypt │            │
│   │  (FHE)  │        │  (FHE)  │        │  (FHE)  │            │
│   └────┬────┘        └────┬────┘        └────┬────┘            │
│        │                  │                   │                  │
│        └──────────────────┼───────────────────┘                  │
│                           ▼                                      │
│                  ┌─────────────────┐                            │
│                  │  Encrypted Pool │                            │
│                  │   (Ciphertext)  │                            │
│                  └────────┬────────┘                            │
│                           │                                      │
│                           ▼                                      │
│                  ┌─────────────────┐                            │
│                  │  Train Model    │                            │
│                  │ (on ciphertext) │                            │
│                  └────────┬────────┘                            │
│                           │                                      │
│                           ▼                                      │
│                  ┌─────────────────┐                            │
│                  │  Shared Model   │◄── Solo parámetros,        │
│                  │   (weights)     │    no datos                │
│                  └─────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo Detallado

#### Paso 1: Cada banco cifra sus datos localmente

```python
# Bank Alpha (Argentina)
from sdk.utils.data_loader import SecureDataLoader

loader = SecureDataLoader(encryption_scheme="CKKS")

# Datos ANTES de cifrar (NUNCA salen del banco)
plaintext_data = {
    "amount": 523.45,
    "hour": 14,
    "distance_km": 25.3,
    "is_online": False
}

# Datos DESPUÉS de cifrar (esto sí se comparte)
ciphertext = loader.encrypt(plaintext_data)
# Output: [0x7a3f8c2d...4096 coefficients]
```

#### Paso 2: Votación para iniciar entrenamiento

```python
# Cada banco vota (commit-reveal)

# FASE COMMIT: Voto oculto
commitment = hash(proposal_id + vote + salt)
# Bank Alpha: 0x5f93bee2... (voto: ???)
# Bank Beta:  0x891ba778... (voto: ???)
# Bank Gamma: 0x30093675... (voto: ???)

# FASE REVEAL: Votos verificados
# Bank Alpha: YES ✓ Verified
# Bank Beta:  YES ✓ Verified
# Bank Gamma: YES ✓ Verified

# Resultado: 3/3 = 100% > 51% quorum → APROBADO
```

#### Paso 3: Entrenamiento sobre datos cifrados

```python
# El modelo se entrena sobre ciphertext
model.fit(encrypted_X_train, encrypted_y_train)

# Operaciones matemáticas sobre datos cifrados:
# - Multiplicación de matrices
# - Sumas ponderadas
# - Funciones de activación aproximadas

# Resultado: modelo con 94.5% accuracy
```

#### Paso 4: Predicciones en tiempo real

```python
# Nueva transacción sospechosa
new_tx = {
    "amount": 5200.00,
    "hour": 2,          # 2 AM
    "distance_km": 800, # Lejos del hogar
    "is_online": True
}

risk_score = model.predict(new_tx)
# Output: 100% → 🚨 FRAUDE
```

### Resultados del Demo

| Transacción | Monto | Hora | Distancia | Riesgo | Resultado |
|-------------|-------|------|-----------|--------|-----------|
| TX-001 | $45.99 | 14:00 | 2.5km | 0.0% | ✅ Legítimo |
| TX-002 | $2,500 | 03:00 | 450km | 62.8% | 🚨 Fraude |
| TX-003 | $89.50 | 10:00 | 0km | 0.0% | ✅ Legítimo |
| TX-004 | $5,200 | 02:00 | 800km | 100% | 🚨 Fraude |
| TX-005 | $12.99 | 18:00 | 5km | 0.0% | ✅ Legítimo |

**Patrones detectados:**
- 🔴 Transacciones nocturnas (2-3 AM) + alta distancia = alto riesgo
- 🟢 Transacciones diurnas + baja distancia = bajo riesgo

---

## Caso 2: Investigación Médica (Hospitales)

### El Problema

Tres hospitales quieren predecir riesgo de diabetes:
- 🏥 **Hospital Central**: 10,000 pacientes
- 🏥 **Clínica Norte**: 5,000 pacientes
- 🏥 **Centro Sur**: 8,000 pacientes

**Desafíos:**
- HIPAA prohíbe compartir datos de pacientes
- Cada hospital tiene diferentes demografías
- Modelos individuales tienen sesgo

### La Solución

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONSORCIO MÉDICO PARA DIABETES                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Hospital Central    Clínica Norte      Centro Sur              │
│   (10,000 pac)       (5,000 pac)       (8,000 pac)             │
│        │                  │                  │                   │
│        ▼                  ▼                  ▼                   │
│   ┌─────────┐        ┌─────────┐       ┌─────────┐             │
│   │ Cifrar  │        │ Cifrar  │       │ Cifrar  │             │
│   │ glucosa │        │ glucosa │       │ glucosa │             │
│   │  IMC    │        │  IMC    │       │  IMC    │             │
│   │  edad   │        │  edad   │       │  edad   │             │
│   └────┬────┘        └────┬────┘       └────┬────┘             │
│        │                  │                  │                   │
│        └──────────────────┼──────────────────┘                   │
│                           ▼                                      │
│                  ┌─────────────────┐                            │
│                  │ Modelo Federado │                            │
│                  │   (23,000 pac)  │                            │
│                  └─────────────────┘                            │
│                           │                                      │
│                           ▼                                      │
│              Predicción: Riesgo de Diabetes                     │
│              (sin ver datos individuales)                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Datos de Ejemplo

**Antes (Datos sensibles):**
```
Paciente: Juan García
Edad: 45 años
Glucosa: 126 mg/dL
IMC: 28.5
Presión: 140/90
Historial familiar: Sí
```

**Después (Cifrado FHE):**
```
Paciente: [ENCRYPTED]
Edad: [0x8f3a2b...4096 coef]
Glucosa: [0x2c7d1e...4096 coef]
IMC: [0x5b9f4a...4096 coef]
...
```

### Beneficios

| Aspecto | Sin FHE | Con FHE |
|---------|---------|---------|
| Datos compartidos | Sí (violación HIPAA) | No |
| Tamaño dataset | 10,000 (un hospital) | 23,000 (todos) |
| Sesgo demográfico | Alto | Bajo |
| Auditoría | Difícil | Blockchain |

---

## Caso 3: Credit Scoring (Fintech)

### El Problema

Fintechs quieren evaluar riesgo crediticio:
- Tienen datos de transacciones
- Necesitan datos de burós de crédito
- Los burós no pueden compartir datos directamente

### La Solución

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONSORCIO DE CREDIT SCORING                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Fintech A          Buró Crédito         Fintech B             │
│ (transacciones)     (historial)       (transacciones)          │
│        │                  │                   │                  │
│        ▼                  ▼                   ▼                  │
│   ┌─────────┐        ┌─────────┐        ┌─────────┐            │
│   │ Encrypt │        │ Encrypt │        │ Encrypt │            │
│   └────┬────┘        └────┬────┘        └────┬────┘            │
│        │                  │                   │                  │
│        └──────────────────┼───────────────────┘                  │
│                           ▼                                      │
│                  ┌─────────────────┐                            │
│                  │  Modelo Unificado│                           │
│                  │  de Credit Score │                           │
│                  └─────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tecnología: FHE (Fully Homomorphic Encryption)

### ¿Qué es FHE?

FHE permite realizar operaciones matemáticas sobre datos cifrados **sin descifrarlos**.

```
Ejemplo tradicional:
  Datos → Descifrar → Procesar → Cifrar → Resultado
  ⚠️ Datos expuestos durante procesamiento

Ejemplo FHE:
  Datos cifrados → Procesar (cifrado) → Resultado cifrado
  ✅ Datos NUNCA expuestos
```

### Esquema CKKS

Usamos **CKKS** (Cheon-Kim-Kim-Song) porque:

| Característica | CKKS | BFV/BGV |
|----------------|------|---------|
| Tipo de datos | Números reales | Enteros |
| Ideal para | ML/AI | Votación |
| Precisión | Aproximada | Exacta |
| Velocidad | Más rápido | Más lento |

**Parámetros de seguridad:**
```
Esquema:           CKKS
Seguridad:         128-bit (estándar NIST)
Grado polinomial:  8192
Factor de escala:  2^40
```

### Operaciones Soportadas

```python
# Sobre datos cifrados podemos hacer:
encrypted_sum = enc_a + enc_b          # Suma
encrypted_product = enc_a * enc_b      # Multiplicación
encrypted_scaled = enc_a * 2.5         # Escalar

# Lo que permite entrenar:
# - Regresión Lineal
# - Regresión Logística
# - Árboles de Decisión (aproximados)
# - K-Means Clustering
```

---

## Tecnología: Blockchain (Arbitrum)

### ¿Por qué Blockchain?

| Función | Implementación |
|---------|----------------|
| Gobernanza | Votación on-chain |
| Auditoría | Registro inmutable |
| Verificación | Hashes de datos |
| Transparencia | Contratos públicos |

### Smart Contracts Desplegados

```
Red: Arbitrum Sepolia (Testnet)
Chain ID: 421614

Contratos:
├── ConsortiumGovernanceV2
│   └── 0xda52326d106A91A1F22A0c41Be2dc1F531C01F11
├── ModelRegistryV2
│   └── 0x1296cCeF7803Bff51FB690afCFc586E7012417b8
└── ComputationVerifierV2
    └── 0xa5f04E0aefe55173C91b949Aa2385f0228dd2921
```

### Flujo de Gobernanza

```
1. CREAR PROPUESTA
   └── "Entrenar modelo de fraude"

2. COMMIT PHASE (24h)
   ├── Bank Alpha: commit(hash(YES + salt_a))
   ├── Bank Beta:  commit(hash(YES + salt_b))
   └── Bank Gamma: commit(hash(YES + salt_c))

3. REVEAL PHASE (24h)
   ├── Bank Alpha: reveal(YES, salt_a) → ✓ Verified
   ├── Bank Beta:  reveal(YES, salt_b) → ✓ Verified
   └── Bank Gamma: reveal(YES, salt_c) → ✓ Verified

4. EJECUCIÓN
   └── 100% > 51% quorum → APROBADO
```

---

## Comparación: Con vs Sin Xcapit

| Aspecto | Sin Xcapit | Con Xcapit |
|---------|------------|------------|
| Datos compartidos | Sí (riesgo) | No |
| Cumplimiento GDPR/HIPAA | Difícil | Automático |
| Tamaño del dataset | Limitado | Combinado |
| Auditoría | Manual | Blockchain |
| Confianza | Basada en contratos | Criptográfica |
| Costo de integración | Alto | API simple |

---

## Próximos Pasos

### Para Bancos/Fintech
1. Contactar: privacy@xcapit.com
2. Demo personalizado con sus datos (cifrados)
3. Pilot de 3 meses en testnet
4. Producción en Arbitrum mainnet

### Para Hospitales/Healthcare
1. Evaluación de cumplimiento HIPAA
2. Integración con sistemas HIS/EMR
3. Entrenamiento de modelos específicos

### Links

- **Plataforma**: https://xcapit-privacy.vercel.app
- **Documentación API**: /docs/api-reference.md
- **Contratos**: https://sepolia.arbiscan.io
- **Contacto**: privacy@xcapit.com
