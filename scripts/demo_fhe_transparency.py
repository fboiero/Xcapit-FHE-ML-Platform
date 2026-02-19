#!/usr/bin/env python3
"""
Xcapit Privacy Platform - FHE Transparency Demo

Esta demo muestra paso a paso como la encriptacion homomorfica
protege tus datos. Veras los bytes REALES del ciphertext.

Uso:
    python scripts/demo_fhe_transparency.py
"""

import sys
import time
import os

# Add SDK to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tenseal as ts
    import numpy as np
    HAS_TENSEAL = True
except ImportError:
    HAS_TENSEAL = False
    print("\n⚠️  TenSEAL no instalado. Usando simulacion.")
    print("   Para ver bytes reales: pip install tenseal\n")


# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def print_step(num, text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Paso {num}]{Colors.ENDC} {Colors.BOLD}{text}{Colors.ENDC}")
    print("-" * 50)


def print_data(label, value, encrypted=False):
    if encrypted:
        print(f"  {Colors.DIM}{label}:{Colors.ENDC}")
        # Show first 100 chars of hex
        hex_str = value.hex() if isinstance(value, bytes) else str(value)
        print(f"  {Colors.YELLOW}{hex_str[:80]}...{Colors.ENDC}")
        print(f"  {Colors.DIM}({len(value) if isinstance(value, bytes) else len(str(value))} bytes){Colors.ENDC}")
    else:
        print(f"  {Colors.GREEN}{label}: {value}{Colors.ENDC}")


def print_server_view(label, value):
    print(f"  {Colors.RED}{label}:{Colors.ENDC}")
    hex_str = value.hex() if isinstance(value, bytes) else str(value)
    print(f"  {Colors.YELLOW}{hex_str[:80]}...{Colors.ENDC}")


def wait_for_user():
    input(f"\n{Colors.DIM}Presiona Enter para continuar...{Colors.ENDC}")


def animate_text(text, delay=0.03):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


class FHEDemo:
    def __init__(self):
        self.context = None
        self.secret_key = None
        self.public_key = None

        if HAS_TENSEAL:
            self._setup_real_fhe()

    def _setup_real_fhe(self):
        """Initialize real TenSEAL context."""
        print(f"{Colors.DIM}Inicializando contexto CKKS...{Colors.ENDC}")

        # Create CKKS context
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[60, 40, 40, 60]
        )
        self.context.generate_galois_keys()
        self.context.global_scale = 2**40

        # Store secret key separately
        self.secret_key = self.context.secret_key()

        # Create public context (what server would have)
        self.public_context = self.context.copy()
        self.public_context.make_context_public()

        print(f"{Colors.GREEN}✓ Contexto CKKS inicializado{Colors.ENDC}")
        print(f"  Polynomial degree: 8192")
        print(f"  Security level: 128 bits")

    def encrypt(self, values):
        """Encrypt values using CKKS."""
        if HAS_TENSEAL:
            encrypted = ts.ckks_vector(self.context, values)
            return encrypted.serialize()
        else:
            # Simulation
            import hashlib
            data = str(values).encode()
            return hashlib.sha256(data).digest() * 4

    def decrypt(self, encrypted_bytes):
        """Decrypt values (only works with secret key)."""
        if HAS_TENSEAL:
            encrypted = ts.ckks_vector_from(self.context, encrypted_bytes)
            return encrypted.decrypt()
        else:
            return [0.0]  # Simulation

    def homomorphic_add(self, enc_a, enc_b):
        """Add two encrypted vectors."""
        if HAS_TENSEAL:
            vec_a = ts.ckks_vector_from(self.context, enc_a)
            vec_b = ts.ckks_vector_from(self.context, enc_b)
            result = vec_a + vec_b
            return result.serialize()
        else:
            import hashlib
            return hashlib.sha256(enc_a + enc_b).digest() * 4

    def homomorphic_multiply_plain(self, enc, scalar):
        """Multiply encrypted vector by plaintext scalar."""
        if HAS_TENSEAL:
            vec = ts.ckks_vector_from(self.context, enc)
            result = vec * scalar
            return result.serialize()
        else:
            import hashlib
            return hashlib.sha256(enc + str(scalar).encode()).digest() * 4


def run_demo():
    clear_screen()

    print_header("XCAPIT PRIVACY - DEMO DE TRANSPARENCIA FHE")

    animate_text("Esta demo te muestra EXACTAMENTE como tus datos")
    animate_text("permanecen cifrados durante todo el proceso.")
    animate_text("")
    animate_text("Veras los bytes REALES del ciphertext.")

    wait_for_user()

    # Initialize FHE
    print_step(0, "Inicializacion del Sistema FHE")
    demo = FHEDemo()
    wait_for_user()

    # Step 1: Original Data
    print_step(1, "DATOS ORIGINALES (Solo visibles en tu maquina)")

    print(f"\n  {Colors.BOLD}Empresa A - Datos de Credito:{Colors.ENDC}")
    empresa_a_data = {
        "salario_promedio": 55000.0,
        "edad_promedio": 38.5,
        "tasa_default": 0.03,
    }
    for key, value in empresa_a_data.items():
        print_data(key, value)

    print(f"\n  {Colors.BOLD}Empresa B - Datos de Credito:{Colors.ENDC}")
    empresa_b_data = {
        "salario_promedio": 48000.0,
        "edad_promedio": 42.1,
        "tasa_default": 0.05,
    }
    for key, value in empresa_b_data.items():
        print_data(key, value)

    wait_for_user()

    # Step 2: Encryption
    print_step(2, "CIFRADO LOCAL (Con tu clave privada)")

    print(f"\n  {Colors.CYAN}Cifrando datos de Empresa A...{Colors.ENDC}")
    time.sleep(0.5)

    enc_a = demo.encrypt(list(empresa_a_data.values()))
    print(f"\n  {Colors.BOLD}Ciphertext Empresa A:{Colors.ENDC}")
    print_data("encrypted_data", enc_a, encrypted=True)

    print(f"\n  {Colors.CYAN}Cifrando datos de Empresa B...{Colors.ENDC}")
    time.sleep(0.5)

    enc_b = demo.encrypt(list(empresa_b_data.values()))
    print(f"\n  {Colors.BOLD}Ciphertext Empresa B:{Colors.ENDC}")
    print_data("encrypted_data", enc_b, encrypted=True)

    print(f"\n  {Colors.GREEN}✓ Claves privadas permanecen en cada empresa{Colors.ENDC}")
    print(f"  {Colors.GREEN}✓ Solo el ciphertext viaja al servidor{Colors.ENDC}")

    wait_for_user()

    # Step 3: Server receives encrypted data
    print_step(3, "SERVIDOR RECIBE DATOS (Solo ve ciphertext)")

    print(f"\n  {Colors.RED}{'='*50}{Colors.ENDC}")
    print(f"  {Colors.RED}  VISTA DEL SERVIDOR - NO PUEDE DESCIFRAR{Colors.ENDC}")
    print(f"  {Colors.RED}{'='*50}{Colors.ENDC}")

    print(f"\n  Datos recibidos de Empresa A:")
    print_server_view("ciphertext_empresa_a", enc_a)

    print(f"\n  Datos recibidos de Empresa B:")
    print_server_view("ciphertext_empresa_b", enc_b)

    print(f"\n  {Colors.RED}⚠ El servidor NO SABE que:{Colors.ENDC}")
    print(f"    - Salario promedio A = 55000")
    print(f"    - Salario promedio B = 48000")
    print(f"    - Ni ningun otro valor original")

    wait_for_user()

    # Step 4: Homomorphic computation
    print_step(4, "COMPUTACION SOBRE DATOS CIFRADOS")

    print(f"\n  {Colors.CYAN}El servidor ejecuta operaciones homomorficas...{Colors.ENDC}")
    time.sleep(0.3)

    print(f"\n  {Colors.BOLD}Operacion: Suma homomorfica{Colors.ENDC}")
    print(f"  Enc(A) + Enc(B) = Enc(A + B)")
    time.sleep(0.5)

    enc_sum = demo.homomorphic_add(enc_a, enc_b)
    print(f"\n  Resultado de suma (CIFRADO):")
    print_server_view("encrypted_sum", enc_sum)

    print(f"\n  {Colors.BOLD}Operacion: Multiplicacion por escalar{Colors.ENDC}")
    print(f"  Enc(sum) * 0.5 = Enc(promedio)")
    time.sleep(0.5)

    enc_avg = demo.homomorphic_multiply_plain(enc_sum, 0.5)
    print(f"\n  Resultado promedio (CIFRADO):")
    print_server_view("encrypted_average", enc_avg)

    print(f"\n  {Colors.GREEN}✓ Todas las operaciones fueron sobre ciphertext{Colors.ENDC}")
    print(f"  {Colors.GREEN}✓ El servidor calculo el promedio SIN ver los valores{Colors.ENDC}")

    wait_for_user()

    # Step 5: Server sends encrypted result
    print_step(5, "SERVIDOR ENVIA RESULTADO (Aun cifrado)")

    print(f"\n  {Colors.RED}El servidor NO SABE el resultado:{Colors.ENDC}")
    print_server_view("resultado_cifrado", enc_avg)

    print(f"\n  {Colors.DIM}El servidor solo puede enviar estos bytes.{Colors.ENDC}")
    print(f"  {Colors.DIM}No tiene la clave para descifrarlos.{Colors.ENDC}")

    wait_for_user()

    # Step 6: Decryption
    print_step(6, "DESCIFRADO LOCAL (Solo tu puedes)")

    print(f"\n  {Colors.CYAN}Descifrando con tu clave privada...{Colors.ENDC}")
    time.sleep(0.5)

    if HAS_TENSEAL:
        decrypted = demo.decrypt(enc_avg)
        print(f"\n  {Colors.GREEN}{Colors.BOLD}RESULTADO DESCIFRADO:{Colors.ENDC}")
        print(f"\n  Promedio de ambas empresas:")
        labels = ["salario_promedio", "edad_promedio", "tasa_default"]
        expected = [(55000 + 48000) / 2, (38.5 + 42.1) / 2, (0.03 + 0.05) / 2]

        for i, (label, exp) in enumerate(zip(labels, expected)):
            actual = decrypted[i] if i < len(decrypted) else 0
            print(f"    {Colors.GREEN}{label}: {actual:.2f}{Colors.ENDC} (esperado: {exp:.2f})")
    else:
        print(f"\n  {Colors.YELLOW}[Simulacion - instala TenSEAL para valores reales]{Colors.ENDC}")
        print(f"\n  {Colors.GREEN}Resultado descifrado:{Colors.ENDC}")
        print(f"    salario_promedio: 51500.00")
        print(f"    edad_promedio: 40.30")
        print(f"    tasa_default: 0.04")

    wait_for_user()

    # Summary
    print_header("RESUMEN DE SEGURIDAD")

    print(f"""
  {Colors.GREEN}✓ Datos originales{Colors.ENDC}: Solo visibles en tu maquina
  {Colors.GREEN}✓ Cifrado{Colors.ENDC}: Realizado localmente con tu clave privada
  {Colors.GREEN}✓ Transmision{Colors.ENDC}: Solo ciphertext viaja al servidor
  {Colors.GREEN}✓ Procesamiento{Colors.ENDC}: Operaciones sobre datos cifrados
  {Colors.GREEN}✓ Resultado{Colors.ENDC}: Cifrado hasta que TU lo descifras

  {Colors.BOLD}El servidor NUNCA vio:{Colors.ENDC}
  {Colors.RED}✗{Colors.ENDC} Los salarios originales
  {Colors.RED}✗{Colors.ENDC} Las edades de los empleados
  {Colors.RED}✗{Colors.ENDC} Las tasas de default
  {Colors.RED}✗{Colors.ENDC} El resultado final

  {Colors.BOLD}{Colors.CYAN}Esto es Encriptacion Homomorfica (FHE) en accion.{Colors.ENDC}
  {Colors.BOLD}{Colors.CYAN}Tus datos siempre permanecen privados.{Colors.ENDC}
""")

    print(f"\n{Colors.DIM}Demo completada. Gracias por usar Xcapit Privacy.{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.DIM}Demo cancelada.{Colors.ENDC}\n")
        sys.exit(0)
