"""
Record a cinematic video of the commercial landing page.

Uses Playwright to open the page in a real browser,
scroll through it smoothly, and capture the result as video.
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
HTML_FILE = HERE / "commercial.html"
OUTPUT_DIR = HERE / "video_raw"
FINAL_VIDEO = HERE / "xcapit_fhe_commercial.mp4"

# Video settings
WIDTH = 1920
HEIGHT = 1080
SCROLL_SPEED = 2.5        # pixels per frame-step
PAUSE_HERO = 4.0          # seconds to linger on hero
PAUSE_SECTION = 2.0       # seconds to pause at each section
PAUSE_END = 3.0           # seconds at the end
FPS = 30


async def record():
    OUTPUT_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=2,
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = await context.new_page()

        # Load the page
        await page.goto(f"file://{HTML_FILE}", wait_until="networkidle")
        await page.wait_for_timeout(2000)  # let fonts + animations settle

        # Force all reveal elements visible for clean recording
        await page.evaluate("""
            document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale')
                .forEach(el => el.classList.add('visible'));
        """)
        await page.wait_for_timeout(500)

        # Get total page height
        total_height = await page.evaluate("document.documentElement.scrollHeight")
        print(f"Page height: {total_height}px")
        print(f"Recording at {WIDTH}x{HEIGHT} @ {FPS}fps")

        # ── SCENE 1: Hero (hold) ─────────────────────
        print("[1/7] Hero — holding...")
        await page.wait_for_timeout(int(PAUSE_HERO * 1000))

        # ── SCENE 2: Scroll to Problem ───────────────
        print("[2/7] Scrolling to Problem section...")
        await smooth_scroll_to(page, "#problema", duration=3.0)
        await trigger_reveals(page)
        await page.wait_for_timeout(int(PAUSE_SECTION * 1000))

        # ── SCENE 3: Scroll to Solution / Timeline ───
        print("[3/7] Scrolling through Solution timeline...")
        await smooth_scroll_to(page, "#solucion", duration=3.0)
        await trigger_reveals(page)
        await page.wait_for_timeout(1000)

        # Scroll through each timeline step slowly
        steps = await page.query_selector_all(".timeline-step")
        for i, step in enumerate(steps):
            bbox = await step.bounding_box()
            if bbox:
                target_y = await page.evaluate(
                    f"document.querySelector('.timeline-step:nth-child({i+1})').offsetTop - 100"
                )
                await smooth_scroll_to_y(page, target_y, duration=2.0)
                await trigger_reveals(page)
                await page.wait_for_timeout(1500)

        # ── SCENE 4: FHE Section ─────────────────────
        print("[4/8] FHE Real section...")
        await smooth_scroll_to(page, "#fhe", duration=3.0)
        await trigger_reveals(page)
        await page.wait_for_timeout(int(PAUSE_SECTION * 1500))

        # ── SCENE 4b: 4 Pillars ────────────────────
        print("[5/8] 4 Pilares de Privacidad...")
        await smooth_scroll_to(page, "#pilares", duration=3.0)
        await trigger_reveals(page)
        await page.wait_for_timeout(int(PAUSE_SECTION * 2000))

        # ── SCENE 5: Demo / Metrics ─────────────────
        print("[6/8] Demo metrics...")
        await smooth_scroll_to(page, "#demo", duration=3.0)
        await trigger_reveals(page)
        # Animate the counters
        await page.evaluate("""
            document.querySelectorAll('.metric-value[data-target]').forEach(el => {
                const target = parseFloat(el.dataset.target);
                const decimals = parseInt(el.dataset.decimals || '0');
                const suffix = el.dataset.suffix || '';
                el.textContent = target.toFixed(decimals) + suffix;
            });
            document.querySelectorAll('.usage-fill').forEach(bar => {
                bar.style.width = bar.dataset.width + '%';
            });
        """)
        await page.wait_for_timeout(int(PAUSE_SECTION * 1500))

        # Scroll to usage bars
        await smooth_scroll_to_y(
            page,
            await page.evaluate("document.querySelector('.usage-bars').offsetTop - 200"),
            duration=2.0
        )
        await page.wait_for_timeout(2000)

        # ── SCENE 7: Pricing ─────────────────────────
        print("[7/8] Pricing section...")
        await smooth_scroll_to(page, "#planes", duration=3.0)
        await trigger_reveals(page)
        await page.wait_for_timeout(int(PAUSE_SECTION * 1000))

        # Scroll to comparison table
        table_top = await page.evaluate(
            "document.querySelector('.comparison-table')?.offsetTop - 100 || 0"
        )
        if table_top > 0:
            await smooth_scroll_to_y(page, table_top, duration=2.5)
            await trigger_reveals(page)
            await page.wait_for_timeout(2000)

        # ── SCENE 8: CTA Final ──────────────────────
        print("[8/8] Final CTA...")
        await smooth_scroll_to(page, ".cta-section", duration=3.0)
        await trigger_reveals(page)
        await page.wait_for_timeout(int(PAUSE_END * 1000))

        # Close
        await context.close()
        await browser.close()

    # Find the recorded video
    webm_files = list(OUTPUT_DIR.glob("*.webm"))
    if not webm_files:
        print("ERROR: No video file found!")
        return

    raw_video = webm_files[0]
    print(f"\nRaw video: {raw_video} ({raw_video.stat().st_size / 1024 / 1024:.1f} MB)")

    # Convert to MP4 with high quality
    print(f"Converting to MP4...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-vf", f"scale={WIDTH}:{HEIGHT}:flags=lanczos",
        "-r", str(FPS),
        str(FINAL_VIDEO),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr[-500:]}")
        return

    size_mb = FINAL_VIDEO.stat().st_size / 1024 / 1024
    print(f"\n✓ Video generado: {FINAL_VIDEO}")
    print(f"  Tamaño: {size_mb:.1f} MB")
    print(f"  Resolución: {WIDTH}x{HEIGHT}")
    print(f"  FPS: {FPS}")


async def smooth_scroll_to(page, selector: str, duration: float = 2.0):
    """Smoothly scroll to a CSS selector."""
    target_y = await page.evaluate(f"""
        (() => {{
            const el = document.querySelector('{selector}');
            return el ? el.offsetTop - 80 : 0;
        }})()
    """)
    await smooth_scroll_to_y(page, target_y, duration)


async def smooth_scroll_to_y(page, target_y: int, duration: float = 2.0):
    """Smoothly scroll to a Y position with easing."""
    steps = int(duration * 30)  # 30 checks per second
    current_y = await page.evaluate("window.scrollY")
    distance = target_y - current_y

    for i in range(steps + 1):
        t = i / steps
        # Ease in-out cubic
        eased = t * t * (3 - 2 * t)
        y = current_y + distance * eased
        await page.evaluate(f"window.scrollTo(0, {y})")
        await page.wait_for_timeout(int(1000 / 30))


async def trigger_reveals(page):
    """Force reveal animations for elements currently in viewport."""
    await page.evaluate("""
        const vh = window.innerHeight;
        const scrollY = window.scrollY;
        document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale')
            .forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.top < vh * 1.1 && rect.bottom > -100) {
                    el.classList.add('visible');
                }
            });
    """)


if __name__ == "__main__":
    asyncio.run(record())
