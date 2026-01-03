// service-worker.js
// Local Writing Assistant - Background Service Worker
// Handles background tasks and extension lifecycle

chrome.runtime.onInstalled.addListener((details) => {
    console.log('Local Writing Assistant: Extension installed/updated', details);
    
    // Set default configuration on first install
    if (details.reason === 'install') {
        chrome.storage.sync.set({
            serverUrl: 'http://127.0.0.1:8001',
            apiToken: '',
            language: 'en-US',
            debounceDelay: 600,
            enabled: true,
            showToolbar: true
        });
        
        // Open options page on first install
        chrome.runtime.openOptionsPage();
    }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    // Check if we can inject into this tab
    if (tab.url.startsWith('chrome://') || 
        tab.url.startsWith('chrome-extension://') ||
        tab.url.startsWith('moz-extension://')) {
        // Can't inject into browser pages, open options instead
        chrome.runtime.openOptionsPage();
        return;
    }
    
    // Toggle extension enabled state
    chrome.storage.sync.get(['enabled'], (result) => {
        const newState = !result.enabled;
        chrome.storage.sync.set({ enabled: newState });
        
        // Update icon based on state
        updateIcon(newState);
        
        // Send message to content script
        chrome.tabs.sendMessage(tab.id, {
            action: 'toggleEnabled',
            enabled: newState
        }).catch(() => {
            // Content script might not be loaded yet, that's OK
        });
    });
});

// Update extension icon based on enabled state
function updateIcon(enabled) {
    // Just update the title since we don't have icon files
    chrome.action.setTitle({ 
        title: enabled ? 'Local Writing Assistant (Enabled)' : 'Local Writing Assistant (Disabled)'
    });
}

// Initialize icon state on startup
chrome.storage.sync.get(['enabled'], (result) => {
    updateIcon(result.enabled !== false); // Default to enabled
});

// Listen for storage changes to update icon
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'sync' && changes.enabled) {
        updateIcon(changes.enabled.newValue);
    }
});

// Handle messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getConfig') {
        // Return current configuration
        chrome.storage.sync.get([
            'serverUrl',
            'apiToken', 
            'language',
            'debounceDelay',
            'enabled',
            'showToolbar'
        ], (result) => {
            sendResponse(result);
        });
        return true; // Keep message channel open for async response
    }
    
    if (request.action === 'checkServerHealth') {
        // Check if the local server is running
        checkServerHealth(request.serverUrl, request.apiToken)
            .then(result => sendResponse(result))
            .catch(error => sendResponse({ 
                healthy: false, 
                error: error.message 
            }));
        return true;
    }
});

// Check server health
async function checkServerHealth(serverUrl, apiToken) {
    try {
        // Create timeout controller for older browser compatibility
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${serverUrl}/health`, {
            method: 'GET',
            headers: apiToken ? {
                'X-Local-Auth': apiToken
            } : {},
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return {
            healthy: true,
            data: data
        };
        
    } catch (error) {
        console.error('Server health check failed:', error);
        return {
            healthy: false,
            error: error.message
        };
    }
}

// Handle context menu (optional feature)
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "rewrite-selection",
        title: "Rewrite with Local Writing Assistant",
        contexts: ["selection"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "rewrite-selection" && info.selectionText) {
        // Send selected text to content script for rewriting
        chrome.tabs.sendMessage(tab.id, {
            action: 'rewriteSelection',
            text: info.selectionText
        }).catch(() => {
            console.log('Could not send message to content script');
        });
    }
});

// Cleanup on extension disable/uninstall
chrome.runtime.onSuspend.addListener(() => {
    console.log('Local Writing Assistant: Extension suspended');
});

// Handle alarms (for periodic tasks if needed)
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'healthCheck') {
        // Periodic health check could be implemented here
        console.log('Periodic health check triggered');
    }
});

// Optional: Set up periodic health check
chrome.storage.sync.get(['serverUrl', 'apiToken', 'enabled'], (result) => {
    if (result.enabled && result.serverUrl) {
        // Set up a periodic alarm to check server health
        chrome.alarms.create('healthCheck', { 
            delayInMinutes: 1, 
            periodInMinutes: 5 
        });
    }
});
