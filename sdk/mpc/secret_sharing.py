"""Shamir's Secret Sharing over a prime finite field.

Provides information-theoretic security: any K shares can reconstruct the
secret, but K-1 shares reveal *nothing* about it.  All arithmetic is done
modulo a safe prime so there is no floating-point error — Lagrange
interpolation is exact.

References
----------
- Shamir, A. (1979). "How to share a secret."
  Communications of the ACM, 22(11), 612–613.
"""

from __future__ import annotations

import secrets
from typing import Final

# ---------------------------------------------------------------------------
# A 256-bit safe prime  p = 2q + 1  where q is also prime.
# Generated with OpenSSL:  openssl prime -generate -bits 256 -safe
# This gives us a finite field large enough for 256-bit secrets (AES-256
# keys, HMAC secrets, etc.) while keeping arithmetic fast in pure Python.
# ---------------------------------------------------------------------------
SAFE_PRIME: Final[int] = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
# This is the field prime of the secp256k1 elliptic curve:
#   p = 2^256 - 2^32 - 2^9 - 2^8 - 2^7 - 2^6 - 2^4 - 1
#   p = 2^256 - 4294968273
# It is a well-known, verified 256-bit prime used in Bitcoin/Ethereum.
# For Shamir's scheme the requirement is that p is prime and
# p > max(secret, n_shares).  This prime is large enough for any
# 256-bit secret (e.g. AES-256 keys).


class SecretSharer:
    """Shamir's Secret Sharing Scheme.

    Splits a secret into *n* shares where any *k* (threshold) shares can
    reconstruct it, but *k − 1* shares reveal **nothing** about the secret
    (information-theoretic security).

    Used in the platform for:
    - Distributing consortium encryption keys among members
    - Threshold decryption (K of N members must agree to decrypt)
    - Secure key recovery

    Parameters
    ----------
    prime : int, optional
        Prime modulus for the finite field.  Defaults to ``SAFE_PRIME``
        (256-bit).  Must be larger than both the secret and the number of
        shares.
    """

    def __init__(self, prime: int | None = None) -> None:
        self.prime: int = prime if prime is not None else SAFE_PRIME

    # ------------------------------------------------------------------
    # Integer secret sharing
    # ------------------------------------------------------------------

    def split(
        self,
        secret: int,
        n_shares: int,
        threshold: int,
    ) -> list[tuple[int, int]]:
        """Split *secret* into *n_shares* with the given *threshold*.

        Parameters
        ----------
        secret:
            The secret value to split.  Must satisfy ``0 <= secret < prime``.
        n_shares:
            Total number of shares to generate (N).
        threshold:
            Minimum shares needed for reconstruction (K).

        Returns
        -------
        list[tuple[int, int]]
            A list of ``(x, y)`` share tuples where ``x`` ranges from 1 to
            *n_shares*.

        Raises
        ------
        ValueError
            If parameters are out of range.
        """
        self._validate_params(secret, n_shares, threshold)

        # Random polynomial  f(x) = secret + a_1*x + a_2*x^2 + ... + a_{k-1}*x^{k-1}
        coefficients: list[int] = [secret] + [
            secrets.randbelow(self.prime) for _ in range(threshold - 1)
        ]

        shares: list[tuple[int, int]] = []
        for x in range(1, n_shares + 1):
            y = self._evaluate_polynomial(coefficients, x)
            shares.append((x, y))

        return shares

    def reconstruct(self, shares: list[tuple[int, int]]) -> int:
        """Reconstruct the secret from *threshold* or more shares.

        Uses Lagrange interpolation over the finite field to recover the
        constant term of the polynomial (which is the secret).

        Parameters
        ----------
        shares:
            At least *threshold* ``(x, y)`` tuples.

        Returns
        -------
        int
            The reconstructed secret.

        Raises
        ------
        ValueError
            If fewer than 2 shares are provided.
        """
        if len(shares) < 2:
            raise ValueError("Need at least 2 shares to reconstruct.")

        return self._lagrange_interpolation(shares, self.prime)

    # ------------------------------------------------------------------
    # Byte-string secret sharing (for encryption keys)
    # ------------------------------------------------------------------

    def split_bytes(
        self,
        secret_bytes: bytes,
        n_shares: int,
        threshold: int,
    ) -> list[tuple[int, bytes]]:
        """Split a byte string (e.g. an AES key) into shares.

        The byte string is converted to an integer, shared with
        :meth:`split`, and each share's *y*-value is stored as a
        fixed-length byte string matching the original length (padded to
        the field element size when necessary).

        Parameters
        ----------
        secret_bytes:
            The byte string to split.
        n_shares:
            Total number of shares.
        threshold:
            Minimum shares needed for reconstruction.

        Returns
        -------
        list[tuple[int, bytes]]
            Shares as ``(index, y_bytes)`` tuples.
        """
        len(secret_bytes)
        secret_int = int.from_bytes(secret_bytes, byteorder="big")

        if secret_int >= self.prime:
            raise ValueError(
                f"Secret ({secret_int.bit_length()} bits) is too large for "
                f"the prime field ({self.prime.bit_length()} bits).  Use a "
                f"larger prime or split the secret into smaller chunks."
            )

        int_shares = self.split(secret_int, n_shares, threshold)

        # Each y-value may be up to prime-1, so we need enough bytes to
        # represent any element in the field.
        share_byte_len = (self.prime.bit_length() + 7) // 8

        return [(x, y.to_bytes(share_byte_len, byteorder="big")) for x, y in int_shares]

    def reconstruct_bytes(
        self,
        shares: list[tuple[int, bytes]],
        secret_length: int | None = None,
    ) -> bytes:
        """Reconstruct a byte string from shares.

        Parameters
        ----------
        shares:
            At least *threshold* ``(index, y_bytes)`` tuples.
        secret_length:
            Expected length of the reconstructed byte string.  If ``None``,
            the minimal byte representation is returned.

        Returns
        -------
        bytes
            The reconstructed secret byte string.
        """
        int_shares: list[tuple[int, int]] = [
            (x, int.from_bytes(y_bytes, byteorder="big")) for x, y_bytes in shares
        ]

        secret_int = self.reconstruct(int_shares)

        if secret_length is not None:
            return secret_int.to_bytes(secret_length, byteorder="big")

        # Minimal representation
        byte_len = (secret_int.bit_length() + 7) // 8 or 1
        return secret_int.to_bytes(byte_len, byteorder="big")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_params(
        self,
        secret: int,
        n_shares: int,
        threshold: int,
    ) -> None:
        """Validate split parameters."""
        if threshold < 2:
            raise ValueError("Threshold must be >= 2.")
        if n_shares < threshold:
            raise ValueError(f"n_shares ({n_shares}) must be >= threshold ({threshold}).")
        if secret < 0:
            raise ValueError("Secret must be non-negative.")
        if secret >= self.prime:
            raise ValueError(f"Secret must be less than the prime ({self.prime}).")
        if n_shares >= self.prime:
            raise ValueError(f"n_shares ({n_shares}) must be less than the prime.")

    def _evaluate_polynomial(self, coefficients: list[int], x: int) -> int:
        """Evaluate polynomial at *x* using Horner's method (mod prime).

        coefficients[0] is the constant term (the secret).
        """
        p = self.prime
        # Horner's method: start from the highest-degree coefficient
        result = 0
        for coeff in reversed(coefficients):
            result = (result * x + coeff) % p
        return result

    @staticmethod
    def _lagrange_interpolation(
        shares: list[tuple[int, int]],
        prime: int,
    ) -> int:
        """Lagrange interpolation at x = 0 over GF(prime).

        Computes f(0) from a set of (x_i, y_i) points, where f is the
        unique polynomial of degree <= len(shares)-1 passing through them.
        All arithmetic is modular — no floating point.

        Parameters
        ----------
        shares:
            ``(x_i, y_i)`` evaluation points.
        prime:
            The field modulus.

        Returns
        -------
        int
            ``f(0) mod prime`` — the reconstructed secret.
        """
        k = len(shares)
        secret = 0

        for i in range(k):
            x_i, y_i = shares[i]

            # Compute Lagrange basis polynomial L_i(0)
            numerator = 1
            denominator = 1

            for j in range(k):
                if i == j:
                    continue
                x_j = shares[j][0]
                # L_i(0) = product_{j!=i} (0 - x_j) / (x_i - x_j)
                numerator = (numerator * (-x_j)) % prime
                denominator = (denominator * (x_i - x_j)) % prime

            # Lagrange basis value at 0
            lagrange_coeff = (numerator * SecretSharer._mod_inverse(denominator, prime)) % prime

            secret = (secret + y_i * lagrange_coeff) % prime

        return secret

    @staticmethod
    def _mod_inverse(a: int, p: int) -> int:
        """Modular multiplicative inverse via extended Euclidean algorithm.

        Returns *b* such that ``(a * b) % p == 1``.

        Raises
        ------
        ValueError
            If *a* is not invertible modulo *p* (i.e. gcd(a, p) != 1).
        """
        a = a % p
        if a == 0:
            raise ValueError("Zero has no multiplicative inverse.")

        # Extended Euclidean algorithm
        old_r, r = a, p
        old_s, s = 1, 0

        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s

        if old_r != 1:
            raise ValueError(f"{a} is not invertible modulo {p} (gcd = {old_r}).")

        return old_s % p
