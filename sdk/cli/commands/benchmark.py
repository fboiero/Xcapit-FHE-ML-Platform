"""Benchmark command."""

import time

import numpy as np


def cmd_benchmark(args) -> int:
    """Run FHE benchmark tests."""
    from ...encryption import CKKSEncryptor, CKKSParameters, FHEContextManager

    print("Running FHE Benchmarks...")
    print("=" * 50)

    # Create context
    print("\n1. Context Creation")
    start = time.perf_counter()
    params = CKKSParameters(poly_modulus_degree=args.poly_degree)
    manager = FHEContextManager(params=params)
    manager.create_context()
    encryptor = CKKSEncryptor(manager)
    context_time = (time.perf_counter() - start) * 1000
    print(f"   Time: {context_time:.1f} ms")

    # Encryption benchmark
    print(f"\n2. Vector Encryption ({args.vector_size} elements)")
    test_vector = np.random.randn(args.vector_size).tolist()

    start = time.perf_counter()
    for _ in range(args.iterations):
        encrypted = encryptor.encrypt_vector(test_vector)
    encrypt_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {encrypt_time:.2f} ms (avg of {args.iterations})")

    # Decryption benchmark
    print("\n3. Vector Decryption")
    start = time.perf_counter()
    for _ in range(args.iterations):
        decrypted = encryptor.decrypt_vector(encrypted)
    decrypt_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {decrypt_time:.2f} ms (avg of {args.iterations})")

    # Addition benchmark
    print("\n4. Encrypted Addition")
    encrypted2 = encryptor.encrypt_vector(test_vector)
    start = time.perf_counter()
    for _ in range(args.iterations):
        encrypted + encrypted2
    add_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {add_time:.2f} ms (avg of {args.iterations})")

    # Multiplication benchmark
    print("\n5. Encrypted Multiplication")
    start = time.perf_counter()
    for _ in range(args.iterations):
        encrypted * encrypted2
    mul_time = (time.perf_counter() - start) * 1000 / args.iterations
    print(f"   Time: {mul_time:.2f} ms (avg of {args.iterations})")

    # Precision check
    print("\n6. Precision Check")
    original = np.array(test_vector)
    decrypted = np.array(encryptor.decrypt_vector(encrypted))
    error = np.max(np.abs(original - decrypted[: len(original)]))
    print(f"   Max error: {error:.2e}")

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Poly degree:    {args.poly_degree}")
    print(f"Vector size:    {args.vector_size}")
    print(f"Context:        {context_time:.1f} ms")
    print(f"Encrypt:        {encrypt_time:.2f} ms")
    print(f"Decrypt:        {decrypt_time:.2f} ms")
    print(f"Addition:       {add_time:.2f} ms")
    print(f"Multiplication: {mul_time:.2f} ms")
    print(f"Precision:      {error:.2e}")

    return 0


__all__ = ["cmd_benchmark"]
