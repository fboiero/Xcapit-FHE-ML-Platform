#!/usr/bin/env python3
"""
Xcapit Privacy Platform - Demo Launcher
=========================================
Script para ejecutar el demo completo con dos clientes
y entrenamiento federado.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

BASE_DIR = Path(__file__).parent


def show_main_banner():
    """Display main demo banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║   ██╗  ██╗ ██████╗ █████╗ ██████╗ ██╗████████╗    ██████╗ ███████╗███╗   ███╗║
    ║   ╚██╗██╔╝██╔════╝██╔══██╗██╔══██╗██║╚══██╔══╝    ██╔══██╗██╔════╝████╗ ████║║
    ║    ╚███╔╝ ██║     ███████║██████╔╝██║   ██║       ██║  ██║█████╗  ██╔████╔██║║
    ║    ██╔██╗ ██║     ██╔══██║██╔═══╝ ██║   ██║       ██║  ██║██╔══╝  ██║╚██╔╝██║║
    ║   ██╔╝ ██╗╚██████╗██║  ██║██║     ██║   ██║       ██████╔╝███████╗██║ ╚═╝ ██║║
    ║   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝   ╚═╝       ╚═════╝ ╚══════╝╚═╝     ╚═╝║
    ║                                                                              ║
    ║              🔐 Privacy-Preserving Machine Learning Platform 🔐              ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold green", box=box.DOUBLE))


def show_demo_info():
    """Display demo information"""
    console.print(Panel(
        "[bold]Demo: Predicción de Riesgo Crediticio Federado[/bold]\n\n"
        "Este demo muestra cómo dos empresas competidoras pueden colaborar\n"
        "en un modelo de ML sin compartir sus datos sensibles.\n\n"
        "[cyan]Participantes:[/cyan]\n"
        "  • FinBank Corp - Banco tradicional (25 registros)\n"
        "  • RetailCorp LATAM - Empresa de retail (30 registros)\n\n"
        "[cyan]Tecnología:[/cyan]\n"
        "  • Cifrado Homomórfico (FHE) - Los datos permanecen cifrados\n"
        "  • Aprendizaje Federado - Entrenamiento distribuido\n"
        "  • Random Forest - Modelo de clasificación\n\n"
        "[cyan]Flujo del Demo:[/cyan]\n"
        "  1️⃣  Cliente 1 (FinBank) carga y cifra sus datos\n"
        "  2️⃣  Cliente 2 (RetailCorp) carga y cifra sus datos\n"
        "  3️⃣  Servidor coordina entrenamiento sobre datos cifrados\n"
        "  4️⃣  Se genera modelo colaborativo con ~92% accuracy",
        title="📋 Información del Demo",
        style="cyan"
    ))


def show_menu():
    """Show demo menu"""
    table = Table(title="🚀 Opciones del Demo", box=box.ROUNDED)
    table.add_column("Opción", style="cyan", width=8)
    table.add_column("Descripción", style="white", width=50)

    table.add_row("1", "Ejecutar Cliente 1 (FinBank Corp)")
    table.add_row("2", "Ejecutar Cliente 2 (RetailCorp LATAM)")
    table.add_row("3", "Ejecutar Entrenamiento Federado (Servidor)")
    table.add_row("4", "Ejecutar Demo Completo (Automático)")
    table.add_row("5", "Ver CSVs de datos de ejemplo")
    table.add_row("0", "Salir")

    console.print(table)

    return input("\n[Selecciona una opción]: ").strip()


def run_client1():
    """Run FinBank client"""
    console.print("\n[blue]🏦 Iniciando Cliente FinBank...[/blue]\n")
    time.sleep(1)
    subprocess.run([sys.executable, str(BASE_DIR / "client1_finbank" / "client_app.py")])


def run_client2():
    """Run RetailCorp client"""
    console.print("\n[magenta]🛒 Iniciando Cliente RetailCorp...[/magenta]\n")
    time.sleep(1)
    subprocess.run([sys.executable, str(BASE_DIR / "client2_retailcorp" / "client_app.py")])


def run_server():
    """Run federated training server"""
    console.print("\n[cyan]🖥️ Iniciando Servidor de Entrenamiento Federado...[/cyan]\n")
    time.sleep(1)
    subprocess.run([sys.executable, str(BASE_DIR / "shared" / "federated_training.py")])


def show_csv_data():
    """Show sample CSV data"""
    import pandas as pd

    console.print("\n[cyan]📊 Datos de FinBank (primeros 5 registros):[/cyan]")
    df1 = pd.read_csv(BASE_DIR / "client1_finbank" / "customer_data.csv")
    console.print(df1.head().to_string())

    console.print("\n[magenta]📊 Datos de RetailCorp (primeros 5 registros):[/magenta]")
    df2 = pd.read_csv(BASE_DIR / "client2_retailcorp" / "customer_data.csv")
    console.print(df2.head().to_string())

    input("\n[Presiona ENTER para continuar...]")


def run_full_demo():
    """Run complete demo sequence"""
    console.print(Panel(
        "[bold]Modo Demo Completo[/bold]\n\n"
        "Se ejecutarán las siguientes aplicaciones en secuencia:\n"
        "  1. Cliente FinBank (cifrado y envío de datos)\n"
        "  2. Cliente RetailCorp (cifrado y envío de datos)\n"
        "  3. Servidor (entrenamiento federado y resultados)\n\n"
        "[yellow]Nota: Sigue las instrucciones en pantalla (presiona ENTER)[/yellow]",
        title="🎬 Demo Completo",
        style="green"
    ))

    input("\n[Presiona ENTER para comenzar el demo completo...]")

    # Run each component
    console.rule("[blue]PARTE 1: Cliente FinBank[/blue]")
    run_client1()

    console.rule("[magenta]PARTE 2: Cliente RetailCorp[/magenta]")
    run_client2()

    console.rule("[cyan]PARTE 3: Entrenamiento Federado[/cyan]")
    run_server()


def main():
    """Main demo launcher"""
    while True:
        console.clear()
        show_main_banner()
        show_demo_info()
        choice = show_menu()

        if choice == "1":
            run_client1()
            input("\n[Presiona ENTER para volver al menú...]")
        elif choice == "2":
            run_client2()
            input("\n[Presiona ENTER para volver al menú...]")
        elif choice == "3":
            run_server()
            input("\n[Presiona ENTER para volver al menú...]")
        elif choice == "4":
            run_full_demo()
            input("\n[Presiona ENTER para volver al menú...]")
        elif choice == "5":
            show_csv_data()
        elif choice == "0":
            console.print("\n[green]¡Gracias por usar Xcapit Privacy Platform![/green]")
            break
        else:
            console.print("[red]Opción no válida[/red]")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo cancelado[/yellow]")
        sys.exit(0)
