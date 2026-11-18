# Optional browser QA

Run from repository root with the static server running. Install Node.js, then `npm install --no-save playwright` and `npx playwright install chromium`; node_modules is not committed. Run `node scripts/browser/d-smoke.mjs`, `e-smoke.mjs`, `m-smoke.mjs`, `f-smoke.mjs`. Default URL is http://127.0.0.1:8780; set DEMO_URL to a hosted root URL for public verification. Optional PLAYWRIGHT_MODULE and CHROMIUM_EXECUTABLE override installed module/binary locations. Scripts save evidence screenshots and JSON. Playwright is only for QA, not required to use the dashboard.
