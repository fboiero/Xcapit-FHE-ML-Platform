#!/usr/bin/env python3
"""
Captura screenshots de las demos HTML usando Selenium.
"""

import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DEMOS_DIR = PROJECT_ROOT / "output" / "demos"
SCREENSHOTS_DIR = PROJECT_ROOT / "output" / "screenshots"


def setup_driver():
    """Configure Chrome driver for screenshots."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,2000")
    options.add_argument("--force-device-scale-factor=2")  # High DPI

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def capture_screenshot(driver, html_path, output_path, wait_time=2):
    """Capture screenshot of an HTML file."""
    file_url = f"file://{html_path.absolute()}"
    print(f"  Loading: {file_url}")

    driver.get(file_url)
    time.sleep(wait_time)  # Wait for page to render

    # Get full page height
    total_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1400, total_height + 100)
    time.sleep(0.5)

    driver.save_screenshot(str(output_path))
    print(f"  Saved: {output_path}")


def main():
    """Capture all demo screenshots."""
    print("=" * 60)
    print("Capturando screenshots de demos con Selenium")
    print("=" * 60)

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    # Demo files to capture - Professional dashboards
    demos = [
        ("dashboard_main.html", "demo_01_dashboard.png"),
        ("dashboard_prediction.html", "demo_02_prediction.png"),
        ("dashboard_healthcare.html", "demo_03_healthcare.png"),
    ]

    print("\nIniciando Chrome headless...")
    driver = setup_driver()

    try:
        for html_file, output_file in demos:
            html_path = DEMOS_DIR / html_file
            output_path = SCREENSHOTS_DIR / output_file

            if html_path.exists():
                print(f"\nCapturando: {html_file}")
                capture_screenshot(driver, html_path, output_path)
            else:
                print(f"\nAdvertencia: {html_file} no encontrado")

    finally:
        driver.quit()

    print("\n" + "=" * 60)
    print("✅ Capturas completadas")
    print("=" * 60)

    # List captured files
    print("\nArchivos generados:")
    for f in SCREENSHOTS_DIR.glob("demo_*.png"):
        size = f.stat().st_size / 1024
        print(f"  - {f.name} ({size:.1f} KB)")


if __name__ == "__main__":
    main()
