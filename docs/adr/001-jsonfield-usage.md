# ADR-001: JSONField Usage Strategy

## Status
Accepted

## Context
The platform uses Django JSONField extensively (29+ instances). Without validation, fields accept any JSON structure leading to runtime errors and inconsistent data.

## Decision
Implement JSON Schema validation (Draft 7) for critical JSONFields using `jsonschema` library.

### Validated Fields
| Model | Field | Schema |
|-------|-------|--------|
| Proposal | data | Per proposal_type |
| QualityRule | condition | Operator-based |
| RewardDistribution | distributions | Array of distributions |

## Consequences
- **Positive**: Clear error messages, self-documenting schemas, consistent data
- **Negative**: Additional dependency, schema maintenance overhead

## References
- Implementation: `apps/core/validators/json_schemas.py`
