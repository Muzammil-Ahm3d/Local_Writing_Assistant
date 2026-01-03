# Local Writing Assistant - Chrome Extension

## Installation Instructions

### Step 1: Prepare the Extension Icons
Since the extension requires icon files, you'll need to create simple placeholder icons or download proper ones.

**Quick Solution - Create placeholder icons:**
1. Create 4 simple PNG files in the `icons/` folder:
   - `icon-16.png` (16x16 pixels)
   - `icon-32.png` (32x32 pixels) 
   - `icon-48.png` (48x48 pixels)
   - `icon-128.png` (128x128 pixels)

You can create these using any image editor, or use online tools like:
- https://favicon.io/favicon-generator/
- https://www.canva.com/

**Or temporarily remove icon requirements:**
Edit `manifest.json` and remove the icon sections if you want to test immediately.

### Step 2: Load the Extension in Chrome

1. **Start your Local Writing Assistant server:**
   ```batch
   python simple_server.py
   ```
   (Or use the full server: `.\start_server.bat`)

2. **Open Chrome and go to Extensions:**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

3. **Load the Extension:**
   - Click "Load unpacked"
   - Select the `extension` folder
   - The extension should appear in your extensions list

### Step 3: Configure the Extension

1. **Open Extension Options:**
   - Click the extension icon in Chrome toolbar
   - Or go to `chrome://extensions/` and click "Options" under Local Writing Assistant

2. **Configure Settings:**
   - **Server URL**: `http://127.0.0.1:8000` (default)
   - **API Token**: Copy from your `.env` file (currently: `test123456789`)
   - Click "Test Connection" to verify it works
   - Enable/disable features as needed

### Step 4: Test the Extension

1. **Visit any webpage with text inputs**
2. **Click on a text area or input field**
3. **Look for the Writing Assistant toolbar/overlay**
4. **Test features like:**
   - Grammar checking
   - Text rewriting
   - Tone analysis
   - Voice input (if microphone permissions granted)

## Features

- ✅ **Grammar Checking**: Real-time grammar and spelling correction
- ✅ **AI Rewriting**: Improve text with different styles (fix, concise, formal, friendly)
- ✅ **Tone Analysis**: Analyze sentiment and formality
- ✅ **Voice Input**: Speech-to-text transcription
- ✅ **Privacy First**: All processing happens locally, no cloud services

## Troubleshooting

### Extension Won't Load
- Make sure all required files exist (especially icons)
- Check Chrome developer console for errors
- Ensure manifest.json is valid JSON

### Server Connection Issues
- Verify server is running: http://127.0.0.1:8000/health
- Check API token matches your .env file
- Ensure no firewall blocking localhost connections

### Features Not Working
- Check if Java is installed (for grammar checking)
- Verify AI models were downloaded successfully
- Check server logs for errors

## Files Structure

```
extension/
├── manifest.json          # Extension configuration
├── content-script.js      # Main functionality injected into web pages
├── service-worker.js      # Background service worker
├── options.html          # Settings page
├── popup.html           # Extension popup
├── overlay.css          # Styles for the writing assistant UI
└── icons/              # Extension icons (16, 32, 48, 128px)
```

## Privacy

This extension operates completely offline:
- ✅ No data sent to external servers
- ✅ No user accounts or registration required  
- ✅ No tracking or analytics
- ✅ All AI processing happens locally on your computer
- ✅ Your text never leaves your machine
