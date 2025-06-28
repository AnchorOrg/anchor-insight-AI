// Popup script for Anchor Insight AI Chrome Extension

document.addEventListener('DOMContentLoaded', async () => {
  const statusElement = document.getElementById('status');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');

  // Update UI status
  function updateStatus(isCapturing) {
    if (isCapturing) {
      statusElement.textContent = 'Active - Capturing';
      statusElement.className = 'status active';
      startBtn.disabled = true;
      stopBtn.disabled = false;
    } else {
      statusElement.textContent = 'Inactive';
      statusElement.className = 'status inactive';
      startBtn.disabled = false;
      stopBtn.disabled = true;
    }
  }

  // Get current status
  async function getStatus() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({action: 'get_status'}, (response) => {
        resolve(response.isCapturing || false);
      });
    });
  }

  // Start capture
  startBtn.addEventListener('click', async () => {
    try {
      chrome.runtime.sendMessage({action: 'start_capture'}, (response) => {
        if (response.success) {
          updateStatus(true);
          showNotification('Screen capture started');
        } else {
          showNotification('Failed to start capture', 'error');
        }
      });
    } catch (error) {
      console.error('Start capture error:', error);
      showNotification('Error starting capture', 'error');
    }
  });

  // Stop capture
  stopBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({action: 'stop_capture'}, (response) => {
      if (response.success) {
        updateStatus(false);
        showNotification('Screen capture stopped');
      }
    });
  });

  // Show notification
  function showNotification(message, type = 'info') {
    // Create temporary notification element
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 10px;
      left: 50%;
      transform: translateX(-50%);
      padding: 10px 20px;
      border-radius: 5px;
      color: white;
      font-weight: bold;
      z-index: 1000;
      background-color: ${type === 'error' ? '#f44336' : '#4CAF50'};
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  // Initialize status
  const currentStatus = await getStatus();
  updateStatus(currentStatus);
});