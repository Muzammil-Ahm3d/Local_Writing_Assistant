document.addEventListener('DOMContentLoaded', function() {
  console.log('=== OPTIONS PAGE LOADED ===');
  loadSettings();
  
  console.log('Binding event listeners...');
  document.getElementById('btnSave').addEventListener('click', function() {
    console.log('Save button clicked');
    saveSettings();
  });
  document.getElementById('btnTest').addEventListener('click', function() {
    console.log('Test button clicked');
    testConnection();
  });
  document.getElementById('btnReset').addEventListener('click', function() {
    console.log('Reset button clicked');
    resetSettings();
  });
  console.log('Event listeners bound successfully');
  
  // Add debug button for storage inspection
  const debugBtn = document.createElement('button');
  debugBtn.textContent = 'Debug Storage';
  debugBtn.onclick = inspectStorageDebug;
  document.body.appendChild(debugBtn);
});

async function loadSettings() {
  console.log('>>> Loading settings from chrome.storage.local...');
  try {
    const settings = await chrome.storage.local.get({
      serverUrl: 'http://127.0.0.1:8001',
      apiToken: 'test123456789'
    });
    
    console.log('Raw settings from storage:', JSON.stringify(settings, null, 2));
    console.log('Setting serverUrl input to:', settings.serverUrl);
    console.log('Setting apiToken input to:', settings.apiToken.substring(0, 8) + '...');
    
    document.getElementById('serverUrl').value = settings.serverUrl;
    document.getElementById('apiToken').value = settings.apiToken;
    
    // Verify values were set correctly
    const actualServerUrl = document.getElementById('serverUrl').value;
    const actualApiToken = document.getElementById('apiToken').value;
    console.log('Verification - serverUrl input now contains:', actualServerUrl);
    console.log('Verification - apiToken input now contains:', actualApiToken.substring(0, 8) + '...');
    
    console.log('<<< Settings loaded successfully');
  } catch (error) {
    console.error('!!! Failed to load settings:', error);
  }
}

async function saveSettings() {
  console.log('>>> Saving settings to chrome.storage.local...');
  try {
    const serverUrlInput = document.getElementById('serverUrl').value.trim();
    const apiTokenInput = document.getElementById('apiToken').value.trim();
    
    console.log('Reading from inputs - serverUrl:', serverUrlInput);
    console.log('Reading from inputs - apiToken:', apiTokenInput.substring(0, 8) + '...');
    
    const settings = {
      serverUrl: serverUrlInput,
      apiToken: apiTokenInput
    };
    
    console.log('About to save settings:', JSON.stringify(settings, null, 2));
    await chrome.storage.local.set(settings);
    console.log('Storage.set() completed successfully');
    
    // Verify the save worked by reading back
    const verification = await chrome.storage.local.get(['serverUrl', 'apiToken']);
    console.log('Verification read from storage:', JSON.stringify(verification, null, 2));
    
    showStatus('✅ Settings saved!', 'success');
    console.log('<<< Settings saved successfully');
  } catch (error) {
    console.error('!!! Failed to save settings:', error);
    showStatus('❌ Failed to save settings: ' + error.message, 'error');
  }
}

async function testConnection() {
  const serverUrl = document.getElementById('serverUrl').value.trim();
  if (!serverUrl) {
    showStatus('❌ Please enter a server URL', 'error');
    return;
  }
  
  showStatus('🔍 Testing connection...', '');
  
  try {
    const response = await fetch(`${serverUrl}/health`);
    if (response.ok) {
      const data = await response.json();
      showStatus(`✅ Connection successful! Version: ${data.version || 'Unknown'}`, 'success');
    } else {
      showStatus(`❌ Server returned ${response.status}`, 'error');
    }
  } catch (error) {
    console.error('Connection test failed:', error);
    showStatus('❌ Connection failed. Is the server running?', 'error');
  }
}

function resetSettings() {
  console.log('>>> Resetting settings to defaults...');
  if (confirm('Reset to default settings?')) {
    console.log('User confirmed reset');
    document.getElementById('serverUrl').value = 'http://127.0.0.1:8001';
    document.getElementById('apiToken').value = 'test123456789';
    console.log('Input values reset, now calling saveSettings()');
    saveSettings();
  } else {
    console.log('User cancelled reset');
  }
}

function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = 'status ' + type;
  
  if (type) {
    setTimeout(() => {
      statusDiv.textContent = '';
      statusDiv.className = '';
    }, 3000);
  }
}

// Debug function to inspect storage state
async function inspectStorageDebug() {
  console.log('=== STORAGE DEBUG INSPECTION ===');
  try {
    // Get all storage contents
    const allStorage = await chrome.storage.local.get(null);
    console.log('All storage contents:', JSON.stringify(allStorage, null, 2));
    
    // Get specific keys
    const specific = await chrome.storage.local.get(['serverUrl', 'apiToken']);
    console.log('Specific keys (serverUrl, apiToken):', JSON.stringify(specific, null, 2));
    
    // Check current input values
    const currentServerUrl = document.getElementById('serverUrl').value;
    const currentApiToken = document.getElementById('apiToken').value;
    console.log('Current input values:');
    console.log('  serverUrl input:', currentServerUrl);
    console.log('  apiToken input:', currentApiToken.substring(0, 8) + '...');
    
    // Check if values match
    const match = {
      serverUrl: currentServerUrl === specific.serverUrl,
      apiToken: currentApiToken === specific.apiToken
    };
    console.log('Storage vs Input match:', match);
    
    alert(`Storage Debug:\nStorage serverUrl: ${specific.serverUrl}\nInput serverUrl: ${currentServerUrl}\nMatch: ${match.serverUrl}`);
    
  } catch (error) {
    console.error('Storage debug failed:', error);
  }
  console.log('=== END STORAGE DEBUG ===');
}
