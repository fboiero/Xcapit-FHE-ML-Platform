"""
JSON Schema definitions and validators.

Provides validation for JSONFields in the platform:
- Proposal.data (governance)
- QualityRule.condition (data_quality)
- RewardDistribution.distributions (governance)
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from django.core.exceptions import ValidationError
from rest_framework import serializers

logger = logging.getLogger(__name__)

# Try to import jsonschema, fall back to basic validation if not available
try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError as JSONSchemaValidationError
    from jsonschema import FormatChecker

    JSONSCHEMA_AVAILABLE = True
    # Create format checker with common formats
    format_checker = FormatChecker()
except (ImportError, TypeError):
    JSONSCHEMA_AVAILABLE = False
    format_checker = None
    logger.warning("jsonschema not available or incompatible. JSON schema validation will be basic.")


# =============================================================================
# PROPOSAL DATA SCHEMAS
# =============================================================================

PROPOSAL_DATA_SCHEMAS = {
    "add_member": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["company_email"],
        "properties": {
            "company_email": {
                "type": "string",
                "format": "email",
                "description": "Email of the company to add",
            },
            "role": {
                "type": "string",
                "enum": ["contributor", "admin", "observer"],
                "default": "contributor",
                "description": "Role of the new member",
            },
            "message": {
                "type": "string",
                "maxLength": 500,
                "description": "Optional invitation message",
            },
        },
        "additionalProperties": False,
    },
    "remove_member": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["company_id"],
        "properties": {
            "company_id": {
                "type": "string",
                "format": "uuid",
                "description": "ID of the company to remove",
            },
            "reason": {
                "type": "string",
                "maxLength": 500,
                "description": "Reason for removal",
            },
        },
        "additionalProperties": False,
    },
    "change_model": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["model_id"],
        "properties": {
            "model_id": {
                "type": "string",
                "format": "uuid",
                "description": "ID of the new model",
            },
            "version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+\\.\\d+$",
                "description": "Model version (semver)",
            },
        },
        "additionalProperties": False,
    },
    "start_training": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "model_type": {
                "type": "string",
                "enum": ["logistic_regression", "linear_regression", "decision_tree", "kmeans"],
                "description": "Type of model to train",
            },
            "epochs": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 10,
                "description": "Number of training epochs",
            },
            "learning_rate": {
                "type": "number",
                "minimum": 0.0001,
                "maximum": 1.0,
                "default": 0.01,
                "description": "Learning rate",
            },
            "batch_size": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10000,
                "default": 32,
                "description": "Training batch size",
            },
        },
        "additionalProperties": True,
    },
    "distribute_rewards": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["amount", "currency"],
        "properties": {
            "amount": {
                "type": "number",
                "minimum": 0,
                "description": "Total amount to distribute",
            },
            "currency": {
                "type": "string",
                "enum": ["ETH", "USDC", "DAI"],
                "description": "Currency for distribution",
            },
            "distribution_method": {
                "type": "string",
                "enum": ["equal", "contribution_weighted", "custom"],
                "default": "contribution_weighted",
                "description": "How to distribute rewards",
            },
            "custom_weights": {
                "type": "object",
                "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
                "description": "Custom weights by company_id (only for custom method)",
            },
        },
        "additionalProperties": False,
    },
    "update_config": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["config_key", "config_value"],
        "properties": {
            "config_key": {
                "type": "string",
                "enum": [
                    "voting_duration",
                    "min_voting_quorum",
                    "model_config",
                    "privacy_budget",
                ],
                "description": "Configuration key to update",
            },
            "config_value": {
                "description": "New value for the configuration",
            },
            "reason": {
                "type": "string",
                "maxLength": 500,
                "description": "Reason for the change",
            },
        },
        "additionalProperties": False,
    },
    "dissolve": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["reason"],
        "properties": {
            "reason": {
                "type": "string",
                "minLength": 10,
                "maxLength": 1000,
                "description": "Detailed reason for dissolution",
            },
            "distribute_remaining_funds": {
                "type": "boolean",
                "default": True,
                "description": "Whether to distribute remaining funds to members",
            },
        },
        "additionalProperties": False,
    },
}


# =============================================================================
# QUALITY RULE CONDITION SCHEMA
# =============================================================================

QUALITY_RULE_CONDITION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["operator"],
    "properties": {
        "operator": {
            "type": "string",
            "enum": [">=", "<=", ">", "<", "==", "!=", "between", "in", "not_in"],
            "description": "Comparison operator",
        },
        "value": {
            "description": "Value to compare against (number for comparison, array for in/not_in)",
        },
        "min_value": {
            "type": "number",
            "description": "Minimum value (for 'between' operator)",
        },
        "max_value": {
            "type": "number",
            "description": "Maximum value (for 'between' operator)",
        },
    },
    "additionalProperties": False,
    "allOf": [
        {
            "if": {"properties": {"operator": {"const": "between"}}},
            "then": {"required": ["min_value", "max_value"]},
        },
        {
            "if": {"properties": {"operator": {"enum": ["in", "not_in"]}}},
            "then": {"required": ["value"], "properties": {"value": {"type": "array"}}},
        },
        {
            "if": {"properties": {"operator": {"enum": [">=", "<=", ">", "<", "==", "!="]}}},
            "then": {"required": ["value"], "properties": {"value": {"type": "number"}}},
        },
    ],
}


# =============================================================================
# REWARD DISTRIBUTION SCHEMA
# =============================================================================

REWARD_DISTRIBUTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "object",
        "required": ["company_id", "amount"],
        "properties": {
            "company_id": {
                "type": "string",
                "format": "uuid",
                "description": "ID of the receiving company",
            },
            "amount": {
                "type": "number",
                "minimum": 0,
                "description": "Amount distributed",
            },
            "contribution_weight": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Weight used for calculation",
            },
            "tx_hash": {
                "type": "string",
                "pattern": "^0x[a-fA-F0-9]{64}$",
                "description": "Blockchain transaction hash",
            },
        },
        "additionalProperties": False,
    },
}


# =============================================================================
# VALIDATOR CLASS
# =============================================================================

class JSONSchemaValidator:
    """
    Reusable JSON schema validator.

    Can be used as a Django/DRF validator or standalone.

    Usage:
        # As DRF field validator
        data = serializers.JSONField(validators=[
            JSONSchemaValidator(PROPOSAL_DATA_SCHEMAS["add_member"])
        ])

        # Standalone
        validator = JSONSchemaValidator(schema)
        try:
            validator(data)
        except ValidationError as e:
            print(e.messages)
    """

    def __init__(
        self,
        schema: dict[str, Any],
        allow_empty: bool = False,
    ) -> None:
        """
        Initialize validator with schema.

        Args:
            schema: JSON Schema (Draft 7)
            allow_empty: If True, empty dict/list passes validation
        """
        self.schema = schema
        self.allow_empty = allow_empty

        # Pre-compile validator if jsonschema is available
        if JSONSCHEMA_AVAILABLE:
            self._validator = Draft7Validator(schema, format_checker=format_checker)
        else:
            self._validator = None

    def __call__(self, value: Any) -> None:
        """
        Validate value against schema.

        Raises:
            ValidationError: If validation fails
        """
        # Handle empty values
        if not value:
            if self.allow_empty:
                return
            raise ValidationError("This field cannot be empty.")

        # Use jsonschema if available
        if self._validator:
            errors = list(self._validator.iter_errors(value))
            if errors:
                messages = [
                    f"{error.json_path}: {error.message}"
                    for error in errors
                ]
                raise ValidationError(messages)
        else:
            # Basic validation without jsonschema
            self._basic_validate(value)

    def _basic_validate(self, value: Any) -> None:
        """Basic validation when jsonschema is not available."""
        self._validate_against_schema(value, self.schema)

    def _validate_against_schema(self, value: Any, schema: dict) -> None:
        """Recursively validate value against a JSON schema (basic fallback)."""
        import re
        import uuid as _uuid

        schema_type = schema.get("type")
        errors: list[str] = []

        # Type checking
        type_map = {
            "object": dict,
            "array": list,
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
        }

        if schema_type and schema_type in type_map:
            expected = type_map[schema_type]
            if not isinstance(value, expected):
                # In Python, bool is a subclass of int; reject bools for int/number
                if schema_type in ("integer", "number") and isinstance(value, bool):
                    raise ValidationError(f"Expected {schema_type}, got {type(value).__name__}.")
                raise ValidationError(f"Expected {schema_type}, got {type(value).__name__}.")

        if schema_type == "object" and isinstance(value, dict):
            # Check required fields
            for field in schema.get("required", []):
                if field not in value:
                    errors.append(f"Missing required field: {field}")

            # Validate each property against its sub-schema
            properties = schema.get("properties", {})
            for key, val in value.items():
                if key in properties:
                    prop_schema = properties[key]

                    # Enum check
                    if "enum" in prop_schema and val not in prop_schema["enum"]:
                        errors.append(
                            f"'{key}': '{val}' is not one of {prop_schema['enum']}"
                        )

                    # Type check for property
                    prop_type = prop_schema.get("type")
                    if prop_type and prop_type in type_map:
                        expected_prop = type_map[prop_type]
                        if not isinstance(val, expected_prop):
                            errors.append(
                                f"'{key}': expected {prop_type}, got {type(val).__name__}"
                            )
                        elif prop_type in ("integer", "number") and isinstance(val, bool):
                            errors.append(
                                f"'{key}': expected {prop_type}, got bool"
                            )

                    # Minimum / maximum
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        if "minimum" in prop_schema and val < prop_schema["minimum"]:
                            errors.append(
                                f"'{key}': {val} is less than minimum {prop_schema['minimum']}"
                            )
                        if "maximum" in prop_schema and val > prop_schema["maximum"]:
                            errors.append(
                                f"'{key}': {val} is greater than maximum {prop_schema['maximum']}"
                            )

                    # Format check (basic)
                    fmt = prop_schema.get("format")
                    if fmt and isinstance(val, str):
                        if fmt == "email" and "@" not in val:
                            errors.append(f"'{key}': '{val}' is not a valid email")
                        elif fmt == "uuid":
                            try:
                                _uuid.UUID(val)
                            except (ValueError, AttributeError):
                                errors.append(f"'{key}': '{val}' is not a valid UUID")

            # Check additionalProperties: false
            if schema.get("additionalProperties") is False:
                allowed_keys = set(properties.keys())
                extra = set(value.keys()) - allowed_keys
                if extra:
                    errors.append(f"Additional properties not allowed: {extra}")

        elif schema_type == "array" and isinstance(value, list):
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(value):
                    try:
                        self._validate_against_schema(item, items_schema)
                    except ValidationError as e:
                        msgs = "; ".join(str(m) for m in e.messages)
                        errors.append(f"Item {i}: {msgs}")

        if errors:
            raise ValidationError(errors)

    def __eq__(self, other: object) -> bool:
        """Compare validators by schema."""
        if not isinstance(other, JSONSchemaValidator):
            return False
        return self.schema == other.schema

    def __hash__(self) -> int:
        """Hash by schema for use in sets."""
        return hash(str(self.schema))


def validate_json_schema(value: Any, schema: dict[str, Any]) -> None:
    """
    Validate a value against a JSON schema.

    Convenience function for one-off validation.

    Args:
        value: Value to validate
        schema: JSON Schema

    Raises:
        ValidationError: If validation fails
    """
    validator = JSONSchemaValidator(schema)
    validator(value)


@lru_cache(maxsize=32)
def get_proposal_validator(proposal_type: str) -> JSONSchemaValidator | None:
    """
    Get cached validator for a proposal type.

    Args:
        proposal_type: The type of proposal

    Returns:
        Validator for the proposal type, or None if not defined
    """
    schema = PROPOSAL_DATA_SCHEMAS.get(proposal_type)
    if schema:
        return JSONSchemaValidator(schema)
    return None


class ProposalDataField(serializers.JSONField):
    """
    Custom DRF field for validating Proposal.data.

    Validates against schema based on proposal_type.
    """

    def to_internal_value(self, data: Any) -> Any:
        """Validate data against proposal-type-specific schema."""
        value = super().to_internal_value(data)

        # Get proposal_type from context or parent
        proposal_type = None
        if self.parent:
            proposal_type = self.parent.initial_data.get("proposal_type")

        if proposal_type:
            validator = get_proposal_validator(proposal_type)
            if validator:
                try:
                    validator(value)
                except ValidationError as e:
                    raise serializers.ValidationError(e.messages)

        return value


class QualityRuleConditionField(serializers.JSONField):
    """
    Custom DRF field for validating QualityRule.condition.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("validators", [])
        kwargs["validators"].append(
            JSONSchemaValidator(QUALITY_RULE_CONDITION_SCHEMA)
        )
        super().__init__(**kwargs)
