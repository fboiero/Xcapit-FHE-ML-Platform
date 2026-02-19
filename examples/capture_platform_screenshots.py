#!/usr/bin/env python3
"""
Screenshot Automation for Notebook and Platform

Captures screenshots of:
1. Jupyter notebook execution
2. Xcapit Privacy Platform (production dashboard)
"""

import os
import sys
import time
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Installing selenium...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC


def setup_driver(headless=True):
    """Setup Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=2")

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome: {e}")
        return None


def capture_platform_pages(driver, output_dir):
    """Capture screenshots of the production platform."""

    pages = [
        ("https://xcapit-privacy.vercel.app/", "platform_01_landing.png", "Landing Page"),
        ("https://xcapit-privacy.vercel.app/hub", "platform_02_hub.png", "Industry Hub"),
        ("https://xcapit-privacy.vercel.app/fintech", "platform_03_fintech.png", "Fintech Landing"),
        ("https://xcapit-privacy.vercel.app/dashboard", "platform_04_dashboard.png", "Main Dashboard"),
        ("https://xcapit-privacy.vercel.app/governance", "platform_05_governance.png", "Governance"),
        ("https://xcapit-privacy.vercel.app/compliance", "platform_06_compliance.png", "Compliance"),
        ("https://xcapit-privacy.vercel.app/models", "platform_07_models.png", "ML Models"),
        ("https://xcapit-privacy.vercel.app/consortiums", "platform_08_consortiums.png", "Consortiums"),
    ]

    print("\n📸 Capturing Platform Screenshots...")
    print("-" * 50)

    for url, filename, description in pages:
        try:
            print(f"   Loading: {description}...")
            driver.get(url)
            time.sleep(3)  # Wait for animations and data loading

            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            output_path = os.path.join(output_dir, filename)
            driver.save_screenshot(output_path)
            print(f"   ✅ {filename} - {description}")
        except Exception as e:
            print(f"   ⚠️ Failed: {filename} - {e}")


def capture_platform_full_pages(driver, output_dir):
    """Capture full-height screenshots of key pages."""

    pages = [
        ("https://xcapit-privacy.vercel.app/fintech", "platform_fintech_full.png", "Fintech Full"),
        ("https://xcapit-privacy.vercel.app/dashboard", "platform_dashboard_full.png", "Dashboard Full"),
    ]

    print("\n📸 Capturing Full-Page Screenshots...")
    print("-" * 50)

    for url, filename, description in pages:
        try:
            print(f"   Loading: {description}...")
            driver.get(url)
            time.sleep(3)

            # Get full page height
            total_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(1920, min(total_height + 100, 10000))
            time.sleep(1)

            output_path = os.path.join(output_dir, filename)
            driver.save_screenshot(output_path)
            print(f"   ✅ {filename} - {description}")

            # Reset window size
            driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"   ⚠️ Failed: {filename} - {e}")


def capture_arbiscan_contracts(driver, output_dir):
    """Capture screenshots of deployed contracts on Arbiscan."""

    contracts = [
        ("0xda52326d106A91A1F22A0c41Be2dc1F531C01F11", "arbiscan_governance.png", "Governance Contract"),
        ("0x1296cCeF7803Bff51FB690afCFc586E7012417b8", "arbiscan_model_registry.png", "Model Registry"),
        ("0xa5f04E0aefe55173C91b949Aa2385f0228dd2921", "arbiscan_verifier.png", "Computation Verifier"),
    ]

    print("\n📸 Capturing Arbiscan Contract Screenshots...")
    print("-" * 50)

    for address, filename, description in contracts:
        try:
            url = f"https://sepolia.arbiscan.io/address/{address}"
            print(f"   Loading: {description}...")
            driver.get(url)
            time.sleep(4)  # Arbiscan needs more time

            output_path = os.path.join(output_dir, filename)
            driver.save_screenshot(output_path)
            print(f"   ✅ {filename}")
        except Exception as e:
            print(f"   ⚠️ Failed: {filename} - {e}")


def main():
    """Main function."""
    print("=" * 60)
    print("📸 XCAPIT PLATFORM & NOTEBOOK SCREENSHOT AUTOMATION")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Setup directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    screenshots_dir = os.path.join(script_dir, "screenshots")
    platform_dir = os.path.join(screenshots_dir, "platform")
    arbiscan_dir = os.path.join(screenshots_dir, "arbiscan")

    os.makedirs(platform_dir, exist_ok=True)
    os.makedirs(arbiscan_dir, exist_ok=True)

    # Setup driver
    print("\n🌐 Setting up browser...")
    driver = setup_driver(headless=True)

    if driver is None:
        print("❌ Could not setup browser")
        return False

    try:
        # Capture platform pages
        capture_platform_pages(driver, platform_dir)

        # Capture full-page screenshots
        capture_platform_full_pages(driver, platform_dir)

        # Capture Arbiscan contracts
        capture_arbiscan_contracts(driver, arbiscan_dir)

        print("\n" + "=" * 60)
        print("✅ SCREENSHOT CAPTURE COMPLETE!")
        print("=" * 60)

        # List all files
        print(f"\n📁 Platform screenshots: {platform_dir}")
        for f in sorted(os.listdir(platform_dir)):
            size = os.path.getsize(os.path.join(platform_dir, f)) / 1024
            print(f"   - {f} ({size:.0f} KB)")

        print(f"\n📁 Arbiscan screenshots: {arbiscan_dir}")
        for f in sorted(os.listdir(arbiscan_dir)):
            size = os.path.getsize(os.path.join(arbiscan_dir, f)) / 1024
            print(f"   - {f} ({size:.0f} KB)")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    finally:
        driver.quit()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
