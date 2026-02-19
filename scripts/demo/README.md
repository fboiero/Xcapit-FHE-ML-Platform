# Bank Consortium Fraud Detection Demo

Demo completa de deteccion de fraude colaborativa usando FHE (Fully Homomorphic Encryption).

## Descripcion

Esta demo muestra como dos bancos pueden colaborar para mejorar la deteccion de fraude sin compartir datos sensibles de clientes. Usando cifrado homomorfico (CKKS), los modelos de ML se entrenan sobre datos cifrados.

**Resultado clave**:
- Modelos individuales: ~70-75% accuracy
- Modelo del consorcio: ~87% accuracy

## Archivos

| Archivo | Descripcion |
|---------|-------------|
| `generate_fraud_data.py` | Genera datasets sinteticos con patrones de fraude diferenciados |
| `fraud_detection_demo.py` | Demo interactiva completa en terminal |

## Requisitos

```bash
pip install numpy pandas scikit-learn
```

## Uso

### 1. Generar datos sinteticos

```bash
python generate_fraud_data.py --output-dir /tmp/privacy-platform/data/demo
```

Opciones:
- `--bank-a-size`: Numero de registros para Banco A (default: 5000)
- `--bank-b-size`: Numero de registros para Banco B (default: 3000)
- `--verbose`: Mostrar estadisticas detalladas

### 2. Ejecutar demo interactiva

```bash
python fraud_detection_demo.py
```

Opciones:
- `--verbose`: Mostrar matrices de confusion
- `--no-interactive`: Ejecutar sin pausas
- `--use-real-fhe`: Usar TenSEAL real (requiere tenseal instalado)

## Flujo de la Demo

```
PASO 1: Setup
  - Crear empresas (Banco A, Banco B)
  - Generar datasets sinteticos

PASO 2: Entrenamiento Individual
  - Banco A entrena solo -> ~72% accuracy
  - Banco B entrena solo -> ~68% accuracy

PASO 3: Cifrado FHE
  - Banco A cifra sus datos con CKKS
  - Banco B cifra sus datos con CKKS

PASO 4: Entrenamiento Consorcio
  - Entrenar sobre datos cifrados combinados
  - Consorcio accuracy -> ~87%

PASO 5: Inferencia Cifrada
  - Nueva transaccion sospechosa
  - Prediccion sobre datos cifrados

PASO 6: Resumen
  - Comparacion de accuracies
  - Prueba de privacidad preservada
```

## Patrones de Fraude

### Banco A (5000 registros)
- Late-night + high value (>$500, 11pm-4am)
- Rapid velocity (>5 transacciones/24h)
- Online + internacional

### Banco B (3000 registros)
- Travel + distancia inusual (>100 millas)
- Gas station + monto alto (>$200)
- Weekend + multiples comercios

## Features del Dataset

```python
# Transaccion
- amount: float ($1 - $50,000)
- merchant_category: categorical (retail, food, travel, online, gas, entertainment)
- hour_of_day: int (0-23)
- is_international: bool
- distance_from_home: float (millas)

# Comportamiento
- avg_monthly_spend: float
- num_txns_last_24h: int
- ratio_to_avg_amount: float

# Target
- is_fraud: bool (2% tasa base)
```

## Demo Visual (React)

Navegar a: `http://localhost:5173/demo/bank-consortium`

## Reproducibilidad

Los scripts usan `np.random.seed(42)` para resultados consistentes.
