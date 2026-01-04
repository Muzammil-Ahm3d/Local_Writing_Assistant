
// Minimal background service worker (CSP-safe, no icons, no inline code)
console.log('LWA: service worker starting');

chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('LWA: onInstalled', details?.reason);
  if (details?.reason === 'install') {
    await chrome.storage.sync.set({
      serverUrl: 'http://127.0.0.1:8001',
      apiToken: 'test123456789',
      enabled: true
    });      
  }
});

// Handle connection test requests from the popup
chrome.runtime.onMessage.addListener((req, _sender, sendResponse) => {
  if (req?.action === 'testConnection') {
    testConnection(req.serverUrl, req.apiToken)
      .then((res) => sendResponse(res))
      .catch((err) => sendResponse({ success: false, error: err?.message || String(err) }));
    return true; // keep message channel open
  }
});

async function testConnection(serverUrl, apiToken) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const res = await fetch(`${serverUrl}/health`, { method: 'GET', signal: controller.signal });
    clearTimeout(timeout);

    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    const data = await res.json();
    return { success: true, data };
  } catch (err) {
    console.error('LWA: connection test failed', err);
    return { success: false, error: err?.message || String(err) };
  }
}
