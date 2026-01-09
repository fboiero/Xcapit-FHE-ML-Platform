"""
Marketplace operations for consortium management.

This module handles all marketplace-related functionality including:
- Model categories management
- Model listings and search
- Model deployments
- Model reviews and ratings
- Marketplace statistics
"""

import json
import secrets
from datetime import datetime
from typing import Optional

from .database import DatabaseManager


class MarketplaceManager:
    """Manages marketplace operations for pre-trained models."""

    def __init__(self, db_path: str = "fhe_platform.db"):
        """Initialize marketplace manager.

        Args:
            db_path: Path to SQLite database.
        """
        self._db = DatabaseManager(db_path)

    def _get_connection(self):
        """Get database connection."""
        return self._db.get_connection()

    def _init_marketplace_schema(self):
        """Initialize marketplace schema."""
        self._db.init_marketplace_schema()

    def get_marketplace_categories(self) -> list[dict]:
        """Get all marketplace categories."""
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, COUNT(m.id) as model_count
                FROM model_categories c
                LEFT JOIN marketplace_models m ON m.industry = c.id AND m.is_active = 1
                GROUP BY c.id
                ORDER BY c.display_order
            """)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_marketplace_models(
        self,
        industry: Optional[str] = None,
        model_type: Optional[str] = None,
        featured_only: bool = False,
        search: Optional[str] = None,
        sort_by: str = "downloads",
        limit: int = 50,
    ) -> list[dict]:
        """Get marketplace models with optional filters.

        Args:
            industry: Filter by industry/category.
            model_type: Filter by model type.
            featured_only: Only return featured models.
            search: Search term for name/description.
            sort_by: Sort field (downloads, rating, newest, accuracy).
            limit: Maximum number of results.

        Returns:
            List of marketplace models.
        """
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM marketplace_models WHERE is_active = 1"
            params = []

            if industry:
                query += " AND industry = ?"
                params.append(industry)

            if model_type:
                query += " AND model_type = ?"
                params.append(model_type)

            if featured_only:
                query += " AND is_featured = 1"

            if search:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            # Sorting
            sort_options = {
                "downloads": "downloads DESC",
                "rating": "rating DESC",
                "newest": "created_at DESC",
                "accuracy": "accuracy DESC",
            }
            query += f" ORDER BY {sort_options.get(sort_by, 'downloads DESC')}"
            query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        models = []
        for row in rows:
            model = dict(row)
            model["features"] = json.loads(model["features"])
            model["use_cases"] = json.loads(model["use_cases"])
            model["metadata"] = json.loads(model["metadata"])
            models.append(model)

        return models

    def get_marketplace_model(self, model_id: str) -> Optional[dict]:
        """Get a specific marketplace model by ID.

        Args:
            model_id: Model ID.

        Returns:
            Model data or None if not found.
        """
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM marketplace_models WHERE id = ?", (model_id,))
            row = cursor.fetchone()

        if not row:
            return None

        model = dict(row)
        model["features"] = json.loads(model["features"])
        model["use_cases"] = json.loads(model["use_cases"])
        model["metadata"] = json.loads(model["metadata"])
        return model

    def deploy_marketplace_model(
        self, model_id: str, consortium_id: str, deployed_by: str, config: Optional[dict] = None
    ) -> dict:
        """Deploy a marketplace model to a consortium.

        Args:
            model_id: Model ID to deploy.
            consortium_id: Target consortium ID.
            deployed_by: Company ID deploying the model.
            config: Optional deployment configuration.

        Returns:
            Deployment result.
        """
        self._init_marketplace_schema()

        # Verify model exists
        model = self.get_marketplace_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        deployment_id = f"deploy_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check for existing deployment
            cursor.execute(
                """
                SELECT id FROM model_deployments
                WHERE model_id = ? AND consortium_id = ? AND status = 'active'
            """,
                (model_id, consortium_id),
            )

            existing = cursor.fetchone()
            if existing:
                return {
                    "id": existing["id"],
                    "model_id": model_id,
                    "consortium_id": consortium_id,
                    "status": "already_deployed",
                    "message": "Model already deployed to this consortium",
                }

            # Create deployment
            cursor.execute(
                """
                INSERT INTO model_deployments
                (id, model_id, consortium_id, deployed_by, config)
                VALUES (?, ?, ?, ?, ?)
            """,
                (deployment_id, model_id, consortium_id, deployed_by, json.dumps(config or {})),
            )

            # Increment downloads
            cursor.execute(
                """
                UPDATE marketplace_models
                SET downloads = downloads + 1
                WHERE id = ?
            """,
                (model_id,),
            )

            conn.commit()

        return {
            "id": deployment_id,
            "model_id": model_id,
            "model_name": model["name"],
            "consortium_id": consortium_id,
            "deployed_by": deployed_by,
            "status": "deployed",
            "deployed_at": datetime.utcnow().isoformat(),
        }

    def get_consortium_deployments(self, consortium_id: str) -> list[dict]:
        """Get all model deployments for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            List of deployments.
        """
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.*, m.name as model_name, m.model_type, m.accuracy,
                       m.industry, c.name as category_name
                FROM model_deployments d
                JOIN marketplace_models m ON d.model_id = m.id
                LEFT JOIN model_categories c ON m.industry = c.id
                WHERE d.consortium_id = ?
                ORDER BY d.deployed_at DESC
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        deployments = []
        for row in rows:
            deployment = dict(row)
            deployment["config"] = json.loads(deployment["config"])
            deployments.append(deployment)

        return deployments

    def undeploy_model(self, deployment_id: str, undeployed_by: Optional[str] = None) -> bool:
        """Undeploy a model from a consortium.

        Args:
            deployment_id: Deployment ID.
            undeployed_by: Optional company ID undeploying.

        Returns:
            True if successful.
        """
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE model_deployments
                SET status = 'undeployed'
                WHERE id = ?
            """,
                (deployment_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def add_model_review(
        self,
        model_id: str,
        reviewer_id: str,
        rating: int,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        consortium_id: Optional[str] = None,
    ) -> str:
        """Add a review for a marketplace model.

        Args:
            model_id: Model ID to review.
            reviewer_id: Reviewer company ID.
            rating: Rating (1-5).
            title: Optional review title.
            comment: Optional review comment.
            consortium_id: Optional consortium where model was used.

        Returns:
            Review ID.
        """
        self._init_marketplace_schema()

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        review_id = f"review_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Add review
            cursor.execute(
                """
                INSERT INTO model_reviews
                (id, model_id, reviewer_id, consortium_id, rating, title, comment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (review_id, model_id, reviewer_id, consortium_id, rating, title, comment),
            )

            # Update model rating
            cursor.execute(
                """
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM model_reviews
                WHERE model_id = ?
            """,
                (model_id,),
            )
            stats = cursor.fetchone()

            cursor.execute(
                """
                UPDATE marketplace_models
                SET rating = ?, rating_count = ?
                WHERE id = ?
            """,
                (round(stats["avg_rating"], 1), stats["count"], model_id),
            )

            conn.commit()

        return review_id

    def get_model_reviews(self, model_id: str, limit: int = 50) -> list[dict]:
        """Get reviews for a marketplace model.

        Args:
            model_id: Model ID.
            limit: Maximum number of reviews.

        Returns:
            List of reviews.
        """
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.*, c.name as reviewer_name
                FROM model_reviews r
                LEFT JOIN companies c ON r.reviewer_id = c.id
                WHERE r.model_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
            """,
                (model_id, limit),
            )
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_featured_models(self, limit: int = 6) -> list[dict]:
        """Get featured marketplace models.

        Args:
            limit: Maximum number of models.

        Returns:
            List of featured models.
        """
        return self.get_marketplace_models(featured_only=True, limit=limit)

    def get_marketplace_stats(self) -> dict:
        """Get marketplace statistics.

        Returns:
            Marketplace statistics.
        """
        self._init_marketplace_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM marketplace_models WHERE is_active = 1")
            total_models = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(downloads) FROM marketplace_models")
            total_downloads = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(DISTINCT consortium_id) FROM model_deployments WHERE status = 'active'"
            )
            active_consortiums = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM model_reviews")
            total_reviews = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(rating) FROM marketplace_models WHERE rating > 0")
            avg_rating = cursor.fetchone()[0] or 0

        return {
            "total_models": total_models,
            "total_downloads": total_downloads,
            "active_consortiums": active_consortiums,
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating, 1),
        }


# Export all public classes and functions
__all__ = ["MarketplaceManager"]
