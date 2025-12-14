#!/usr/bin/env python3
"""
RetailCorp - Cliente Demo para Xcapit Privacy Platform
=======================================================
Aplicación que simula una empresa retail compartiendo datos de riesgo crediticio
de forma privada usando cifrado homomórfico (FHE).
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

console = Console()

# Client configuration
CLIENT_NAME = "RetailCorp LATAM"
CLIENT_ID = "retailcorp_002"
CLIENT_COLOR = "magenta"
DATA_FILE = Path(__file__).parent / "customer_data.csv"
OUTPUT_DIR = Path(__file__).parent / "encrypted_output"


def show_banner():
    """Display client banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ██████╗ ███████╗████████╗ █████╗ ██╗██╗      ██████╗██████╗    ║
    ║   ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██║██║     ██╔════╝██╔══██╗   ║
    ║   ██████╔╝█████╗     ██║   ███████║██║██║     ██║     ██████╔╝   ║
    ║   ██╔══██╗██╔══╝     ██║   ██╔══██║██║██║     ██║     ██╔═══╝    ║
    ║   ██║  ██║███████╗   ██║   ██║  ██║██║███████╗╚██████╗██║        ║
    ║   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝╚═╝        ║
    ║                        LATAM                                      ║
    ║                                                                   ║
    ║            Xcapit Privacy Platform - Demo Client                  ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style=f"bold {CLIENT_COLOR}", box=box.DOUBLE))


def load_data():
    """Load customer data from CSV"""
    console.print(f"\n[{CLIENT_COLOR}]📂 Cargando datos de clientes...[/{CLIENT_COLOR}]")

    df = pd.read_csv(DATA_FILE)

    # Show data summary
    table = Table(title=f"📊 Dataset: {DATA_FILE.name}", box=box.ROUNDED)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Total registros", str(len(df)))
    table.add_row("Total columnas", str(len(df.columns)))
    table.add_row("Clientes alto riesgo", str(len(df[df['risk_label'] == 1])))
    table.add_row("Clientes bajo riesgo", str(len(df[df['risk_label'] == 0])))
    table.add_row("Ingreso promedio", f"${df['income'].mean():,.0f}")
    table.add_row("Score crediticio promedio", f"{df['credit_score'].mean():.0f}")

    console.print(table)

    return df


def show_sample_data(df):
    """Show sample of original data"""
    console.print(f"\n[{CLIENT_COLOR}]👁️ Muestra de datos ORIGINALES (sin cifrar):[/{CLIENT_COLOR}]")

    table = Table(title="Datos sensibles - VISIBLES", box=box.ROUNDED, style="red")
    for col in df.columns[:6]:
        table.add_column(col, style="yellow")

    for _, row in df.head(5).iterrows():
        table.add_row(*[str(row[col]) for col in df.columns[:6]])

    console.print(table)
    console.print("[red]⚠️  ADVERTENCIA: Estos datos son sensibles y no deben compartirse![/red]")


def simulate_fhe_encryption(df):
    """Simulate FHE encryption process with visual feedback"""
    console.print(f"\n[{CLIENT_COLOR}]🔐 Iniciando cifrado homomórfico (FHE)...[/{CLIENT_COLOR}]")

    OUTPUT_DIR.mkdir(exist_ok=True)

    encrypted_data = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        # Step 1: Generate keys
        task1 = progress.add_task("[cyan]Generando claves FHE...", total=100)
        for i in range(100):
            time.sleep(0.02)
            progress.update(task1, advance=1)

        console.print("  ✅ Claves públicas y privadas generadas")
        console.print("  📁 Clave pública: [green]pk_retailcorp_2024.key[/green]")
        console.print("  📁 Clave privada: [red]sk_retailcorp_2024.key (NUNCA compartir)[/red]")

        # Step 2: Encrypt each column
        numeric_cols = ['age', 'income', 'debt_ratio', 'credit_score',
                       'employment_years', 'loan_amount', 'previous_defaults']

        task2 = progress.add_task("[yellow]Cifrando columnas numéricas...", total=len(numeric_cols))

        for col in numeric_cols:
            time.sleep(0.5)  # Simulate encryption time

            # Simulate encrypted values (in real FHE, these would be ciphertexts)
            encrypted_col = []
            for val in df[col]:
                # Generate fake ciphertext representation
                encrypted_val = f"ENC[{np.random.bytes(8).hex()}]"
                encrypted_col.append(encrypted_val)

            encrypted_data[col] = encrypted_col
            progress.update(task2, advance=1)
            console.print(f"    🔒 Columna '{col}' cifrada")

        # Step 3: Package encrypted data
        task3 = progress.add_task("[green]Empaquetando datos cifrados...", total=100)
        for i in range(100):
            time.sleep(0.01)
            progress.update(task3, advance=1)

    # Show encrypted data sample
    console.print(f"\n[{CLIENT_COLOR}]🔒 Muestra de datos CIFRADOS (seguros para compartir):[/{CLIENT_COLOR}]")

    table = Table(title="Datos cifrados - SEGUROS", box=box.ROUNDED, style="green")
    for col in list(encrypted_data.keys())[:4]:
        table.add_column(col, style="green")

    for i in range(3):
        row_data = [encrypted_data[col][i] for col in list(encrypted_data.keys())[:4]]
        table.add_row(*row_data)

    console.print(table)
    console.print("[green]✅ Los datos cifrados pueden compartirse sin revelar información sensible[/green]")

    # Save encrypted data info
    metadata = {
        "client_id": CLIENT_ID,
        "client_name": CLIENT_NAME,
        "timestamp": datetime.now().isoformat(),
        "records_count": len(df),
        "columns_encrypted": numeric_cols,
        "encryption_scheme": "CKKS (FHE)",
        "security_level": "128-bit"
    }

    return encrypted_data, metadata


def send_to_consortium(encrypted_data, metadata):
    """Simulate sending encrypted data to consortium"""
    console.print(f"\n[{CLIENT_COLOR}]📤 Enviando datos cifrados al consorcio...[/{CLIENT_COLOR}]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:

        task = progress.add_task("[cyan]Transmitiendo al servidor seguro...", total=100)

        # Simulate network transfer
        for i in range(100):
            time.sleep(0.03)
            progress.update(task, advance=1)

    console.print("\n[green]✅ Datos enviados exitosamente al consorcio[/green]")

    # Show transmission summary
    table = Table(title="📋 Resumen de Contribución", box=box.ROUNDED)
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="white")

    table.add_row("Cliente", metadata["client_name"])
    table.add_row("ID de Cliente", metadata["client_id"])
    table.add_row("Registros enviados", str(metadata["records_count"]))
    table.add_row("Columnas cifradas", str(len(metadata["columns_encrypted"])))
    table.add_row("Esquema de cifrado", metadata["encryption_scheme"])
    table.add_row("Nivel de seguridad", metadata["security_level"])
    table.add_row("Timestamp", metadata["timestamp"])
    table.add_row("Hash de verificación", f"0x{np.random.bytes(16).hex()}")

    console.print(table)

    return True


def wait_for_other_clients():
    """Wait for other consortium members"""
    console.print(f"\n[{CLIENT_COLOR}]⏳ Esperando a otros miembros del consorcio...[/{CLIENT_COLOR}]")

    members = [
        ("FinBank Corp", "Completado ✅"),
        ("RetailCorp LATAM", "Completado ✅"),
    ]

    with Live(console=console, refresh_per_second=4) as live:
        for i in range(8):
            table = Table(title="👥 Miembros del Consorcio", box=box.ROUNDED)
            table.add_column("Miembro", style="cyan")
            table.add_column("Estado", style="white")

            for name, status in members:
                table.add_row(name, "[green]Completado ✅[/green]")

            live.update(table)
            time.sleep(0.3)

    console.print("\n[green]✅ Todos los miembros han contribuido sus datos[/green]")


def main():
    """Main client application flow"""
    show_banner()

    console.print(Panel(
        f"[bold]Cliente:[/bold] {CLIENT_NAME}\n"
        f"[bold]ID:[/bold] {CLIENT_ID}\n"
        f"[bold]Modo:[/bold] Demo - Predicción de Riesgo Crediticio",
        title="ℹ️ Información del Cliente",
        style=CLIENT_COLOR
    ))

    # Step 1: Load data
    input("\n[Presiona ENTER para cargar los datos...]")
    df = load_data()

    # Step 2: Show original data
    input("\n[Presiona ENTER para ver los datos originales...]")
    show_sample_data(df)

    # Step 3: Encrypt data
    input("\n[Presiona ENTER para iniciar el cifrado FHE...]")
    encrypted_data, metadata = simulate_fhe_encryption(df)

    # Step 4: Send to consortium
    input("\n[Presiona ENTER para enviar al consorcio...]")
    send_to_consortium(encrypted_data, metadata)

    # Step 5: Wait for others
    input("\n[Presiona ENTER para ver el estado del consorcio...]")
    wait_for_other_clients()

    console.print(Panel(
        "[bold green]🎉 Proceso completado exitosamente![/bold green]\n\n"
        "Los datos de RetailCorp han sido:\n"
        "  ✅ Cifrados con FHE (cifrado homomórfico)\n"
        "  ✅ Enviados al consorcio de forma segura\n"
        "  ✅ Listos para entrenamiento federado\n\n"
        "[dim]Los datos originales NUNCA salieron de este sistema.[/dim]",
        title="✨ Contribución Completada",
        style="green"
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operación cancelada por el usuario[/yellow]")
        sys.exit(0)
