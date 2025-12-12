#!/usr/bin/env python3
"""
Xcapit Privacy - Web Demo Recorder

Usa Selenium para automatizar la demo web y grabarla.

Requisitos:
    pip install selenium webdriver-manager

Para grabar la pantalla, usa QuickTime (Mac) o OBS mientras corre este script.
"""

import time
import sys
import os

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
    os.system("pip install selenium webdriver-manager")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager


class DemoRecorder:
    def __init__(self, base_url="http://localhost:5173"):
        self.base_url = base_url
        self.driver = None

    def setup(self):
        """Configure Chrome driver."""
        print("🚀 Configurando navegador...")

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        # Bigger window for better recording
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        print("✓ Navegador listo")

    def wait_and_click(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Wait for element and click it."""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        time.sleep(0.3)  # Small pause for visual effect
        element.click()
        return element

    def wait_for_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Wait for element to be visible."""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )

    def type_slowly(self, element, text, delay=0.05):
        """Type text slowly for visual effect."""
        element.clear()
        for char in str(text):
            element.send_keys(char)
            time.sleep(delay)

    def run_demo_flow(self):
        """Execute the full demo flow."""

        print("\n" + "="*60)
        print("  XCAPIT PRIVACY - GRABACION DE DEMO WEB")
        print("="*60)
        print("\n⚠️  IMPORTANTE: Inicia la grabacion de pantalla AHORA")
        print("   (QuickTime Player > Archivo > Nueva grabacion de pantalla)")
        input("\nPresiona Enter cuando estes grabando...")

        # === SCENE 1: Login/Register ===
        print("\n📍 Escena 1: Registro de empresa")
        self.driver.get(f"{self.base_url}/register")
        time.sleep(2)

        # Fill registration form
        name_input = self.wait_for_element("input[type='text']")
        self.type_slowly(name_input, "FinTech Alpha")
        time.sleep(0.5)

        email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        self.type_slowly(email_input, "demo@fintech-alpha.com")
        time.sleep(1)

        # Submit
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        time.sleep(3)

        print("✓ Empresa registrada")

        # === SCENE 2: Dashboard ===
        print("\n📍 Escena 2: Dashboard principal")
        time.sleep(2)

        # Navigate to demo
        print("\n📍 Escena 3: Demo de Privacidad")
        self.driver.get(f"{self.base_url}/demo")
        time.sleep(2)

        # === SCENE 3: Privacy Demo ===
        print("✓ Cargando demo de privacidad...")

        # Scroll to see the full page
        self.driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)

        # Click "Iniciar Demo" button
        start_btn = self.wait_and_click("button.bg-brand-600")
        print("✓ Demo iniciada")

        # Wait for demo to complete (around 25 seconds)
        print("⏳ Ejecutando demo... (25 segundos)")
        time.sleep(28)

        # Scroll to see result
        self.driver.execute_script("window.scrollTo(0, 300)")
        time.sleep(3)

        print("✓ Demo completada")

        # === SCENE 4: Show info section ===
        print("\n📍 Escena 4: Informacion de FHE")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(4)

        # === SCENE 5: Create Consortium ===
        print("\n📍 Escena 5: Crear consorcio")
        self.driver.get(f"{self.base_url}/consortiums/new")
        time.sleep(2)

        # Step 1: Basic info
        name_input = self.wait_for_element("input[type='text']")
        self.type_slowly(name_input, "Consorcio de Deteccion de Fraude")
        time.sleep(0.5)

        desc_input = self.driver.find_element(By.CSS_SELECTOR, "textarea")
        self.type_slowly(desc_input, "Modelo colaborativo para detectar fraude financiero usando datos de multiples instituciones sin compartir informacion sensible.", delay=0.02)
        time.sleep(1)

        # Click continue
        continue_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continuar')]")
        continue_btn.click()
        time.sleep(2)

        print("✓ Paso 1 completado")

        # Step 2: Model type
        print("📍 Seleccionando tipo de modelo...")
        # Click on Logistic Regression
        model_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.border-2")
        if len(model_buttons) >= 2:
            model_buttons[1].click()  # Logistic Regression
        time.sleep(1)

        continue_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continuar')]")
        continue_btn.click()
        time.sleep(2)

        print("✓ Paso 2 completado")

        # Step 3: Review
        print("📍 Revision final...")
        time.sleep(2)

        print("\n✓ Flujo de demo completado!")

        # Final pause
        print("\n⏹️  Puedes detener la grabacion ahora")
        time.sleep(5)

    def cleanup(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()
            print("✓ Navegador cerrado")


def main():
    recorder = DemoRecorder()

    try:
        recorder.setup()
        recorder.run_demo_flow()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo cancelada por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        recorder.cleanup()


if __name__ == "__main__":
    main()
