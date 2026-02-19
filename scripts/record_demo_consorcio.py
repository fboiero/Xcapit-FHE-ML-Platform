#!/usr/bin/env python3
"""
Xcapit Privacy - Demo Consorcio Recorder

Graba la demo del consorcio con DOS casos de uso:
1. Fraude Bancario (3 bancos)
2. Investigacion Medica (3 hospitales)
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
SCREENSHOTS_DIR = RECORDINGS_DIR / f"consorcio_{TIMESTAMP}"


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


def run_demo_for_usecase(driver, usecase_name, usecase_prefix, step_start):
    """Run demo for a specific use case (banks or health)."""
    screenshots = []
    step = step_start

    log(f"\n{'='*50}")
    log(f"CASO DE USO: {usecase_name.upper()}")
    log(f"{'='*50}")

    # Wait for page to stabilize
    time.sleep(1)

    # Take initial screenshot
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_00_inicio", step)); step += 1

    # Click Start Demo button
    log("\nIniciando demo automatica...")
    try:
        start_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Iniciar Demo')]"))
        )
        time.sleep(0.5)
        screenshots.append(take_screenshot(driver, f"{usecase_prefix}_01_antes_iniciar", step)); step += 1
        start_btn.click()
    except Exception as e:
        log(f"No se encontro boton Iniciar: {e}", "WARNING")
        return screenshots, step

    # Step 0: Problem statement
    time.sleep(3)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_02_problema", step)); step += 1

    # Step 1: Sensitive data
    time.sleep(3)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_03_datos_sensibles", step)); step += 1

    # Step 2: Encryption - capture each entity encrypting
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_04_cifrando_1", step)); step += 1
    time.sleep(1.5)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_05_cifrando_2", step)); step += 1
    time.sleep(1.5)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_06_cifrando_3", step)); step += 1
    time.sleep(1)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_07_todos_cifrados", step)); step += 1

    # Step 3: Server view
    time.sleep(3)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_08_servidor", step)); step += 1
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_09_ciphertext", step)); step += 1

    # Step 4: Training
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_10_training_inicio", step)); step += 1
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_11_training_medio", step)); step += 1
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_12_training_fin", step)); step += 1

    # Step 5: Results
    time.sleep(3)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_13_resultados", step)); step += 1
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_14_metricas", step)); step += 1

    # Scroll to see takeaways
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)
    screenshots.append(take_screenshot(driver, f"{usecase_prefix}_15_takeaways", step)); step += 1

    log(f"\nScreenshots {usecase_name}: {len(screenshots)}", "SUCCESS")
    return screenshots, step


def run_consorcio_demo():
    """Run consortium demo with both use cases."""
    log("=" * 60)
    log("DEMO CONSORCIO - DOS CASOS DE USO")
    log("=" * 60)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    driver = setup_driver()
    all_screenshots = []
    step = 0

    try:
        base_url = "http://localhost:3000"

        # ========================================
        # CASO 1: FRAUDE BANCARIO
        # ========================================
        log("\n\nAbriendo demo - Caso Bancario...")
        driver.get(f"{base_url}/demo-consorcio")
        time.sleep(3)

        # Make sure Banks tab is selected (should be default)
        try:
            banks_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Fraude Bancario')]")
            banks_tab.click()
            time.sleep(1)
        except:
            pass  # Already selected

        screenshots, step = run_demo_for_usecase(driver, "Fraude Bancario", "banks", step)
        all_screenshots.extend(screenshots)

        # ========================================
        # CASO 2: INVESTIGACION MEDICA
        # ========================================
        log("\n\nCambiando a caso Medico...")

        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)

        # Click Health tab
        try:
            health_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Medica') or contains(text(), 'Hospitales')]"))
            )
            health_tab.click()
            time.sleep(2)
            screenshots.append(take_screenshot(driver, "health_00_tab_switch", step)); step += 1
        except Exception as e:
            log(f"No se encontro tab de salud: {e}", "WARNING")
            # Try alternative
            try:
                health_tab = driver.find_element(By.XPATH, "//button[contains(@class, 'rose') or contains(text(), 'Investigaci')]")
                health_tab.click()
                time.sleep(2)
            except:
                log("No se pudo cambiar de tab", "ERROR")

        screenshots, step = run_demo_for_usecase(driver, "Investigacion Medica", "health", step)
        all_screenshots.extend(screenshots)

        log(f"\n\nTOTAL SCREENSHOTS: {len(all_screenshots)}", "SUCCESS")

    finally:
        driver.quit()

    return all_screenshots


def create_video(screenshots_dir):
    """Create video and GIF from screenshots."""
    log("\nCreando video y GIF...")

    mp4_file = RECORDINGS_DIR / f"demo_consorcio_{TIMESTAMP}.mp4"
    gif_file = RECORDINGS_DIR / f"demo_consorcio_{TIMESTAMP}.gif"

    png_pattern = str(screenshots_dir / "*.png")

    # Create video (1.5 seconds per frame)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "0.67",  # ~1.5 seconds per image
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

        # Create GIF
        gif_cmd = [
            "ffmpeg", "-y",
            "-i", str(mp4_file),
            "-vf", "fps=0.67,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            str(gif_file)
        ]
        result = subprocess.run(gif_cmd, capture_output=True)

        if result.returncode == 0 and gif_file.exists():
            log(f"GIF creado: {gif_file}", "SUCCESS")
        else:
            log("No se pudo crear GIF", "WARNING")
    else:
        log("No se pudo crear video", "WARNING")
        log(result.stderr.decode()[:500], "ERROR")

    return mp4_file, gif_file


def main():
    print("\n" + "=" * 60)
    print("  GRABADOR DEMO CONSORCIO - DOS CASOS DE USO")
    print("  1. Fraude Bancario (3 bancos)")
    print("  2. Investigacion Medica (3 hospitales)")
    print("=" * 60 + "\n")

    RECORDINGS_DIR.mkdir(exist_ok=True)

    # Run demo
    screenshots = run_consorcio_demo()

    if screenshots:
        create_video(SCREENSHOTS_DIR)

    # Summary
    print("\n" + "=" * 60)
    log("GRABACION COMPLETADA", "SUCCESS")
    print("=" * 60)
    print(f"\nArchivos en: {RECORDINGS_DIR}/")

    for f in sorted(RECORDINGS_DIR.iterdir()):
        if f.is_file() and 'consorcio' in f.name:
            size = f.stat().st_size
            size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
            print(f"  - {f.name} ({size_str})")

    print(f"\nScreenshots en: {SCREENSHOTS_DIR}/")
    print(f"  ({len(list(SCREENSHOTS_DIR.glob('*.png')))} archivos)")


if __name__ == "__main__":
    main()
