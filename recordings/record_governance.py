"""Record governance demo using Playwright screenshots."""

import subprocess
import time
from datetime import datetime
from pathlib import Path

# Use playwright sync API
from playwright.sync_api import sync_playwright


def record_governance_demo():
    """Record governance page demo."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"governance_{timestamp}")
    output_dir.mkdir(exist_ok=True)

    screenshots = []
    frame_num = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=2
        )
        page = context.new_page()

        # Navigate to demo governance page (public route)
        print("Opening demo governance page...")
        page.goto("http://localhost:3000/demo-governance")
        page.wait_for_load_state("networkidle")
        time.sleep(3)  # Wait for React to render

        # Take a debug screenshot to see what loaded
        page.screenshot(path=str(output_dir / "debug.png"))
        print("Debug screenshot saved")

        # Wait for tabs to be visible
        print("Waiting for tabs to load...")
        try:
            page.wait_for_selector("text=Contribuciones", timeout=10000)
        except Exception as e:
            print(f"Selector not found, checking page content...")
            # Print page content for debugging
            content = page.content()
            print(content[:2000])
            raise e

        time.sleep(1)

        # Capture initial state (Contribuciones tab is default)
        print("Recording Contribuciones tab...")
        for _ in range(15):  # ~1.5 seconds
            frame_num += 1
            screenshot_path = output_dir / f"frame_{frame_num:04d}.png"
            page.screenshot(path=str(screenshot_path))
            screenshots.append(screenshot_path)
            time.sleep(0.1)

        # Click on Propuestas tab
        print("Clicking Propuestas tab...")
        page.click("text=Propuestas")
        time.sleep(0.5)

        # Capture Propuestas tab
        print("Recording Propuestas tab...")
        for _ in range(20):  # ~2 seconds
            frame_num += 1
            screenshot_path = output_dir / f"frame_{frame_num:04d}.png"
            page.screenshot(path=str(screenshot_path))
            screenshots.append(screenshot_path)
            time.sleep(0.1)

        # Scroll down to see more proposals
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(0.3)

        for _ in range(10):
            frame_num += 1
            screenshot_path = output_dir / f"frame_{frame_num:04d}.png"
            page.screenshot(path=str(screenshot_path))
            screenshots.append(screenshot_path)
            time.sleep(0.1)

        # Scroll back up
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)

        # Click on Audit Trail tab
        print("Clicking Audit Trail tab...")
        page.click("text=Audit Trail")
        time.sleep(0.5)

        # Capture Audit Trail tab
        print("Recording Audit Trail tab...")
        for _ in range(20):  # ~2 seconds
            frame_num += 1
            screenshot_path = output_dir / f"frame_{frame_num:04d}.png"
            page.screenshot(path=str(screenshot_path))
            screenshots.append(screenshot_path)
            time.sleep(0.1)

        # Go back to Contribuciones
        print("Back to Contribuciones...")
        page.click("text=Contribuciones")
        time.sleep(0.5)

        for _ in range(10):
            frame_num += 1
            screenshot_path = output_dir / f"frame_{frame_num:04d}.png"
            page.screenshot(path=str(screenshot_path))
            screenshots.append(screenshot_path)
            time.sleep(0.1)

        browser.close()

    print(f"Captured {frame_num} frames")

    # Create video from screenshots
    print("Creating video...")
    video_path = f"demo_governance_{timestamp}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-framerate", "10",
        "-i", f"{output_dir}/frame_%04d.png",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        video_path
    ]

    subprocess.run(cmd, check=True)
    print(f"Video saved to: {video_path}")

    # Also create GIF
    print("Creating GIF...")
    gif_path = f"demo_governance_{timestamp}.gif"

    cmd_gif = [
        "ffmpeg", "-y",
        "-framerate", "10",
        "-i", f"{output_dir}/frame_%04d.png",
        "-vf", "scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        gif_path
    ]

    subprocess.run(cmd_gif, check=True)
    print(f"GIF saved to: {gif_path}")

    return video_path


if __name__ == "__main__":
    record_governance_demo()
