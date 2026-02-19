"""
Tests for JSON schema validation.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.core.validators.json_schemas import (
    JSONSchemaValidator,
    PROPOSAL_DATA_SCHEMAS,
    QUALITY_RULE_CONDITION_SCHEMA,
    REWARD_DISTRIBUTION_SCHEMA,
    validate_json_schema,
    get_proposal_validator,
)


class TestJSONSchemaValidator:
    """Tests for the JSONSchemaValidator class."""

    def test_validator_accepts_valid_data(self):
        """Validator should accept data matching schema."""
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
            },
        }
        validator = JSONSchemaValidator(schema)

        # Should not raise
        validator({"name": "test"})

    def test_validator_rejects_invalid_data(self):
        """Validator should reject data not matching schema."""
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
            },
        }
        validator = JSONSchemaValidator(schema)

        with pytest.raises(ValidationError):
            validator({"other": "test"})  # Missing required 'name'

    def test_validator_rejects_wrong_type(self):
        """Validator should reject data with wrong type."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
            },
        }
        validator = JSONSchemaValidator(schema)

        with pytest.raises(ValidationError):
            validator({"count": "not a number"})

    def test_validator_allows_empty_when_configured(self):
        """Validator should allow empty data when configured."""
        schema = {"type": "object", "required": ["name"]}
        validator = JSONSchemaValidator(schema, allow_empty=True)

        # Should not raise
        validator({})
        validator(None)

    def test_validator_rejects_empty_by_default(self):
        """Validator should reject empty data by default."""
        schema = {"type": "object"}
        validator = JSONSchemaValidator(schema)

        with pytest.raises(ValidationError):
            validator({})


class TestProposalDataSchemas:
    """Tests for proposal data schemas."""

    def test_add_member_valid(self):
        """Valid add_member proposal data."""
        validator = get_proposal_validator("add_member")
        assert validator is not None

        # Valid data
        validator({
            "company_email": "test@example.com",
            "role": "contributor",
        })

    def test_add_member_invalid_email(self):
        """Invalid email in add_member proposal."""
        validator = get_proposal_validator("add_member")

        with pytest.raises(ValidationError):
            validator({
                "company_email": "not-an-email",
                "role": "contributor",
            })

    def test_add_member_invalid_role(self):
        """Invalid role in add_member proposal."""
        validator = get_proposal_validator("add_member")

        with pytest.raises(ValidationError):
            validator({
                "company_email": "test@example.com",
                "role": "superadmin",  # Invalid role
            })

    def test_add_member_missing_required(self):
        """Missing required field in add_member proposal."""
        validator = get_proposal_validator("add_member")

        with pytest.raises(ValidationError):
            validator({
                "role": "contributor",
                # Missing company_email
            })

    def test_distribute_rewards_valid(self):
        """Valid distribute_rewards proposal data."""
        validator = get_proposal_validator("distribute_rewards")
        assert validator is not None

        validator({
            "amount": 1000.0,
            "currency": "ETH",
            "distribution_method": "contribution_weighted",
        })

    def test_distribute_rewards_invalid_currency(self):
        """Invalid currency in distribute_rewards proposal."""
        validator = get_proposal_validator("distribute_rewards")

        with pytest.raises(ValidationError):
            validator({
                "amount": 1000.0,
                "currency": "BTC",  # Not allowed
            })

    def test_distribute_rewards_negative_amount(self):
        """Negative amount in distribute_rewards proposal."""
        validator = get_proposal_validator("distribute_rewards")

        with pytest.raises(ValidationError):
            validator({
                "amount": -100.0,
                "currency": "ETH",
            })

    def test_start_training_valid(self):
        """Valid start_training proposal data."""
        validator = get_proposal_validator("start_training")
        assert validator is not None

        validator({
            "model_type": "logistic_regression",
            "epochs": 100,
            "learning_rate": 0.01,
            "batch_size": 64,
        })

    def test_start_training_invalid_epochs(self):
        """Invalid epochs in start_training proposal."""
        validator = get_proposal_validator("start_training")

        with pytest.raises(ValidationError):
            validator({
                "model_type": "logistic_regression",
                "epochs": 10000,  # Exceeds max
            })

    def test_unknown_proposal_type(self):
        """Unknown proposal type returns None."""
        validator = get_proposal_validator("unknown_type")
        assert validator is None


class TestQualityRuleConditionSchema:
    """Tests for quality rule condition schema."""

    def test_threshold_condition_valid(self):
        """Valid threshold condition."""
        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)

        validator({
            "operator": ">=",
            "value": 80,
        })

    def test_between_condition_valid(self):
        """Valid between condition."""
        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)

        validator({
            "operator": "between",
            "min_value": 0,
            "max_value": 100,
        })

    def test_in_condition_valid(self):
        """Valid in condition."""
        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)

        validator({
            "operator": "in",
            "value": [1, 2, 3],
        })

    def test_invalid_operator(self):
        """Invalid operator in condition."""
        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)

        with pytest.raises(ValidationError):
            validator({
                "operator": "like",  # Not allowed
                "value": 80,
            })

    def test_missing_required_field(self):
        """Missing required field in condition."""
        validator = JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)

        with pytest.raises(ValidationError):
            validator({
                "value": 80,
                # Missing operator
            })


class TestRewardDistributionSchema:
    """Tests for reward distribution schema."""

    def test_valid_distribution(self):
        """Valid distribution array."""
        validator = JSONSchemaValidator(REWARD_DISTRIBUTION_SCHEMA)

        validator([
            {
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 100.5,
                "contribution_weight": 0.5,
            },
            {
                "company_id": "223e4567-e89b-12d3-a456-426614174001",
                "amount": 100.5,
                "contribution_weight": 0.5,
            },
        ])

    def test_empty_distribution(self):
        """Empty distribution array is valid."""
        validator = JSONSchemaValidator(REWARD_DISTRIBUTION_SCHEMA, allow_empty=True)
        validator([])

    def test_invalid_company_id(self):
        """Invalid company_id format."""
        validator = JSONSchemaValidator(REWARD_DISTRIBUTION_SCHEMA)

        with pytest.raises(ValidationError):
            validator([
                {
                    "company_id": "not-a-uuid",
                    "amount": 100.0,
                },
            ])

    def test_negative_amount(self):
        """Negative amount in distribution."""
        validator = JSONSchemaValidator(REWARD_DISTRIBUTION_SCHEMA)

        with pytest.raises(ValidationError):
            validator([
                {
                    "company_id": "123e4567-e89b-12d3-a456-426614174000",
                    "amount": -100.0,
                },
            ])

    def test_missing_required_field(self):
        """Missing required field in distribution item."""
        validator = JSONSchemaValidator(REWARD_DISTRIBUTION_SCHEMA)

        with pytest.raises(ValidationError):
            validator([
                {
                    "company_id": "123e4567-e89b-12d3-a456-426614174000",
                    # Missing amount
                },
            ])


class TestValidateJsonSchemaFunction:
    """Tests for the validate_json_schema convenience function."""

    def test_valid_data(self):
        """Function accepts valid data."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # Should not raise
        validate_json_schema({"name": "test"}, schema)

    def test_invalid_data(self):
        """Function rejects invalid data."""
        schema = {"type": "object", "required": ["name"]}

        with pytest.raises(ValidationError):
            validate_json_schema({}, schema)


class TestValidatorEquality:
    """Tests for validator equality and hashing."""

    def test_validators_with_same_schema_are_equal(self):
        """Validators with identical schemas should be equal."""
        schema = {"type": "object"}
        v1 = JSONSchemaValidator(schema)
        v2 = JSONSchemaValidator(schema)

        assert v1 == v2

    def test_validators_with_different_schemas_not_equal(self):
        """Validators with different schemas should not be equal."""
        v1 = JSONSchemaValidator({"type": "object"})
        v2 = JSONSchemaValidator({"type": "array"})

        assert v1 != v2

    def test_validators_can_be_used_in_sets(self):
        """Validators should be hashable for use in sets."""
        schema = {"type": "object"}
        v1 = JSONSchemaValidator(schema)
        v2 = JSONSchemaValidator(schema)

        validator_set = {v1, v2}
        assert len(validator_set) == 1  # Same schema = same validator
