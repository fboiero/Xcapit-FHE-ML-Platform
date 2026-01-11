"""Tests for multi-model ensemble module."""

import tempfile
from pathlib import Path

import pytest


def load_module_from_path(module_name: str, file_path: Path):
    """Load a Python module from a file path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_ensemble.db"
        yield db_path


@pytest.fixture
def consortium_manager(temp_db):
    """Create a ConsortiumManager with temporary database."""
    sdk_api_path = Path(__file__).parent.parent / "sdk" / "api"
    consortium_module = load_module_from_path(
        "sdk.api.consortium",
        sdk_api_path / "consortium" / "__init__.py"
    )
    ConsortiumManager = consortium_module.ConsortiumManager
    manager = ConsortiumManager(db_path=temp_db)
    return manager


class TestCreateEnsemble:
    """Tests for ensemble creation."""

    def test_create_ensemble_basic(self, consortium_manager):
        """Test basic ensemble creation."""
        result = consortium_manager.create_ensemble(
            name="Test Ensemble",
            description="A test ensemble",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        assert "ensemble_id" in result
        assert result["ensemble_id"].startswith("ens_")
        assert result["name"] == "Test Ensemble"
        assert result["status"] == "draft"

    def test_create_ensemble_averaging(self, consortium_manager):
        """Test creating averaging ensemble."""
        result = consortium_manager.create_ensemble(
            name="Averaging Ensemble",
            description="Averages model outputs",
            owner_id="owner_002",
            ensemble_type="averaging"
        )

        assert result["ensemble_type"] == "averaging"

    def test_create_ensemble_weighted(self, consortium_manager):
        """Test creating weighted ensemble."""
        result = consortium_manager.create_ensemble(
            name="Weighted Ensemble",
            description="Weighted model combination",
            owner_id="owner_003",
            ensemble_type="weighted"
        )

        assert result["ensemble_type"] == "weighted"

    def test_create_ensemble_stacking(self, consortium_manager):
        """Test creating stacking ensemble."""
        result = consortium_manager.create_ensemble(
            name="Stacking Ensemble",
            description="Stacked model combination",
            owner_id="owner_004",
            ensemble_type="stacking"
        )

        assert result["ensemble_type"] == "stacking"

    def test_create_ensemble_boosting(self, consortium_manager):
        """Test creating boosting ensemble."""
        result = consortium_manager.create_ensemble(
            name="Boosting Ensemble",
            description="Boosted model combination",
            owner_id="owner_005",
            ensemble_type="boosting"
        )

        assert result["ensemble_type"] == "boosting"

    def test_create_ensemble_invalid_type(self, consortium_manager):
        """Test creating ensemble with invalid type."""
        with pytest.raises(ValueError) as exc_info:
            consortium_manager.create_ensemble(
                name="Invalid Ensemble",
                description="Should fail",
                owner_id="owner_006",
                ensemble_type="invalid_type"
            )

        assert "Invalid ensemble type" in str(exc_info.value)


class TestAddModelToEnsemble:
    """Tests for adding models to ensembles."""

    def test_add_model_basic(self, consortium_manager):
        """Test adding a model to ensemble."""
        # Create ensemble first
        ensemble = consortium_manager.create_ensemble(
            name="Test Ensemble",
            description="Test",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        result = consortium_manager.add_model_to_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            model_id="model_001",
            consortium_id="consortium_001",
            model_type="logistic_regression"
        )

        assert "entry_id" in result
        assert result["entry_id"].startswith("em_")
        assert result["model_id"] == "model_001"
        assert result["weight"] == 1.0

    def test_add_model_with_custom_weight(self, consortium_manager):
        """Test adding model with custom weight."""
        ensemble = consortium_manager.create_ensemble(
            name="Weighted Ensemble",
            description="Test",
            owner_id="owner_002",
            ensemble_type="weighted"
        )

        result = consortium_manager.add_model_to_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            model_id="model_002",
            consortium_id="consortium_002",
            model_type="decision_tree",
            weight=2.5
        )

        assert result["weight"] == 2.5

    def test_add_model_nonexistent_ensemble(self, consortium_manager):
        """Test adding model to non-existent ensemble."""
        with pytest.raises(ValueError) as exc_info:
            consortium_manager.add_model_to_ensemble(
                ensemble_id="nonexistent_ensemble",
                model_id="model_003",
                consortium_id="consortium_003",
                model_type="linear_regression"
            )

        assert "not found" in str(exc_info.value)

    def test_add_multiple_models(self, consortium_manager):
        """Test adding multiple models to ensemble."""
        ensemble = consortium_manager.create_ensemble(
            name="Multi-Model Ensemble",
            description="Test",
            owner_id="owner_003",
            ensemble_type="voting"
        )

        # Add multiple models
        for i in range(3):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"model_{i}",
                consortium_id=f"consortium_{i}",
                model_type="logistic_regression"
            )

        # Verify ensemble has models
        details = consortium_manager.get_ensemble(ensemble["ensemble_id"])
        assert details["model_count"] == 3


class TestGetEnsemble:
    """Tests for getting ensemble details."""

    def test_get_ensemble_basic(self, consortium_manager):
        """Test getting ensemble details."""
        created = consortium_manager.create_ensemble(
            name="Test Ensemble",
            description="Test description",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        result = consortium_manager.get_ensemble(created["ensemble_id"])

        assert result is not None
        assert result["name"] == "Test Ensemble"
        assert result["description"] == "Test description"
        assert "models" in result
        assert "model_count" in result

    def test_get_ensemble_with_models(self, consortium_manager):
        """Test getting ensemble with models."""
        created = consortium_manager.create_ensemble(
            name="Ensemble with Models",
            description="Has models",
            owner_id="owner_002",
            ensemble_type="averaging"
        )

        # Add models
        consortium_manager.add_model_to_ensemble(
            ensemble_id=created["ensemble_id"],
            model_id="model_a",
            consortium_id="consortium_a",
            model_type="logistic_regression"
        )

        result = consortium_manager.get_ensemble(created["ensemble_id"])

        assert result["model_count"] == 1
        assert len(result["models"]) == 1
        assert result["models"][0]["model_id"] == "model_a"

    def test_get_nonexistent_ensemble(self, consortium_manager):
        """Test getting non-existent ensemble returns None."""
        result = consortium_manager.get_ensemble("nonexistent_id")
        assert result is None


class TestListEnsembles:
    """Tests for listing ensembles."""

    def test_list_ensembles_empty(self, consortium_manager):
        """Test listing when no ensembles exist."""
        result = consortium_manager.list_ensembles()
        assert isinstance(result, list)

    def test_list_ensembles_all(self, consortium_manager):
        """Test listing all ensembles."""
        # Create some ensembles
        for i in range(3):
            consortium_manager.create_ensemble(
                name=f"Ensemble {i}",
                description=f"Description {i}",
                owner_id="owner_001",
                ensemble_type="voting"
            )

        result = consortium_manager.list_ensembles()

        assert len(result) >= 3
        assert all("model_count" in e for e in result)

    def test_list_ensembles_by_owner(self, consortium_manager):
        """Test filtering ensembles by owner."""
        # Create ensembles for different owners
        consortium_manager.create_ensemble(
            name="Owner A Ensemble",
            description="Owned by A",
            owner_id="owner_a",
            ensemble_type="voting"
        )
        consortium_manager.create_ensemble(
            name="Owner B Ensemble",
            description="Owned by B",
            owner_id="owner_b",
            ensemble_type="voting"
        )

        result = consortium_manager.list_ensembles(owner_id="owner_a")

        assert len(result) >= 1
        assert all(e.get("owner_id") == "owner_a" for e in result)

    def test_list_ensembles_by_status(self, consortium_manager):
        """Test filtering ensembles by status."""
        consortium_manager.create_ensemble(
            name="Draft Ensemble",
            description="In draft",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        result = consortium_manager.list_ensembles(status="draft")

        assert all(e.get("status") == "draft" for e in result)

    def test_list_ensembles_with_limit(self, consortium_manager):
        """Test listing ensembles with limit."""
        # Create many ensembles
        for i in range(10):
            consortium_manager.create_ensemble(
                name=f"Ensemble {i}",
                description=f"Description {i}",
                owner_id="owner_001",
                ensemble_type="voting"
            )

        result = consortium_manager.list_ensembles(limit=5)

        assert len(result) <= 5


class TestActivateEnsemble:
    """Tests for activating ensembles."""

    def test_activate_ensemble_success(self, consortium_manager):
        """Test successfully activating an ensemble."""
        # Create ensemble with 2+ models
        ensemble = consortium_manager.create_ensemble(
            name="Activatable Ensemble",
            description="Has enough models",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        # Add at least 2 models
        for i in range(2):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"model_{i}",
                consortium_id=f"consortium_{i}",
                model_type="logistic_regression"
            )

        result = consortium_manager.activate_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="requester_001"
        )

        assert result["status"] == "active"
        assert result["model_count"] == 2

    def test_activate_ensemble_not_enough_models(self, consortium_manager):
        """Test activating ensemble with insufficient models."""
        ensemble = consortium_manager.create_ensemble(
            name="Single Model Ensemble",
            description="Only one model",
            owner_id="owner_002",
            ensemble_type="voting"
        )

        # Add only 1 model
        consortium_manager.add_model_to_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            model_id="model_single",
            consortium_id="consortium_single",
            model_type="logistic_regression"
        )

        with pytest.raises(ValueError) as exc_info:
            consortium_manager.activate_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                requester_id="requester_002"
            )

        assert "at least 2 models" in str(exc_info.value)

    def test_activate_nonexistent_ensemble(self, consortium_manager):
        """Test activating non-existent ensemble."""
        with pytest.raises(ValueError) as exc_info:
            consortium_manager.activate_ensemble(
                ensemble_id="nonexistent",
                requester_id="requester_003"
            )

        assert "not found" in str(exc_info.value)


class TestPredictWithEnsemble:
    """Tests for ensemble predictions."""

    @pytest.fixture
    def active_ensemble(self, consortium_manager):
        """Create an active ensemble for testing."""
        ensemble = consortium_manager.create_ensemble(
            name="Active Prediction Ensemble",
            description="Ready for predictions",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        # Add models
        for i in range(3):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"pred_model_{i}",
                consortium_id=f"pred_consortium_{i}",
                model_type="logistic_regression"
            )

        # Activate
        consortium_manager.activate_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="activator"
        )

        return ensemble["ensemble_id"]

    def test_predict_voting(self, consortium_manager, active_ensemble):
        """Test voting ensemble prediction."""
        result = consortium_manager.predict_with_ensemble(
            ensemble_id=active_ensemble,
            requester_id="requester_001",
            input_data={"features": [1, 2, 3, 4]}
        )

        assert "prediction_id" in result
        assert "prediction" in result
        assert "confidence" in result
        assert result["ensemble_type"] == "voting"
        assert result["models_used"] == 3

    def test_predict_averaging(self, consortium_manager):
        """Test averaging ensemble prediction."""
        # Create averaging ensemble
        ensemble = consortium_manager.create_ensemble(
            name="Averaging Ensemble",
            description="Averages predictions",
            owner_id="owner_002",
            ensemble_type="averaging"
        )

        for i in range(2):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"avg_model_{i}",
                consortium_id=f"avg_consortium_{i}",
                model_type="linear_regression"
            )

        consortium_manager.activate_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="activator"
        )

        result = consortium_manager.predict_with_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="requester_002",
            input_data={"features": [1, 2]}
        )

        assert result["ensemble_type"] == "averaging"
        assert 0 <= result["prediction"] <= 1

    def test_predict_weighted(self, consortium_manager):
        """Test weighted ensemble prediction."""
        ensemble = consortium_manager.create_ensemble(
            name="Weighted Ensemble",
            description="Weighted predictions",
            owner_id="owner_003",
            ensemble_type="weighted"
        )

        # Add models with different weights
        consortium_manager.add_model_to_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            model_id="weight_model_1",
            consortium_id="weight_consortium_1",
            model_type="logistic_regression",
            weight=2.0
        )
        consortium_manager.add_model_to_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            model_id="weight_model_2",
            consortium_id="weight_consortium_2",
            model_type="logistic_regression",
            weight=1.0
        )

        consortium_manager.activate_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="activator"
        )

        result = consortium_manager.predict_with_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="requester_003",
            input_data={"features": [1]}
        )

        assert result["ensemble_type"] == "weighted"

    def test_predict_includes_model_predictions(self, consortium_manager, active_ensemble):
        """Test prediction includes individual model predictions."""
        result = consortium_manager.predict_with_ensemble(
            ensemble_id=active_ensemble,
            requester_id="requester_004",
            input_data={"features": [1, 2, 3]}
        )

        assert "model_predictions" in result
        assert len(result["model_predictions"]) == 3
        for pred in result["model_predictions"]:
            assert "model_id" in pred
            assert "prediction" in pred
            assert "weight" in pred

    def test_predict_inactive_ensemble(self, consortium_manager):
        """Test predicting with inactive ensemble fails."""
        ensemble = consortium_manager.create_ensemble(
            name="Inactive Ensemble",
            description="Not activated",
            owner_id="owner_004",
            ensemble_type="voting"
        )

        # Add models but don't activate
        for i in range(2):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"inactive_model_{i}",
                consortium_id=f"inactive_consortium_{i}",
                model_type="logistic_regression"
            )

        with pytest.raises(ValueError) as exc_info:
            consortium_manager.predict_with_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                requester_id="requester_005",
                input_data={"features": [1]}
            )

        assert "not active" in str(exc_info.value)

    def test_predict_nonexistent_ensemble(self, consortium_manager):
        """Test predicting with non-existent ensemble."""
        with pytest.raises(ValueError) as exc_info:
            consortium_manager.predict_with_ensemble(
                ensemble_id="nonexistent",
                requester_id="requester_006",
                input_data={"features": [1]}
            )

        assert "not found" in str(exc_info.value)


class TestGetEnsemblePerformance:
    """Tests for ensemble performance metrics."""

    def test_get_performance_basic(self, consortium_manager):
        """Test getting basic performance metrics."""
        # Create and activate ensemble
        ensemble = consortium_manager.create_ensemble(
            name="Performance Ensemble",
            description="Track performance",
            owner_id="owner_001",
            ensemble_type="voting"
        )

        for i in range(2):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"perf_model_{i}",
                consortium_id=f"perf_consortium_{i}",
                model_type="logistic_regression"
            )

        consortium_manager.activate_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="activator"
        )

        # Make some predictions
        for i in range(3):
            consortium_manager.predict_with_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                requester_id="requester",
                input_data={"features": [i]}
            )

        result = consortium_manager.get_ensemble_performance(ensemble["ensemble_id"])

        assert result["ensemble_id"] == ensemble["ensemble_id"]
        assert result["model_count"] == 2
        assert result["total_predictions"] == 3
        assert "avg_confidence" in result
        assert "avg_latency_ms" in result

    def test_get_performance_no_predictions(self, consortium_manager):
        """Test performance metrics with no predictions."""
        ensemble = consortium_manager.create_ensemble(
            name="Empty Ensemble",
            description="No predictions yet",
            owner_id="owner_002",
            ensemble_type="voting"
        )

        result = consortium_manager.get_ensemble_performance(ensemble["ensemble_id"])

        assert result["total_predictions"] == 0


class TestGetEnsembleStats:
    """Tests for overall ensemble statistics."""

    def test_get_stats_basic(self, consortium_manager):
        """Test getting overall statistics."""
        stats = consortium_manager.get_ensemble_stats()

        assert "total_ensembles" in stats
        assert "active_ensembles" in stats
        assert "total_models_in_ensembles" in stats
        assert "total_predictions" in stats
        assert "ensemble_types_available" in stats
        assert stats["privacy_preserved"] is True

    def test_get_stats_by_owner(self, consortium_manager):
        """Test getting stats filtered by owner."""
        # Create ensembles for specific owner
        consortium_manager.create_ensemble(
            name="Owner Stats Ensemble",
            description="For stats test",
            owner_id="stats_owner",
            ensemble_type="voting"
        )

        stats = consortium_manager.get_ensemble_stats(owner_id="stats_owner")

        assert stats["total_ensembles"] >= 1

    def test_stats_reflect_activity(self, consortium_manager):
        """Test stats reflect ensemble activity."""
        initial_stats = consortium_manager.get_ensemble_stats()
        initial_count = initial_stats["total_ensembles"]

        # Create new ensemble
        consortium_manager.create_ensemble(
            name="New Ensemble",
            description="Should increase count",
            owner_id="owner_new",
            ensemble_type="voting"
        )

        updated_stats = consortium_manager.get_ensemble_stats()

        assert updated_stats["total_ensembles"] == initial_count + 1


class TestEnsembleIntegration:
    """Integration tests for ensemble operations."""

    def test_full_ensemble_workflow(self, consortium_manager):
        """Test complete ensemble workflow."""
        # 1. Create ensemble
        ensemble = consortium_manager.create_ensemble(
            name="Workflow Ensemble",
            description="Complete workflow test",
            owner_id="workflow_owner",
            ensemble_type="voting"
        )
        assert ensemble["status"] == "draft"

        # 2. Add models
        for i in range(3):
            consortium_manager.add_model_to_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                model_id=f"workflow_model_{i}",
                consortium_id=f"workflow_consortium_{i}",
                model_type="logistic_regression",
                weight=1.0 + i * 0.5
            )

        # 3. Verify models added
        details = consortium_manager.get_ensemble(ensemble["ensemble_id"])
        assert details["model_count"] == 3

        # 4. Activate ensemble
        activation = consortium_manager.activate_ensemble(
            ensemble_id=ensemble["ensemble_id"],
            requester_id="workflow_activator"
        )
        assert activation["status"] == "active"

        # 5. Make predictions
        predictions = []
        for i in range(5):
            pred = consortium_manager.predict_with_ensemble(
                ensemble_id=ensemble["ensemble_id"],
                requester_id="workflow_requester",
                input_data={"features": [i, i * 2, i * 3]}
            )
            predictions.append(pred)

        assert len(predictions) == 5
        assert all("prediction" in p for p in predictions)

        # 6. Check performance
        performance = consortium_manager.get_ensemble_performance(ensemble["ensemble_id"])
        assert performance["total_predictions"] == 5

        # 7. Check overall stats
        stats = consortium_manager.get_ensemble_stats()
        assert stats["total_predictions"] >= 5

    def test_multiple_ensemble_types(self, consortium_manager):
        """Test creating ensembles of different types."""
        ensemble_types = ["voting", "averaging", "weighted", "stacking", "boosting"]

        for etype in ensemble_types:
            ensemble = consortium_manager.create_ensemble(
                name=f"{etype.title()} Ensemble",
                description=f"Testing {etype}",
                owner_id="type_tester",
                ensemble_type=etype
            )
            assert ensemble["ensemble_type"] == etype

        # Check stats by type
        stats = consortium_manager.get_ensemble_stats()
        assert len(stats.get("by_type", {})) >= len(ensemble_types)
