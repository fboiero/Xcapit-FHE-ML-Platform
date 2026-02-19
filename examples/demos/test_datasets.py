"""
Xcapit FHE-ML Platform - Generador de Datasets de Testing

Este modulo proporciona datasets sinteticos para testing de:
- SDK de encriptacion FHE
- API REST del backend
- Frontend Dashboard
- Integracion end-to-end

Cada dataset esta disenado para un vertical especifico con datos
realistas pero completamente sinteticos.
"""

import numpy as np
import pandas as pd
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sklearn.datasets import make_classification, make_regression


@dataclass
class DatasetConfig:
    """Configuracion para generacion de datasets."""
    name: str
    vertical: str
    n_samples: int
    features: List[Dict]
    target_column: str
    target_type: str  # 'binary', 'multiclass', 'regression'
    positive_rate: Optional[float] = None
    description: str = ""


# ============================================================================
# FINTECH DATASETS
# ============================================================================

FINTECH_FRAUD_CONFIG = DatasetConfig(
    name="fintech_fraud_transactions",
    vertical="fintech",
    n_samples=10000,
    target_column="is_fraud",
    target_type="binary",
    positive_rate=0.02,
    description="Transacciones bancarias para deteccion de fraude",
    features=[
        {"name": "amount", "type": "float", "min": 10, "max": 10000},
        {"name": "hour", "type": "int", "min": 0, "max": 23},
        {"name": "day_of_week", "type": "int", "min": 0, "max": 6},
        {"name": "merchant_category", "type": "category", "values": ["retail", "food", "travel", "online", "atm"]},
        {"name": "distance_km", "type": "float", "min": 0, "max": 500},
        {"name": "transaction_frequency", "type": "float", "min": 0, "max": 50},
        {"name": "avg_transaction", "type": "float", "min": 50, "max": 2000},
        {"name": "is_international", "type": "bool", "true_ratio": 0.1},
        {"name": "card_age_days", "type": "int", "min": 30, "max": 3650},
        {"name": "failed_attempts_24h", "type": "int", "min": 0, "max": 10},
    ]
)

FINTECH_CREDIT_CONFIG = DatasetConfig(
    name="fintech_credit_scoring",
    vertical="fintech",
    n_samples=5000,
    target_column="default",
    target_type="binary",
    positive_rate=0.08,
    description="Datos de creditos para scoring crediticio",
    features=[
        {"name": "age", "type": "int", "min": 18, "max": 75},
        {"name": "income_monthly", "type": "float", "min": 500, "max": 50000},
        {"name": "employment_years", "type": "float", "min": 0, "max": 40},
        {"name": "debt_to_income", "type": "float", "min": 0, "max": 1},
        {"name": "credit_history_months", "type": "int", "min": 0, "max": 360},
        {"name": "num_open_accounts", "type": "int", "min": 0, "max": 20},
        {"name": "num_late_payments", "type": "int", "min": 0, "max": 24},
        {"name": "credit_utilization", "type": "float", "min": 0, "max": 1},
        {"name": "loan_amount", "type": "float", "min": 1000, "max": 500000},
        {"name": "loan_purpose", "type": "category", "values": ["home", "car", "education", "personal", "business"]},
    ]
)


# ============================================================================
# HEALTHCARE DATASETS
# ============================================================================

HEALTHCARE_DIABETES_CONFIG = DatasetConfig(
    name="healthcare_diabetes_risk",
    vertical="healthcare",
    n_samples=5000,
    target_column="has_diabetes",
    target_type="binary",
    positive_rate=0.15,
    description="Datos clinicos para prediccion de diabetes T2",
    features=[
        {"name": "age", "type": "int", "min": 18, "max": 85},
        {"name": "gender", "type": "category", "values": [0, 1]},
        {"name": "bmi", "type": "float", "min": 15, "max": 50},
        {"name": "blood_pressure_systolic", "type": "int", "min": 80, "max": 200},
        {"name": "blood_pressure_diastolic", "type": "int", "min": 50, "max": 120},
        {"name": "glucose_fasting", "type": "float", "min": 60, "max": 300},
        {"name": "hba1c", "type": "float", "min": 4.0, "max": 14.0},
        {"name": "cholesterol_total", "type": "float", "min": 100, "max": 400},
        {"name": "cholesterol_hdl", "type": "float", "min": 20, "max": 100},
        {"name": "triglycerides", "type": "float", "min": 50, "max": 500},
        {"name": "family_history_diabetes", "type": "bool", "true_ratio": 0.25},
        {"name": "physical_activity_hours", "type": "float", "min": 0, "max": 20},
        {"name": "smoker", "type": "bool", "true_ratio": 0.2},
    ]
)

HEALTHCARE_READMISSION_CONFIG = DatasetConfig(
    name="healthcare_readmission",
    vertical="healthcare",
    n_samples=8000,
    target_column="readmitted_30d",
    target_type="binary",
    positive_rate=0.12,
    description="Datos hospitalarios para prediccion de readmision",
    features=[
        {"name": "age", "type": "int", "min": 18, "max": 95},
        {"name": "length_of_stay_days", "type": "int", "min": 1, "max": 30},
        {"name": "num_procedures", "type": "int", "min": 0, "max": 15},
        {"name": "num_medications", "type": "int", "min": 0, "max": 50},
        {"name": "num_diagnoses", "type": "int", "min": 1, "max": 16},
        {"name": "num_emergency_visits", "type": "int", "min": 0, "max": 10},
        {"name": "num_inpatient_visits", "type": "int", "min": 0, "max": 10},
        {"name": "admission_type", "type": "category", "values": ["emergency", "urgent", "elective"]},
        {"name": "discharge_disposition", "type": "category", "values": ["home", "care_facility", "other"]},
        {"name": "payer_code", "type": "category", "values": ["private", "public", "self_pay"]},
    ]
)


# ============================================================================
# INSURANCE DATASETS
# ============================================================================

INSURANCE_CLAIMS_CONFIG = DatasetConfig(
    name="insurance_claims_fraud",
    vertical="insurance",
    n_samples=15000,
    target_column="is_fraudulent",
    target_type="binary",
    positive_rate=0.05,
    description="Reclamos de seguros para deteccion de fraude",
    features=[
        {"name": "claim_amount", "type": "float", "min": 100, "max": 100000},
        {"name": "policy_age_months", "type": "int", "min": 1, "max": 240},
        {"name": "customer_age", "type": "int", "min": 18, "max": 80},
        {"name": "num_previous_claims", "type": "int", "min": 0, "max": 20},
        {"name": "days_to_report", "type": "int", "min": 0, "max": 365},
        {"name": "claim_type", "type": "category", "values": ["collision", "theft", "injury", "property", "other"]},
        {"name": "policy_type", "type": "category", "values": ["basic", "standard", "premium"]},
        {"name": "region", "type": "category", "values": ["north", "south", "east", "west", "central"]},
        {"name": "witnesses_present", "type": "bool", "true_ratio": 0.3},
        {"name": "police_report", "type": "bool", "true_ratio": 0.6},
    ]
)


# ============================================================================
# GOVERNMENT DATASETS
# ============================================================================

GOVERNMENT_SERVICES_CONFIG = DatasetConfig(
    name="government_service_demand",
    vertical="government",
    n_samples=20000,
    target_column="service_demand_score",
    target_type="regression",
    description="Datos de ciudadanos para prediccion de demanda de servicios",
    features=[
        {"name": "age_group", "type": "category", "values": ["0-17", "18-34", "35-54", "55-64", "65+"]},
        {"name": "household_size", "type": "int", "min": 1, "max": 8},
        {"name": "income_bracket", "type": "category", "values": ["low", "lower_middle", "middle", "upper_middle", "high"]},
        {"name": "education_level", "type": "category", "values": ["none", "primary", "secondary", "tertiary", "university"]},
        {"name": "employment_status", "type": "category", "values": ["employed", "unemployed", "retired", "student", "informal"]},
        {"name": "health_visits", "type": "int", "min": 0, "max": 24},
        {"name": "education_enrollment", "type": "bool", "true_ratio": 0.35},
        {"name": "social_assistance", "type": "bool", "true_ratio": 0.15},
        {"name": "housing_subsidy", "type": "bool", "true_ratio": 0.08},
        {"name": "urban_rural", "type": "category", "values": ["urban", "suburban", "rural"]},
        {"name": "zone_vulnerability_index", "type": "float", "min": 0, "max": 1},
    ]
)


# ============================================================================
# RETAIL DATASETS
# ============================================================================

RETAIL_CHURN_CONFIG = DatasetConfig(
    name="retail_customer_churn",
    vertical="retail",
    n_samples=10000,
    target_column="churned",
    target_type="binary",
    positive_rate=0.18,
    description="Datos de clientes para prediccion de churn",
    features=[
        {"name": "tenure_months", "type": "int", "min": 1, "max": 72},
        {"name": "recency_days", "type": "int", "min": 1, "max": 365},
        {"name": "frequency", "type": "int", "min": 1, "max": 100},
        {"name": "monetary_value", "type": "float", "min": 10, "max": 10000},
        {"name": "avg_order_value", "type": "float", "min": 10, "max": 500},
        {"name": "num_returns", "type": "int", "min": 0, "max": 20},
        {"name": "num_complaints", "type": "int", "min": 0, "max": 10},
        {"name": "channel_preference", "type": "category", "values": ["online", "store", "both"]},
        {"name": "loyalty_program", "type": "bool", "true_ratio": 0.4},
        {"name": "marketing_opt_in", "type": "bool", "true_ratio": 0.6},
    ]
)


# ============================================================================
# GENERATOR FUNCTIONS
# ============================================================================

def generate_feature(feature: Dict, n_samples: int, seed: int = 42) -> np.ndarray:
    """Genera valores para una feature segun su configuracion."""
    np.random.seed(seed)

    ftype = feature["type"]
    name = feature["name"]

    if ftype == "float":
        return np.random.uniform(feature["min"], feature["max"], n_samples).round(2)

    elif ftype == "int":
        return np.random.randint(feature["min"], feature["max"] + 1, n_samples)

    elif ftype == "category":
        return np.random.choice(feature["values"], n_samples)

    elif ftype == "bool":
        return np.random.random(n_samples) < feature.get("true_ratio", 0.5)

    else:
        raise ValueError(f"Unknown feature type: {ftype}")


def generate_dataset(config: DatasetConfig, seed: int = 42) -> pd.DataFrame:
    """
    Genera un dataset sintetico basado en la configuracion.

    Args:
        config: Configuracion del dataset
        seed: Semilla para reproducibilidad

    Returns:
        DataFrame con datos sinteticos
    """
    np.random.seed(seed)
    n = config.n_samples

    # Generar features base con sklearn para correlaciones
    if config.target_type == "binary":
        X_base, y = make_classification(
            n_samples=n,
            n_features=len(config.features),
            n_informative=max(len(config.features) - 2, 3),
            n_redundant=2,
            n_classes=2,
            weights=[1 - config.positive_rate, config.positive_rate],
            random_state=seed
        )
    elif config.target_type == "multiclass":
        X_base, y = make_classification(
            n_samples=n,
            n_features=len(config.features),
            n_informative=max(len(config.features) - 2, 3),
            n_classes=3,
            random_state=seed
        )
    else:  # regression
        X_base, y = make_regression(
            n_samples=n,
            n_features=len(config.features),
            n_informative=max(len(config.features) - 2, 3),
            noise=0.1,
            random_state=seed
        )
        # Normalizar a rango positivo
        y = (y - y.min()) / (y.max() - y.min()) * 10

    # Crear DataFrame
    df = pd.DataFrame()

    # Generar cada feature
    for i, feature in enumerate(config.features):
        # Usar valores de X_base para correlacionar con target
        base_vals = X_base[:, i]

        if feature["type"] == "float":
            min_val = feature["min"]
            max_val = feature["max"]
            # Mapear valores base al rango deseado
            normalized = (base_vals - base_vals.min()) / (base_vals.max() - base_vals.min() + 1e-10)
            df[feature["name"]] = (normalized * (max_val - min_val) + min_val).round(2)

        elif feature["type"] == "int":
            min_val = feature["min"]
            max_val = feature["max"]
            normalized = (base_vals - base_vals.min()) / (base_vals.max() - base_vals.min() + 1e-10)
            df[feature["name"]] = (normalized * (max_val - min_val) + min_val).astype(int)

        elif feature["type"] == "category":
            # Discretizar valores base en categorias
            n_cats = len(feature["values"])
            percentiles = np.percentile(base_vals, np.linspace(0, 100, n_cats + 1)[1:-1])
            indices = np.digitize(base_vals, percentiles)
            df[feature["name"]] = [feature["values"][i] for i in indices]

        elif feature["type"] == "bool":
            threshold = np.percentile(base_vals, 100 * (1 - feature.get("true_ratio", 0.5)))
            df[feature["name"]] = base_vals > threshold

    # Agregar target
    df[config.target_column] = y
    if config.target_type == "binary":
        df[config.target_column] = df[config.target_column].astype(int)
    elif config.target_type == "regression":
        df[config.target_column] = df[config.target_column].round(2)

    # Agregar ID anonimizado
    df["record_id"] = [
        f"REC-{hashlib.sha256(str(i).encode()).hexdigest()[:8].upper()}"
        for i in range(n)
    ]

    # Reordenar columnas
    cols = ["record_id"] + [f["name"] for f in config.features] + [config.target_column]
    df = df[cols]

    return df


def generate_consortium_split(
    df: pd.DataFrame,
    n_members: int = 3,
    member_names: Optional[List[str]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Divide un dataset en partes para simular un consorcio.

    Args:
        df: DataFrame a dividir
        n_members: Numero de miembros del consorcio
        member_names: Nombres opcionales para los miembros

    Returns:
        Diccionario con DataFrames por miembro
    """
    if member_names is None:
        member_names = [f"Member_{i+1}" for i in range(n_members)]

    # Dividir indices aleatoriamente
    indices = np.arange(len(df))
    np.random.shuffle(indices)
    splits = np.array_split(indices, n_members)

    result = {}
    for name, split_indices in zip(member_names, splits):
        result[name] = df.iloc[split_indices].copy().reset_index(drop=True)

    return result


# ============================================================================
# TEST DATA EXPORT
# ============================================================================

def export_all_datasets(output_dir: str = "test_data"):
    """Exporta todos los datasets de testing a archivos CSV."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    configs = [
        FINTECH_FRAUD_CONFIG,
        FINTECH_CREDIT_CONFIG,
        HEALTHCARE_DIABETES_CONFIG,
        HEALTHCARE_READMISSION_CONFIG,
        INSURANCE_CLAIMS_CONFIG,
        GOVERNMENT_SERVICES_CONFIG,
        RETAIL_CHURN_CONFIG,
    ]

    for config in configs:
        print(f"Generating {config.name}...")
        df = generate_dataset(config)

        # Exportar dataset completo
        filepath = os.path.join(output_dir, f"{config.name}.csv")
        df.to_csv(filepath, index=False)
        print(f"  Saved: {filepath} ({len(df)} rows)")

        # Exportar split de consorcio
        if config.vertical == "fintech":
            members = ["Banco Alpha", "Banco Beta", "Banco Gamma"]
        elif config.vertical == "healthcare":
            members = ["Hospital Central", "Clinica Norte", "Hospital Regional"]
        elif config.vertical == "insurance":
            members = ["Seguro A", "Seguro B", "Seguro C"]
        elif config.vertical == "government":
            members = ["Buenos Aires", "Cordoba", "Santa Fe"]
        else:
            members = ["Member A", "Member B", "Member C"]

        splits = generate_consortium_split(df, n_members=3, member_names=members)

        consortium_dir = os.path.join(output_dir, f"{config.name}_consortium")
        os.makedirs(consortium_dir, exist_ok=True)

        for name, split_df in splits.items():
            safe_name = name.replace(" ", "_").lower()
            split_path = os.path.join(consortium_dir, f"{safe_name}.csv")
            split_df.to_csv(split_path, index=False)
            print(f"    {name}: {split_path} ({len(split_df)} rows)")

    print(f"\nAll datasets exported to: {output_dir}/")


def get_sample_data(vertical: str, n_samples: int = 100) -> pd.DataFrame:
    """
    Obtiene una muestra rapida de datos para testing.

    Args:
        vertical: 'fintech', 'healthcare', 'insurance', 'government', 'retail'
        n_samples: Numero de muestras

    Returns:
        DataFrame con datos de muestra
    """
    config_map = {
        "fintech": FINTECH_FRAUD_CONFIG,
        "healthcare": HEALTHCARE_DIABETES_CONFIG,
        "insurance": INSURANCE_CLAIMS_CONFIG,
        "government": GOVERNMENT_SERVICES_CONFIG,
        "retail": RETAIL_CHURN_CONFIG,
    }

    if vertical not in config_map:
        raise ValueError(f"Unknown vertical: {vertical}. Options: {list(config_map.keys())}")

    config = config_map[vertical]
    # Crear copia con menos muestras
    small_config = DatasetConfig(
        name=config.name,
        vertical=config.vertical,
        n_samples=n_samples,
        features=config.features,
        target_column=config.target_column,
        target_type=config.target_type,
        positive_rate=config.positive_rate,
        description=config.description
    )

    return generate_dataset(small_config)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("Xcapit FHE-ML Platform - Test Dataset Generator")
    print("=" * 50)

    # Generar todos los datasets
    export_all_datasets()

    # Mostrar resumen
    print("\nDatasets disponibles por vertical:")
    print("-" * 40)
    print("  fintech:    fraud_transactions, credit_scoring")
    print("  healthcare: diabetes_risk, readmission")
    print("  insurance:  claims_fraud")
    print("  government: service_demand")
    print("  retail:     customer_churn")

    print("\nUso programatico:")
    print("-" * 40)
    print("  from test_datasets import get_sample_data")
    print("  df = get_sample_data('fintech', n_samples=1000)")
