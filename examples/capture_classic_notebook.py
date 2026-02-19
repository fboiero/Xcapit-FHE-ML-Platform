#!/usr/bin/env python3
"""Capture screenshots of executed notebook in classic view"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

def main():
    print("📸 Capturing Classic Notebook View...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "screenshots", "notebook_executed")
    os.makedirs(output_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--force-device-scale-factor=2")

    driver = webdriver.Chrome(options=options)

    try:
        # Use nbviewer-style HTML export for better screenshots
        # First convert notebook to HTML
        import subprocess
        subprocess.run([
            "/Library/Developer/CommandLineTools/usr/bin/python3", "-m", "jupyter", "nbconvert",
            "--to", "html",
            "--output", "06_executed_output.html",
            os.path.join(script_dir, "06_real_execution_demo_executed.ipynb")
        ], capture_output=True)

        html_path = os.path.join(script_dir, "06_executed_output.html")
        url = f"file://{html_path}"

        print(f"   Opening HTML export: {url}")
        driver.get(url)
        time.sleep(3)

        # Capture at different scroll positions
        screenshots = [
            (0, "01_title_imports.png"),
            (800, "02_blockchain_connection.png"),
            (1600, "03_plaintext_data.png"),
            (2400, "04_bank_contributions.png"),
            (3200, "05_fhe_encryption.png"),
            (4000, "06_commit_phase.png"),
            (4800, "07_reveal_phase.png"),
            (5600, "08_model_training.png"),
            (6400, "09_classification_report.png"),
            (7200, "10_new_transactions.png"),
            (8000, "11_predictions.png"),
            (8800, "12_privacy_summary.png"),
        ]

        for scroll_y, filename in screenshots:
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.5)
            filepath = os.path.join(output_dir, filename)
            driver.save_screenshot(filepath)
            print(f"   ✅ {filename}")

        # Full page
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1400, min(total_height + 100, 25000))
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        driver.save_screenshot(os.path.join(output_dir, "00_full_notebook.png"))
        print("   ✅ 00_full_notebook.png")

        print(f"\n📁 Saved to: {output_dir}")
        for f in sorted(os.listdir(output_dir)):
            size = os.path.getsize(os.path.join(output_dir, f)) / 1024
            print(f"   - {f} ({size:.0f} KB)")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
