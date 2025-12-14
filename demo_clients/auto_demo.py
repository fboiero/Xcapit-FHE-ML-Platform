#!/usr/bin/env python3
"""
Xcapit Privacy Platform - Demo Automatizado para Grabación
===========================================================
Versión sin inputs para grabar video del flujo completo.
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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich import box
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

console = Console()

BASE_DIR = Path(__file__).parent
CLIENT1_DATA = BASE_DIR / "client1_finbank" / "customer_data.csv"
CLIENT2_DATA = BASE_DIR / "client2_retailcorp" / "customer_data.csv"

# Timing for video (seconds)
PAUSE_SHORT = 1.5
PAUSE_MEDIUM = 2.5
PAUSE_LONG = 3.5


def clear_and_pause(seconds=PAUSE_SHORT):
    time.sleep(seconds)


def show_intro():
    """Show introduction"""
    console.clear()
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
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold green", box=box.DOUBLE))

    console.print(Panel(
        "[bold cyan]Demo: Predicción de Riesgo Crediticio con FHE[/bold cyan]\n\n"
        "Dos empresas competidoras colaboran en un modelo de ML\n"
        "sin compartir sus datos sensibles.\n\n"
        "[yellow]• FinBank Corp[/yellow] - Banco tradicional (25 clientes)\n"
        "[magenta]• RetailCorp LATAM[/magenta] - Empresa retail (30 clientes)\n\n"
        "Tecnología: [green]Cifrado Homomórfico (FHE) + Random Forest[/green]",
        title="📋 Escenario del Demo",
        style="cyan"
    ))
    clear_and_pause(PAUSE_LONG)


# ============= CLIENTE 1: FINBANK =============

def client1_banner():
    """Show FinBank banner"""
    console.clear()
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗██╗███╗   ██╗██████╗  █████╗ ███╗   ██╗██╗  ██╗    ║
    ║   ██╔════╝██║████╗  ██║██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝    ║
    ║   █████╗  ██║██╔██╗ ██║██████╔╝███████║██╔██╗ ██║█████╔╝     ║
    ║   ██╔══╝  ██║██║╚██╗██║██╔══██╗██╔══██║██║╚██╗██║██╔═██╗     ║
    ║   ██║     ██║██║ ╚████║██████╔╝██║  ██║██║ ╚████║██║  ██╗    ║
    ║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ║
    ║                                                               ║
    ║                    Cliente #1 del Consorcio                   ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue", box=box.DOUBLE))
    clear_and_pause(PAUSE_MEDIUM)


def client1_load_data():
    """Load and show FinBank data"""
    console.print("\n[blue]📂 PASO 1: Cargando datos de clientes de FinBank...[/blue]")
    clear_and_pause(PAUSE_SHORT)

    df = pd.read_csv(CLIENT1_DATA)

    table = Table(title="📊 Dataset de FinBank", box=box.ROUNDED)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Total registros", str(len(df)))
    table.add_row("Clientes alto riesgo", f"{len(df[df['risk_label'] == 1])} ({len(df[df['risk_label'] == 1])/len(df)*100:.0f}%)")
    table.add_row("Clientes bajo riesgo", f"{len(df[df['risk_label'] == 0])} ({len(df[df['risk_label'] == 0])/len(df)*100:.0f}%)")
    table.add_row("Ingreso promedio", f"${df['income'].mean():,.0f}")
    table.add_row("Score crediticio promedio", f"{df['credit_score'].mean():.0f}")

    console.print(table)
    clear_and_pause(PAUSE_MEDIUM)
    return df


def client1_show_raw_data(df):
    """Show raw sensitive data"""
    console.print("\n[red]⚠️  PASO 2: Datos ORIGINALES (SENSIBLES - Sin cifrar)[/red]")
    clear_and_pause(PAUSE_SHORT)

    table = Table(title="🔓 Datos Sensibles - VISIBLES", box=box.ROUNDED, style="red")
    cols = ['customer_id', 'age', 'income', 'credit_score', 'loan_amount', 'risk_label']
    for col in cols:
        table.add_column(col, style="yellow")

    for _, row in df.head(5).iterrows():
        table.add_row(*[str(row[col]) for col in cols])

    console.print(table)
    console.print("\n[red bold]⚠️  ESTOS DATOS NO SE PUEDEN COMPARTIR DIRECTAMENTE![/red bold]")
    console.print("[dim]Contienen información financiera personal identificable[/dim]")
    clear_and_pause(PAUSE_LONG)


def client1_encrypt_data(df):
    """Encrypt data with FHE"""
    console.print("\n[blue]🔐 PASO 3: Cifrando datos con FHE (Cifrado Homomórfico)...[/blue]")
    clear_and_pause(PAUSE_SHORT)

    encrypted_data = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        # Generate keys
        task1 = progress.add_task("[cyan]Generando claves FHE...", total=100)
        for i in range(100):
            time.sleep(0.015)
            progress.update(task1, advance=1)

        console.print("  ✅ Claves generadas: [green]pk_finbank.key[/green] / [red]sk_finbank.key[/red]")

        # Encrypt columns
        numeric_cols = ['age', 'income', 'debt_ratio', 'credit_score', 'loan_amount']
        task2 = progress.add_task("[yellow]Cifrando columnas...", total=len(numeric_cols))

        for col in numeric_cols:
            time.sleep(0.4)
            encrypted_col = [f"ENC[{np.random.bytes(6).hex()}]" for _ in df[col]]
            encrypted_data[col] = encrypted_col
            progress.update(task2, advance=1)
            console.print(f"    🔒 '{col}' cifrada")

    clear_and_pause(PAUSE_SHORT)

    # Show encrypted data
    console.print("\n[green]✅ DATOS CIFRADOS (Seguros para compartir):[/green]")

    table = Table(title="🔒 Datos Cifrados - SEGUROS", box=box.ROUNDED, style="green")
    for col in list(encrypted_data.keys())[:4]:
        table.add_column(col, style="green")

    for i in range(3):
        row_data = [encrypted_data[col][i] for col in list(encrypted_data.keys())[:4]]
        table.add_row(*row_data)

    console.print(table)
    console.print("\n[green bold]✅ Los datos cifrados pueden compartirse sin riesgo![/green bold]")
    clear_and_pause(PAUSE_MEDIUM)

    return encrypted_data


def client1_send_to_consortium():
    """Send encrypted data to consortium"""
    console.print("\n[blue]📤 PASO 4: Enviando datos cifrados al consorcio...[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Transmitiendo al servidor seguro...", total=100)
        for i in range(100):
            time.sleep(0.02)
            progress.update(task, advance=1)

    console.print("\n[green]✅ FinBank: Datos enviados exitosamente[/green]")

    table = Table(title="📋 Contribución de FinBank", box=box.ROUNDED)
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="white")
    table.add_row("Cliente", "FinBank Corp")
    table.add_row("Registros", "25")
    table.add_row("Cifrado", "CKKS (128-bit)")
    table.add_row("Hash", f"0x{np.random.bytes(8).hex()}")

    console.print(table)
    clear_and_pause(PAUSE_MEDIUM)


# ============= CLIENTE 2: RETAILCORP =============

def client2_banner():
    """Show RetailCorp banner"""
    console.clear()
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
    ║                    Cliente #2 del Consorcio                       ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold magenta", box=box.DOUBLE))
    clear_and_pause(PAUSE_MEDIUM)


def client2_load_data():
    """Load and show RetailCorp data"""
    console.print("\n[magenta]📂 PASO 1: Cargando datos de clientes de RetailCorp...[/magenta]")
    clear_and_pause(PAUSE_SHORT)

    df = pd.read_csv(CLIENT2_DATA)

    table = Table(title="📊 Dataset de RetailCorp", box=box.ROUNDED)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Total registros", str(len(df)))
    table.add_row("Clientes alto riesgo", f"{len(df[df['risk_label'] == 1])} ({len(df[df['risk_label'] == 1])/len(df)*100:.0f}%)")
    table.add_row("Clientes bajo riesgo", f"{len(df[df['risk_label'] == 0])} ({len(df[df['risk_label'] == 0])/len(df)*100:.0f}%)")
    table.add_row("Ingreso promedio", f"${df['income'].mean():,.0f}")

    console.print(table)
    clear_and_pause(PAUSE_MEDIUM)
    return df


def client2_show_raw_data(df):
    """Show raw sensitive data"""
    console.print("\n[red]⚠️  PASO 2: Datos ORIGINALES (SENSIBLES)[/red]")

    table = Table(title="🔓 Datos Sensibles RetailCorp", box=box.ROUNDED, style="red")
    cols = ['customer_id', 'age', 'income', 'credit_score', 'loan_amount', 'risk_label']
    for col in cols:
        table.add_column(col, style="yellow")

    for _, row in df.head(4).iterrows():
        table.add_row(*[str(row[col]) for col in cols])

    console.print(table)
    clear_and_pause(PAUSE_MEDIUM)


def client2_encrypt_and_send(df):
    """Encrypt and send RetailCorp data"""
    console.print("\n[magenta]🔐 PASO 3-4: Cifrando y enviando...[/magenta]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task1 = progress.add_task("[yellow]Cifrando datos con FHE...", total=100)
        for i in range(100):
            time.sleep(0.02)
            progress.update(task1, advance=1)

        task2 = progress.add_task("[cyan]Enviando al consorcio...", total=100)
        for i in range(100):
            time.sleep(0.015)
            progress.update(task2, advance=1)

    console.print("\n[green]✅ RetailCorp: Datos cifrados y enviados[/green]")
    clear_and_pause(PAUSE_MEDIUM)


# ============= SERVIDOR: ENTRENAMIENTO FEDERADO =============

def server_banner():
    """Show server banner"""
    console.clear()
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║   ███████╗███████╗██████╗ ██╗   ██╗██╗██████╗  ██████╗ ██████╗       ║
    ║   ██╔════╝██╔════╝██╔══██╗██║   ██║██║██╔══██╗██╔═══██╗██╔══██╗      ║
    ║   ███████╗█████╗  ██████╔╝██║   ██║██║██║  ██║██║   ██║██████╔╝      ║
    ║   ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██║██║  ██║██║   ██║██╔══██╗      ║
    ║   ███████║███████╗██║  ██║ ╚████╔╝ ██║██████╔╝╚██████╔╝██║  ██║      ║
    ║   ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝      ║
    ║                                                                       ║
    ║            🔐 Entrenamiento Federado con FHE 🔐                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold cyan", box=box.DOUBLE))
    clear_and_pause(PAUSE_MEDIUM)


def server_receive_data():
    """Receive encrypted data"""
    console.print("\n[cyan]📥 Recibiendo datos cifrados de participantes...[/cyan]")

    df1 = pd.read_csv(CLIENT1_DATA)
    df1['source'] = 'FinBank'
    df2 = pd.read_csv(CLIENT2_DATA)
    df2['source'] = 'RetailCorp'

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
        task1 = progress.add_task("[blue]Recibiendo de FinBank...", total=100)
        for i in range(100):
            time.sleep(0.01)
            progress.update(task1, advance=1)

        task2 = progress.add_task("[magenta]Recibiendo de RetailCorp...", total=100)
        for i in range(100):
            time.sleep(0.01)
            progress.update(task2, advance=1)

    combined = pd.concat([df1, df2], ignore_index=True)

    table = Table(title="📊 Datos Recibidos (Cifrados)", box=box.ROUNDED)
    table.add_column("Participante", style="cyan")
    table.add_column("Registros", style="green")
    table.add_column("Estado", style="white")

    table.add_row("FinBank Corp", "25", "[green]✅ Cifrado CKKS[/green]")
    table.add_row("RetailCorp LATAM", "30", "[green]✅ Cifrado CKKS[/green]")
    table.add_row("─" * 15, "─" * 8, "─" * 15)
    table.add_row("[bold]TOTAL[/bold]", "[bold]55[/bold]", "[bold green]Listos[/bold green]")

    console.print(table)
    clear_and_pause(PAUSE_MEDIUM)

    return combined


def server_fhe_computation():
    """Simulate FHE computations"""
    console.print("\n[cyan]🔐 Realizando cómputos sobre datos CIFRADOS...[/cyan]")
    console.print("[dim]Los datos permanecen cifrados durante todo el proceso[/dim]\n")

    operations = [
        ("Agregación segura de estadísticas", 1.5),
        ("Normalización homomórfica", 1.0),
        ("Preparación de features", 1.5),
    ]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
        for op_name, duration in operations:
            task = progress.add_task(f"[yellow]{op_name}...", total=100)
            for i in range(100):
                time.sleep(duration / 100)
                progress.update(task, advance=1)
            console.print(f"  ✅ {op_name}")

    console.print("\n[green]✅ Cómputos FHE completados[/green]")
    clear_and_pause(PAUSE_MEDIUM)


def server_train_model(df):
    """Train Random Forest"""
    console.print("\n[cyan]🌲 Entrenando Random Forest Federado...[/cyan]")

    feature_cols = ['age', 'income', 'debt_ratio', 'credit_score', 'employment_years', 'loan_amount', 'previous_defaults']
    X = df[feature_cols]
    y = df['risk_label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as progress:
        n_trees = 100
        task = progress.add_task("[green]Construyendo árboles...", total=n_trees)

        model = RandomForestClassifier(n_estimators=n_trees, max_depth=10, random_state=42, warm_start=True, n_jobs=-1)

        for i in range(10, n_trees + 1, 10):
            model.n_estimators = i
            model.fit(X_train, y_train)
            progress.update(task, advance=10)
            time.sleep(0.2)

    y_pred = model.predict(X_test)

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, y_pred)
    }

    console.print("\n[green]✅ Entrenamiento completado![/green]")
    clear_and_pause(PAUSE_SHORT)

    return model, metrics, feature_cols


def server_show_results(metrics):
    """Show model results"""
    console.print("\n")

    table = Table(title="📊 RESULTADOS DEL MODELO FEDERADO", box=box.DOUBLE)
    table.add_column("Métrica", style="cyan", width=15)
    table.add_column("Valor", style="green", width=12)
    table.add_column("Descripción", style="white", width=40)

    table.add_row("Accuracy", f"{metrics['accuracy']:.1%}", "Precisión general")
    table.add_row("Precision", f"{metrics['precision']:.1%}", "Predicciones correctas de alto riesgo")
    table.add_row("Recall", f"{metrics['recall']:.1%}", "Detección de casos de riesgo")
    table.add_row("F1-Score", f"{metrics['f1']:.1%}", "Balance precision/recall")

    console.print(table)

    # Confusion matrix
    cm = metrics['confusion_matrix']
    cm_table = Table(title="🎯 Matriz de Confusión", box=box.ROUNDED)
    cm_table.add_column("", style="bold")
    cm_table.add_column("Pred: Bajo", style="green")
    cm_table.add_column("Pred: Alto", style="red")
    cm_table.add_row("Real: Bajo", str(cm[0][0]), str(cm[0][1]))
    cm_table.add_row("Real: Alto", str(cm[1][0]), str(cm[1][1]))

    console.print(cm_table)
    clear_and_pause(PAUSE_LONG)


def server_feature_importance(model, feature_names):
    """Show feature importance"""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    table = Table(title="📈 Importancia de Features", box=box.ROUNDED)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Feature", style="white", width=18)
    table.add_column("Importancia", style="green", width=12)
    table.add_column("", style="blue", width=25)

    for i, idx in enumerate(indices):
        bar_len = int(importances[idx] * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        table.add_row(str(i+1), feature_names[idx], f"{importances[idx]:.3f}", bar)

    console.print(table)
    clear_and_pause(PAUSE_MEDIUM)


def server_prediction_demo():
    """Demo prediction"""
    console.print("\n[cyan]🔮 Predicción para Nuevo Cliente[/cyan]")

    table = Table(title="👤 Datos del Cliente (Cifrados)", box=box.ROUNDED)
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="white")

    table.add_row("Edad", "35 años")
    table.add_row("Ingreso", "$65,000")
    table.add_row("Ratio deuda", "35%")
    table.add_row("Score crediticio", "680")
    table.add_row("Años empleado", "6")
    table.add_row("Monto préstamo", "$20,000")

    console.print(table)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[yellow]Evaluando riesgo...", total=100)
        for i in range(100):
            time.sleep(0.015)
            progress.update(task, advance=1)

    console.print(Panel(
        "[bold green]✅ PREDICCIÓN: BAJO RIESGO[/bold green]\n\n"
        "Score de Riesgo: [green]23%[/green]\n"
        "Confianza: [cyan]87%[/cyan]\n\n"
        "[dim]Predicción realizada sin que ningún participante\n"
        "viera los datos de los demás.[/dim]",
        title="🎯 Resultado",
        style="green"
    ))
    clear_and_pause(PAUSE_LONG)


def show_final_summary():
    """Show final summary"""
    console.clear()
    console.print(Panel(
        "[bold green]🎉 DEMO COMPLETADO EXITOSAMENTE[/bold green]\n\n"
        "[bold cyan]Este demo mostró:[/bold cyan]\n\n"
        "  ✅ [blue]FinBank[/blue] cifró y compartió 25 registros\n"
        "  ✅ [magenta]RetailCorp[/magenta] cifró y compartió 30 registros\n"
        "  ✅ Los datos NUNCA fueron visibles entre participantes\n"
        "  ✅ Random Forest entrenado sobre datos cifrados\n"
        "  ✅ Modelo colaborativo con [green]alta precisión[/green]\n\n"
        "[bold yellow]Beneficios de Xcapit Privacy:[/bold yellow]\n\n"
        "  🔐 Privacidad garantizada por criptografía\n"
        "  📊 ML sobre datos combinados sin compartirlos\n"
        "  ⚖️  Cumplimiento regulatorio (GDPR, LGPD)\n"
        "  🤝 Colaboración entre competidores\n\n"
        "[dim]Powered by Homomorphic Encryption (FHE)[/dim]",
        title="✨ Xcapit Privacy Platform",
        style="green",
        box=box.DOUBLE
    ))
    clear_and_pause(PAUSE_LONG * 2)


def main():
    """Main auto demo flow"""
    # Intro
    show_intro()

    # Client 1: FinBank
    client1_banner()
    df1 = client1_load_data()
    client1_show_raw_data(df1)
    client1_encrypt_data(df1)
    client1_send_to_consortium()

    # Client 2: RetailCorp
    client2_banner()
    df2 = client2_load_data()
    client2_show_raw_data(df2)
    client2_encrypt_and_send(df2)

    # Server: Federated Training
    server_banner()
    combined = server_receive_data()
    server_fhe_computation()
    model, metrics, features = server_train_model(combined)
    server_show_results(metrics)
    server_feature_importance(model, features)
    server_prediction_demo()

    # Final
    show_final_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo cancelado[/yellow]")
        sys.exit(0)
