# Voice Assistant Implementation Guide

## Current Implementation

The voice transcription feature is designed to use **browser-based speech recognition** for the following reasons:
1. **Privacy**: No audio data is sent to the server
2. **Performance**: Instant recognition without server roundtrips
3. **No dependencies**: Works without installing heavy ML models

## How It Should Work

### In Your Chrome Extension

Instead of sending audio files to the server, use the Web Speech API directly:

```javascript
// Example implementation for your Chrome extension
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US';

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    console.log('Transcript:', transcript);
    
    // Now send the transcript to your rewrite API
    fetch('http://127.0.0.1:8001/api/rewrite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Local-Auth': 'test123456789'
        },
        body: JSON.stringify({
            text: transcript,
            mode: 'fix'  // or any other mode
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Rewritten text:', data.text);
        // Use the rewritten text in your extension
    });
};

// Start recognition
recognition.start();
```

## Server Configuration with OpenAI

Your server is now configured to use OpenAI's GPT-4 mini model for text rewriting. The delay you're experiencing is due to:

1. **API calls to OpenAI**: Network latency to reach the API
2. **Model processing time**: Time for GPT-4 mini to generate responses

### To Reduce Delays:

1. **Use the fast rewriter for simple fixes**: The rule-based rewriter has <10ms response time
2. **Cache common corrections**: Store frequently used corrections
3. **Use shorter prompts**: We've already optimized max_tokens to 500
4. **Consider using a local model**: For offline use, you could use smaller models like Llama

## Recommended Workflow

1. **Voice Input**: Use browser's Web Speech API in the extension
2. **Quick Fixes**: Use the fast rewriter for grammar/spelling
3. **Advanced Rewrites**: Use OpenAI for formal/creative rewrites
4. **Display Results**: Show the corrected text in your extension

This approach gives you the best of both worlds: instant voice recognition and powerful AI-based text correction.
