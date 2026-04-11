"""CKKS context manager for TenSEAL."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import tenseal as ts


class SecurityLevel(Enum):
    """CKKS security levels."""
    TC128 = 128
    TC192 = 192
    TC256 = 256

    def to_tenseal(self):
        return {
            128: ts.ENCRYPTION_TYPE.ASYMMETRIC,
            192: ts.ENCRYPTION_TYPE.ASYMMETRIC,
            256: ts.ENCRYPTION_TYPE.ASYMMETRIC,
        }[self.value]


@dataclass
class CKKSParameters:
    """Parameters for CKKS encryption scheme."""
    poly_modulus_degree: int = 8192
    coeff_mod_bit_sizes: tuple = (60, 40, 40, 60)
    scale: float = 2**40
    security_level: SecurityLevel = SecurityLevel.TC128

    def create_context(self) -> ts.Context:
        """Create a TenSEAL context from these parameters."""
        ctx = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=self.poly_modulus_degree,
            coeff_mod_bit_sizes=list(self.coeff_mod_bit_sizes),
        )
        ctx.generate_galois_keys()
        ctx.global_scale = self.scale
        return ctx
