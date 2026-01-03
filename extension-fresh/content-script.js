// content-script.js
// Local Writing Assistant - Content Script
// Handles grammar checking, text rewriting, and voice input on web pages

(function() {
    'use strict';

    // Configuration
    let config = {
        serverUrl: 'http://127.0.0.1:8001',
        apiToken: '',
        language: 'en-US',
        debounceDelay: 600,
        enabled: true,
        showToolbar: true
    };

    // State
    let debounceTimer = null;
    let currentElement = null;
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];

    // Initialize the extension
    async function init() {
        console.log('Local Writing Assistant: Initializing...');
        
        await loadConfig();
        
        if (!config.enabled) {
            console.log('Local Writing Assistant: Disabled');
            return;
        }

        setupEventListeners();
        createToolbar();
        
        console.log('Local Writing Assistant: Initialized');
    }

    // Load configuration from chrome storage
    async function loadConfig() {
        return new Promise((resolve) => {
            chrome.storage.local.get({
                serverUrl: 'http://127.0.0.1:8001',
                apiToken: '',
                language: 'en-US',
                debounceDelay: 600,
                enabled: true,
                showToolbar: true
            }, (result) => {
                config = result;
                resolve();
            });
        });
    }

    // Setup event listeners for text inputs
    function setupEventListeners() {
        // Handle all text inputs and textareas
        document.addEventListener('input', handleInput, true);
        document.addEventListener('focus', handleFocus, true);
        document.addEventListener('blur', handleBlur, true);
        
        // Handle contenteditable elements
        document.addEventListener('input', handleContentEditableInput, true);
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', cleanup);
    }

    // Handle input events
    function handleInput(event) {
        const element = event.target;
        
        if (!isTextElement(element)) {
            return;
        }

        currentElement = element;
        
        // Clear existing timer
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
        
        // Set new timer
        debounceTimer = setTimeout(() => {
            checkGrammar(element);
        }, config.debounceDelay);
    }

    // Handle focus events
    function handleFocus(event) {
        const element = event.target;
        
        if (!isTextElement(element)) {
            return;
        }
        
        currentElement = element;
        showToolbar(element);
    }

    // Handle blur events  
    function handleBlur(event) {
        // Keep toolbar visible for a short time
        setTimeout(() => {
            if (document.activeElement !== event.target) {
                hideToolbar();
            }
        }, 100);
    }

    // Handle contenteditable input
    function handleContentEditableInput(event) {
        const element = event.target;
        
        if (!element.isContentEditable) {
            return;
        }
        
        handleInput(event);
    }

    // Check if element is a text input
    function isTextElement(element) {
        if (!element) return false;
        
        const tagName = element.tagName.toLowerCase();
        
        // Regular input/textarea elements
        if (tagName === 'textarea') return true;
        if (tagName === 'input') {
            const type = element.type.toLowerCase();
            return ['text', 'email', 'search', 'url', 'tel'].includes(type);
        }
        
        // Contenteditable elements
        if (element.isContentEditable) return true;
        
        // Common rich text editors
        const richTextClasses = [
            'ql-editor',      // Quill
            'DraftEditor',    // Draft.js
            'ace_editor',     // Ace Editor
            'CodeMirror',     // CodeMirror
            'fr-element'      // Froala
        ];
        
        return richTextClasses.some(cls => element.classList.contains(cls));
    }

    // Check grammar for the given element
    async function checkGrammar(element) {
        if (!config.apiToken) {
            console.log('Local Writing Assistant: No API token configured');
            return;
        }
        
        const text = getElementText(element);
        
        if (!text || text.length < 3) {
            clearUnderlines(element);
            return;
        }
        
        try {
            const response = await fetch(`${config.serverUrl}/api/check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Local-Auth': config.apiToken
                },
                body: JSON.stringify({
                    text: text,
                    language: config.language
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            displayGrammarIssues(element, result.issues);
            
        } catch (error) {
            console.error('Local Writing Assistant: Grammar check failed:', error);
            showNotification('Grammar check failed. Check if the local server is running.', 'error');
        }
    }

    // Get text content from element
    function getElementText(element) {
        if (element.tagName.toLowerCase() === 'textarea' || 
            (element.tagName.toLowerCase() === 'input')) {
            return element.value;
        } else if (element.isContentEditable) {
            return element.textContent || element.innerText;
        }
        return '';
    }

    // Display grammar issues with underlines
    function displayGrammarIssues(element, issues) {
        clearUnderlines(element);
        
        if (!issues || issues.length === 0) {
            return;
        }
        
        // For simple text inputs, we can't add underlines directly
        // Instead, we'll add a visual indicator and show issues on hover
        if (element.tagName.toLowerCase() === 'textarea' || 
            element.tagName.toLowerCase() === 'input') {
            
            addInputIndicator(element, issues);
        } else if (element.isContentEditable) {
            // For contenteditable, we can add actual underlines
            addContentEditableUnderlines(element, issues);
        }
    }

    // Add indicator for regular input/textarea elements
    function addInputIndicator(element, issues) {
        // Add a subtle border color change
        element.style.borderBottomColor = '#ff6b6b';
        element.style.borderBottomWidth = '2px';
        element.setAttribute('data-lwa-issues', issues.length);
        
        // Add tooltip on hover
        element.title = `${issues.length} writing issue${issues.length !== 1 ? 's' : ''} found. Click the toolbar for details.`;
    }

    // Add underlines for contenteditable elements
    function addContentEditableUnderlines(element, issues) {
        const text = element.textContent;
        
        // Create spans with underlines for each issue
        issues.forEach((issue, index) => {
            try {
                const range = document.createRange();
                const walker = document.createTreeWalker(
                    element,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let currentPos = 0;
                let node;
                
                while (node = walker.nextNode()) {
                    const nodeLength = node.textContent.length;
                    const nodeStart = currentPos;
                    const nodeEnd = currentPos + nodeLength;
                    
                    if (nodeStart <= issue.start && issue.end <= nodeEnd) {
                        // Issue is within this text node
                        const relativeStart = issue.start - nodeStart;
                        const relativeEnd = issue.end - nodeStart;
                        
                        range.setStart(node, relativeStart);
                        range.setEnd(node, relativeEnd);
                        
                        const span = document.createElement('span');
                        span.className = 'lwa-underline';
                        span.setAttribute('data-issue-index', index);
                        span.style.textDecoration = 'underline wavy #ff6b6b';
                        span.style.textDecorationThickness = '2px';
                        span.style.cursor = 'pointer';
                        span.title = issue.message;
                        
                        try {
                            range.surroundContents(span);
                        } catch (e) {
                            // Fallback if range spans multiple elements
                            console.log('Could not add underline to complex range');
                        }
                        
                        break;
                    }
                    
                    currentPos = nodeEnd;
                }
            } catch (error) {
                console.warn('Failed to add underline for issue:', issue, error);
            }
        });
    }

    // Clear all underlines from element
    function clearUnderlines(element) {
        // Reset input/textarea styles
        if (element.tagName.toLowerCase() === 'textarea' || 
            element.tagName.toLowerCase() === 'input') {
            element.style.borderBottomColor = '';
            element.style.borderBottomWidth = '';
            element.removeAttribute('data-lwa-issues');
            element.title = '';
        }
        
        // Remove underline spans from contenteditable
        const underlines = element.querySelectorAll('.lwa-underline');
        underlines.forEach(span => {
            const parent = span.parentNode;
            parent.insertBefore(document.createTextNode(span.textContent), span);
            parent.removeChild(span);
        });
        
        // Normalize text nodes
        if (element.isContentEditable) {
            element.normalize();
        }
    }

    // Create and show floating toolbar
    function createToolbar() {
        if (!config.showToolbar) return;
        
        const toolbar = document.createElement('div');
        toolbar.id = 'lwa-toolbar';
        toolbar.className = 'lwa-toolbar';
        toolbar.style.cssText = `
            position: fixed;
            top: -100px;
            left: 0;
            background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 8px;
            z-index: 10000;
            display: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
        `;
        
        toolbar.innerHTML = `
            <div class="lwa-toolbar-buttons">
                <button id="lwa-fix" class="lwa-btn" title="Fix grammar and spelling">Fix</button>
                <button id="lwa-concise" class="lwa-btn" title="Make more concise">Concise</button>
                <button id="lwa-formal" class="lwa-btn" title="Make more formal">Formal</button>
                <button id="lwa-friendly" class="lwa-btn" title="Make more friendly">Friendly</button>
                <button id="lwa-mic" class="lwa-btn lwa-mic-btn" title="Voice input">🎤</button>
                <button id="lwa-close" class="lwa-btn lwa-close-btn" title="Close">×</button>
            </div>
        `;
        
        document.body.appendChild(toolbar);
        
        // Add event listeners
        document.getElementById('lwa-fix').addEventListener('click', () => rewriteText('fix'));
        document.getElementById('lwa-concise').addEventListener('click', () => rewriteText('concise'));
        document.getElementById('lwa-formal').addEventListener('click', () => rewriteText('formal'));
        document.getElementById('lwa-friendly').addEventListener('click', () => rewriteText('friendly'));
        document.getElementById('lwa-mic').addEventListener('click', toggleVoiceRecording);
        document.getElementById('lwa-close').addEventListener('click', hideToolbar);
    }

    // Show toolbar near element
    function showToolbar(element) {
        if (!config.showToolbar) return;
        
        const toolbar = document.getElementById('lwa-toolbar');
        if (!toolbar) return;
        
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        toolbar.style.display = 'block';
        toolbar.style.left = Math.max(10, rect.left) + 'px';
        toolbar.style.top = (rect.top + scrollTop - 50) + 'px';
    }

    // Hide toolbar
    function hideToolbar() {
        const toolbar = document.getElementById('lwa-toolbar');
        if (toolbar) {
            toolbar.style.display = 'none';
        }
    }

    // Rewrite text using AI
    async function rewriteText(mode) {
        if (!currentElement || !config.apiToken) {
            showNotification('No text selected or API token missing', 'error');
            return;
        }
        
        const text = getElementText(currentElement);
        if (!text.trim()) {
            showNotification('No text to rewrite', 'error');
            return;
        }
        
        const button = document.getElementById(`lwa-${mode}`);
        const originalText = button.textContent;
        button.textContent = '...';
        button.disabled = true;
        
        try {
            const response = await fetch(`${config.serverUrl}/api/rewrite`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Local-Auth': config.apiToken
                },
                body: JSON.stringify({
                    text: text,
                    mode: mode
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Replace text in element
            setElementText(currentElement, result.text);
            
            showNotification('Text rewritten successfully', 'success');
            
        } catch (error) {
            console.error('Local Writing Assistant: Rewrite failed:', error);
            showNotification('Text rewriting failed. Check if the local server is running.', 'error');
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    // Set text content in element
    function setElementText(element, text) {
        if (element.tagName.toLowerCase() === 'textarea' || 
            (element.tagName.toLowerCase() === 'input')) {
            element.value = text;
        } else if (element.isContentEditable) {
            element.textContent = text;
        }
        
        // Trigger input event to update any frameworks
        element.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Toggle voice recording
    async function toggleVoiceRecording() {
        if (!config.apiToken) {
            showNotification('API token not configured', 'error');
            return;
        }
        
        if (isRecording) {
            stopRecording();
        } else {
            await startRecording();
        }
    }

    // Start voice recording
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000
                } 
            });
            
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                await transcribeAudio(audioBlob);
                
                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            isRecording = true;
            
            const micButton = document.getElementById('lwa-mic');
            micButton.textContent = '🔴';
            micButton.title = 'Stop recording';
            
            showNotification('Recording... Click mic again to stop.', 'info');
            
        } catch (error) {
            console.error('Local Writing Assistant: Failed to start recording:', error);
            showNotification('Failed to access microphone', 'error');
        }
    }

    // Stop voice recording
    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            
            const micButton = document.getElementById('lwa-mic');
            micButton.textContent = '🎤';
            micButton.title = 'Voice input';
            
            showNotification('Processing audio...', 'info');
        }
    }

    // Transcribe audio using the local API
    async function transcribeAudio(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('language', 'en');
            
            const response = await fetch(`${config.serverUrl}/api/transcribe`, {
                method: 'POST',
                headers: {
                    'X-Local-Auth': config.apiToken
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.text && currentElement) {
                // Insert transcribed text at cursor position
                insertTextAtCursor(currentElement, result.text);
                showNotification('Voice input successful', 'success');
            } else {
                showNotification('No speech detected', 'warning');
            }
            
        } catch (error) {
            console.error('Local Writing Assistant: Transcription failed:', error);
            showNotification('Voice transcription failed. Check if the local server is running.', 'error');
        }
    }

    // Insert text at cursor position
    function insertTextAtCursor(element, text) {
        if (element.tagName.toLowerCase() === 'textarea' || 
            (element.tagName.toLowerCase() === 'input')) {
            
            const start = element.selectionStart;
            const end = element.selectionEnd;
            const value = element.value;
            
            element.value = value.substring(0, start) + text + value.substring(end);
            element.selectionStart = element.selectionEnd = start + text.length;
            
        } else if (element.isContentEditable) {
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                range.deleteContents();
                range.insertNode(document.createTextNode(text));
                range.collapse(false);
            } else {
                element.textContent += text;
            }
        }
        
        // Trigger input event
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.focus();
    }

    // Show notification
    function showNotification(message, type = 'info') {
        // Remove existing notification
        const existing = document.getElementById('lwa-notification');
        if (existing) {
            existing.remove();
        }
        
        const notification = document.createElement('div');
        notification.id = 'lwa-notification';
        notification.className = `lwa-notification lwa-notification-${type}`;
        
        const colors = {
            success: '#4caf50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196f3'
        };
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 10001;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            max-width: 300px;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Cleanup function
    function cleanup() {
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
        
        if (isRecording && mediaRecorder) {
            mediaRecorder.stop();
        }
        
        // Remove toolbar
        const toolbar = document.getElementById('lwa-toolbar');
        if (toolbar) {
            toolbar.remove();
        }
        
        // Remove notification
        const notification = document.getElementById('lwa-notification');
        if (notification) {
            notification.remove();
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
