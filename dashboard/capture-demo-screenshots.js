const puppeteer = require('puppeteer');
const path = require('path');

const SCREENSHOTS_DIR = '/tmp/privacy-platform/docs/demos/bank-consortium/screenshots';

async function captureScreenshots() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  console.log('Navigating to demo...');
  await page.goto('http://localhost:3000/demo-bank', { waitUntil: 'networkidle0' });

  // Wait for page to load
  await page.waitForSelector('button', { timeout: 10000 });

  const steps = [
    { num: 0, name: '00_problema', description: 'El Problema' },
    { num: 1, name: '01_setup_datos', description: 'Setup - Datos de los Bancos' },
    { num: 2, name: '02_entrenamiento_individual', description: 'Entrenamiento Individual' },
    { num: 3, name: '03_cifrado_fhe', description: 'Cifrado FHE' },
    { num: 4, name: '04_entrenamiento_consorcio', description: 'Entrenamiento Consorcio' },
    { num: 5, name: '05_inferencia_cifrada', description: 'Inferencia Cifrada' },
    { num: 6, name: '06_resultados', description: 'Resultados Finales' },
  ];

  for (const step of steps) {
    console.log(`Capturing Step ${step.num}: ${step.description}...`);

    // Click the step button
    const stepButtons = await page.$$('button');
    for (const btn of stepButtons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text.includes(step.description) || text.includes(step.num.toString())) {
        await btn.click();
        break;
      }
    }

    // Also try clicking by step number in the navigation
    try {
      const navButtons = await page.$$('button');
      for (const btn of navButtons) {
        const text = await page.evaluate(el => el.textContent, btn);
        if (text.includes(step.description.split(' ')[0])) {
          await btn.click();
          break;
        }
      }
    } catch (e) {}

    // For step navigation, click "Siguiente" the right number of times from start
    if (step.num > 0) {
      // Click siguiente button
      const siguienteBtn = await page.$('button:has-text("Siguiente")');
      if (siguienteBtn) {
        await siguienteBtn.click();
      }
    }

    // Wait for animations
    await new Promise(r => setTimeout(r, 1500));

    // Take screenshot
    const screenshotPath = path.join(SCREENSHOTS_DIR, `${step.name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`  Saved: ${screenshotPath}`);
  }

  await browser.close();
  console.log('\nAll screenshots captured!');
}

captureScreenshots().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
