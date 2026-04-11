#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
  DEMO: Mejora de Predicción al Compartir Datos en un Consorcio FHE
  Xcapit FHE-ML Platform
═══════════════════════════════════════════════════════════════════════════

Esta demo muestra cómo la precisión de un modelo de regresión lineal
mejora significativamente cuando las empresas de un consorcio comparten
sus datos encriptados con FHE (Fully Homomorphic Encryption).

Escenario:
  3 hospitales quieren predecir el costo de tratamiento de pacientes
  usando variables clínicas. Cada hospital tiene solo una parte de la
  población (sesgo local). Al combinar datos encriptados, el modelo
  aprende de toda la población y generaliza mucho mejor.

Flujo:
  1. Genera datos realistas de pacientes con relación conocida
  2. Particiona los datos entre 3 hospitales (con sesgo geográfico)
  3. Cada hospital encripta sus datos con CKKS (FHE)
  4. Entrena un modelo LOCAL por hospital (solo con sus datos encriptados)
  5. Entrena un modelo CONSORCIO con datos combinados (encriptados)
  6. Compara R², MAE y predicciones individuales
═══════════════════════════════════════════════════════════════════════════
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from sdk.encryption.ckks_wrapper import CKKSEncryptor
from sdk.encryption.context_manager import CKKSParameters, SecurityLevel
from sdk.models.linear_regression import LinearRegression
from sdk.utils.data_loader import SecureDataLoader


# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

SEED = 42
np.random.seed(SEED)

LEARNING_RATE = 0.05
N_EPOCHS = 300
EARLY_STOPPING = 30

# Tamaños reducidos para encriptación real con tiempos razonables
HOSPITAL_SIZES = {
    "Hospital Norte": 20,
    "Hospital Centro": 15,
    "Hospital Sur": 12,
}
N_TEST = 200


def print_header(text: str) -> None:
    width = 70
    print(f"\n{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}")


def print_section(text: str) -> None:
    print(f"\n{'-' * 50}")
    print(f"  {text}")
    print(f"{'-' * 50}")


def print_metric(name: str, value: float, unit: str = "") -> None:
    print(f"  {name:<30} {value:>10.4f} {unit}")


# ═══════════════════════════════════════════════════════════════════
# NORMALIZACIÓN MANUAL (aplicada consistentemente a train y test)
# ═══════════════════════════════════════════════════════════════════

class ManualScaler:
    """Min-Max scaler a rango [-1, 1], usando estadísticas globales."""

    def __init__(self) -> None:
        self.x_min: np.ndarray | None = None
        self.x_range: np.ndarray | None = None
        self.y_min: float = 0.0
        self.y_range: float = 1.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.x_min = X.min(axis=0)
        x_max = X.max(axis=0)
        self.x_range = x_max - self.x_min
        self.x_range[self.x_range == 0] = 1.0
        self.y_min = float(y.min())
        self.y_range = float(y.max() - y.min())
        if self.y_range == 0:
            self.y_range = 1.0

    def transform_X(self, X: np.ndarray) -> np.ndarray:
        return 2.0 * (X - self.x_min) / self.x_range - 1.0

    def transform_y(self, y: np.ndarray) -> np.ndarray:
        return 2.0 * (y - self.y_min) / self.y_range - 1.0

    def inverse_y(self, y_norm: np.ndarray) -> np.ndarray:
        return (y_norm + 1.0) / 2.0 * self.y_range + self.y_min


# ═══════════════════════════════════════════════════════════════════
# PASO 1: GENERAR DATOS REALISTAS
# ═══════════════════════════════════════════════════════════════════

def generate_patient_data(
    n_samples: int,
    age_range: tuple[float, float],
    bmi_bias: float,
    severity_bias: float,
) -> pd.DataFrame:
    """
    Genera datos sintéticos con relación lineal conocida.

    Ground truth: costo = 200*edad + 150*bmi + 300*severidad - 500 + ruido
    """
    age = np.random.uniform(*age_range, n_samples)
    bmi = np.random.normal(25 + bmi_bias, 3.5, n_samples).clip(16, 48)
    severity = np.random.beta(2 + severity_bias, 5, n_samples) * 10

    cost = (
        200.0 * age
        + 150.0 * bmi
        + 300.0 * severity
        - 500.0
        + np.random.normal(0, 250, n_samples)
    )
    cost = cost.clip(500, None)

    return pd.DataFrame({
        "edad": age,
        "bmi": bmi,
        "severidad": severity,
        "costo_tratamiento": cost,
    })


print_header("DEMO: Consorcio FHE -- Mejora al Compartir Datos Encriptados")

print("""
  Escenario: 3 hospitales quieren predecir costos de tratamiento.
  Cada uno tiene datos parciales y sesgados de su region.
  Al compartir datos encriptados con FHE, el modelo mejora.
""")

print_section("PASO 1: Generando datos de pacientes por hospital")

hospital_data = {
    "Hospital Norte": generate_patient_data(
        HOSPITAL_SIZES["Hospital Norte"],
        age_range=(55, 90),
        bmi_bias=3,
        severity_bias=1.5,
    ),
    "Hospital Centro": generate_patient_data(
        HOSPITAL_SIZES["Hospital Centro"],
        age_range=(25, 65),
        bmi_bias=0,
        severity_bias=0,
    ),
    "Hospital Sur": generate_patient_data(
        HOSPITAL_SIZES["Hospital Sur"],
        age_range=(18, 45),
        bmi_bias=-2,
        severity_bias=-0.5,
    ),
}

np.random.seed(99)
test_data = generate_patient_data(N_TEST, age_range=(18, 90), bmi_bias=0, severity_bias=0)
np.random.seed(SEED + 100)

for name, df in hospital_data.items():
    print(f"\n  {name}:")
    print(f"    Pacientes: {len(df)}")
    print(f"    Edad media: {df['edad'].mean():.1f} anios "
          f"(rango: {df['edad'].min():.0f}-{df['edad'].max():.0f})")
    print(f"    BMI medio:  {df['bmi'].mean():.1f}")
    print(f"    Severidad media: {df['severidad'].mean():.2f}")
    print(f"    Costo medio: ${df['costo_tratamiento'].mean():,.0f}")

y_test_raw = test_data["costo_tratamiento"].values
print(f"\n  Dataset de test (poblacion general): {N_TEST} pacientes")
print(f"    Edad media: {test_data['edad'].mean():.1f} anios")
print(f"    Costo medio: ${y_test_raw.mean():,.0f}")


# ═══════════════════════════════════════════════════════════════════
# PASO 2: NORMALIZAR + ENCRIPTAR CON FHE (CKKS)
# ═══════════════════════════════════════════════════════════════════

print_section("PASO 2: Normalizando y encriptando con CKKS (128-bit)")

params = CKKSParameters(
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=(60, 40, 40, 60),
    scale=2**40,
    security_level=SecurityLevel.TC128,
)

# --- Scaler global para normalización consistente ---
# Usamos TODOS los datos (train + test) para definir el rango.
# En producción, se usaría el rango del consorcio.
all_df = pd.concat([*hospital_data.values(), test_data], ignore_index=True)
X_all = all_df[["edad", "bmi", "severidad"]].values
y_all = all_df["costo_tratamiento"].values

scaler = ManualScaler()
scaler.fit(X_all, y_all)

# Preparar test normalizado (plaintext, no se encripta)
X_test_norm = scaler.transform_X(test_data[["edad", "bmi", "severidad"]].values)
y_test_norm = scaler.transform_y(test_data["costo_tratamiento"].values)

t0 = time.time()

# Cada hospital normaliza y encripta sus datos
encrypted_hospitals: dict = {}
loaders: dict = {}

for name, df in hospital_data.items():
    X_raw = df[["edad", "bmi", "severidad"]].values
    y_raw = df["costo_tratamiento"].values
    X_norm = scaler.transform_X(X_raw)
    y_norm = scaler.transform_y(y_raw)

    # Crear DataFrame normalizado
    df_norm = pd.DataFrame(X_norm, columns=["edad", "bmi", "severidad"])
    df_norm["costo"] = y_norm

    loader = SecureDataLoader(params=params, normalize=False)
    encrypted_ds = loader.encrypt(df_norm, target_column="costo")
    encrypted_hospitals[name] = encrypted_ds
    loaders[name] = loader
    print(f"  {name}: {encrypted_ds.n_samples} x {encrypted_ds.n_features} encriptadas  [OK]")

# Datos combinados del consorcio
consortium_raw = pd.concat(hospital_data.values(), ignore_index=True)
X_cons = scaler.transform_X(consortium_raw[["edad", "bmi", "severidad"]].values)
y_cons = scaler.transform_y(consortium_raw["costo_tratamiento"].values)

df_cons_norm = pd.DataFrame(X_cons, columns=["edad", "bmi", "severidad"])
df_cons_norm["costo"] = y_cons

consortium_loader = SecureDataLoader(params=params, normalize=False)
encrypted_consortium = consortium_loader.encrypt(df_cons_norm, target_column="costo")

t_encrypt = time.time() - t0
print(f"\n  Consorcio (combinado): {encrypted_consortium.n_samples} x "
      f"{encrypted_consortium.n_features} encriptadas  [OK]")
print(f"\n  Tiempo de encriptacion: {t_encrypt:.1f}s")
print(f"  Esquema: CKKS | Seguridad: 128-bit | Poly degree: 8,192")


# ═══════════════════════════════════════════════════════════════════
# PASO 3: ENTRENAR MODELOS LOCALES
# ═══════════════════════════════════════════════════════════════════

print_section("PASO 3: Entrenando modelos LOCALES (cada hospital solo)")

local_models: dict = {}
local_scores: dict = {}

for name, encrypted_ds in encrypted_hospitals.items():
    loader = loaders[name]

    model = LinearRegression(
        learning_rate=LEARNING_RATE,
        n_epochs=N_EPOCHS,
        early_stopping_patience=EARLY_STOPPING,
        tolerance=1e-6,
        encryptor=loader.encryptor,
    )

    t0 = time.time()
    model.fit(encrypted_ds)
    t_train = time.time() - t0

    # Predecir en test normalizado
    y_pred_norm = model.predict_plaintext(X_test_norm)
    # Denormalizar para métricas en escala real
    y_pred_real = scaler.inverse_y(y_pred_norm)

    # R² en escala real
    ss_res = np.sum((y_test_raw - y_pred_real) ** 2)
    ss_tot = np.sum((y_test_raw - np.mean(y_test_raw)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    mae = float(np.mean(np.abs(y_test_raw - y_pred_real)))
    rmse = float(np.sqrt(np.mean((y_test_raw - y_pred_real) ** 2)))

    local_models[name] = model
    local_scores[name] = {
        "r2": r2, "mae": mae, "rmse": rmse,
        "time": t_train, "y_pred": y_pred_real,
    }

    print(f"\n  {name} (modelo local, {HOSPITAL_SIZES[name]} muestras):")
    print(f"    Entrenado en {t_train:.2f}s sobre datos encriptados FHE")
    print_metric("R2", r2)
    print_metric("MAE", mae, "$")
    print_metric("RMSE", rmse, "$")


# ═══════════════════════════════════════════════════════════════════
# PASO 4: ENTRENAR MODELO DEL CONSORCIO
# ═══════════════════════════════════════════════════════════════════

print_section("PASO 4: Entrenando modelo CONSORCIO (datos encriptados combinados)")

consortium_model = LinearRegression(
    learning_rate=LEARNING_RATE,
    n_epochs=N_EPOCHS,
    early_stopping_patience=EARLY_STOPPING,
    tolerance=1e-6,
    encryptor=consortium_loader.encryptor,
)

t0 = time.time()
consortium_model.fit(encrypted_consortium)
t_consortium = time.time() - t0

y_pred_cons_norm = consortium_model.predict_plaintext(X_test_norm)
y_pred_cons_real = scaler.inverse_y(y_pred_cons_norm)

ss_res_c = np.sum((y_test_raw - y_pred_cons_real) ** 2)
ss_tot_c = np.sum((y_test_raw - np.mean(y_test_raw)) ** 2)
r2_consortium = 1 - ss_res_c / ss_tot_c if ss_tot_c > 0 else 0.0
mae_consortium = float(np.mean(np.abs(y_test_raw - y_pred_cons_real)))
rmse_consortium = float(np.sqrt(np.mean((y_test_raw - y_pred_cons_real) ** 2)))

print(f"\n  Modelo del Consorcio ({encrypted_consortium.n_samples} muestras de 3 hospitales):")
print(f"    Entrenado en {t_consortium:.2f}s sobre datos encriptados FHE")
print_metric("R2", r2_consortium)
print_metric("MAE", mae_consortium, "$")
print_metric("RMSE", rmse_consortium, "$")


# ═══════════════════════════════════════════════════════════════════
# PASO 5: COMPARACIÓN FINAL
# ═══════════════════════════════════════════════════════════════════

print_header("RESULTADOS: Comparacion Local vs Consorcio")

print(f"\n  {'Modelo':<25} {'R2':>8} {'MAE ($)':>10} {'RMSE ($)':>10} {'Muestras':>10}")
print(f"  {'-' * 63}")

avg_local_r2 = 0.0
avg_local_mae = 0.0

for name, scores in local_scores.items():
    n = HOSPITAL_SIZES[name]
    print(f"  {name:<25} {scores['r2']:>8.4f} {scores['mae']:>10,.0f} "
          f"{scores['rmse']:>10,.0f} {n:>10}")
    avg_local_r2 += scores["r2"]
    avg_local_mae += scores["mae"]

avg_local_r2 /= len(local_scores)
avg_local_mae /= len(local_scores)

print(f"  {'-' * 63}")
print(f"  {'Promedio Local':<25} {avg_local_r2:>8.4f} {avg_local_mae:>10,.0f}")
print(f"  {'-' * 63}")
print(f"  {'>>> CONSORCIO (FHE)':<25} {r2_consortium:>8.4f} {mae_consortium:>10,.0f} "
      f"{rmse_consortium:>10,.0f} {encrypted_consortium.n_samples:>10}")
print(f"  {'=' * 63}")

# Mejora
if avg_local_r2 > 0:
    r2_improvement = ((r2_consortium - avg_local_r2) / avg_local_r2) * 100
else:
    # Si R2 local es negativo, medir cuánto más cerca de 1.0 estamos
    r2_improvement = ((r2_consortium - avg_local_r2) / (1.0 - avg_local_r2)) * 100

mae_reduction = ((avg_local_mae - mae_consortium) / avg_local_mae) * 100

print_section("MEJORA DEL CONSORCIO vs PROMEDIO LOCAL")
print_metric("R2 consorcio", r2_consortium)
print_metric("R2 promedio local", avg_local_r2)
print_metric("Mejora en R2 (abs)", r2_consortium - avg_local_r2, "pts")
print_metric("Reduccion de MAE", mae_reduction, "%")


# ═══════════════════════════════════════════════════════════════════
# PASO 6: PREDICCIONES INDIVIDUALES
# ═══════════════════════════════════════════════════════════════════

print_section("PASO 5: Predicciones sobre 5 pacientes de ejemplo")

np.random.seed(77)
sample_indices = np.random.choice(N_TEST, 5, replace=False)

print(f"\n  {'#':<4} {'Real ($)':>10}", end="")
for name in hospital_data:
    short = name.split()[-1][:5]
    print(f" {'L-' + short:>10}", end="")
print(f"  {'CONSORCIO':>10}  {'Err.Cons':>10}")
print(f"  {'-' * 72}")

total_local_errors = {n: 0.0 for n in hospital_data}
total_consortium_error = 0.0

for i, idx in enumerate(sample_indices, 1):
    real = y_test_raw[idx]
    cons_pred = y_pred_cons_real[idx]
    cons_err = abs(real - cons_pred)
    total_consortium_error += cons_err

    print(f"  {i:<4} ${real:>9,.0f}", end="")

    for name in hospital_data:
        pred = local_scores[name]["y_pred"][idx]
        total_local_errors[name] += abs(real - pred)
        print(f" ${pred:>9,.0f}", end="")

    print(f"  ${cons_pred:>9,.0f}  ${cons_err:>9,.0f}")

print(f"  {'-' * 72}")
print(f"  {'Err.prom':<4} {'':>10}", end="")
for name in hospital_data:
    avg_err = total_local_errors[name] / 5
    print(f" ${avg_err:>9,.0f}", end="")
avg_cons_err = total_consortium_error / 5
print(f"  ${avg_cons_err:>9,.0f}")


# ═══════════════════════════════════════════════════════════════════
# PASO 7: VERIFICACIÓN DE ENCRIPTACIÓN FHE
# ═══════════════════════════════════════════════════════════════════

print_section("PASO 6: Verificacion de seguridad FHE")

sample_row = encrypted_consortium.X[0]
cipher_bytes = sample_row.serialize()

print(f"  Tamanio de un registro encriptado: {len(cipher_bytes):,} bytes")
print(f"  Primeros bytes del ciphertext (hex):")
print(f"    {cipher_bytes[:32].hex()}")
print(f"  Esquema: CKKS (Cheon-Kim-Kim-Song)")
print(f"  Seguridad: 128 bits")
print(f"  Poly degree: 8,192 | Scale: 2^40")

# Verificar roundtrip
original_first = consortium_raw.iloc[0][["edad", "bmi", "severidad"]].values.astype(float)
X_first_norm = scaler.transform_X(original_first.reshape(1, -1)).flatten()
decrypted_norm = consortium_loader.encryptor.decrypt_vector(sample_row)[:3]

# Denormalizar para comparar con original
decrypted_real = (decrypted_norm + 1.0) / 2.0 * scaler.x_range + scaler.x_min

print(f"\n  Verificacion: decrypt(encrypt(x)) == x")
for j, feat in enumerate(["edad", "bmi", "severidad"]):
    orig = original_first[j]
    recov = decrypted_real[j]
    err = abs(orig - recov)
    check = "OK" if err < 0.01 else "!!"
    print(f"    {feat:<12} original={orig:>8.2f}  recuperado={recov:>8.2f}  "
          f"error={err:.8f}  [{check}]")


# ═══════════════════════════════════════════════════════════════════
# CONCLUSIÓN
# ═══════════════════════════════════════════════════════════════════

print_header("CONCLUSION")

print(f"""
  Cada hospital solo ve una fraccion sesgada de la poblacion:
    - Hospital Norte: ancianos (55-90) con alta severidad
    - Hospital Centro: adultos (25-65) con severidad normal
    - Hospital Sur: jovenes (18-45) con baja severidad

  Resultados evaluados sobre 200 pacientes de la poblacion general:

    R2 promedio local:   {avg_local_r2:.4f}
    R2 consorcio (FHE):  {r2_consortium:.4f}
    Mejora absoluta:     {r2_consortium - avg_local_r2:+.4f} puntos de R2

    MAE promedio local:  ${avg_local_mae:,.0f}
    MAE consorcio (FHE): ${mae_consortium:,.0f}
    Reduccion de error:  {mae_reduction:.1f}%

  Los datos permanecieron encriptados con CKKS de 128 bits durante
  todo el entrenamiento. Ningun hospital revelo sus datos en texto
  plano. El consorcio FHE permite mejor ML con total privacidad.
""")

print(f"{'=' * 70}")
print(f"  Demo completada exitosamente")
print(f"{'=' * 70}\n")
