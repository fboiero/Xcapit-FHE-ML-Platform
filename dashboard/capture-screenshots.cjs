const puppeteer = require('puppeteer');

const SCREENSHOTS_DIR = '/tmp/privacy-platform/docs/demos/bank-consortium/screenshots';

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function captureScreenshots() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  console.log('Navigating to demo...');
  await page.goto('http://localhost:3000/demo-bank', { waitUntil: 'networkidle0', timeout: 30000 });
  await delay(2000);

  const steps = [
    '00_problema',
    '01_setup_datos',
    '02_entrenamiento_individual',
    '03_cifrado_fhe',
    '04_entrenamiento_consorcio',
    '05_inferencia_cifrada',
    '06_resultados',
  ];

  for (let i = 0; i < steps.length; i++) {
    console.log(`\nStep ${i}: ${steps[i]}`);

    // Take screenshot
    const screenshotPath = `${SCREENSHOTS_DIR}/${steps[i]}.png`;
    await page.screenshot({ path: screenshotPath });
    console.log(`  Screenshot saved: ${screenshotPath}`);

    // Click "Siguiente" button to go to next step
    if (i < steps.length - 1) {
      try {
        // Find and click the "Siguiente" button
        const clicked = await page.evaluate(() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const nextBtn = buttons.find(b => b.textContent.includes('Siguiente'));
          if (nextBtn && !nextBtn.disabled) {
            nextBtn.click();
            return true;
          }
          return false;
        });

        if (clicked) {
          console.log('  Clicked Siguiente');
          await delay(2000); // Wait for transition
        } else {
          console.log('  Could not find Siguiente button');
        }
      } catch (err) {
        console.log('  Error clicking:', err.message);
      }
    }
  }

  await browser.close();
  console.log('\n✅ All screenshots captured!');
  console.log(`\nScreenshots saved to: ${SCREENSHOTS_DIR}/`);
}

captureScreenshots().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
