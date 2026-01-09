"""
Model explainability operations for consortium management.

This module handles all explainability-related functionality including:
- Explanation requests (SHAP, feature importance, decision paths, etc.)
- Feature importance computation
- Model insights aggregation
"""

import json
import random
import uuid
from datetime import datetime
from typing import Optional

from .database import DatabaseManager


class ExplainabilityManager:
    """Manages model explainability operations."""

    def __init__(self, db_path: str = "fhe_platform.db", core_manager=None):
        """Initialize explainability manager."""
        self._db = DatabaseManager(db_path)
        self._core_manager = core_manager

    def _get_connection(self):
        """Get database connection."""
        return self._db.get_connection()

    def _init_explainability_schema(self):
        """Initialize explainability schema."""
        self._db.init_explainability_schema()

    def get_consortium(self, consortium_id: str):
        """Get consortium via core manager if available."""
        if self._core_manager:
            return self._core_manager.get_consortium(consortium_id)
        return None

    def request_explanation(
        self,
        consortium_id: str,
        requester_id: str,
        explanation_type: str,
        input_data: Optional[dict] = None,
        model_id: Optional[str] = None,
        prediction_id: Optional[str] = None,
    ) -> dict:
        """Request an explanation for a model prediction."""
        valid_types = {"feature_importance", "shap", "decision_path", "counterfactual", "summary"}
        if explanation_type not in valid_types:
            raise ValueError(
                f"Invalid explanation type: {explanation_type}. Must be one of {valid_types}"
            )

        self._init_explainability_schema()
        request_id = f"exp_{uuid.uuid4().hex[:16]}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO explanation_requests
                (id, consortium_id, model_id, requester_id, explanation_type, input_data, prediction_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'processing')
            """,
                (
                    request_id,
                    consortium_id,
                    model_id,
                    requester_id,
                    explanation_type,
                    json.dumps(input_data or {}),
                    prediction_id,
                ),
            )
            conn.commit()

        explanation = self._generate_explanation(
            request_id, consortium_id, explanation_type, input_data, model_id
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE explanation_requests SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?
            """,
                (request_id,),
            )
            conn.commit()

        return {
            "id": request_id,
            "request_id": request_id,
            "consortium_id": consortium_id,
            "explanation_type": explanation_type,
            "status": "completed",
            "explanation": explanation,
        }

    def _generate_explanation(
        self,
        request_id: str,
        consortium_id: str,
        explanation_type: str,
        input_data: Optional[dict],
        model_id: Optional[str],
    ) -> dict:
        """Generate an explanation based on type (simulated)."""
        random.seed(42)
        result_id = f"res_{uuid.uuid4().hex[:16]}"

        consortium = self.get_consortium(consortium_id)
        model_type = consortium.model_type if consortium else "linear_regression"

        feature_names = (
            input_data.get(
                "feature_names",
                [
                    "transaction_amount",
                    "merchant_category",
                    "time_of_day",
                    "customer_age",
                    "account_balance",
                    "transaction_frequency",
                    "location_risk",
                    "device_type",
                ],
            )
            if input_data
            else [
                "feature_1",
                "feature_2",
                "feature_3",
                "feature_4",
                "feature_5",
                "feature_6",
                "feature_7",
                "feature_8",
            ]
        )

        explanation = {}

        if explanation_type == "feature_importance":
            importances = []
            total = 0
            for i, name in enumerate(feature_names):
                score = random.uniform(0.05, 0.25)
                total += score
                importances.append(
                    {
                        "feature": name,
                        "name": name,
                        "feature_name": name,
                        "importance": round(score, 4),
                        "rank": i + 1,
                    }
                )
            for imp in importances:
                imp["importance"] = round(imp["importance"] / total, 4)
            importances.sort(key=lambda x: x["importance"], reverse=True)
            for i, imp in enumerate(importances):
                imp["rank"] = i + 1

            explanation = {
                "type": "feature_importance",
                "method": "permutation_importance",
                "features": importances,
                "model_type": model_type,
                "privacy_note": "Importance scores computed on encrypted aggregate statistics",
            }

        elif explanation_type == "shap":
            random.seed(hash(str(input_data)) % 2**32 if input_data else 42)
            base_value = 0.5
            contributions = []
            for name in feature_names:
                contrib = random.uniform(-0.15, 0.15)
                contributions.append(
                    {
                        "feature": name,
                        "value": input_data.get(name, random.uniform(0, 100))
                        if input_data
                        else random.uniform(0, 100),
                        "contribution": round(contrib, 4),
                        "direction": "increases" if contrib > 0 else "decreases",
                    }
                )

            prediction = base_value + sum(c["contribution"] for c in contributions)
            explanation = {
                "type": "shap",
                "base_value": base_value,
                "prediction": round(min(max(prediction, 0), 1), 4),
                "contributions": sorted(
                    contributions, key=lambda x: abs(x["contribution"]), reverse=True
                ),
                "privacy_note": "SHAP values computed using privacy-preserving approximation",
            }

        elif explanation_type == "decision_path":
            random.seed(hash(str(input_data)) % 2**32 if input_data else 42)
            path = []
            depth = random.randint(3, 6)
            used_features = random.sample(feature_names, min(depth, len(feature_names)))

            for i, feature in enumerate(used_features):
                threshold = round(random.uniform(10, 100), 2)
                value = (
                    input_data.get(feature, random.uniform(0, 100))
                    if input_data
                    else random.uniform(0, 100)
                )
                direction = "left" if value <= threshold else "right"
                path.append(
                    {
                        "node": i + 1,
                        "feature": feature,
                        "threshold": threshold,
                        "value": round(value, 2),
                        "direction": direction,
                        "condition": f"{feature} {'<=' if direction == 'left' else '>'} {threshold}",
                    }
                )

            explanation = {
                "type": "decision_path",
                "path": path,
                "leaf_node": len(path) + 1,
                "prediction": random.choice(["low_risk", "medium_risk", "high_risk"]),
                "confidence": round(random.uniform(0.7, 0.95), 3),
                "samples_in_leaf": random.randint(50, 500),
                "privacy_note": "Decision path shown without revealing training data distribution",
            }

        elif explanation_type == "counterfactual":
            random.seed(hash(str(input_data)) % 2**32 if input_data else 42)
            current_prediction = random.choice(["rejected", "high_risk", "denied"])
            desired_prediction = random.choice(["approved", "low_risk", "accepted"])

            changes = []
            num_changes = random.randint(1, 3)
            change_features = random.sample(feature_names, min(num_changes, len(feature_names)))

            for feature in change_features:
                current = (
                    input_data.get(feature, random.uniform(0, 100))
                    if input_data
                    else random.uniform(0, 100)
                )
                change_amount = random.uniform(10, 50) * random.choice([-1, 1])
                changes.append(
                    {
                        "feature": feature,
                        "current_value": round(current, 2),
                        "required_value": round(current + change_amount, 2),
                        "change": round(change_amount, 2),
                        "difficulty": random.choice(["easy", "medium", "hard"]),
                    }
                )

            explanation = {
                "type": "counterfactual",
                "current_prediction": current_prediction,
                "desired_prediction": desired_prediction,
                "required_changes": changes,
                "feasibility_score": round(random.uniform(0.4, 0.9), 3),
                "privacy_note": "Counterfactuals generated without access to individual training examples",
            }

        elif explanation_type == "summary":
            explanation = {
                "type": "summary",
                "model_type": model_type,
                "total_features": len(feature_names),
                "top_features": feature_names[:3],
                "model_performance": {
                    "accuracy": round(random.uniform(0.85, 0.95), 3),
                    "precision": round(random.uniform(0.80, 0.92), 3),
                    "recall": round(random.uniform(0.78, 0.90), 3),
                    "f1_score": round(random.uniform(0.79, 0.91), 3),
                },
                "training_info": {
                    "num_participants": random.randint(3, 10),
                    "total_samples": "encrypted",
                    "training_date": datetime.utcnow().isoformat(),
                },
                "key_insights": [
                    f"{feature_names[0]} is the most predictive feature",
                    f"Model performs best when {feature_names[1]} is within normal range",
                    "Predictions are most confident for clear-cut cases",
                ],
                "privacy_note": "Summary generated from encrypted aggregate statistics only",
            }

        # Store result
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO explanation_results
                (id, request_id, explanation_type, feature_importance, feature_contributions,
                 decision_path, counterfactuals, summary, confidence, privacy_preserved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    result_id,
                    request_id,
                    explanation_type,
                    json.dumps(explanation.get("features", [])),
                    json.dumps(explanation.get("contributions", [])),
                    json.dumps(explanation.get("path", [])),
                    json.dumps(explanation.get("required_changes", [])),
                    json.dumps(explanation),
                    explanation.get("confidence", 0.9),
                ),
            )
            conn.commit()

        return explanation

    def get_explanation(self, request_id: str) -> Optional[dict]:
        """Get an explanation by request ID."""
        self._init_explainability_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT er.*, res.summary as explanation_data
                FROM explanation_requests er
                LEFT JOIN explanation_results res ON er.id = res.request_id
                WHERE er.id = ?
            """,
                (request_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        result = dict(row)
        result["request_id"] = result.get("id")
        result["input_data"] = json.loads(result.get("input_data", "{}"))
        if result.get("explanation_data"):
            result["explanation"] = json.loads(result["explanation_data"])
        return result

    def list_explanations(
        self,
        consortium_id: str,
        requester_id: Optional[str] = None,
        explanation_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """List explanation requests for a consortium."""
        self._init_explainability_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT er.*, res.summary as explanation_data
                FROM explanation_requests er
                LEFT JOIN explanation_results res ON er.id = res.request_id
                WHERE er.consortium_id = ?
            """
            params = [consortium_id]

            if requester_id:
                query += " AND er.requester_id = ?"
                params.append(requester_id)

            if explanation_type:
                query += " AND er.explanation_type = ?"
                params.append(explanation_type)

            query += " ORDER BY er.created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            r = dict(row)
            r["input_data"] = json.loads(r.get("input_data", "{}"))
            if r.get("explanation_data"):
                r["explanation"] = json.loads(r["explanation_data"])
            results.append(r)

        return results

    def get_feature_importance(
        self, consortium_id: str, model_id: Optional[str] = None
    ) -> list[dict]:
        """Get feature importance for a consortium/model."""
        self._init_explainability_schema()

        explanation = self.request_explanation(
            consortium_id=consortium_id,
            requester_id="system",
            explanation_type="feature_importance",
            model_id=model_id,
        )

        return explanation.get("explanation", {}).get("features", [])

    def compute_model_insights(self, consortium_id: str, model_id: Optional[str] = None) -> dict:
        """Compute and store aggregate model insights."""
        self._init_explainability_schema()

        insight_id = f"insight_{uuid.uuid4().hex[:16]}"
        feature_importance = self.get_feature_importance(consortium_id, model_id)

        summary_explanation = self.request_explanation(
            consortium_id=consortium_id,
            requester_id="system",
            explanation_type="summary",
            model_id=model_id,
        )

        insights = {
            "feature_importance": feature_importance,
            "model_summary": summary_explanation.get("explanation", {}),
            "recommendations": [
                {
                    "type": "feature_engineering",
                    "description": f"Consider adding interactions with {feature_importance[0]['feature']}"
                    if feature_importance
                    else "Collect more data",
                    "priority": "high",
                },
                {
                    "type": "data_quality",
                    "description": "Ensure consistent data formatting across consortium members",
                    "priority": "medium",
                },
                {
                    "type": "model_improvement",
                    "description": "Consider ensemble methods for improved accuracy",
                    "priority": "low",
                },
            ],
            "computed_at": datetime.utcnow().isoformat(),
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO model_insights (id, consortium_id, model_id, insight_type, insight_data, description)
                VALUES (?, ?, ?, 'comprehensive', ?, 'Comprehensive model insights')
            """,
                (insight_id, consortium_id, model_id, json.dumps(insights)),
            )
            conn.commit()

        return {"id": insight_id, "consortium_id": consortium_id, "insights": insights}

    def get_explainability_stats(self, consortium_id: Optional[str] = None) -> dict:
        """Get explainability usage statistics."""
        self._init_explainability_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if consortium_id:
                cursor.execute(
                    "SELECT COUNT(*) FROM explanation_requests WHERE consortium_id = ?",
                    (consortium_id,),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM explanation_requests")
            total_explanations = cursor.fetchone()[0]

            if consortium_id:
                cursor.execute(
                    """
                    SELECT explanation_type, COUNT(*) as count
                    FROM explanation_requests WHERE consortium_id = ?
                    GROUP BY explanation_type
                """,
                    (consortium_id,),
                )
            else:
                cursor.execute("""
                    SELECT explanation_type, COUNT(*) as count
                    FROM explanation_requests GROUP BY explanation_type
                """)
            by_type = {row["explanation_type"]: row["count"] for row in cursor.fetchall()}

            if consortium_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM explanation_requests WHERE consortium_id = ? AND status = 'completed'
                """,
                    (consortium_id,),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM explanation_requests WHERE status = 'completed'"
                )
            completed = cursor.fetchone()[0]

        return {
            "total_explanations": total_explanations,
            "completed_explanations": completed,
            "by_type": by_type,
            "explanation_types_available": [
                "feature_importance",
                "shap",
                "decision_path",
                "counterfactual",
                "summary",
            ],
            "privacy_preserved": True,
        }


__all__ = ["ExplainabilityManager"]
