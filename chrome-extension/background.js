// Background service worker for Anchor Insight AI Chrome Extension
// Handles screen capture and communication with the AI backend

const AI_BACKEND_URL = 'http://localhost:8000';
let captureInterval = null;
let isCapturing = false;

// Start screen capture
async function startScreenCapture() {
  if (isCapturing) return;
  
  try {
    const streamId = await new Promise((resolve, reject) => {
      chrome.desktopCapture.chooseDesktopMedia(
        ['screen', 'window', 'tab'],
        (streamId) => {
          if (streamId) {
            resolve(streamId);
          } else {
            reject(new Error('User cancelled screen capture'));
          }
        }
      );
    });

    // Capture screenshots every 5 seconds
    captureInterval = setInterval(async () => {
      try {
        await captureAndSendScreenshot(streamId);
      } catch (error) {
        console.error('Screen capture error:', error);
      }
    }, 5000);

    isCapturing = true;
    console.log('Screen capture started');
    
  } catch (error) {
    console.error('Failed to start screen capture:', error);
  }
}

// Stop screen capture
function stopScreenCapture() {
  if (captureInterval) {
    clearInterval(captureInterval);
    captureInterval = null;
  }
  isCapturing = false;
  console.log('Screen capture stopped');
}

// Capture screenshot and send to AI backend
async function captureAndSendScreenshot(streamId) {
  try {
    // Get active tab
    const [activeTab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    if (!activeTab) return;

    // Capture visible tab as image
    const dataUrl = await chrome.tabs.captureVisibleTab(activeTab.windowId, {
      format: 'jpeg',
      quality: 80
    });

    // Send to AI backend
    await fetch(`${AI_BACKEND_URL}/screen-capture`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image: dataUrl,
        timestamp: new Date().toISOString(),
        tab_url: activeTab.url,
        tab_title: activeTab.title
      })
    });

  } catch (error) {
    console.error('Screenshot capture error:', error);
  }
}

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'start_capture':
      startScreenCapture();
      sendResponse({success: true});
      break;
      
    case 'stop_capture':
      stopScreenCapture();
      sendResponse({success: true});
      break;
      
    case 'get_status':
      sendResponse({isCapturing});
      break;
      
    default:
      sendResponse({error: 'Unknown action'});
  }
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Anchor Insight AI extension installed');
});