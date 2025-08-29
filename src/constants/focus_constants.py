"""
Constants for focus score analysis
"""

# Allowed image MIME types for file upload and URL analysis
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", 
    "image/gif", "image/webp", "image/bmp"
}

# OpenAI prompt for focus analysis
FOCUS_ANALYSIS_PROMPT = (
    "This is a screenshot taken from a user's computer screen. Please analyze the probability of the user being distracted at this moment.\n"
    "Note: To assess distraction probability, consider whether the user is working, such as using code editors, video editors, work software, etc., "
    "or analyze whether the screenshot shows a webpage and what content it contains. If watching a video, is it work-related? "
    "For example, if watching educational videos, consider it as working or studying; if watching entertainment or gaming videos, consider it as resting or being distracted.\n"
    "Please directly output a focus attention score, where 0 means completely distracted and 100 means highly focused. "
    "You can freely choose a score between 0-100 to evaluate the user's attention focus level.\n"
    "Please return in JSON format: {\"focus_score\": number}"
)

# API response confidence levels
CONFIDENCE_HIGH = "high"

# File size limits
BYTES_PER_MB = 1024 * 1024

# API version and metadata
API_VERSION = "1.0.0"
API_TITLE = "Focus Analysis API"
API_DESCRIPTION = "An API service that uses GPT-4o-mini to analyze screenshots and return focus scores"
