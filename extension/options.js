// options.js
// Local Writing Assistant - Options Page Script
// Handles settings configuration and testing

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settingsForm');
    const testButton = document.getElementById('testConnection');
    const resetButton = document.getElementById('resetSettings');
    
    // Load saved settings
    loadSettings();
    
    // Save settings on form submit
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });
    
    // Test connection
    testButton.addEventListener('click', testConnection);
    
    // Reset settings
    resetButton.addEventListener('click', resetToDefaults);
});

// Load settings from storage
function loadSettings() {
    chrome.storage.sync.get({
        serverUrl: 'http://127.0.0.1:8001',
        apiToken: '',
        language: 'en-US',
        debounceDelay: 600,
        enabled: true,
        showToolbar: true
    }, function(items) {
        document.getElementById('serverUrl').value = items.serverUrl;
        document.getElementById('apiToken').value = items.apiToken;
        document.getElementById('language').value = items.language;
        document.getElementById('debounceDelay').value = items.debounceDelay;
        document.getElementById('enabled').checked = items.enabled;
        document.getElementById('showToolbar').checked = items.showToolbar;
    });
}

// Save settings to storage
function saveSettings() {
    const settings = {
        serverUrl: document.getElementById('serverUrl').value.trim(),
        apiToken: document.getElementById('apiToken').value.trim(),
        language: document.getElementById('language').value,
        debounceDelay: parseInt(document.getElementById('debounceDelay').value) || 600,
        enabled: document.getElementById('enabled').checked,
        showToolbar: document.getElementById('showToolbar').checked
    };
    
    // Validate server URL
    if (settings.serverUrl && !isValidUrl(settings.serverUrl)) {
        showStatus('saveStatus', 'Please enter a valid server URL', 'error');
        return;
    }
    
    // Validate debounce delay
    if (settings.debounceDelay < 100 || settings.debounceDelay > 2000) {
        showStatus('saveStatus', 'Check delay must be between 100 and 2000 milliseconds', 'error');
        return;
    }
    
    chrome.storage.sync.set(settings, function() {
        if (chrome.runtime.lastError) {
            showStatus('saveStatus', 'Failed to save settings: ' + chrome.runtime.lastError.message, 'error');
        } else {
            showStatus('saveStatus', '✓ Settings saved successfully!', 'success');
            
            // Notify content scripts of the change
            chrome.tabs.query({}, function(tabs) {
                tabs.forEach(tab => {
                    chrome.tabs.sendMessage(tab.id, {
                        action: 'configUpdated',
                        config: settings
                    }).catch(() => {
                        // Content script might not be loaded, that's OK
                    });
                });
            });
        }
    });
}

// Test connection to the local server
async function testConnection() {
    const serverUrl = document.getElementById('serverUrl').value.trim();
    const apiToken = document.getElementById('apiToken').value.trim();
    
    if (!serverUrl) {
        showStatus('connectionStatus', 'Please enter a server URL first', 'error');
        return;
    }
    
    const button = testButton;
    const originalText = button.textContent;
    button.textContent = 'Testing...';
    button.disabled = true;
    
    try {
        // Test basic health endpoint with timeout controller
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const healthResponse = await fetch(`${serverUrl}/health`, {
            method: 'GET',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!healthResponse.ok) {
            throw new Error(`Server returned ${healthResponse.status}: ${healthResponse.statusText}`);
        }
        
        const healthData = await healthResponse.json();
        
        if (!healthData.ok) {
            throw new Error('Server health check failed');
        }
        
        // Test API endpoints with token if provided
        if (apiToken) {
            await testApiEndpoints(serverUrl, apiToken);
        }
        
        showStatus('connectionStatus', 
            `✓ Connection successful! Server version: ${healthData.version || 'Unknown'}`, 
            'success'
        );
        
    } catch (error) {
        console.error('Connection test failed:', error);
        
        let errorMessage = 'Connection failed: ';
        
        if (error.name === 'TimeoutError') {
            errorMessage += 'Request timed out. Make sure the server is running.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage += 'Could not reach server. Check the URL and ensure the server is running.';
        } else {
            errorMessage += error.message;
        }
        
        showStatus('connectionStatus', errorMessage, 'error');
        
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Test API endpoints
async function testApiEndpoints(serverUrl, apiToken) {
    const testEndpoints = [
        { path: '/api/check', method: 'POST', data: { text: 'This is a test.', language: 'en-US' } },
        { path: '/api/tone', method: 'POST', data: { text: 'This is a test message.' } }
    ];
    
    for (const endpoint of testEndpoints) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${serverUrl}${endpoint.path}`, {
            method: endpoint.method,
            headers: {
                'Content-Type': 'application/json',
                'X-Local-Auth': apiToken
            },
            body: JSON.stringify(endpoint.data),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Invalid API token. Check your .env file for the correct token.');
            }
            throw new Error(`API test failed for ${endpoint.path}: ${response.status} ${response.statusText}`);
        }
    }
}

// Reset settings to defaults
function resetToDefaults() {
    if (confirm('Are you sure you want to reset all settings to their default values?')) {
        const defaults = {
            serverUrl: 'http://127.0.0.1:8001',
            apiToken: '',
            language: 'en-US',
            debounceDelay: 600,
            enabled: true,
            showToolbar: true
        };
        
        chrome.storage.sync.set(defaults, function() {
            if (chrome.runtime.lastError) {
                showStatus('saveStatus', 'Failed to reset settings: ' + chrome.runtime.lastError.message, 'error');
            } else {
                loadSettings(); // Reload form with defaults
                showStatus('saveStatus', '✓ Settings reset to defaults', 'success');
            }
        });
    }
}

// Show status message
function showStatus(elementId, message, type) {
    const statusElement = document.getElementById(elementId);
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
    statusElement.classList.remove('hidden');
    
    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            statusElement.classList.add('hidden');
        }, 5000);
    }
}

// Validate URL format
function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

// Listen for storage changes from other parts of the extension
chrome.storage.onChanged.addListener(function(changes, namespace) {
    if (namespace === 'sync') {
        // Reload settings if they were changed elsewhere
        setTimeout(loadSettings, 100);
    }
});
