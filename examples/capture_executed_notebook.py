#!/usr/bin/env python3
"""Capture screenshots of executed notebook with real outputs"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def main():
    print("📸 Capturing Executed Notebook Screenshots...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "screenshots", "executed_notebook")
    os.makedirs(output_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1200")
    options.add_argument("--force-device-scale-factor=2")

    driver = webdriver.Chrome(options=options)

    try:
        # Open executed notebook in JupyterLab
        url = "http://localhost:8890/lab/tree/examples/06_real_execution_demo_executed.ipynb"
        print(f"   Opening: {url}")
        driver.get(url)
        time.sleep(6)  # Wait for notebook to load

        # Take screenshots at different scroll positions to capture all cells
        screenshots = [
            (0, "01_imports_blockchain.png", "Imports & Blockchain"),
            (600, "02_plaintext_data.png", "Plaintext Data"),
            (1200, "03_bank_contributions.png", "Bank Contributions"),
            (1800, "04_fhe_encryption.png", "FHE Encryption"),
            (2400, "05_commit_phase.png", "Commit Phase"),
            (3000, "06_reveal_phase.png", "Reveal Phase"),
            (3600, "07_model_training.png", "Model Training"),
            (4200, "08_classification.png", "Classification Report"),
            (4800, "09_new_transactions.png", "New Transactions"),
            (5400, "10_predictions.png", "Fraud Predictions"),
            (6000, "11_privacy_summary.png", "Privacy Summary"),
        ]

        for scroll_y, filename, description in screenshots:
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.8)
            filepath = os.path.join(output_dir, filename)
            driver.save_screenshot(filepath)
            print(f"   ✅ {filename} - {description}")

        # Full notebook screenshot
        print("\n   Capturing full notebook...")
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, min(total_height + 200, 20000))
        time.sleep(1)
        driver.save_screenshot(os.path.join(output_dir, "00_full_notebook.png"))
        print("   ✅ 00_full_notebook.png")

        print(f"\n📁 Screenshots saved to: {output_dir}")
        for f in sorted(os.listdir(output_dir)):
            size = os.path.getsize(os.path.join(output_dir, f)) / 1024
            print(f"   - {f} ({size:.0f} KB)")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
