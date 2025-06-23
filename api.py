"""FastAPI server for anchor-insight-AI web interface and API."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from main import AnchorInsightAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Anchor Insight AI API",
    description="Real-time scoring and notifications based on user behavior analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global app instance
ai_app: Optional[AnchorInsightAI] = None
analysis_task: Optional[asyncio.Task] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the AI application on startup."""
    global ai_app
    try:
        ai_app = AnchorInsightAI()
        await ai_app.initialize()
        logger.info("AI application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI application: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global ai_app, analysis_task
    if analysis_task:
        analysis_task.cancel()
    if ai_app:
        await ai_app.stop_analysis()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Anchor Insight AI API", "status": "running"}


@app.get("/status")
async def get_status():
    """Get current system status."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    try:
        status = await ai_app.get_current_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/start")
async def start_analysis(background_tasks: BackgroundTasks):
    """Start real-time analysis."""
    global ai_app, analysis_task
    
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    if analysis_task and not analysis_task.done():
        return {"message": "Analysis already running"}
    
    try:
        # Start analysis in background
        analysis_task = asyncio.create_task(ai_app.start_analysis())
        background_tasks.add_task(lambda: None)  # Keep task alive
        
        return {"message": "Analysis started successfully"}
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/stop")
async def stop_analysis():
    """Stop real-time analysis."""
    global ai_app, analysis_task
    
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    try:
        if analysis_task:
            analysis_task.cancel()
        await ai_app.stop_analysis()
        return {"message": "Analysis stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def add_feedback(feedback: Dict[str, str]):
    """Add user feedback."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    feedback_text = feedback.get("text", "")
    if not feedback_text:
        raise HTTPException(status_code=400, detail="Feedback text is required")
    
    try:
        await ai_app.input_processor.add_user_feedback(feedback_text)
        return {"message": "Feedback added successfully"}
    except Exception as e:
        logger.error(f"Error adding feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scores/recent")
async def get_recent_scores(limit: int = 10):
    """Get recent scores."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    try:
        recent_data = await ai_app.db_manager.get_recent_sessions(limit=limit)
        scores = []
        for session in recent_data:
            if 'scores' in session:
                scores.append({
                    'timestamp': session['timestamp'],
                    'scores': session['scores']
                })
        
        return JSONResponse(content={"scores": scores})
    except Exception as e:
        logger.error(f"Error getting recent scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics")
async def get_statistics(hours: int = 24):
    """Get session statistics."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    try:
        stats = await ai_app.db_manager.get_session_stats(hours=hours)
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trends")
async def get_trends(days: int = 7):
    """Get score trends."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    try:
        trends = await ai_app.db_manager.get_score_trends(days=days)
        return JSONResponse(content={"trends": trends})
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications")
async def get_notifications(limit: int = 10):
    """Get recent notifications."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    try:
        notifications = await ai_app.notification_system.get_recent_notifications(limit=limit)
        return JSONResponse(content={"notifications": notifications})
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/custom")
async def send_custom_notification(notification: Dict[str, str]):
    """Send a custom notification."""
    if not ai_app:
        raise HTTPException(status_code=500, detail="AI application not initialized")
    
    title = notification.get("title", "")
    message = notification.get("message", "")
    severity = notification.get("severity", "info")
    
    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and message are required")
    
    try:
        await ai_app.notification_system.send_custom_notification(title, message, severity)
        return {"message": "Notification sent successfully"}
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )