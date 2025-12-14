#!/usr/bin/env python3
"""
Captura screenshots del demo web para la presentacion
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://dashboard-qr7j0tsio-fernando-boieros-projects.vercel.app"

def capture_demo_screenshots():
    """Capture screenshots from the web demo"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2  # Retina quality
        )
        page = context.new_page()

        # Screenshot 1: Initial state with raw data
        print("Capturando: Demo de clientes (estado inicial)...")
        page.goto(f"{BASE_URL}/clients-demo", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_raw_data.png"), full_page=False)

        # Click start demo button - try both languages
        print("Iniciando demo...")
        try:
            # Try clicking the button
            button = page.locator("button:has-text('Start Demo'), button:has-text('Iniciar Demo')")
            if button.count() > 0:
                button.first.click()
                time.sleep(4)
                print("Capturando: Proceso de cifrado...")
                page.screenshot(path=str(SCREENSHOTS_DIR / "02_encryption.png"), full_page=False)

                time.sleep(6)
                print("Capturando: Entrenamiento...")
                page.screenshot(path=str(SCREENSHOTS_DIR / "03_training.png"), full_page=False)

                time.sleep(10)
                print("Capturando: Resultados...")
                page.screenshot(path=str(SCREENSHOTS_DIR / "04_results.png"), full_page=False)

                time.sleep(4)
                print("Capturando: Prediccion...")
                page.screenshot(path=str(SCREENSHOTS_DIR / "05_prediction.png"), full_page=False)
            else:
                print("No se encontro el boton de inicio")
        except Exception as e:
            print(f"Error al hacer click: {e}")

        # Galeria de demos
        print("Capturando: Galeria de demos...")
        page.goto(f"{BASE_URL}/demos", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "demos_gallery.png"), full_page=False)

        # Scroll down to see more
        page.evaluate("window.scrollBy(0, 600)")
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS_DIR / "demos_gallery_2.png"), full_page=False)

        # Sandbox demo
        print("Capturando: Sandbox demo...")
        page.goto(f"{BASE_URL}/sandbox-demo", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "sandbox_demo.png"), full_page=False)

        # Governance
        print("Capturando: Governance...")
        page.goto(f"{BASE_URL}/demo-governance", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "governance.png"), full_page=False)

        # Compliance
        print("Capturando: Compliance...")
        page.goto(f"{BASE_URL}/demo-compliance", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "compliance.png"), full_page=False)

        # Federated inference
        print("Capturando: Federated Inference...")
        page.goto(f"{BASE_URL}/demo-federated", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "federated.png"), full_page=False)

        browser.close()

    print(f"\nScreenshots guardados en: {SCREENSHOTS_DIR}")
    print("Archivos:")
    for f in sorted(SCREENSHOTS_DIR.glob("*.png")):
        size = f.stat().st_size / 1024
        print(f"  - {f.name} ({size:.1f} KB)")


if __name__ == "__main__":
    capture_demo_screenshots()
