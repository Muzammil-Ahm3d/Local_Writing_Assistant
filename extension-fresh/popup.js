document.addEventListener('DOMContentLoaded', async function() {
  console.log('Popup loaded');
  
  // Load serverUrl from storage and test server connection
  try {
    const cfg = await chrome.storage.local.get({ serverUrl: 'http://127.0.0.1:8001' });
    const response = await fetch(`${cfg.serverUrl}/health`);
    if (response.ok) {
      document.getElementById('status').className = 'status ok';
      document.getElementById('status').textContent = '✅ Server online';
    } else {
      throw new Error('Server not responding');
    }
  } catch (error) {
    document.getElementById('status').className = 'status err';
    document.getElementById('status').textContent = '❌ Server offline';
  }
  
  // Settings button
  document.getElementById('btnSettings').addEventListener('click', function() {
    console.log('Settings button clicked');
    chrome.runtime.openOptionsPage();
  });
  
  // Docs button
  document.getElementById('btnDocs').addEventListener('click', function() {
    chrome.tabs.create({ url: 'http://127.0.0.1:8001/docs' });
  });
});
