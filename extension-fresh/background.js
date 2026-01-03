console.log('Writing Assistant background script loaded');

chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed/updated');
  chrome.storage.local.set({
    serverUrl: 'http://127.0.0.1:8001',
    apiToken: 'test123456789'
  });
});
