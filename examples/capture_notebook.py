#!/usr/bin/env python3
"""
Capture Jupyter Notebook Screenshots
"""

import os
import sys
import time

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By


def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=2")
    return webdriver.Chrome(options=options)


def main():
    print("=" * 60)
    print("📸 JUPYTER NOTEBOOK SCREENSHOT CAPTURE")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    notebook_dir = os.path.join(script_dir, "screenshots", "notebook")
    os.makedirs(notebook_dir, exist_ok=True)

    driver = setup_driver()

    try:
        # Jupyter Lab main view
        print("\n📓 Capturing Jupyter Lab...")
        driver.get("http://localhost:8889/lab/tree/examples")
        time.sleep(4)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_01_lab_main.png"))
        print("   ✅ jupyter_01_lab_main.png")

        # Open the consortium demo notebook
        print("\n📓 Opening consortium demo notebook...")
        driver.get("http://localhost:8889/lab/tree/examples/05_consortium_e2e_demo.ipynb")
        time.sleep(5)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_02_notebook_open.png"))
        print("   ✅ jupyter_02_notebook_open.png")

        # Scroll down to see more cells
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_03_notebook_scroll1.png"))
        print("   ✅ jupyter_03_notebook_scroll1.png")

        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_04_notebook_scroll2.png"))
        print("   ✅ jupyter_04_notebook_scroll2.png")

        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_05_notebook_scroll3.png"))
        print("   ✅ jupyter_05_notebook_scroll3.png")

        # Classic notebook view
        print("\n📓 Opening classic notebook view...")
        driver.get("http://localhost:8889/notebooks/examples/05_consortium_e2e_demo.ipynb")
        time.sleep(4)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_06_classic_view.png"))
        print("   ✅ jupyter_06_classic_view.png")

        # File browser
        print("\n📓 Capturing file browser...")
        driver.get("http://localhost:8889/tree/examples")
        time.sleep(3)
        driver.save_screenshot(os.path.join(notebook_dir, "jupyter_07_file_browser.png"))
        print("   ✅ jupyter_07_file_browser.png")

        print("\n" + "=" * 60)
        print("✅ NOTEBOOK CAPTURE COMPLETE!")
        print("=" * 60)

        print(f"\n📁 Screenshots saved to: {notebook_dir}")
        for f in sorted(os.listdir(notebook_dir)):
            size = os.path.getsize(os.path.join(notebook_dir, f)) / 1024
            print(f"   - {f} ({size:.0f} KB)")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
