/**
 * Warm Nuxt/Vite dev server routes before Cypress starts.
 *
 * The first route hits can trigger Vite dependency optimization + reloads, which
 * can transiently break Cypress cy.visit() with network timeouts. This script
 * triggers those reloads before tests run.
 */

const baseUrl = (process.env.WARMUP_BASE_URL || 'http://localhost:3000').replace(/\/$/, '');

const paths = ['/', '/books/search', '/library'];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithRetry(path, { attempts = 30, delayMs = 500 } = {}) {
  const url = `${baseUrl}${path}`;
  let lastErr;
  for (let i = 1; i <= attempts; i++) {
    try {
      const res = await fetch(url, { redirect: 'manual' });
      // Accept 2xx and redirects; we just need the server to respond.
      if ((res.status >= 200 && res.status < 300) || (res.status >= 300 && res.status < 400)) {
        return res.status;
      }
      lastErr = new Error(`Unexpected status ${res.status} for ${url}`);
    } catch (err) {
      lastErr = err;
    }
    await sleep(delayMs);
  }
  throw lastErr || new Error(`Warmup failed for ${url}`);
}

async function main() {
  console.log(`[warmup] baseUrl=${baseUrl}`);
  for (const path of paths) {
    const status = await fetchWithRetry(path);
    console.log(`[warmup] ${path} -> ${status}`);
  }

  // Give Vite a moment if it decides to restart after optimizing deps.
  await sleep(1500);
  const status = await fetchWithRetry('/books/search', { attempts: 10, delayMs: 300 });
  console.log(`[warmup] stable check /books/search -> ${status}`);
}

await main();
