#!/usr/bin/env python3
"""Capture screenshots of the real demo report"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    print("📸 Capturing Real Demo Report Screenshots...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, "real_demo_report.html")
    output_dir = os.path.join(script_dir, "screenshots", "real_demo")
    os.makedirs(output_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=2")

    driver = webdriver.Chrome(options=options)

    try:
        url = f"file://{report_path}"
        driver.get(url)
        time.sleep(2)

        # Full page screenshot
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, min(total_height + 100, 15000))
        time.sleep(1)
        driver.save_screenshot(os.path.join(output_dir, "00_full_report.png"))
        print("   ✅ 00_full_report.png")

        # Individual sections
        driver.set_window_size(1920, 1080)
        sections = [
            (0, "01_header.png"),
            (400, "02_blockchain.png"),
            (900, "03_data.png"),
            (1400, "04_encryption.png"),
            (2100, "05_voting.png"),
            (2700, "06_training.png"),
            (3300, "07_predictions.png"),
            (3900, "08_privacy.png"),
        ]

        for scroll_y, filename in sections:
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.5)
            driver.save_screenshot(os.path.join(output_dir, filename))
            print(f"   ✅ {filename}")

        print(f"\n📁 Screenshots saved to: {output_dir}")
        for f in sorted(os.listdir(output_dir)):
            size = os.path.getsize(os.path.join(output_dir, f)) / 1024
            print(f"   - {f} ({size:.0f} KB)")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
