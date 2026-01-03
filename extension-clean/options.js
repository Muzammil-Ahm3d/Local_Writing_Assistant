// Options page script
document.addEventListener('DOMContentLoaded', function() {
    // Load settings when page loads
    loadSettings();
    
    // Set up event listeners
    document.getElementById('testConnection').addEventListener('click', testConnection);
    document.getElementById('saveSettings').addEventListener('click', saveSettings);
    document.getElementById('resetSettings').addEventListener('click', resetSettings);
});

// Load settings from storage
async function loadSettings() {
    try {
        const settings = await chrome.storage.sync.get({
            serverUrl: 'http://127.0.0.1:8000',
            apiToken: 'test123456789',
            enabled: true,
            language: 'en-US'
        });
        
        document.getElementById('serverUrl').value = settings.serverUrl;
        document.getElementById('apiToken').value = settings.apiToken;
        document.getElementById('enabled').checked = settings.enabled;
        document.getElementById('language').value = settings.language;
        document.getElementById('currentServer').textContent = settings.serverUrl;
        
    } catch (error) {
        console.error('Failed to load settings:', error);
        showStatus('saveStatus', 'Failed to load settings', 'error');
    }
}

// Save settings to storage
async function saveSettings() {
    try {
        const settings = {
            serverUrl: document.getElementById('serverUrl').value.trim(),
            apiToken: document.getElementById('apiToken').value.trim(),
            enabled: document.getElementById('enabled').checked,
            language: document.getElementById('language').value
        };
        
        // Validate server URL
        if (settings.serverUrl && !isValidUrl(settings.serverUrl)) {
            showStatus('saveStatus', 'Please enter a valid server URL', 'error');
            return;
        }
        
        await chrome.storage.sync.set(settings);
        document.getElementById('currentServer').textContent = settings.serverUrl;
        showStatus('saveStatus', '✅ Settings saved successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save settings:', error);
        showStatus('saveStatus', 'Failed to save settings', 'error');
    }
}

// Test connection to server
async function testConnection() {
    const serverUrl = document.getElementById('serverUrl').value.trim();
    const apiToken = document.getElementById('apiToken').value.trim();
    
    if (!serverUrl) {
        showStatus('connectionStatus', 'Please enter a server URL first', 'error');
        return;
    }
    
    const button = document.getElementById('testConnection');
    const originalText = button.textContent;
    button.textContent = 'Testing...';
    button.disabled = true;
    
    try {
        const result = await chrome.runtime.sendMessage({
            action: 'testConnection',
            serverUrl: serverUrl,
            apiToken: apiToken
        });
        
        if (result.success) {
            showStatus('connectionStatus', 
                `✅ Connection successful! Server version: ${result.data?.version || 'Unknown'}`, 
                'success'
            );
        } else {
            showStatus('connectionStatus', `❌ Connection failed: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showStatus('connectionStatus', `❌ Test failed: ${error.message}`, 'error');
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Reset settings to defaults
async function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to their default values?')) {
        try {
            const defaults = {
                serverUrl: 'http://127.0.0.1:8000',
                apiToken: 'test123456789',
                enabled: true,
                language: 'en-US'
            };
            
            await chrome.storage.sync.set(defaults);
            loadSettings(); // Reload the form
            showStatus('saveStatus', '✅ Settings reset to defaults', 'success');
            
        } catch (error) {
            console.error('Failed to reset settings:', error);
            showStatus('saveStatus', 'Failed to reset settings', 'error');
        }
    }
}

// Show status message
function showStatus(elementId, message, type) {
    const statusDiv = document.getElementById(elementId);
    statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
    setTimeout(() => statusDiv.innerHTML = '', 3000);
}

// Validate URL format
function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
        return false;
    }
}
