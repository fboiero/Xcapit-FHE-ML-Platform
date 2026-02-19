#!/usr/bin/env python3
"""
Xcapit Privacy - Grabador Automatico de Demos

Este script graba automaticamente:
1. Demo Web (navegador con Selenium + grabacion de pantalla)
2. Demo CLI (terminal con script/ttyrec)

No requiere intervencion del usuario.

Uso:
    python scripts/record_all_demos.py
"""

import subprocess
import time
import os
import sys
import signal
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_DIR = Path(__file__).parent.parent
RECORDINGS_DIR = PROJECT_DIR / "recordings"
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Output files
WEB_VIDEO = RECORDINGS_DIR / f"demo_web_{TIMESTAMP}.mp4"
CLI_VIDEO = RECORDINGS_DIR / f"demo_cli_{TIMESTAMP}.mp4"
CLI_CAST = RECORDINGS_DIR / f"demo_cli_{TIMESTAMP}.cast"
CLI_LOG = RECORDINGS_DIR / f"demo_cli_{TIMESTAMP}.txt"

# Process handles
processes = []


def log(msg, level="INFO"):
    """Print colored log message."""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
    }
    reset = "\033[0m"
    print(f"{colors.get(level, '')}{level}: {msg}{reset}")


def cleanup():
    """Kill all spawned processes."""
    log("Limpiando procesos...", "WARNING")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass
    processes.clear()


def setup():
    """Create output directories."""
    RECORDINGS_DIR.mkdir(exist_ok=True)
    log(f"Directorio de grabaciones: {RECORDINGS_DIR}", "INFO")


def start_backend():
    """Start the backend API server."""
    log("Iniciando backend API...", "INFO")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_DIR)

    proc = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "sdk.api.server"],
        cwd=str(PROJECT_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(proc)

    # Wait for backend to be ready
    for i in range(30):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:8000/health", timeout=1)
            log("Backend listo en http://localhost:8000", "SUCCESS")
            return True
        except:
            time.sleep(1)

    log("Backend no respondio", "ERROR")
    return False


def start_frontend():
    """Start the frontend dev server."""
    log("Iniciando frontend...", "INFO")

    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(PROJECT_DIR / "dashboard"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(proc)

    # Wait for frontend (port 3000)
    for i in range(30):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:3000", timeout=1)
            log("Frontend listo en http://localhost:3000", "SUCCESS")
            return True
        except:
            time.sleep(1)

    log("Frontend no respondio", "ERROR")
    return False


def start_screen_recording(output_file, duration=90):
    """Start screen recording with ffmpeg."""
    log(f"Iniciando grabacion de pantalla ({duration}s)...", "INFO")

    # Use screen capture device (index 4 on this Mac)
    proc = subprocess.Popen([
        "ffmpeg",
        "-y",  # Overwrite output
        "-f", "avfoundation",
        "-framerate", "30",
        "-i", "4:none",  # Screen 0, no audio
        "-t", str(duration),
        "-vf", "scale=1920:1080",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        str(output_file)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    processes.append(proc)
    return proc


def run_web_demo_selenium():
    """Run the web demo using Selenium (no interaction needed)."""
    log("Ejecutando demo web con Selenium...", "INFO")

    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        log("Instalando selenium y webdriver-manager...", "WARNING")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "selenium", "webdriver-manager"])
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--window-position=0,0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        base_url = "http://localhost:3000"

        # Scene 1: Register
        log("  Escena 1: Registro", "INFO")
        driver.get(f"{base_url}/register")
        time.sleep(2)

        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        for char in "FinTech Alpha":
            name_input.send_keys(char)
            time.sleep(0.05)

        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        for char in "demo@fintech.com":
            email_input.send_keys(char)
            time.sleep(0.05)

        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)

        # Scene 2: Navigate to Demo
        log("  Escena 2: Demo de Privacidad", "INFO")
        driver.get(f"{base_url}/demo")
        time.sleep(2)

        # Click start demo
        start_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bg-brand-600"))
        )
        start_btn.click()

        # Wait for demo to complete
        log("  Esperando demo (30s)...", "INFO")
        time.sleep(32)

        # Scroll to see results
        driver.execute_script("window.scrollTo(0, 400)")
        time.sleep(3)

        # Scroll to info section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(4)

        # Scene 3: Create Consortium
        log("  Escena 3: Crear Consorcio", "INFO")
        driver.get(f"{base_url}/consortiums/new")
        time.sleep(2)

        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        for char in "Consorcio Fraude Bancario":
            name_input.send_keys(char)
            time.sleep(0.03)

        desc_input = driver.find_element(By.CSS_SELECTOR, "textarea")
        desc_text = "Modelo colaborativo para detectar fraude usando datos cifrados de multiples bancos."
        for char in desc_text:
            desc_input.send_keys(char)
            time.sleep(0.02)

        time.sleep(1)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Continuar')]").click()
        time.sleep(2)

        # Select model type
        model_btns = driver.find_elements(By.CSS_SELECTOR, "button.border-2")
        if len(model_btns) >= 2:
            model_btns[1].click()
        time.sleep(1)

        driver.find_element(By.XPATH, "//button[contains(text(), 'Continuar')]").click()
        time.sleep(3)

        log("  Demo web completada", "SUCCESS")

    finally:
        driver.quit()


def run_cli_demo():
    """Run and record the CLI demo."""
    log("Ejecutando demo CLI...", "INFO")

    # Create a modified demo script that doesn't wait for user input
    auto_demo_script = '''
import sys
import os
sys.path.insert(0, "{project_dir}")
os.chdir("{project_dir}")

# Monkey-patch input to auto-continue
original_input = input
def auto_input(prompt=""):
    import time
    time.sleep(1.5)  # Pause for readability
    return ""
import builtins
builtins.input = auto_input

# Now run the demo
exec(open("{project_dir}/scripts/demo_fhe_transparency.py").read())
'''.format(project_dir=str(PROJECT_DIR))

    # Save temp script
    temp_script = RECORDINGS_DIR / "temp_auto_demo.py"
    temp_script.write_text(auto_demo_script)

    # Record using script command (captures terminal output)
    log("  Grabando sesion de terminal...", "INFO")

    # Use script to record terminal session
    proc = subprocess.Popen(
        ["script", "-q", str(CLI_LOG), str(VENV_PYTHON), str(temp_script)],
        cwd=str(PROJECT_DIR),
        env={**os.environ, "TERM": "xterm-256color"}
    )

    proc.wait()

    # Clean up temp script
    temp_script.unlink()

    log(f"  Log guardado en: {CLI_LOG}", "SUCCESS")

    # Try to convert to video using termtosvg or similar
    try:
        # Check if we can make a GIF
        result = subprocess.run(
            ["which", "termtosvg"],
            capture_output=True
        )
        if result.returncode == 0:
            log("  Generando SVG animado...", "INFO")
            svg_file = RECORDINGS_DIR / f"demo_cli_{TIMESTAMP}.svg"
            subprocess.run([
                "termtosvg", "record", str(svg_file),
                "-c", f"{VENV_PYTHON} {temp_script}"
            ])
    except:
        pass

    log("Demo CLI completada", "SUCCESS")


def record_cli_with_screen():
    """Record CLI demo by capturing a terminal window."""
    log("Grabando demo CLI con captura de pantalla...", "INFO")

    # Open Terminal and run the demo
    applescript = '''
    tell application "Terminal"
        activate
        set newWindow to do script "cd '{project_dir}' && source .venv/bin/activate && python scripts/demo_fhe_transparency_auto.py"
        delay 2
        set bounds of front window to {{0, 0, 1200, 800}}
    end tell
    '''.format(project_dir=str(PROJECT_DIR))

    # First create auto version of demo
    create_auto_cli_demo()

    # Start screen recording
    ffmpeg_proc = subprocess.Popen([
        "ffmpeg",
        "-y",
        "-f", "avfoundation",
        "-framerate", "30",
        "-i", "4:none",
        "-t", "70",
        "-vf", "scale=1920:1080",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        str(CLI_VIDEO)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(2)  # Let ffmpeg start

    # Run applescript to open terminal
    subprocess.run(["osascript", "-e", applescript])

    # Wait for demo to complete
    time.sleep(65)

    # Stop recording
    ffmpeg_proc.terminate()

    log(f"Video CLI guardado en: {CLI_VIDEO}", "SUCCESS")


def create_auto_cli_demo():
    """Create a version of CLI demo that auto-advances."""
    auto_script = PROJECT_DIR / "scripts" / "demo_fhe_transparency_auto.py"

    original = PROJECT_DIR / "scripts" / "demo_fhe_transparency.py"
    content = original.read_text()

    # Replace wait_for_user() with automatic delay
    content = content.replace(
        'def wait_for_user():\n    input(f"\\n{Colors.DIM}Presiona Enter para continuar...{Colors.ENDC}")',
        'def wait_for_user():\n    import time\n    print(f"\\n{Colors.DIM}[Auto-avanzando en 2s...]{Colors.ENDC}")\n    time.sleep(2)'
    )

    auto_script.write_text(content)
    log(f"  Script auto creado: {auto_script.name}", "INFO")


def main():
    """Main recording flow."""
    print("\n" + "="*60)
    print("  XCAPIT PRIVACY - GRABADOR AUTOMATICO DE DEMOS")
    print("="*60 + "\n")

    # Handle Ctrl+C
    signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(0)))

    try:
        setup()

        # === PART 1: WEB DEMO ===
        log("=" * 50, "INFO")
        log("PARTE 1: DEMO WEB", "INFO")
        log("=" * 50, "INFO")

        if not start_backend():
            return

        if not start_frontend():
            return

        time.sleep(2)

        # Start screen recording
        ffmpeg_proc = start_screen_recording(WEB_VIDEO, duration=90)
        time.sleep(2)  # Let ffmpeg initialize

        # Run selenium demo
        run_web_demo_selenium()

        # Wait for ffmpeg to finish
        log("Finalizando grabacion de video...", "INFO")
        ffmpeg_proc.wait()

        log(f"Video web guardado: {WEB_VIDEO}", "SUCCESS")

        # === PART 2: CLI DEMO ===
        log("\n" + "=" * 50, "INFO")
        log("PARTE 2: DEMO CLI", "INFO")
        log("=" * 50, "INFO")

        create_auto_cli_demo()
        record_cli_with_screen()

        # === SUMMARY ===
        print("\n" + "="*60)
        log("GRABACION COMPLETADA", "SUCCESS")
        print("="*60)
        print(f"\nArchivos generados en: {RECORDINGS_DIR}/")
        print(f"  - {WEB_VIDEO.name}")
        print(f"  - {CLI_VIDEO.name}")
        if CLI_LOG.exists():
            print(f"  - {CLI_LOG.name}")
        print()

    finally:
        cleanup()

        # Clean up auto script
        auto_script = PROJECT_DIR / "scripts" / "demo_fhe_transparency_auto.py"
        if auto_script.exists():
            auto_script.unlink()


if __name__ == "__main__":
    main()
