#!/usr/bin/env python3
"""
Script para grabar demos de TIER 3 y TIER 4 features
Usa Selenium para navegar y hacer screenshots, luego crea videos con ffmpeg
"""

import os
import time
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Configuracion
BASE_URL = "http://localhost:3000"
RECORDINGS_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Demos a grabar
DEMOS = {
    # TIER 3
    "compliance": {
        "url": "/demo-compliance",
        "title": "Compliance Dashboard",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "frameworks"},
            {"type": "click", "selector": "button", "text": "Run Check", "optional": True},
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "check_result"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "details"},
        ]
    },
    "quality": {
        "url": "/demo-quality",
        "title": "Data Quality Score",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "dimensions"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "columns"},
            {"type": "click", "selector": "button", "text": "Analyze", "optional": True},
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "analysis"},
        ]
    },
    "marketplace": {
        "url": "/demo-marketplace",
        "title": "Model Marketplace",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "models"},
            {"type": "click", "selector": "button", "text": "View", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "model_detail"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "deploy"},
        ]
    },
    "sandbox": {
        "url": "/demo-sandbox",
        "title": "Sandbox Mode",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "environments"},
            {"type": "click", "selector": "button", "text": "Create", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "create_modal"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "experiments"},
        ]
    },
    # TIER 4
    "federated": {
        "url": "/demo-federated",
        "title": "Federated Inference",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "endpoints"},
            {"type": "click", "selector": "button", "text": "Create", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "create_endpoint"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "edge_nodes"},
        ]
    },
    "explainability": {
        "url": "/demo-explainability",
        "title": "Model Explainability",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "click", "selector": "button", "text": "Feature", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "feature_importance"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "shap_values"},
            {"type": "click", "selector": "button", "text": "Explain", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "explanation"},
        ]
    },
    "competitive": {
        "url": "/demo-competitive",
        "title": "Competitive Insights",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "benchmarks"},
            {"type": "click", "selector": "button", "text": "Compare", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "comparison"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "trends"},
        ]
    },
    "ensemble": {
        "url": "/demo-ensemble",
        "title": "Multi-Model Ensemble",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "screenshot", "name": "overview"},
            {"type": "scroll", "pixels": 200},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "ensembles"},
            {"type": "click", "selector": "button", "text": "Create", "optional": True},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "create_modal"},
            {"type": "scroll", "pixels": 300},
            {"type": "wait", "seconds": 1},
            {"type": "screenshot", "name": "models"},
        ]
    },
}


def setup_driver():
    """Configura el driver de Chrome"""
    options = Options()
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # NO usar headless para ver las interacciones
    # options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    return driver


def execute_action(driver, action, screenshot_dir, demo_name, frame_count):
    """Ejecuta una accion y retorna el nuevo frame_count"""
    action_type = action.get("type")

    if action_type == "wait":
        time.sleep(action.get("seconds", 1))

    elif action_type == "screenshot":
        name = action.get("name", f"frame_{frame_count:03d}")
        filepath = os.path.join(screenshot_dir, f"{frame_count:03d}_{name}.png")
        driver.save_screenshot(filepath)
        print(f"  Screenshot: {name}")
        frame_count += 1

    elif action_type == "scroll":
        pixels = action.get("pixels", 200)
        driver.execute_script(f"window.scrollBy(0, {pixels});")
        time.sleep(0.5)

    elif action_type == "click":
        selector = action.get("selector", "button")
        text = action.get("text", "")
        optional = action.get("optional", False)

        try:
            if text:
                # Buscar elemento por texto
                elements = driver.find_elements(By.XPATH,
                    f"//{selector}[contains(text(), '{text}')]")
                if elements:
                    elements[0].click()
                    print(f"  Click: {text}")
            else:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                element.click()
                print(f"  Click: {selector}")
        except Exception as e:
            if not optional:
                print(f"  Warning: Could not click {text or selector}: {e}")

    elif action_type == "hover":
        selector = action.get("selector")
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            ActionChains(driver).move_to_element(element).perform()
            time.sleep(0.5)
        except Exception as e:
            print(f"  Warning: Could not hover {selector}: {e}")

    return frame_count


def record_demo(driver, demo_name, demo_config):
    """Graba un demo individual"""
    print(f"\n{'='*50}")
    print(f"Recording: {demo_config['title']}")
    print(f"{'='*50}")

    # Crear directorio para screenshots
    screenshot_dir = os.path.join(RECORDINGS_DIR, f"{demo_name}_{TIMESTAMP}")
    os.makedirs(screenshot_dir, exist_ok=True)

    # Navegar a la pagina
    url = BASE_URL + demo_config["url"]
    driver.get(url)
    print(f"  URL: {url}")
    time.sleep(2)  # Esperar carga inicial

    # Ejecutar acciones
    frame_count = 1
    for action in demo_config["actions"]:
        frame_count = execute_action(driver, action, screenshot_dir, demo_name, frame_count)

    # Crear video con ffmpeg
    video_path = os.path.join(RECORDINGS_DIR, f"demo_{demo_name}_{TIMESTAMP}.mp4")
    gif_path = os.path.join(RECORDINGS_DIR, f"demo_{demo_name}_{TIMESTAMP}.gif")

    # Crear video desde screenshots
    cmd_video = [
        "ffmpeg", "-y",
        "-framerate", "1",  # 1 frame por segundo
        "-pattern_type", "glob",
        "-i", f"{screenshot_dir}/*.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        video_path
    ]

    try:
        subprocess.run(cmd_video, check=True, capture_output=True)
        print(f"  Video created: {video_path}")
    except subprocess.CalledProcessError as e:
        print(f"  Error creating video: {e}")
        return None

    # Crear GIF
    cmd_gif = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "fps=1,scale=640:-1:flags=lanczos",
        "-loop", "0",
        gif_path
    ]

    try:
        subprocess.run(cmd_gif, check=True, capture_output=True)
        print(f"  GIF created: {gif_path}")
    except subprocess.CalledProcessError as e:
        print(f"  Error creating GIF: {e}")

    return video_path


def main():
    print(f"\n{'#'*60}")
    print("# XCAPIT PRIVACY - DEMO RECORDER")
    print(f"# Timestamp: {TIMESTAMP}")
    print(f"{'#'*60}")

    driver = setup_driver()
    videos_created = []

    try:
        for demo_name, demo_config in DEMOS.items():
            video_path = record_demo(driver, demo_name, demo_config)
            if video_path:
                videos_created.append(video_path)

    finally:
        driver.quit()

    print(f"\n{'='*60}")
    print("RECORDING COMPLETE")
    print(f"{'='*60}")
    print(f"Videos created: {len(videos_created)}")
    for v in videos_created:
        print(f"  - {os.path.basename(v)}")

    return videos_created


if __name__ == "__main__":
    main()
