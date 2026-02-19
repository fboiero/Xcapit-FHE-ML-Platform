# Capítulo 9: Guía de Inicio Rápido

## 9.1 Instalación

### 9.1.1 Requisitos del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REQUISITOS MÍNIMOS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   Sistema Operativo:                                                  │
│   • Linux (Ubuntu 20.04+, Debian 11+)                                │
│   • macOS (11.0+)                                                    │
│   • Windows 10+ (con WSL2 recomendado)                               │
│                                                                       │
│   Hardware:                                                          │
│   • RAM: 8GB mínimo (16GB recomendado)                              │
│   • CPU: x86_64 con AVX2 (aceleración criptográfica)                │
│   • Disco: 2GB libres                                                │
│                                                                       │
│   Software:                                                          │
│   • Python 3.9+                                                      │
│   • pip 21+                                                          │
│   • (Opcional) Docker 20+                                            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.1.2 Instalación con pip

```bash
# Crear entorno virtual
python3 -m venv fhe-ml-env
source fhe-ml-env/bin/activate  # Linux/macOS
# o: fhe-ml-env\Scripts\activate  # Windows

# Instalar el SDK
pip install xcapit-fhe-ml

# Verificar instalación
python -c "import xcapit_fhe_ml; print(xcapit_fhe_ml.__version__)"
```

### 9.1.3 Instalación desde código fuente

```bash
# Clonar repositorio
git clone https://github.com/xcapit/fhe-ml-platform.git
cd fhe-ml-platform

# Instalar dependencias
pip install -e ".[dev]"

# Ejecutar tests
pytest tests/ -v
```

### 9.1.4 Instalación con Docker

```bash
# Construir imagen
docker build -t xcapit-fhe-ml .

# Ejecutar contenedor
docker run -p 8000:8000 xcapit-fhe-ml

# O usar docker-compose
docker-compose up -d
```

---

## 9.2 Tu Primera Predicción Encriptada

### 9.2.1 Ejemplo Mínimo

```python
"""
Ejemplo mínimo: Predicción sobre datos encriptados.
Los datos NUNCA son vistos en texto plano por el modelo.
"""
import numpy as np
from xcapit_fhe_ml import (
    create_context,
    LinearRegression,
    encrypt_vector,
    decrypt_vector
)

# 1. Crear contexto criptográfico
print("1. Creando contexto CKKS...")
context = create_context(preset="balanced")

# 2. Datos de entrenamiento (en texto plano para entrenar)
X_train = np.array([
    [1.0, 2.0],
    [2.0, 3.0],
    [3.0, 4.0],
    [4.0, 5.0]
])
y_train = np.array([3.0, 5.0, 7.0, 9.0])  # y = x1 + x2

# 3. Entrenar modelo
print("2. Entrenando modelo...")
model = LinearRegression()
model.fit(X_train, y_train)
print(f"   Pesos aprendidos: {model.weights}")
print(f"   Bias aprendido: {model.bias}")

# 4. Datos de prueba - ENCRIPTAR antes de predecir
print("3. Encriptando datos de prueba...")
X_test = np.array([5.0, 6.0])
X_encrypted = encrypt_vector(context, X_test)
print(f"   Datos originales: {X_test}")
print(f"   Datos encriptados: [ciphertext - no visible]")

# 5. Predicción sobre datos encriptados
print("4. Realizando predicción sobre datos ENCRIPTADOS...")
y_encrypted = model.predict_encrypted(X_encrypted)
print(f"   Resultado encriptado: [ciphertext - no visible]")

# 6. Descifrar resultado
print("5. Descifrando resultado...")
y_pred = decrypt_vector(context, y_encrypted)
print(f"   Predicción: {y_pred[0]:.4f}")
print(f"   Valor esperado: {X_test[0] + X_test[1]:.4f}")

# Verificar precisión
error = abs(y_pred[0] - (X_test[0] + X_test[1]))
print(f"\n   Error de aproximación: {error:.6f}")
```

**Salida esperada:**
```
1. Creando contexto CKKS...
2. Entrenando modelo...
   Pesos aprendidos: [1.0, 1.0]
   Bias aprendido: 0.0
3. Encriptando datos de prueba...
   Datos originales: [5. 6.]
   Datos encriptados: [ciphertext - no visible]
4. Realizando predicción sobre datos ENCRIPTADOS...
   Resultado encriptado: [ciphertext - no visible]
5. Descifrando resultado...
   Predicción: 11.0000
   Valor esperado: 11.0000

   Error de aproximación: 0.000001
```

---

## 9.3 Clasificación Binaria con Privacidad

```python
"""
Clasificación binaria: Predicción de diabetes.
Los datos del paciente permanecen encriptados.
"""
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from xcapit_fhe_ml import (
    create_context,
    LogisticRegression,
    encrypt_vector,
    decrypt_vector
)

# 1. Cargar y preparar datos
print("Cargando datos...")
diabetes = load_diabetes()
X = diabetes.data[:, :4]  # Usar 4 features para simplicidad
y = (diabetes.target > 150).astype(float)  # Binarizar

# Dividir datos
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Normalizar (importante para FHE)
scaler = StandardScaler()
X_train_norm = scaler.fit_transform(X_train)
X_test_norm = scaler.transform(X_test)

# 2. Crear contexto y modelo
print("Configurando FHE...")
context = create_context(preset="ml_optimized")
model = LogisticRegression(sigmoid_degree=5)

# 3. Entrenar
print("Entrenando modelo...")
model.fit(X_train_norm, y_train)

# 4. Predicción encriptada
print("\nRealizando predicciones encriptadas...")
correct = 0
total = min(10, len(X_test_norm))  # Primeras 10 muestras

for i in range(total):
    # Encriptar muestra
    X_enc = encrypt_vector(context, X_test_norm[i])

    # Predecir (sobre datos encriptados)
    y_enc = model.predict_encrypted(X_enc)

    # Descifrar
    prob = decrypt_vector(context, y_enc)[0]
    pred = 1 if prob > 0.5 else 0

    # Evaluar
    actual = int(y_test[i])
    match = "✓" if pred == actual else "✗"
    correct += (pred == actual)

    print(f"  Muestra {i+1}: prob={prob:.3f}, pred={pred}, real={actual} {match}")

print(f"\nPrecisión: {correct}/{total} ({100*correct/total:.1f}%)")
print("\n¡Los datos del paciente NUNCA fueron expuestos al modelo!")
```

---

## 9.4 Uso del Cliente API

### 9.4.1 Iniciar el Servidor

```bash
# Terminal 1: Iniciar servidor
python -m xcapit_fhe_ml.api.server

# Salida:
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 9.4.2 Usar el Cliente

```python
"""
Ejemplo de uso del cliente API.
"""
from xcapit_fhe_ml.api import FHEMLClient

# Conectar al servidor
client = FHEMLClient("http://localhost:8000")

# Crear modelo
model_id = client.create_model(
    model_type="linear_regression",
    config={"regularization": 0.01}
)
print(f"Modelo creado: {model_id}")

# Entrenar
import numpy as np
X_train = np.random.randn(100, 5)
y_train = X_train @ np.array([1, 2, 3, 4, 5]) + 0.1

result = client.train(model_id, X_train, y_train)
print(f"Entrenamiento completado: {result}")

# Predecir
X_test = np.random.randn(10, 5)
predictions = client.predict(model_id, X_test)
print(f"Predicciones: {predictions}")

# Los datos fueron encriptados automáticamente antes de enviar
```

---

## 9.5 Uso del CLI

### 9.5.1 Comandos Básicos

```bash
# Ver versión
fheml version

# Inicializar proyecto
fheml init --name my_project

# Ver información del contexto
fheml info

# Encriptar datos
fheml encrypt --input data.csv --output data.enc

# Entrenar modelo
fheml train --model linear --data data.enc --output model.pkl

# Hacer predicción
fheml predict --model model.pkl --input new_data.csv
```

### 9.5.2 Ejemplo Completo con CLI

```bash
# 1. Preparar datos de ejemplo
cat > train_data.csv << EOF
feature1,feature2,feature3,target
1.0,2.0,3.0,6.0
2.0,3.0,4.0,9.0
3.0,4.0,5.0,12.0
4.0,5.0,6.0,15.0
EOF

# 2. Inicializar contexto
fheml init --preset balanced

# 3. Entrenar modelo
fheml train \
    --model linear_regression \
    --data train_data.csv \
    --target target \
    --output my_model.pkl

# 4. Preparar datos de prueba
cat > test_data.csv << EOF
feature1,feature2,feature3
5.0,6.0,7.0
6.0,7.0,8.0
EOF

# 5. Predecir (datos se encriptan automáticamente)
fheml predict \
    --model my_model.pkl \
    --input test_data.csv \
    --encrypted  # Flag para usar encriptación

# Salida:
# Predicciones:
# [0] 18.0
# [1] 21.0
```

---

## 9.6 Integración con scikit-learn

```python
"""
Xcapit FHE-ML es compatible con la API de scikit-learn.
"""
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import numpy as np

from xcapit_fhe_ml import (
    LinearRegression as FHELinearRegression,
    create_context
)

# Datos de ejemplo
X = np.random.randn(200, 5)
y = X @ np.array([1, 2, 3, 4, 5]) + np.random.randn(200) * 0.1

# Pipeline compatible con sklearn
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", FHELinearRegression())
])

# Cross-validation funciona normalmente
# (entrenamiento en texto plano, predicción puede ser encriptada)
scores = cross_val_score(pipeline, X, y, cv=5)
print(f"R² scores: {scores}")
print(f"Mean R²: {scores.mean():.4f} (+/- {scores.std()*2:.4f})")

# Entrenar pipeline final
pipeline.fit(X, y)

# Predicción encriptada
context = create_context()
X_new = np.array([[1, 2, 3, 4, 5]])
X_scaled = pipeline.named_steps["scaler"].transform(X_new)

from xcapit_fhe_ml import encrypt_vector, decrypt_vector
X_enc = encrypt_vector(context, X_scaled[0])
y_enc = pipeline.named_steps["model"].predict_encrypted(X_enc)
y_pred = decrypt_vector(context, y_enc)

print(f"\nPredicción encriptada: {y_pred[0]:.4f}")
```

---

## 9.7 Mejores Prácticas

### 9.7.1 Normalización de Datos

```python
"""
IMPORTANTE: Siempre normalizar datos antes de encriptar.
FHE funciona mejor con valores en rangos pequeños.
"""
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Opción 1: StandardScaler (recomendado para regresión)
scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)

# Opción 2: MinMaxScaler (para datos acotados)
scaler = MinMaxScaler(feature_range=(-1, 1))
X_normalized = scaler.fit_transform(X)

# NUNCA encriptar datos sin normalizar
# X_enc = encrypt_vector(context, X)  # MAL
X_enc = encrypt_vector(context, X_normalized[0])  # BIEN
```

### 9.7.2 Selección de Preset

```python
"""
Elegir el preset correcto según el caso de uso.
"""
from xcapit_fhe_ml import create_context

# Para pruebas rápidas y desarrollo
context_fast = create_context(preset="fast")
# - Menos precisión
# - Menos operaciones permitidas
# - Muy rápido

# Para producción típica
context_balanced = create_context(preset="balanced")
# - Buena precisión
# - ~5 multiplicaciones
# - Balance velocidad/precisión

# Para modelos profundos
context_precise = create_context(preset="precise")
# - Alta precisión
# - Muchas operaciones
# - Más lento, más memoria
```

### 9.7.3 Manejo de Errores

```python
"""
Manejo robusto de errores FHE.
"""
from xcapit_fhe_ml import (
    create_context,
    encrypt_vector,
    EncryptionError,
    NoiseOverflowError
)

try:
    context = create_context(preset="fast")
    X_enc = encrypt_vector(context, X)

    # Muchas operaciones pueden causar overflow de ruido
    for _ in range(100):
        X_enc = X_enc * X_enc  # Multiplicaciones acumulan ruido

except NoiseOverflowError as e:
    print(f"Error: Ruido FHE excedido")
    print(f"Solución: Usar preset 'precise' o reducir operaciones")

except EncryptionError as e:
    print(f"Error de encriptación: {e}")
    print(f"Verificar que los datos estén normalizados")
```

---

## 9.8 Próximos Pasos

| Quiero... | Ir a... |
|-----------|---------|
| Entender la teoría de FHE | [Teoría: Encriptación Homomórfica](../theory/01-homomorphic-encryption.md) |
| Ver más ejemplos de modelos | [Demos](../demos/) |
| Usar la API REST | [Referencia API](../api/rest-api.md) |
| Entrenar modelos personalizados | [Entrenamiento de Modelos](06-training-models.md) |
| Desplegar en producción | [Deployment](07-deployment.md) |

---

## 9.9 Solución de Problemas Comunes

### Error: "TenSEAL not installed"

```bash
pip install tenseal
```

### Error: "Context not initialized"

```python
# Asegurarse de crear contexto primero
from xcapit_fhe_ml import create_context
context = create_context()
```

### Error: "Noise budget exhausted"

```python
# Usar configuración con más niveles
context = create_context(preset="precise")

# O reducir número de operaciones en el modelo
```

### Predicciones muy imprecisas

```python
# 1. Verificar normalización
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_norm = scaler.fit_transform(X)

# 2. Usar mayor escala
context = create_context(
    poly_modulus_degree=8192,
    scale=2**50  # Mayor precisión
)
```

---

**Siguiente capítulo**: [Entrenamiento de Modelos →](06-training-models.md)
