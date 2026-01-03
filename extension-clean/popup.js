// No inline JS. All DOM wiring happens here to satisfy CSP.
const els = {
  status: document.getElementById('status'),
  btnTest: document.getElementById('btnTest'),
  btnOptions: document.getElementById('btnOptions'),
  btnDocs: document.getElementById('btnDocs'),
  serverTxt: document.getElementById('serverTxt'),
  tokenTxt: document.getElementById('tokenTxt'),
};

async function loadSettings() {
  const cfg = await chrome.storage.sync.get(['serverUrl', 'apiToken']);
  els.serverTxt.textContent = cfg.serverUrl || 'http://127.0.0.1:8000';
  els.tokenTxt.textContent = cfg.apiToken ? 'set' : 'not set';
  return { serverUrl: els.serverTxt.textContent, apiToken: cfg.apiToken || '' };
}

async function testConnection() {
  els.status.className = 'status';
  els.status.textContent = 'Testing connection...';
  els.btnTest.disabled = true;
  try {
    const { serverUrl, apiToken } = await loadSettings();
    const res = await chrome.runtime.sendMessage({
      action: 'testConnection',
      serverUrl,
      apiToken
    });
    if (res?.success) {
      els.status.className = 'status ok';
      els.status.textContent = `✅ Server online (version: ${res.data?.version || 'unknown'})`;
    } else {
      els.status.className = 'status err';
      els.status.textContent = `❌ ${res?.error || 'Connection failed'}`;
    }
  } catch (e) {
    els.status.className = 'status err';
    els.status.textContent = `❌ ${e?.message || e}`;
  } finally {
    els.btnTest.disabled = false;
  }
}

els.btnTest.addEventListener('click', testConnection);
els.btnOptions.addEventListener('click', () => chrome.runtime.openOptionsPage());
els.btnDocs.addEventListener('click', async () => {
  const { serverUrl } = await loadSettings();
  chrome.tabs.create({ url: `${serverUrl}/docs` });
});

// Initial auto test
loadSettings().then(testConnection);