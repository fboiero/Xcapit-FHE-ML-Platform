# Capítulo 7: Modelos de Machine Learning

## 7.1 Visión General

Xcapit FHE-ML incluye cuatro modelos de ML optimizados para operar sobre datos encriptados:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODELOS DISPONIBLES                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   LinearRegression      │   Predicción de valores continuos          │
│   ─────────────────────────────────────────────────────────────      │
│   • FHE-nativo (solo operaciones lineales)                           │
│   • Muy rápido                                                       │
│   • Ideal para: precios, cantidades, scores                          │
│                                                                       │
│   LogisticRegression    │   Clasificación binaria                    │
│   ─────────────────────────────────────────────────────────────      │
│   • Sigmoid aproximado con polinomios                                │
│   • Precisión configurable (grados 3, 5, 7)                          │
│   • Ideal para: detección de fraude, diagnóstico                     │
│                                                                       │
│   DecisionTree          │   Clasificación/regresión con reglas       │
│   ─────────────────────────────────────────────────────────────      │
│   • Comparaciones suaves (soft decisions)                            │
│   • Evalúa todas las ramas                                           │
│   • Ideal para: scoring de riesgo, segmentación                      │
│                                                                       │
│   KMeans                │   Clustering no supervisado                │
│   ─────────────────────────────────────────────────────────────      │
│   • Asignación probabilística a clusters                             │
│   • Softmax aproximado                                               │
│   • Ideal para: segmentación de clientes, anomalías                  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7.2 LinearRegression

### 7.2.1 Fundamento Matemático

La regresión lineal modela la relación entre features `X` y target `y`:

```
ŷ = X · w + b

Donde:
• X ∈ ℝⁿˣᵈ : matriz de features (n muestras, d dimensiones)
• w ∈ ℝᵈ   : vector de pesos
• b ∈ ℝ    : término de sesgo (bias)
• ŷ ∈ ℝⁿ   : predicciones
```

**Entrenamiento (Mínimos Cuadrados Ordinarios):**

```
w* = (XᵀX)⁻¹ Xᵀy

Con regularización L2 (Ridge):
w* = (XᵀX + λI)⁻¹ Xᵀy
```

### 7.2.2 Implementación FHE

```python
class LinearRegression:
    """
    Regresión lineal compatible con FHE.

    En FHE:
    - Pesos (w) y bias (b) son texto plano
    - Datos de entrada (X) son encriptados
    - Resultado (ŷ) es encriptado

    Operaciones FHE requeridas:
    - Multiplicación ciphertext × plaintext
    - Suma de elementos (rotaciones)
    - Suma ciphertext + plaintext
    """

    def __init__(self, regularization: float = 0.0):
        self.regularization = regularization
        self.weights = None
        self.bias = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Entrena en texto plano usando OLS."""
        n, d = X.shape

        # Agregar columna de 1s para el bias
        X_aug = np.column_stack([X, np.ones(n)])

        # Resolver sistema normal
        if self.regularization > 0:
            reg_matrix = self.regularization * np.eye(d + 1)
            reg_matrix[-1, -1] = 0  # No regularizar el bias
            solution = np.linalg.solve(
                X_aug.T @ X_aug + reg_matrix,
                X_aug.T @ y
            )
        else:
            solution = np.linalg.lstsq(X_aug, y, rcond=None)[0]

        self.weights = solution[:-1]
        self.bias = solution[-1]

    def predict_encrypted(self, X_encrypted):
        """
        Predicción sobre datos encriptados.

        Operaciones:
        1. X_enc * weights (multiplicación elemento a elemento)
        2. sum(resultado) (suma con rotaciones)
        3. resultado + bias
        """
        # Multiplicación ciphertext × plaintext vector
        weighted = X_encrypted * self.weights

        # Suma de todos los elementos
        dot_product = weighted.sum()

        # Agregar bias
        result = dot_product + self.bias

        return result
```

### 7.2.3 Ejemplo de Uso

```python
import numpy as np
from xcapit_fhe_ml import create_context, LinearRegression
from xcapit_fhe_ml import encrypt_vector, decrypt_vector

# Datos de ejemplo
X_train = np.array([
    [1, 2, 3],
    [2, 3, 4],
    [3, 4, 5],
    [4, 5, 6]
])
y_train = np.array([6, 9, 12, 15])  # y = x1 + x2 + x3

# Entrenar
model = LinearRegression(regularization=0.01)
model.fit(X_train, y_train)
print(f"Pesos: {model.weights}")  # [1, 1, 1]
print(f"Bias: {model.bias}")      # 0

# Predicción encriptada
context = create_context()
X_test = np.array([5, 6, 7])
X_enc = encrypt_vector(context, X_test)

y_enc = model.predict_encrypted(X_enc)
y_pred = decrypt_vector(context, y_enc)

print(f"Predicción: {y_pred[0]}")  # 18.0
```

### 7.2.4 Complejidad FHE

| Operación | Cantidad | Profundidad Multiplicativa |
|-----------|----------|---------------------------|
| Multiplicación ct×pt | d | 1 |
| Rotaciones (suma) | log₂(d) | 0 |
| Suma ct+pt | 1 | 0 |
| **Total** | - | **1** |

---

## 7.3 LogisticRegression

### 7.3.1 Fundamento Matemático

Clasificación binaria con función sigmoid:

```
P(y=1|X) = σ(X · w + b)

Donde:
σ(z) = 1 / (1 + e⁻ᶻ)
```

**El problema en FHE:**
- La función sigmoid contiene `e^x` y división
- Ambas operaciones no son nativas en FHE

**Solución: Aproximación Polinomial**

```
σ(z) ≈ Σᵢ cᵢ · zⁱ

Grado 5:
σ(z) ≈ 0.5 + 0.197z - 0.004z³ + 0.00008z⁵
```

### 7.3.2 Implementación FHE

```python
class LogisticRegression:
    """
    Regresión logística compatible con FHE.

    Usa aproximación polinomial para sigmoid:
    - Grado 3: rápido, menos preciso (1 mult)
    - Grado 5: balance (2 mults)
    - Grado 7: preciso, más lento (3 mults)
    """

    SIGMOID_COEFFS = {
        3: [0.5, 0.197, 0.0, -0.004],
        5: [0.5, 0.197, 0.0, -0.004, 0.0, 0.00008],
        7: [0.5, 0.197, 0.0, -0.004, 0.0, 0.00008, 0.0, -0.000002]
    }

    def __init__(self, sigmoid_degree: int = 5, learning_rate: float = 0.1,
                 max_iter: int = 100, regularization: float = 0.01):
        self.degree = sigmoid_degree
        self.lr = learning_rate
        self.max_iter = max_iter
        self.reg = regularization
        self.weights = None
        self.bias = None
        self.coeffs = self.SIGMOID_COEFFS[sigmoid_degree]

    def _sigmoid(self, z):
        """Sigmoid real para entrenamiento."""
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def _sigmoid_poly(self, z_encrypted):
        """Sigmoid aproximado con polinomio para FHE."""
        result = z_encrypted * 0 + self.coeffs[0]

        z_power = z_encrypted
        for i in range(1, len(self.coeffs)):
            if self.coeffs[i] != 0:
                result = result + z_power * self.coeffs[i]
            z_power = z_power * z_encrypted

        return result

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Entrena con gradient descent en texto plano."""
        n, d = X.shape

        self.weights = np.zeros(d)
        self.bias = 0.0

        for _ in range(self.max_iter):
            # Forward pass
            z = X @ self.weights + self.bias
            pred = self._sigmoid(z)

            # Gradients
            error = pred - y
            grad_w = (X.T @ error) / n + self.reg * self.weights
            grad_b = np.mean(error)

            # Update
            self.weights -= self.lr * grad_w
            self.bias -= self.lr * grad_b

    def predict_encrypted(self, X_encrypted):
        """Predicción encriptada con sigmoid aproximado."""
        # Combinación lineal
        z = (X_encrypted * self.weights).sum() + self.bias

        # Sigmoid aproximado
        probability = self._sigmoid_poly(z)

        return probability

    def predict_class_encrypted(self, X_encrypted, threshold=0.5):
        """Retorna probabilidad (clasificación requiere descifrar)."""
        return self.predict_encrypted(X_encrypted)
```

### 7.3.3 Ejemplo de Uso

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Generar datos
X, y = make_classification(n_samples=200, n_features=5, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Normalizar (importante para FHE)
scaler = StandardScaler()
X_train_norm = scaler.fit_transform(X_train)
X_test_norm = scaler.transform(X_test)

# Entrenar
model = LogisticRegression(sigmoid_degree=5)
model.fit(X_train_norm, y_train)

# Predicción encriptada
context = create_context()
correct = 0

for i in range(len(X_test_norm)):
    X_enc = encrypt_vector(context, X_test_norm[i])
    prob_enc = model.predict_encrypted(X_enc)
    prob = decrypt_vector(context, prob_enc)[0]

    pred = 1 if prob > 0.5 else 0
    correct += (pred == y_test[i])

print(f"Accuracy: {correct / len(X_test):.2%}")
```

### 7.3.4 Complejidad FHE

| Grado | Multiplicaciones | Profundidad | Error Máx |
|-------|-----------------|-------------|-----------|
| 3 | 1 | 2 | ~0.05 |
| 5 | 2 | 3 | ~0.01 |
| 7 | 3 | 4 | ~0.002 |

---

## 7.4 DecisionTree

### 7.4.1 Fundamento Matemático

Un árbol de decisión tradicional usa comparaciones:

```
if x[feature] <= threshold:
    go_left()
else:
    go_right()
```

**Problema en FHE:** No podemos comparar valores encriptados.

**Solución: Comparaciones Suaves**

```
P(left) = σ(β × (threshold - x[feature]))
P(right) = 1 - P(left)

Resultado = P(left) × valor_izquierda + P(right) × valor_derecha
```

### 7.4.2 Implementación FHE

```python
class DecisionTreeNode:
    """Nodo del árbol de decisión."""
    def __init__(self, feature_idx=None, threshold=None,
                 left=None, right=None, value=None):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    @property
    def is_leaf(self):
        return self.value is not None


class DecisionTree:
    """
    Árbol de decisión compatible con FHE.

    Usa comparaciones suaves (soft comparisons):
    - Evalúa TODAS las ramas
    - Combina resultados con probabilidades
    - Más profundidad del árbol = más operaciones FHE
    """

    def __init__(self, max_depth: int = 5, beta: float = 5.0,
                 sigmoid_degree: int = 5):
        self.max_depth = max_depth
        self.beta = beta
        self.degree = sigmoid_degree
        self.root = None

    def _sigmoid_poly(self, z):
        """Sigmoid aproximado."""
        coeffs = [0.5, 0.197, 0.0, -0.004, 0.0, 0.00008]
        result = coeffs[0]
        z_power = z
        for c in coeffs[1:]:
            if c != 0:
                result = result + z_power * c
            z_power = z_power * z
        return result

    def _soft_compare(self, x_val, threshold):
        """
        Comparación suave: P(x <= threshold)

        P = σ(β × (threshold - x))

        β alto → comparación más "dura"
        β bajo → comparación más "suave"
        """
        diff = (threshold - x_val) * self.beta
        return self._sigmoid_poly(diff)

    def _evaluate_node(self, node, X_encrypted):
        """Evalúa nodo recursivamente sobre datos encriptados."""
        if node.is_leaf:
            # Retornar valor de la hoja
            return X_encrypted * 0 + node.value

        # Obtener feature específica
        feature_val = X_encrypted[node.feature_idx]

        # Calcular probabilidades de ir a cada rama
        p_left = self._soft_compare(feature_val, node.threshold)
        p_right = 1.0 - p_left

        # Evaluar ambas ramas
        val_left = self._evaluate_node(node.left, X_encrypted)
        val_right = self._evaluate_node(node.right, X_encrypted)

        # Combinar resultados ponderados
        result = p_left * val_left + p_right * val_right

        return result

    def predict_encrypted(self, X_encrypted):
        """Predicción encriptada evaluando todas las ramas."""
        return self._evaluate_node(self.root, X_encrypted)
```

### 7.4.3 Ejemplo de Uso

```python
from sklearn.tree import DecisionTreeClassifier as SKTree
from sklearn.datasets import make_classification

# Generar datos
X, y = make_classification(n_samples=200, n_features=4, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Entrenar árbol sklearn primero
sk_tree = SKTree(max_depth=3)
sk_tree.fit(X_train, y_train)

# Convertir a árbol FHE
model = DecisionTree(max_depth=3, beta=5.0)
model.from_sklearn(sk_tree)  # Método de conversión

# Predicción encriptada
context = create_context(preset="precise")
scaler = StandardScaler().fit(X_train)

for i in range(5):
    X_norm = scaler.transform([X_test[i]])[0]
    X_enc = encrypt_vector(context, X_norm)

    pred_enc = model.predict_encrypted(X_enc)
    pred_prob = decrypt_vector(context, pred_enc)[0]

    pred_class = 1 if pred_prob > 0.5 else 0
    print(f"Prob: {pred_prob:.3f}, Pred: {pred_class}, Real: {y_test[i]}")
```

### 7.4.4 Complejidad FHE

| Profundidad | Hojas | Comparaciones | Mults por Nodo |
|-------------|-------|---------------|----------------|
| 2 | 4 | 3 | ~2 |
| 3 | 8 | 7 | ~2 |
| 4 | 16 | 15 | ~2 |
| 5 | 32 | 31 | ~2 |

**Profundidad multiplicativa total:** ~3 × profundidad_árbol

---

## 7.5 KMeans

### 7.5.1 Fundamento Matemático

K-Means asigna cada punto al cluster más cercano:

```
cluster_i = argmin_k ||x_i - c_k||²

Donde c_k es el centroide del cluster k.
```

**Problema en FHE:** `argmin` requiere comparaciones.

**Solución: Asignación Suave (Soft Assignment)**

```
P(cluster=k | x) = exp(-β × d_k) / Σⱼ exp(-β × d_j)

Donde d_k = ||x - c_k||²

Esto es un softmax sobre distancias negativas.
```

### 7.5.2 Implementación FHE

```python
class KMeans:
    """
    K-Means compatible con FHE.

    Características:
    - Entrenamiento en texto plano
    - Inferencia sobre datos encriptados
    - Retorna probabilidades de pertenencia a cada cluster
    """

    def __init__(self, n_clusters: int = 3, beta: float = 1.0,
                 max_iter: int = 100, exp_degree: int = 4):
        self.k = n_clusters
        self.beta = beta
        self.max_iter = max_iter
        self.exp_degree = exp_degree
        self.centroids = None

    def fit(self, X: np.ndarray):
        """K-Means tradicional en texto plano."""
        n, d = X.shape

        # Inicialización K-Means++
        self.centroids = self._kmeans_plusplus(X)

        for _ in range(self.max_iter):
            # Asignar clusters
            distances = np.array([
                np.sum((X - c) ** 2, axis=1)
                for c in self.centroids
            ]).T
            labels = np.argmin(distances, axis=1)

            # Actualizar centroides
            new_centroids = np.array([
                X[labels == k].mean(axis=0) if np.any(labels == k)
                else self.centroids[k]
                for k in range(self.k)
            ])

            if np.allclose(self.centroids, new_centroids):
                break
            self.centroids = new_centroids

    def _compute_distance_encrypted(self, X_encrypted, centroid):
        """
        Calcula ||X - c||² sobre X encriptado.

        ||X - c||² = Σᵢ (xᵢ - cᵢ)²
        """
        diff = X_encrypted - centroid
        diff_sq = diff * diff
        distance = diff_sq.sum()
        return distance

    def _exp_approx(self, x):
        """
        Aproximación de exp(x) con Taylor.
        exp(x) ≈ 1 + x + x²/2 + x³/6 + x⁴/24
        """
        result = 1.0
        term = x
        for i in range(1, self.exp_degree + 1):
            result = result + term
            term = term * x / (i + 1)
        return result

    def _softmax_encrypted(self, neg_distances):
        """
        Softmax sobre distancias negativas.
        P_k = exp(-β×d_k) / Σⱼ exp(-β×d_j)
        """
        exp_vals = [
            self._exp_approx(d * (-self.beta))
            for d in neg_distances
        ]

        total = exp_vals[0]
        for ev in exp_vals[1:]:
            total = total + ev

        # Aproximar 1/total con Newton-Raphson
        inv_total = self._inverse_newton(total)

        probs = [ev * inv_total for ev in exp_vals]
        return probs

    def predict_encrypted(self, X_encrypted):
        """
        Retorna probabilidades de pertenencia a cada cluster.
        """
        distances = [
            self._compute_distance_encrypted(X_encrypted, c)
            for c in self.centroids
        ]

        probs = self._softmax_encrypted(distances)
        return probs
```

### 7.5.3 Ejemplo de Uso

```python
from sklearn.datasets import make_blobs

# Generar clusters
X, y_true = make_blobs(n_samples=200, centers=3, random_state=42)

# Normalizar
scaler = StandardScaler()
X_norm = scaler.fit_transform(X)

# Entrenar
model = KMeans(n_clusters=3, beta=1.0)
model.fit(X_norm)

# Predicción encriptada
context = create_context(preset="precise")

for i in range(5):
    X_enc = encrypt_vector(context, X_norm[i])
    probs_enc = model.predict_encrypted(X_enc)

    # Descifrar probabilidades
    probs = [decrypt_vector(context, p)[0] for p in probs_enc]

    pred_cluster = np.argmax(probs)
    print(f"Probabilities: {probs}, Predicted: {pred_cluster}, True: {y_true[i]}")
```

### 7.5.4 Complejidad FHE

| Operación | Por Cluster | Total (K clusters) |
|-----------|-------------|-------------------|
| Distancia | d mults + suma | K × (d + log d) |
| Exp | ~4 mults | K × 4 |
| Suma exp | K-1 sumas | K-1 |
| Inversión | ~4 iters | 4 |
| Normalización | K mults | K |

**Profundidad multiplicativa total:** ~8-10

---

## 7.6 Comparación de Modelos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPARACIÓN DE MODELOS FHE                        │
├──────────────────┬─────────────┬──────────────┬─────────────────────┤
│   Modelo         │  Prof. Mult │  Velocidad   │  Casos de Uso       │
├──────────────────┼─────────────┼──────────────┼─────────────────────┤
│ LinearRegression │     1       │   Muy rápido │ Regresión simple    │
│ LogisticRegress. │    2-4      │   Rápido     │ Clasificación binaria│
│ DecisionTree     │   6-15      │   Medio      │ Clasificación/regr. │
│ KMeans          │   8-10      │   Lento      │ Clustering          │
└──────────────────┴─────────────┴──────────────┴─────────────────────┘
```

---

## 7.7 Selección de Modelo

```
¿Qué tipo de problema tienes?

    │
    ├── Regresión (predecir valor numérico)
    │   │
    │   ├── Relación lineal → LinearRegression
    │   │
    │   └── Relación no lineal → DecisionTree (modo regresión)
    │
    ├── Clasificación binaria (sí/no)
    │   │
    │   ├── Separable linealmente → LogisticRegression
    │   │
    │   └── Compleja → DecisionTree
    │
    ├── Clasificación multiclase
    │   │
    │   └── DecisionTree (múltiples hojas)
    │
    └── Clustering (agrupar datos)
        │
        └── KMeans
```

---

**Siguiente capítulo**: [Integración Blockchain →](04-blockchain-integration.md)
