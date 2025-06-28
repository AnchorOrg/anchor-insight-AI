# Chrome Extension for Anchor Insight AI

This Chrome extension provides screen capture functionality to integrate with the Anchor Insight AI system for real-time behavior analysis.

## Features

- Screen capture every 5 seconds during active sessions
- Simple start/stop controls via browser popup
- Automatic communication with local AI backend
- Privacy-focused (all data stays local)

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select this directory
4. The extension icon should appear in your browser toolbar

## Usage

1. Start the Anchor Insight AI backend (`python api.py`)
2. Click the extension icon in your browser
3. Click "Start" to begin screen capture
4. The extension will capture your screen every 5 seconds
5. Click "Stop" to end the session

## Backend Integration

The extension sends captured screenshots to:
```
POST http://localhost:8000/screen-capture
```

With payload:
```json
{
  "image": "data:image/jpeg;base64,...",
  "timestamp": "2024-01-01T12:00:00Z",
  "tab_url": "https://example.com",
  "tab_title": "Example Page"
}
```

## Privacy

- All image processing happens locally
- No data is sent to external servers
- Screenshots are only captured when explicitly started
- User has full control over when capture is active

## Development

The extension consists of:
- `manifest.json` - Extension configuration
- `background.js` - Service worker for screen capture
- `popup.html` - User interface
- `popup.js` - Popup functionality

To modify:
1. Edit the files as needed
2. Go to `chrome://extensions/`
3. Click the refresh button for the extension
4. Test the changes