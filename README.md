# 🖋️ Local Writing Assistant

A **privacy-first, offline grammar checker, text rewriter, and voice input tool** powered by local AI models. No data ever leaves your computer.

![Local Writing Assistant Demo](docs/demo.gif)

## ✨ Features

- 🔍 **Real-time Grammar Checking** - Powered by LanguageTool (offline)
- 🤖 **AI Text Rewriting** - Fix, Concise, Formal, Friendly modes using Flan-T5
- 🎤 **Voice-to-Text Input** - Push-to-talk transcription with Whisper
- 📊 **Tone Analysis** - Sentiment and formality detection
- 🌐 **Universal Compatibility** - Works on Gmail, Twitter, Google Docs, and most websites
- 🔒 **100% Private** - All processing happens locally, no cloud API calls
- ⚡ **CPU-Optimized** - Efficient inference on consumer hardware

## 🚀 Quick Start (Windows 10/11)

### One-Click Setup

1. **Download and extract** this repository
2. **Run the setup script**:
   ```batch
   scripts\windows\StartLocalAssistant.bat
   ```
   
3. **Load the Chrome extension**:
   - Open Chrome → Extensions → Developer Mode → Load unpacked
   - Select the `extension` folder
   
4. **Start writing!** - The extension will work on any website with text inputs

### What Gets Installed

- Python 3.11 (via winget)
- Java JDK 17 (for LanguageTool)
- FFmpeg (for audio processing)
- AI Models (Flan-T5-small, Whisper base.en)
- Python dependencies (FastAPI, transformers, etc.)

## 📋 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB+ recommended
- **CPU**: Any modern processor (no GPU required)
- **Storage**: ~3GB for models and dependencies
- **Network**: Only for initial setup and model downloads

## 🛠️ Manual Setup

If you prefer manual installation or the automatic setup fails:

<details>
<summary>Click to expand manual setup instructions</summary>

### Prerequisites

Install these using winget (Windows Package Manager):

```powershell
# Install Python 3.11
winget install -e --id Python.Python.3.11

# Install Java JDK 17 (for LanguageTool)
winget install -e --id EclipseAdoptium.Temurin.17.JDK

# Install FFmpeg (for audio processing)
winget install -e --id Gyan.FFmpeg

# Install Git (optional)
winget install -e --id Git.Git

# Install Visual C++ Redistributable (if needed)
winget install -e --id Microsoft.VCRedist.2015+.x64
```

### Python Environment

```powershell
# Create virtual environment
py -3.11 -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -U pip wheel
pip install -r server/requirements.txt
```

### Configuration

```powershell
# Create environment file
copy .env.example .env

# Edit .env and set your API token (any secure random string)
# LOCAL_API_TOKEN=your-secure-random-token-here
```

### Download AI Models

```powershell
python server/scripts/download_models.py
```

### Start the Server

```powershell
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
```

</details>

## 🎯 Usage

### Grammar Checking
- Type in any text field on any website
- Grammar issues appear with red wavy underlines
- Hover or click for suggested fixes

### Text Rewriting
- Select text and click the floating toolbar buttons:
  - **Fix** - Correct grammar and spelling
  - **Concise** - Make text shorter and clearer
  - **Formal** - Professional, business tone
  - **Friendly** - Casual, conversational tone

### Voice Input
- Click the 🎤 microphone button
- Speak clearly (up to 5 minutes)
- Click again to stop and transcribe
- Text appears at your cursor position

## ⚙️ Configuration

Access settings by:
- Right-clicking the extension icon → Options
- Or visiting `chrome://extensions` and clicking "Options" 

### Key Settings

- **Server URL**: Usually `http://127.0.0.1:8000`
- **API Token**: Found in your `.env` file
- **Language**: English variants (US, UK, Canada, Australia)
- **Check Delay**: How long to wait after typing stops (default: 600ms)
- **Features**: Toggle grammar checking, toolbar, etc.

## 🔧 Troubleshooting

### Server Won't Start

```powershell
# Check if ports are in use
netstat -an | findstr ":8000"

# Stop conflicting processes
scripts\windows\StopLocalAssistant.ps1

# Check Java installation
java -version

# Check Python installation  
python --version

# Check FFmpeg installation
ffmpeg -version
```

### Extension Issues

1. **No underlines/toolbar**: Check if the extension is enabled and server is running
2. **API errors**: Verify your API token in extension settings
3. **Voice input fails**: Grant microphone permissions to Chrome
4. **Connection timeout**: Ensure Windows Firewall isn't blocking the server

### Performance Issues

- **Slow grammar checking**: Increase debounce delay in settings
- **High CPU usage**: Consider switching to Whisper "tiny" model in `.env`
- **Memory usage**: Restart the server periodically with the stop/start scripts

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Chrome         │    │  FastAPI         │    │  AI Models     │
│  Extension      │◄──►│  Server          │◄──►│  (Local)        │
│                 │    │                  │    │                 │
│ • Content Script│    │ • Grammar Check  │    │ • LanguageTool  │
│ • Options Page  │    │ • Text Rewrite   │    │ • Flan-T5-small │
│ • Service Worker│    │ • Voice Input    │    │ • Whisper       │
└─────────────────┘    │ • Tone Analysis  │    │ • NLTK Data     │
                       └──────────────────┘    └─────────────────┘
```

### Privacy Architecture

- **Zero cloud dependencies**: All AI models run locally
- **No telemetry**: No analytics, tracking, or data collection
- **Localhost-only**: Server binds to 127.0.0.1 (not accessible from internet)
- **Token-based auth**: X-Local-Auth header protects API endpoints
- **No data persistence**: Text is processed and immediately discarded

## 📊 Performance Targets

| Feature | Target Latency | Actual (CPU-only) |
|---------|---------------|-------------------|
| Grammar check | <150ms | ~100ms |
| Text rewrite | 0.5-1.5s | ~800ms |
| Voice transcription | 1-3s | ~2s |
| Tone analysis | <50ms | ~20ms |

*Results on Intel i5-8250U (4 cores, 1.6GHz base)*

## 🗂️ Project Structure

```
local-writing-assistant/
├── server/                    # Python FastAPI backend
│   ├── main.py               # Main application
│   ├── routers/              # API endpoints
│   ├── services/             # Core services
│   ├── scripts/              # Utility scripts
│   └── models/               # Downloaded AI models
├── extension/                # Chrome extension
│   ├── manifest.json         # Extension manifest
│   ├── content-script.js     # Main content script
│   ├── service-worker.js     # Background script
│   └── options.html          # Settings page
├── scripts/windows/          # Windows automation
│   ├── StartLocalAssistant.bat
│   ├── StopLocalAssistant.ps1
│   └── SetupEnv.ps1
└── docs/                     # Documentation
```

## 🤝 Contributing

This project is designed to be self-contained and privacy-focused. Contributions welcome for:

- Additional language support
- Performance optimizations  
- UI/UX improvements
- Bug fixes and stability

Please ensure any changes maintain the privacy-first, offline-only architecture.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🛡️ Privacy Statement

**Your data never leaves your computer.** This tool is designed from the ground up to be completely private:

- ✅ All AI models run locally on your machine
- ✅ No network requests to external APIs
- ✅ No telemetry, analytics, or tracking
- ✅ No user accounts or cloud storage
- ✅ Source code is fully auditable

The only network activity is during initial setup to download AI models from their official sources (Hugging Face, OpenAI).

## 🆘 Support

- **Issues**: Check existing solutions in [docs/troubleshooting.md](docs/troubleshooting.md)
- **Performance**: See [docs/performance.md](docs/performance.md) for optimization tips
- **Development**: Read [docs/architecture.md](docs/architecture.md) for technical details

---

*Made with ❤️ for privacy-conscious writers*
