# Chrome Extension Settings Debug Guide

## The Problem
- Extension settings page loads correctly
- Changing server URL from port 8000 to 8001 and clicking Save
- Settings appear to save (green checkmark message shows)
- After refreshing the page, URL reverts back to port 8000
- Buttons may appear non-functional after refresh

## Debug Steps to Follow

### Step 1: Check Console Logs
1. Open Chrome DevTools (F12) on the extension's options page
2. Go to the **Console** tab
3. You should see detailed debug logs starting with `=== OPTIONS PAGE LOADED ===`
4. Perform these actions while watching console:
   - Change server URL from `http://127.0.0.1:8000` to `http://127.0.0.1:8001`
   - Click **Save** button
   - Look for logs starting with `>>> Saving settings...`
   - Wait for `<<< Settings saved successfully`
   - Refresh the page
   - Look for logs starting with `>>> Loading settings...`

### Step 2: Inspect Chrome Storage
1. In DevTools, go to **Application** tab
2. In left sidebar, expand **Storage** → **Extension Storage** 
3. Find your extension ID and click it
4. Look for keys: `serverUrl` and `apiToken`
5. Check what values are actually stored there

### Step 3: Use Debug Storage Button
1. On the options page, you'll see a new **Debug Storage** button at the bottom
2. Click it to get a popup showing:
   - Current storage values
   - Current input field values  
   - Whether they match
3. This will also log detailed info to console

### Step 4: Manual Storage Test
1. In DevTools Console tab, run these commands manually:
   ```javascript
   // Check current storage
   chrome.storage.local.get(['serverUrl', 'apiToken']).then(console.log);
   
   // Set storage manually
   chrome.storage.local.set({serverUrl: 'http://127.0.0.1:8001', apiToken: 'test123456789'}).then(() => console.log('Manual save done'));
   
   // Verify manual save worked
   chrome.storage.local.get(['serverUrl', 'apiToken']).then(console.log);
   ```

### Step 5: Check Extension Permissions
1. Go to `chrome://extensions/`
2. Find your extension
3. Click **Details**
4. Verify it has **Storage** permission

### Step 6: Test Event Handlers
1. Watch console when clicking buttons
2. You should see:
   - `Save button clicked` when clicking Save
   - `Test button clicked` when clicking Test
   - `Reset button clicked` when clicking Reset
3. If these don't appear, event handlers aren't binding properly

## Expected Console Output

When working correctly, you should see:
```
=== OPTIONS PAGE LOADED ===
Binding event listeners...
Event listeners bound successfully
>>> Loading settings from chrome.storage.local...
Raw settings from storage: {
  "serverUrl": "http://127.0.0.1:8000",
  "apiToken": "test123456789"
}
Setting serverUrl input to: http://127.0.0.1:8000
Setting apiToken input to: test1234...
Verification - serverUrl input now contains: http://127.0.0.1:8000
Verification - apiToken input now contains: test1234...
<<< Settings loaded successfully

// After changing URL and clicking Save:
Save button clicked
>>> Saving settings to chrome.storage.local...
Reading from inputs - serverUrl: http://127.0.0.1:8001
Reading from inputs - apiToken: test1234...
About to save settings: {
  "serverUrl": "http://127.0.0.1:8001",
  "apiToken": "test123456789"
}
Storage.set() completed successfully
Verification read from storage: {
  "serverUrl": "http://127.0.0.1:8001",
  "apiToken": "test123456789"
}
<<< Settings saved successfully

// After refreshing page:
=== OPTIONS PAGE LOADED ===
>>> Loading settings from chrome.storage.local...
Raw settings from storage: {
  "serverUrl": "http://127.0.0.1:8001",
  "apiToken": "test123456789"
}
// ... should load the 8001 URL, not 8000
```

## Common Issues & Solutions

### Issue: Settings don't persist after refresh
- **Cause**: Storage API not working or permissions missing
- **Check**: Extension permissions include "storage"
- **Solution**: Reload extension completely

### Issue: Event handlers not working
- **Cause**: JavaScript errors preventing event binding
- **Check**: Console for any error messages
- **Solution**: Fix syntax errors, reload extension

### Issue: Storage shows old values
- **Cause**: Storage API calls failing silently
- **Check**: Console logs show storage operations completing
- **Solution**: Check Chrome storage quotas, try `chrome.storage.local.clear()`

### Issue: Values don't load on refresh
- **Cause**: `loadSettings()` not being called or failing
- **Check**: Console shows "Loading settings" logs
- **Solution**: Verify `DOMContentLoaded` event fires

## Nuclear Option: Reset Everything
If all else fails:
1. Go to `chrome://extensions/`
2. Remove the extension completely
3. Run in DevTools console on any page: `chrome.storage.local.clear()`
4. Clear browser cache: Ctrl+Shift+Delete
5. Reload the extension from the folder
6. Try again with fresh state

## Report Results
After following these steps, please provide:
1. All console log output (copy/paste)
2. Screenshot of Chrome Storage contents
3. Results from Debug Storage button
4. Any error messages you see
5. Specific step where the issue occurs

This will help identify the exact point of failure in the settings persistence process.
