# Glosario

## Términos de Encriptación Homomórfica

### Bootstrapping
Técnica para "refrescar" un ciphertext reduciendo su nivel de ruido. Permite operaciones ilimitadas al costo de rendimiento. En CKKS, no siempre es necesario si se diseña el circuito correctamente.

### Ciphertext (ct)
Texto cifrado. En CKKS, es un par de polinomios `(c₀, c₁)` que encripta un mensaje. El servidor opera sobre ciphertexts sin poder ver los datos originales.

### CKKS (Cheon-Kim-Kim-Song)
Esquema de encriptación homomórfica diseñado para números reales aproximados. Ideal para Machine Learning porque soporta operaciones con decimales.

### Coeff Modulus (q)
Módulo de coeficientes. Define el espacio de trabajo de los polinomios. Un q más grande permite más operaciones pero requiere más memoria.

### Contexto (Context)
Configuración completa de CKKS incluyendo parámetros, claves y estado. Es necesario para todas las operaciones FHE.

### Decryption (Descifrado)
Proceso de convertir un ciphertext de vuelta a texto plano usando la clave secreta.

### Encryption (Encriptación)
Proceso de convertir texto plano a ciphertext usando la clave pública.

### Evaluation Keys (evk)
Claves de evaluación. Permiten operaciones como multiplicación y rotación sin revelar la clave secreta. Se envían al servidor.

### FHE (Fully Homomorphic Encryption)
Encriptación Completamente Homomórfica. Permite cualquier operación computable sobre datos encriptados.

### Galois Keys
Claves especiales para operaciones de rotación en los slots de CKKS.

### Homomorfismo
Propiedad matemática donde operaciones en el espacio cifrado corresponden a operaciones en el espacio original.

### Level (Nivel)
En CKKS, indica cuántas multiplicaciones más puede soportar un ciphertext antes de necesitar rescaling.

### LWE (Learning With Errors)
Problema matemático difícil en el que se basa la seguridad de FHE. Resistente incluso a computadoras cuánticas.

### Noise (Ruido)
Error criptográfico añadido durante la encriptación. Crece con cada operación. Si excede el límite, los datos se corrompen.

### PHE (Partially Homomorphic Encryption)
Encriptación Parcialmente Homomórfica. Solo permite una operación (suma O multiplicación).

### Plaintext
Texto plano. Datos sin encriptar.

### Poly Modulus Degree (N)
Grado del polinomio ciclotómico. Determina seguridad y número de slots. Valores típicos: 4096, 8192, 16384.

### Public Key (pk)
Clave pública. Puede compartirse libremente. Usada para encriptar.

### Relinearization
Proceso de reducir un ciphertext de grado 2 a grado 1 después de una multiplicación.

### Rescaling
Operación que reduce la escala y el nivel de un ciphertext después de multiplicaciones.

### RLWE (Ring Learning With Errors)
Variante de LWE sobre anillos de polinomios. Base de la seguridad de CKKS.

### Scale (Δ)
Factor de escala en CKKS. Define la precisión de los números. Típicamente 2^40.

### Secret Key (sk)
Clave secreta. NUNCA se comparte. Solo el propietario puede descifrar.

### SHE (Somewhat Homomorphic Encryption)
Encriptación Algo Homomórfica. Permite ambas operaciones pero con límite.

### SIMD (Single Instruction Multiple Data)
Capacidad de operar sobre múltiples valores en un solo ciphertext simultáneamente.

### Slot
Posición dentro de un ciphertext CKKS que puede contener un valor independiente. Con N=8192, hay 4096 slots.

---

## Términos de Machine Learning

### Activation Function
Función de activación. Introduce no linealidad en redes neuronales (sigmoid, ReLU, tanh).

### Batch
Conjunto de muestras procesadas juntas.

### Bias (b)
Término de sesgo en modelos lineales. Permite desplazar la predicción.

### Cross-Entropy Loss
Función de pérdida para clasificación. Mide diferencia entre probabilidades predichas y reales.

### Decision Tree
Árbol de decisión. Modelo que hace predicciones mediante reglas de decisión.

### Feature
Característica o variable de entrada de un modelo.

### Gradient Descent
Descenso de gradiente. Algoritmo de optimización para entrenar modelos.

### Inference
Inferencia. Proceso de hacer predicciones con un modelo entrenado.

### K-Means
Algoritmo de clustering que agrupa datos en K clusters.

### Learning Rate
Tasa de aprendizaje. Controla el tamaño de los pasos en gradient descent.

### Linear Regression
Regresión lineal. Modelo que predice valores continuos: y = Xw + b.

### Logistic Regression
Regresión logística. Modelo de clasificación binaria: P(y=1) = sigmoid(Xw + b).

### Loss Function
Función de pérdida. Mide el error del modelo.

### MSE (Mean Squared Error)
Error Cuadrático Medio. Métrica común para regresión.

### Normalization
Normalización. Escalar datos a un rango estándar (ej: media 0, desviación 1).

### Overfitting
Sobreajuste. Cuando el modelo memoriza datos de entrenamiento pero no generaliza.

### Polynomial Approximation
Aproximación polinomial. Representar funciones no polinomiales como polinomios para FHE.

### Prediction
Predicción. Salida del modelo para una entrada dada.

### Regularization
Regularización. Técnicas para prevenir overfitting.

### Sigmoid
Función sigmoidea: σ(x) = 1/(1+e^(-x)). Usada en clasificación.

### Softmax
Función que convierte logits en probabilidades sumando 1.

### Training
Entrenamiento. Proceso de ajustar los pesos del modelo con datos.

### Weights (w)
Pesos del modelo. Parámetros aprendidos durante entrenamiento.

---

## Términos de Blockchain

### Arbitrum
Layer 2 de Ethereum con menor costo y mayor velocidad.

### Gas
Unidad de medida del costo computacional en Ethereum/Arbitrum.

### Hash
Función que convierte datos de cualquier tamaño en una huella digital de tamaño fijo.

### Model Registry
Contrato que almacena información de modelos en blockchain.

### Smart Contract
Contrato inteligente. Programa que se ejecuta en blockchain.

### Transaction (tx)
Transacción. Operación registrada en blockchain.

### Verifiable Computation
Computación verificable. Prueba de que un cálculo se ejecutó correctamente.

### Wallet
Billetera. Software que almacena claves privadas para blockchain.

---

## Términos del Sistema

### API (Application Programming Interface)
Interfaz de Programación de Aplicaciones. Permite comunicación entre sistemas.

### CLI (Command Line Interface)
Interfaz de Línea de Comandos.

### Docker
Plataforma de contenedores para desplegar aplicaciones.

### Endpoint
Punto de acceso de una API (ej: /predict).

### FastAPI
Framework Python moderno para crear APIs REST.

### gRPC
Protocolo de comunicación eficiente entre servicios.

### JWT (JSON Web Token)
Estándar para autenticación segura.

### Latency
Latencia. Tiempo de respuesta de una operación.

### REST
Representational State Transfer. Estilo arquitectónico para APIs.

### SDK (Software Development Kit)
Kit de Desarrollo de Software. Herramientas para desarrolladores.

### TenSEAL
Biblioteca Python para FHE, basada en Microsoft SEAL.

### Throughput
Rendimiento. Cantidad de operaciones por unidad de tiempo.

---

## Acrónimos Comunes

| Acrónimo | Significado |
|----------|-------------|
| FHE | Fully Homomorphic Encryption |
| CKKS | Cheon-Kim-Kim-Song |
| HE | Homomorphic Encryption |
| ML | Machine Learning |
| API | Application Programming Interface |
| SDK | Software Development Kit |
| CLI | Command Line Interface |
| LWE | Learning With Errors |
| RLWE | Ring Learning With Errors |
| SIMD | Single Instruction Multiple Data |
| MSE | Mean Squared Error |
| JWT | JSON Web Token |
| REST | Representational State Transfer |
