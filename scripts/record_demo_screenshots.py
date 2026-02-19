#!/usr/bin/env python3
"""
Xcapit Privacy - Demo Screenshot Recorder

Captura screenshots de la demo web y las compila en un GIF animado.
"""

import subprocess
import time
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Instalando dependencias...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "selenium", "webdriver-manager"])
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

# Configuration
PROJECT_DIR = Path(__file__).parent.parent
RECORDINGS_DIR = PROJECT_DIR / "recordings"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SCREENSHOTS_DIR = RECORDINGS_DIR / f"screenshots_{TIMESTAMP}"


def log(msg, level="INFO"):
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
    }
    reset = "\033[0m"
    print(f"{colors.get(level, '')}{level}: {msg}{reset}")


def setup_driver():
    """Configure Chrome driver."""
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--window-position=0,0")
    options.add_argument("--disable-notifications")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def take_screenshot(driver, name, step_num):
    """Take screenshot and save it."""
    filename = SCREENSHOTS_DIR / f"{step_num:03d}_{name}.png"
    driver.save_screenshot(str(filename))
    log(f"  Screenshot: {name}", "SUCCESS")
    return filename


def type_slowly(element, text, delay=0.05):
    """Type text slowly for visual effect."""
    for char in str(text):
        element.send_keys(char)
        time.sleep(delay)


def run_web_demo():
    """Run web demo with screenshots."""
    log("=" * 50)
    log("DEMO WEB CON SCREENSHOTS")
    log("=" * 50)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    driver = setup_driver()
    screenshots = []
    step = 0

    try:
        base_url = "http://localhost:3000"

        # Scene 1: Landing/Register
        log("\nEscena 1: Registro")
        driver.get(f"{base_url}/register")
        time.sleep(2)
        screenshots.append(take_screenshot(driver, "register_empty", step)); step += 1

        # Fill form with unique email
        unique_id = datetime.now().strftime("%H%M%S")
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        type_slowly(name_input, "FinTech Alpha")
        time.sleep(0.5)
        screenshots.append(take_screenshot(driver, "register_name", step)); step += 1

        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        type_slowly(email_input, f"demo_{unique_id}@fintech.com")
        time.sleep(0.5)
        screenshots.append(take_screenshot(driver, "register_email", step)); step += 1

        # Submit
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        screenshots.append(take_screenshot(driver, "dashboard", step)); step += 1

        # Scene 2: Privacy Demo
        log("\nEscena 2: Demo de Privacidad")
        driver.get(f"{base_url}/demo")
        time.sleep(2)
        screenshots.append(take_screenshot(driver, "demo_start", step)); step += 1

        # Click start
        start_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bg-brand-600"))
        )
        start_btn.click()

        # Capture demo progress
        for i in range(6):
            time.sleep(5)
            screenshots.append(take_screenshot(driver, f"demo_step_{i+1}", step)); step += 1

        # Scroll to see results
        driver.execute_script("window.scrollTo(0, 400)")
        time.sleep(2)
        screenshots.append(take_screenshot(driver, "demo_results", step)); step += 1

        # Scroll to info
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        screenshots.append(take_screenshot(driver, "demo_info", step)); step += 1

        # Scene 3: Create Consortium
        log("\nEscena 3: Crear Consorcio")
        driver.get(f"{base_url}/consortiums/new")
        time.sleep(2)
        screenshots.append(take_screenshot(driver, "consortium_new", step)); step += 1

        # Fill consortium form
        try:
            name_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            type_slowly(name_input, "Consorcio Fraude Bancario")
            time.sleep(0.5)
            screenshots.append(take_screenshot(driver, "consortium_name", step)); step += 1

            desc_input = driver.find_element(By.CSS_SELECTOR, "textarea")
            type_slowly(desc_input, "Modelo colaborativo para detectar fraude usando datos cifrados.", delay=0.02)
            time.sleep(0.5)
            screenshots.append(take_screenshot(driver, "consortium_desc", step)); step += 1
        except:
            log("No se encontro formulario de consorcio", "WARNING")

        log(f"\nTotal screenshots: {len(screenshots)}", "SUCCESS")

    finally:
        driver.quit()

    return screenshots


def create_gif(screenshots):
    """Create animated GIF from screenshots."""
    log("\nCreando GIF animado...")

    gif_file = RECORDINGS_DIR / f"demo_web_{TIMESTAMP}.gif"

    # Try using ffmpeg to create GIF
    png_pattern = str(SCREENSHOTS_DIR / "*.png")

    # First, create a video from images
    mp4_file = RECORDINGS_DIR / f"demo_web_{TIMESTAMP}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-framerate", "0.5",  # 2 seconds per image
        "-pattern_type", "glob",
        "-i", png_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720",
        str(mp4_file)
    ]

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode == 0:
        log(f"Video creado: {mp4_file}", "SUCCESS")

        # Also create GIF
        gif_cmd = [
            "ffmpeg", "-y",
            "-i", str(mp4_file),
            "-vf", "fps=1,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            str(gif_file)
        ]
        subprocess.run(gif_cmd, capture_output=True)

        if gif_file.exists():
            log(f"GIF creado: {gif_file}", "SUCCESS")
    else:
        log("No se pudo crear video con ffmpeg", "WARNING")
        log(result.stderr.decode()[:500], "ERROR")

    return mp4_file, gif_file


def run_cli_demo():
    """Run CLI demo and save output."""
    log("\n" + "=" * 50)
    log("DEMO CLI")
    log("=" * 50)

    # Create auto-advancing version
    auto_script = PROJECT_DIR / "scripts" / "demo_fhe_transparency_auto.py"
    original = PROJECT_DIR / "scripts" / "demo_fhe_transparency.py"

    content = original.read_text()
    content = content.replace(
        'def wait_for_user():\n    input(f"\\n{Colors.DIM}Presiona Enter para continuar...{Colors.ENDC}")',
        'def wait_for_user():\n    import time\n    print(f"\\n{Colors.DIM}[Auto-avanzando...]{Colors.ENDC}")\n    time.sleep(1.5)'
    )
    auto_script.write_text(content)

    # Run with script to capture output
    output_file = RECORDINGS_DIR / f"demo_cli_{TIMESTAMP}.txt"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_DIR)
    env["TERM"] = "xterm-256color"

    log("Ejecutando demo CLI...")

    venv_python = PROJECT_DIR / ".venv" / "bin" / "python"

    result = subprocess.run(
        [str(venv_python), str(auto_script)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PROJECT_DIR)
    )

    # Save output
    with open(output_file, "w") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)

    log(f"Output guardado: {output_file}", "SUCCESS")

    # Cleanup
    auto_script.unlink()

    # Try to create cast file for asciinema
    cast_file = RECORDINGS_DIR / f"demo_cli_{TIMESTAMP}.cast"

    # Check if asciinema is available
    result = subprocess.run(["which", "asciinema"], capture_output=True)
    if result.returncode == 0:
        log("Grabando con asciinema...")

        auto_script.write_text(content)  # Recreate for asciinema

        subprocess.run([
            "asciinema", "rec",
            "--title", "Xcapit Privacy - FHE Demo",
            "--idle-time-limit", "2",
            "--command", f"cd {PROJECT_DIR} && source .venv/bin/activate && python {auto_script}",
            str(cast_file)
        ], env=env, timeout=120)

        auto_script.unlink()

        if cast_file.exists():
            log(f"Cast guardado: {cast_file}", "SUCCESS")

    return output_file


def main():
    print("\n" + "=" * 60)
    print("  XCAPIT PRIVACY - GRABADOR DE DEMOS")
    print("=" * 60 + "\n")

    RECORDINGS_DIR.mkdir(exist_ok=True)

    # Part 1: Web Demo
    screenshots = run_web_demo()

    if screenshots:
        create_gif(screenshots)

    # Part 2: CLI Demo
    run_cli_demo()

    # Summary
    print("\n" + "=" * 60)
    log("GRABACION COMPLETADA", "SUCCESS")
    print("=" * 60)
    print(f"\nArchivos en: {RECORDINGS_DIR}/")

    for f in sorted(RECORDINGS_DIR.iterdir()):
        if f.is_file():
            size = f.stat().st_size
            size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
            print(f"  - {f.name} ({size_str})")


if __name__ == "__main__":
    main()
