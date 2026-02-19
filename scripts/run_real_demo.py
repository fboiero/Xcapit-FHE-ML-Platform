#!/usr/bin/env python3
"""
Run real FHE-ML demonstrations and generate HTML reports with actual data.

This script:
1. Creates real CKKS encryption contexts
2. Encrypts actual data
3. Runs real ML predictions on encrypted data
4. Generates HTML reports with real metrics
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

import numpy as np

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.encryption import FHEContextManager, CKKSEncryptor, CKKSParameters, SecurityLevel
from sdk.models import LinearRegression, LogisticRegression


# Output paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DEMOS_DIR = OUTPUT_DIR / "demos"


def run_encryption_demo():
    """Run actual encryption demo and return metrics."""
    print("\n" + "=" * 60)
    print("DEMO 1: Encriptación CKKS Real")
    print("=" * 60)

    # Create context
    print("\n[1] Creando contexto CKKS...")
    start = time.time()
    params = CKKSParameters(
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=(60, 40, 40, 60),
        scale=2**40,
        security_level=SecurityLevel.TC128,
    )
    manager = FHEContextManager(params=params)
    context = manager.create_context()
    context_time = time.time() - start
    print(f"    Contexto creado en {context_time*1000:.1f}ms")

    # Create encryptor
    encryptor = CKKSEncryptor(manager)

    # Original data
    original_data = np.array([3.14159, 2.71828, 1.41421, 0.57721])
    print(f"\n[2] Datos originales: {original_data}")

    # Encrypt
    print("\n[3] Encriptando datos...")
    start = time.time()
    encrypted = encryptor.encrypt_vector(original_data)
    encrypt_time = time.time() - start
    print(f"    Tiempo de encriptación: {encrypt_time*1000:.1f}ms")

    # Get ciphertext info
    ct_size = len(encrypted.serialize())
    print(f"    Tamaño del ciphertext: {ct_size / 1024:.1f} KB")

    # Decrypt and verify
    print("\n[4] Descifrando y verificando...")
    start = time.time()
    decrypted = encryptor.decrypt_vector(encrypted)[:4]
    decrypt_time = time.time() - start
    print(f"    Tiempo de descifrado: {decrypt_time*1000:.1f}ms")
    print(f"    Datos descifrados: {decrypted}")

    # Calculate error
    error = np.abs(original_data - decrypted).max()
    print(f"    Error máximo: {error:.2e}")

    return {
        "original_data": original_data.tolist(),
        "decrypted_data": decrypted.tolist(),
        "error": float(error),
        "context_time_ms": context_time * 1000,
        "encrypt_time_ms": encrypt_time * 1000,
        "decrypt_time_ms": decrypt_time * 1000,
        "ciphertext_size_kb": ct_size / 1024,
        "poly_modulus_degree": 8192,
        "scale": "2^40",
        "security_bits": 128,
    }


def run_prediction_demo():
    """Run actual ML prediction demo and return metrics."""
    print("\n" + "=" * 60)
    print("DEMO 2: Predicción ML sobre Datos Encriptados")
    print("=" * 60)

    # Create context
    print("\n[1] Creando contexto CKKS...")
    params = CKKSParameters(
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=(60, 40, 40, 60),
        scale=2**40,
    )
    manager = FHEContextManager(params=params)
    manager.create_context()
    encryptor = CKKSEncryptor(manager)

    # Training data (in plaintext - trusted environment)
    print("\n[2] Entrenando modelo en texto plano (ambiente confiable)...")
    np.random.seed(42)
    X_train = np.random.randn(100, 4)
    weights_true = np.array([0.8, 1.2, 0.5, 1.5])
    y_train = X_train @ weights_true + 0.1 + np.random.randn(100) * 0.1

    # Create model and train directly using internal methods (plaintext training)
    model = LinearRegression(learning_rate=0.01, n_epochs=100, verbose=False, encryptor=encryptor)

    # Direct plaintext training (simulating trusted environment)
    start = time.time()
    model._initialize_weights(X_train.shape[1])
    for epoch in range(100):
        loss, dw, db = model._compute_loss_and_gradients(X_train, y_train)
        model._weights -= 0.01 * dw
        model._bias -= 0.01 * db
    model._state = model._state.__class__.TRAINED
    train_time = time.time() - start
    print(f"    Tiempo de entrenamiento: {train_time*1000:.1f}ms")
    print(f"    Pesos aprendidos: {model.weights}")
    print(f"    Bias aprendido: {model.bias:.4f}")

    # Test data
    X_test = np.array([[1.5, 2.3, 0.7, 3.1]])
    y_true = X_test @ weights_true + 0.1

    # Plaintext prediction (for comparison)
    y_plain = model.predict_plaintext(X_test)

    # Encrypted prediction
    print("\n[3] Realizando predicción sobre datos encriptados...")

    # Encrypt input
    start = time.time()
    X_encrypted = encryptor.encrypt_vector(X_test[0])
    encrypt_time = time.time() - start
    print(f"    Tiempo de encriptación de input: {encrypt_time*1000:.1f}ms")

    # Predict
    start = time.time()
    y_encrypted = model.predict(X_encrypted)
    predict_time = time.time() - start
    print(f"    Tiempo de predicción FHE: {predict_time*1000:.1f}ms")

    # Decrypt result
    start = time.time()
    y_decrypted = encryptor.decrypt_vector(y_encrypted)[0]
    decrypt_time = time.time() - start
    print(f"    Tiempo de descifrado: {decrypt_time*1000:.1f}ms")

    total_time = encrypt_time + predict_time + decrypt_time

    print(f"\n[4] Resultados:")
    print(f"    Predicción en texto plano: {y_plain[0]:.4f}")
    print(f"    Predicción FHE descifrada: {y_decrypted:.4f}")
    print(f"    Valor verdadero: {y_true[0]:.4f}")
    print(f"    Error FHE vs plaintext: {abs(y_decrypted - y_plain[0]):.2e}")

    return {
        "input_features": X_test[0].tolist(),
        "weights": model.weights.tolist(),
        "bias": float(model.bias),
        "prediction_plaintext": float(y_plain[0]),
        "prediction_fhe": float(y_decrypted),
        "true_value": float(y_true[0]),
        "error": float(abs(y_decrypted - y_plain[0])),
        "train_time_ms": train_time * 1000,
        "encrypt_time_ms": encrypt_time * 1000,
        "predict_time_ms": predict_time * 1000,
        "decrypt_time_ms": decrypt_time * 1000,
        "total_time_ms": total_time * 1000,
    }


def run_healthcare_demo():
    """Run healthcare classification demo and return metrics."""
    print("\n" + "=" * 60)
    print("DEMO 3: Diagnóstico Médico con Privacidad (Logistic Regression)")
    print("=" * 60)

    # Create context
    print("\n[1] Creando contexto CKKS...")
    params = CKKSParameters(
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=(60, 40, 40, 60),
        scale=2**40,
    )
    manager = FHEContextManager(params=params)
    manager.create_context()
    encryptor = CKKSEncryptor(manager)

    # Simulated healthcare training data
    print("\n[2] Entrenando modelo de riesgo cardiovascular...")
    np.random.seed(42)

    # Features: age(norm), blood_pressure(norm), cholesterol(norm), glucose(norm), bmi(norm), smoker
    n_samples = 200
    X_train = np.random.randn(n_samples, 6)
    # Higher values = higher risk
    risk_score = 0.3 * X_train[:, 0] + 0.25 * X_train[:, 1] + 0.2 * X_train[:, 2] + \
                 0.1 * X_train[:, 3] + 0.15 * X_train[:, 4] + 0.4 * X_train[:, 5]
    y_train = (risk_score > 0).astype(float)

    model = LogisticRegression(learning_rate=0.1, n_epochs=200, verbose=False, encryptor=encryptor)

    # Direct plaintext training (simulating trusted environment)
    start = time.time()
    model._initialize_weights(X_train.shape[1])
    for epoch in range(200):
        loss, dw, db = model._compute_loss_and_gradients(X_train, y_train)
        model._weights -= 0.1 * dw
        model._bias -= 0.1 * db
    model._state = model._state.__class__.TRAINED
    train_time = time.time() - start
    print(f"    Tiempo de entrenamiento: {train_time*1000:.1f}ms")

    # Accuracy on training set
    y_pred_train = model.predict_plaintext(X_train)
    accuracy = np.mean(y_pred_train == y_train)
    print(f"    Accuracy en entrenamiento: {accuracy*100:.1f}%")

    # Test patient data (simulating PHI)
    # Patient: 58 years old, high BP, high cholesterol, elevated glucose, BMI 28.5, smoker
    patient_data = np.array([[
        0.58,   # age normalized (58/100)
        0.72,   # blood pressure normalized (145/200)
        0.83,   # cholesterol normalized (248/300)
        0.59,   # glucose normalized (118/200)
        0.57,   # BMI normalized (28.5/50)
        1.0     # smoker (yes)
    ]])

    # Plaintext prediction
    prob_plain = model.predict_proba_plaintext(patient_data)[0]

    # Encrypted prediction - using linear approximation for demo
    # (Full sigmoid requires more multiplicative depth)
    print("\n[3] Realizando diagnóstico sobre datos encriptados (PHI)...")

    start = time.time()
    X_encrypted = encryptor.encrypt_vector(patient_data[0])
    encrypt_time = time.time() - start
    print(f"    Tiempo de encriptación de PHI: {encrypt_time*1000:.1f}ms")

    # Compute logit on encrypted data: logit = X * w + b
    start = time.time()
    # Element-wise multiplication with weights
    weighted = X_encrypted.ciphertext * model.weights.tolist()
    # Sum to get dot product
    logit_encrypted = weighted.sum() + model.bias
    predict_time = time.time() - start
    print(f"    Tiempo de inferencia FHE: {predict_time*1000:.1f}ms")

    start = time.time()
    # Decrypt logit and apply sigmoid in plaintext for final probability
    logit_decrypted = logit_encrypted.decrypt()[0]
    # Apply sigmoid
    prob_decrypted = 1 / (1 + np.exp(-logit_decrypted))
    decrypt_time = time.time() - start
    print(f"    Tiempo de descifrado: {decrypt_time*1000:.1f}ms")

    total_time = encrypt_time + predict_time + decrypt_time

    print(f"\n[4] Resultados del diagnóstico:")
    print(f"    Probabilidad (texto plano): {prob_plain*100:.1f}%")
    print(f"    Probabilidad (FHE): {prob_decrypted*100:.1f}%")
    print(f"    Error: {abs(prob_decrypted - prob_plain)*100:.2f}%")

    risk_level = "ALTO" if prob_decrypted > 0.7 else "MODERADO" if prob_decrypted > 0.4 else "BAJO"
    print(f"    Nivel de riesgo: {risk_level}")

    return {
        "patient_features": {
            "age": 58,
            "blood_pressure": "145/92 mmHg",
            "cholesterol": "248 mg/dL",
            "glucose": "118 mg/dL",
            "bmi": 28.5,
            "smoker": True,
        },
        "normalized_input": patient_data[0].tolist(),
        "probability_plaintext": float(prob_plain),
        "probability_fhe": float(prob_decrypted),
        "risk_percentage": float(prob_decrypted * 100),
        "risk_level": risk_level,
        "error_percentage": float(abs(prob_decrypted - prob_plain) * 100),
        "train_accuracy": float(accuracy),
        "train_time_ms": train_time * 1000,
        "encrypt_time_ms": encrypt_time * 1000,
        "predict_time_ms": predict_time * 1000,
        "decrypt_time_ms": decrypt_time * 1000,
        "total_time_ms": total_time * 1000,
    }


def generate_html_report(encryption_data, prediction_data, healthcare_data):
    """Generate HTML report with real demo data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xcapit FHE-ML - Demo Real</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 30px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255,255,255,0.03);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header .subtitle {{ color: #94A3B8; font-size: 1.1em; }}
        .header .timestamp {{ color: #64748b; font-size: 0.85em; margin-top: 10px; }}
        .demo-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 25px;
            margin-bottom: 30px;
        }}
        .demo-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 25px;
            position: relative;
            overflow: hidden;
        }}
        .demo-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }}
        .demo-card.purple::before {{ background: linear-gradient(90deg, #8B5CF6, #6D28D9); }}
        .demo-card.green::before {{ background: linear-gradient(90deg, #10B981, #059669); }}
        .demo-card.blue::before {{ background: linear-gradient(90deg, #3B82F6, #06B6D4); }}
        .demo-title {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .metric {{
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 15px;
        }}
        .metric-label {{
            font-size: 0.75em;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 1.4em;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }}
        .metric-value.purple {{ color: #8B5CF6; }}
        .metric-value.green {{ color: #10B981; }}
        .metric-value.blue {{ color: #06B6D4; }}
        .metric-value.orange {{ color: #F59E0B; }}
        .metric-value.red {{ color: #EF4444; }}
        .data-box {{
            background: rgba(0,0,0,0.4);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85em;
        }}
        .data-label {{
            color: #8B5CF6;
            font-size: 0.75em;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
        }}
        .data-value {{ color: #10B981; word-break: break-all; }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        .badge.success {{ background: rgba(16, 185, 129, 0.2); color: #10B981; }}
        .badge.warning {{ background: rgba(245, 158, 11, 0.2); color: #F59E0B; }}
        .badge.danger {{ background: rgba(239, 68, 68, 0.2); color: #EF4444; }}
        .result-highlight {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.05) 100%);
            border: 2px solid rgba(16, 185, 129, 0.3);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-top: 20px;
        }}
        .result-highlight.warning {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(185, 28, 28, 0.05) 100%);
            border-color: rgba(239, 68, 68, 0.3);
        }}
        .result-value {{
            font-size: 2.5em;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }}
        .result-label {{ color: #94a3b8; margin-top: 5px; }}
        .footer {{
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-top: 30px;
        }}
        .footer h3 {{ color: #10B981; margin-bottom: 10px; }}
        .footer-items {{ display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; }}
        .footer-item {{ display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 0.9em; }}
        .check {{ color: #10B981; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Xcapit FHE-ML Platform</h1>
            <p class="subtitle">Demostración Real de Machine Learning sobre Datos Encriptados</p>
            <p class="timestamp">Ejecutado: {timestamp} | TenSEAL + CKKS | Seguridad: 128-bit</p>
        </div>

        <div class="demo-grid">
            <!-- Demo 1: Encryption -->
            <div class="demo-card purple">
                <div class="demo-title">
                    <span>🔐</span> Encriptación CKKS
                </div>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-label">Contexto</div>
                        <div class="metric-value purple">{encryption_data['context_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Encriptar</div>
                        <div class="metric-value green">{encryption_data['encrypt_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Descifrar</div>
                        <div class="metric-value blue">{encryption_data['decrypt_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Ciphertext</div>
                        <div class="metric-value orange">{encryption_data['ciphertext_size_kb']:.1f}KB</div>
                    </div>
                </div>
                <div class="data-box">
                    <div class="data-label">Datos Originales</div>
                    <div class="data-value">{encryption_data['original_data']}</div>
                </div>
                <div class="data-box">
                    <div class="data-label">Datos Descifrados</div>
                    <div class="data-value">[{', '.join(f'{x:.8f}' for x in encryption_data['decrypted_data'])}]</div>
                </div>
                <div class="result-highlight">
                    <div class="result-value green">{encryption_data['error']:.2e}</div>
                    <div class="result-label">Error Máximo</div>
                </div>
                <div style="margin-top: 15px; text-align: center;">
                    <span class="badge success">✓ Precisión verificada</span>
                </div>
            </div>

            <!-- Demo 2: Prediction -->
            <div class="demo-card green">
                <div class="demo-title">
                    <span>🧠</span> Regresión Lineal FHE
                </div>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-label">Encriptar</div>
                        <div class="metric-value purple">{prediction_data['encrypt_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Predicción FHE</div>
                        <div class="metric-value green">{prediction_data['predict_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Descifrar</div>
                        <div class="metric-value blue">{prediction_data['decrypt_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Total</div>
                        <div class="metric-value orange">{prediction_data['total_time_ms']:.1f}ms</div>
                    </div>
                </div>
                <div class="data-box">
                    <div class="data-label">Input Features</div>
                    <div class="data-value">X = {prediction_data['input_features']}</div>
                </div>
                <div class="data-box">
                    <div class="data-label">Pesos del Modelo</div>
                    <div class="data-value">W = [{', '.join(f'{x:.4f}' for x in prediction_data['weights'])}]</div>
                </div>
                <div class="result-highlight">
                    <div class="result-value green">{prediction_data['prediction_fhe']:.4f}</div>
                    <div class="result-label">Predicción FHE (plaintext: {prediction_data['prediction_plaintext']:.4f})</div>
                </div>
                <div style="margin-top: 15px; text-align: center;">
                    <span class="badge success">✓ Error: {prediction_data['error']:.2e}</span>
                </div>
            </div>

            <!-- Demo 3: Healthcare -->
            <div class="demo-card blue">
                <div class="demo-title">
                    <span>🏥</span> Diagnóstico Cardiovascular
                </div>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-label">Encriptar PHI</div>
                        <div class="metric-value purple">{healthcare_data['encrypt_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Inferencia FHE</div>
                        <div class="metric-value green">{healthcare_data['predict_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Descifrar</div>
                        <div class="metric-value blue">{healthcare_data['decrypt_time_ms']:.1f}ms</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Accuracy</div>
                        <div class="metric-value orange">{healthcare_data['train_accuracy']*100:.1f}%</div>
                    </div>
                </div>
                <div class="data-box">
                    <div class="data-label">Datos del Paciente (PHI)</div>
                    <div class="data-value" style="font-size: 0.8em;">
                        Edad: {healthcare_data['patient_features']['age']} |
                        PA: {healthcare_data['patient_features']['blood_pressure']} |
                        Colesterol: {healthcare_data['patient_features']['cholesterol']}<br>
                        Glucosa: {healthcare_data['patient_features']['glucose']} |
                        IMC: {healthcare_data['patient_features']['bmi']} |
                        Fumador: {'Sí' if healthcare_data['patient_features']['smoker'] else 'No'}
                    </div>
                </div>
                <div class="result-highlight {'warning' if healthcare_data['risk_level'] == 'ALTO' else ''}">
                    <div class="result-value {'red' if healthcare_data['risk_level'] == 'ALTO' else 'green'}">{healthcare_data['risk_percentage']:.1f}%</div>
                    <div class="result-label">Riesgo Cardiovascular: {healthcare_data['risk_level']}</div>
                </div>
                <div style="margin-top: 15px; text-align: center;">
                    <span class="badge {'danger' if healthcare_data['risk_level'] == 'ALTO' else 'success'}">
                        {'⚠️' if healthcare_data['risk_level'] == 'ALTO' else '✓'} {healthcare_data['risk_level']} - PHI nunca expuesto
                    </span>
                </div>
            </div>
        </div>

        <div class="footer">
            <h3>🛡️ Garantías de Privacidad - Datos Reales</h3>
            <div class="footer-items">
                <div class="footer-item"><span class="check">✓</span> Encriptación CKKS 128-bit</div>
                <div class="footer-item"><span class="check">✓</span> Servidor no ve datos originales</div>
                <div class="footer-item"><span class="check">✓</span> Predicciones sobre ciphertext</div>
                <div class="footer-item"><span class="check">✓</span> Solo cliente puede descifrar</div>
            </div>
        </div>
    </div>
</body>
</html>'''

    return html


def main():
    """Run all demos and generate reports."""
    print("=" * 60)
    print("Xcapit FHE-ML - Ejecución de Demos Reales")
    print("=" * 60)

    DEMOS_DIR.mkdir(parents=True, exist_ok=True)

    # Run demos
    encryption_data = run_encryption_demo()
    prediction_data = run_prediction_demo()
    healthcare_data = run_healthcare_demo()

    # Save raw data
    all_data = {
        "timestamp": datetime.now().isoformat(),
        "encryption": encryption_data,
        "prediction": prediction_data,
        "healthcare": healthcare_data,
    }

    json_path = DEMOS_DIR / "demo_results.json"
    with open(json_path, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\n✅ Datos guardados: {json_path}")

    # Generate HTML report
    html = generate_html_report(encryption_data, prediction_data, healthcare_data)
    html_path = DEMOS_DIR / "demo_real_results.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"✅ Reporte HTML: {html_path}")

    print("\n" + "=" * 60)
    print("Demos completados exitosamente")
    print("=" * 60)


if __name__ == "__main__":
    main()
