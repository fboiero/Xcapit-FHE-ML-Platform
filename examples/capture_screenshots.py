#!/usr/bin/env python3
"""
Selenium Screenshot Automation for Demo Report

Captures screenshots of the HTML demo report for documentation.
"""

import os
import sys
import time
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Installing selenium...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC


def setup_driver():
    """Setup Chrome WebDriver with headless mode."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=2")  # Retina quality

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("\nTrying with Safari...")
        try:
            driver = webdriver.Safari()
            return driver
        except Exception as e2:
            print(f"Safari also failed: {e2}")
            return None


def capture_full_page(driver, url, output_path):
    """Capture full page screenshot."""
    driver.get(url)
    time.sleep(2)  # Wait for any animations

    # Get total page height
    total_height = driver.execute_script("return document.body.scrollHeight")

    # Set window size to capture full page
    driver.set_window_size(1920, total_height + 100)
    time.sleep(1)

    # Take screenshot
    driver.save_screenshot(output_path)
    print(f"✅ Screenshot saved: {output_path}")


def capture_sections(driver, url, output_dir):
    """Capture individual section screenshots."""
    driver.get(url)
    driver.set_window_size(1920, 1080)
    time.sleep(2)

    sections = [
        ("header", "01_header.png"),
        (".section:nth-of-type(1)", "02_blockchain.png"),
        (".section:nth-of-type(2)", "03_dataset.png"),
        (".section:nth-of-type(3)", "04_fhe_encryption.png"),
        (".section:nth-of-type(4)", "05_voting.png"),
        (".section:nth-of-type(5)", "06_model_training.png"),
        (".section:nth-of-type(6)", "07_predictions.png"),
        (".section:nth-of-type(7)", "08_summary.png"),
    ]

    for selector, filename in sections:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)

            # Take viewport screenshot
            output_path = os.path.join(output_dir, filename)
            driver.save_screenshot(output_path)
            print(f"✅ Captured: {filename}")
        except Exception as e:
            print(f"⚠️ Could not capture {filename}: {e}")


def main():
    """Main function to run screenshot capture."""
    print("=" * 60)
    print("📸 XCAPIT DEMO SCREENSHOT AUTOMATION")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, "demo_report.html")
    screenshots_dir = os.path.join(script_dir, "screenshots")

    # Create screenshots directory
    os.makedirs(screenshots_dir, exist_ok=True)

    # Check if report exists
    if not os.path.exists(report_path):
        print("📝 Generating HTML report first...")
        from demo_report_generator import generate_report
        generate_report(report_path)

    report_url = f"file://{report_path}"
    print(f"\n📄 Report URL: {report_url}")

    # Setup driver
    print("\n🌐 Setting up browser...")
    driver = setup_driver()

    if driver is None:
        print("\n❌ Could not setup any browser driver.")
        print("   Please install ChromeDriver: brew install chromedriver")
        print("   Or enable Safari WebDriver: safaridriver --enable")
        return False

    try:
        # Capture full page
        print("\n📸 Capturing full page screenshot...")
        full_page_path = os.path.join(screenshots_dir, "00_full_report.png")
        capture_full_page(driver, report_url, full_page_path)

        # Capture individual sections
        print("\n📸 Capturing section screenshots...")
        capture_sections(driver, report_url, screenshots_dir)

        print("\n" + "=" * 60)
        print("✅ SCREENSHOT CAPTURE COMPLETE!")
        print("=" * 60)
        print(f"\n📁 Screenshots saved to: {screenshots_dir}")
        print(f"\nFiles:")
        for f in sorted(os.listdir(screenshots_dir)):
            print(f"   - {f}")

        return True

    except Exception as e:
        print(f"\n❌ Error during capture: {e}")
        return False

    finally:
        driver.quit()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
