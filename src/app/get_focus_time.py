#!/usr/bin/env python3
"""
Person Monitoring Service using YOLOv11-Pose and FastAPI
Features:
1. Camera-based person detection
2. Focus/Leave time tracking
3. RESTful API endpoints
4. Real-time monitoring with optimized performance
"""

import cv2
import time
import asyncio
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from typing import Optional, Tuple, List, Dict, Any
from threading import Thread, Lock, Event
from queue import Queue, Empty
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Request/Response Models

# move to the config package TODO
class MonitorConfig(BaseModel):
    show_window: bool = Field(False, description="Whether to show monitoring window")
    model_path: Optional[str] = Field(None, description="Path to YOLO model")
    camera_index: int = Field(0, description="Camera device index")
# move to the model package TODO
class StatusResponse(BaseModel):
    is_initialized: bool
    person_detected: Optional[bool]
    current_session: Optional[Dict[str, Any]]
    total_records: int

class SummaryResponse(BaseModel):
    total_focus_minutes: float
    total_leave_minutes: float
    focus_sessions: int
    leave_sessions: int

class TimeRecord(BaseModel):
    type: str
    start: float
    end: float
    formatted: str
    duration_minutes: float
# TODO: this should be within the service package. the class name should end with Service
class PersonMonitor:
    """Optimized Person Monitor with adaptive frame processing"""
    
    def __init__(self, model_path: str = 'yolov11n-pose.pt', camera_index: int = 0):
        """Initialize the person monitor with performance optimizations"""
        # Model and camera
        self.model = YOLO(model_path)
        self.camera_index = camera_index
        self.cap = None
        self._camera_lock = Lock()
        
        # State tracking
        self.person_detected = False
        self.previous_person_state = None 
        self.is_initialized = False  
        
        # Time tracking
        self.focus_start_time = None
        self.leave_start_time = None
        self.time_records = []
        self._records_lock = Lock()
        
        # Thread control with optimization
        self.is_running = False
        self.monitor_thread = None
        self.record_queue = Queue()
        self._stop_event = Event()
        
        # Display settings
        self.window_name = "YOLOv11-Pose Person Monitor"
        self.show_window = False
        
        # Performance optimization
        self.target_fps = 10  # Adaptive FPS for better performance
        self.frame_time = 1.0 / self.target_fps
        self.last_process_time = 0
        
        # Frame buffer for smooth processing
        self.frame_buffer = Queue(maxsize=2)
        self.capture_thread = None
        
    def _init_camera(self) -> bool:
        """Initialize camera with optimized settings"""
        with self._camera_lock:
            if self.cap is not None:
                return True
                
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
                
            # Optimize camera settings for performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # Set camera FPS
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
            
            return True
    
    def _release_camera(self):
        """Safely release camera resources"""
        with self._camera_lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
    
    def _capture_frames(self):
        """Separate thread for frame capture (optimization)"""
        while self.is_running and not self._stop_event.is_set():

            if self.cap is not None:
                ret, frame = self.cap.read()
                if ret:
                    # Drop old frames to maintain real-time processing
                    if self.frame_buffer.full():
                        try:
                            self.frame_buffer.get_nowait()
                        except Empty:
                            pass
                    self.frame_buffer.put(frame)
            # TODO: refrain ussages of sleep to wait for the task completion
            time.sleep(0.001)  # Minimal sleep
    
    def format_time_string(self, start_time: float, end_time: float, time_type: str) -> str:
        """Format time period into readable string"""
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        
        date_str = start_dt.strftime("%d/%m/%Y")
        
        # Format start time
        start_hour = start_dt.strftime("%I").lstrip('0')
        start_minute = start_dt.strftime("%M")
        start_period = start_dt.strftime("%p").lower()
        
        # Format end time
        end_hour = end_dt.strftime("%I").lstrip('0')
        end_minute = end_dt.strftime("%M")
        end_period = end_dt.strftime("%p").lower()
        
        return f"{date_str} {time_type} time: {start_hour}:{start_minute} {start_period} - {end_hour}:{end_minute} {end_period}"
    
    def detect_person(self, frame: np.ndarray) -> Tuple[bool, np.ndarray]:
        """Detect person in frame using YOLO"""
        # Use lower confidence for faster processing
        results = self.model(frame, stream=True, verbose=False, save=False, 
                            conf=0.5, iou=0.45, device='cpu', half=False)
        person_found = False
        rendered_frame = frame.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    if box.cls == 0:  # Person class
                        person_found = True
                        break
            rendered_frame = result.plot()
        
        return person_found, rendered_frame
    
    def update_time_tracking(self, person_detected: bool) -> Optional[str]:
        """Update time tracking based on person detection"""
        current_time = time.time()
        time_record = None
        
        # Initial state handling
        if not self.is_initialized:
            if person_detected:
                self.is_initialized = True
                self.focus_start_time = current_time
                self.previous_person_state = True
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] System initialized, starting focus time tracking")
            return None
        
        # State change detection
        if self.previous_person_state is not None:
            if person_detected and not self.previous_person_state:
                # Person returned, end leave time, start focus time
                if self.leave_start_time is not None:
                    time_record = self.format_time_string(
                        self.leave_start_time, 
                        current_time, 
                        "Leave"
                    )
                    with self._records_lock:
                        self.time_records.append({
                            'type': 'leave',
                            'start': self.leave_start_time,
                            'end': current_time,
                            'formatted': time_record
                        })
                    logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] {time_record}")
                
                self.focus_start_time = current_time
                self.leave_start_time = None
                
            elif not person_detected and self.previous_person_state:
                # Person left, end focus time, start leave time
                if self.focus_start_time is not None:
                    time_record = self.format_time_string(
                        self.focus_start_time, 
                        current_time, 
                        "Focus"
                    )
                    with self._records_lock:
                        self.time_records.append({
                            'type': 'focus',
                            'start': self.focus_start_time,
                            'end': current_time,
                            'formatted': time_record
                        })
                    logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] {time_record}")
                
                self.leave_start_time = current_time
                self.focus_start_time = None
        
        self.previous_person_state = person_detected
        return time_record
    
    def monitor_loop(self):
        """Optimized monitoring loop with adaptive frame processing"""
        try:
            if not self._init_camera():
                logger.error("Failed to initialize camera")
                return
            
            # Start frame capture thread
            self.capture_thread = Thread(target=self._capture_frames, daemon=True)
            self.capture_thread.start()
            
            while self.is_running and not self._stop_event.is_set():
                current_time = time.time()
                
                # Adaptive frame processing
                time_since_last = current_time - self.last_process_time
                if time_since_last < self.frame_time:
                    time.sleep(self.frame_time - time_since_last)
                    continue
                
                try:
                    # Get latest frame (non-blocking)
                    frame = self.frame_buffer.get(timeout=0.1)
                    
                    # Process frame
                    person_detected, rendered_frame = self.detect_person(frame)
                    
                    # Update time tracking
                    time_record = self.update_time_tracking(person_detected)
                    if time_record:
                        self.record_queue.put(time_record)
                    
                    # Display if needed
                    if self.show_window:
                        display_frame = self.draw_info(rendered_frame)
                        cv2.imshow(self.window_name, display_frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            self._stop_event.set()
                            break
                    
                    self.last_process_time = current_time
                    
                except Empty:
                    # No frame available, continue
                    continue
                    
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
        finally:
            if self.show_window:
                cv2.destroyAllWindows()
            self._release_camera()
    
    def draw_info(self, frame: np.ndarray) -> np.ndarray:
        """Draw information overlay on frame"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # Draw status info
        # TODO: it is very likely this would introduce the performance issue. 
        # example: 
        '''
        when the laod is high,
        requestA form A user, 
        reqeustB from B user, 
        sometimes if we save the data within the service class, then there are possiblities that the data from requestA would change the data for requestB
        need explanation on how the current impl prevent that issue or code modification.
        ''' 
        if not self.is_initialized:
            status_text = "Waiting for first detection..."
            status_color = (255, 255, 0)
        else:
            status_text = "Person: Detected" if self.previous_person_state else "Person: Not Detected"
            status_color = (0, 255, 0) if self.previous_person_state else (0, 0, 255)
        
        cv2.putText(frame, status_text, (10, 30), font, font_scale, status_color, thickness)
        
        # Show current time tracking
        if self.focus_start_time is not None:
            elapsed = (time.time() - self.focus_start_time) / 60
            cv2.putText(frame, f"Focus time: {elapsed:.1f} min", (10, 60), font, font_scale, (0, 255, 0), thickness)
        elif self.leave_start_time is not None:
            elapsed = (time.time() - self.leave_start_time) / 60
            cv2.putText(frame, f"Leave time: {elapsed:.1f} min", (10, 60), font, font_scale, (0, 165, 255), thickness)
        
        # Show record count
        cv2.putText(frame, f"Records: {len(self.time_records)}", (10, 90), font, font_scale, (255, 255, 255), thickness)
        
        return frame
    
    def start(self, show_window: bool = False):
        """Start monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.show_window = show_window
        self._stop_event.clear()
        self.monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoring started")
    
    def stop(self):
        """Stop monitoring and finalize records"""
        self.is_running = False
        self._stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3)
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
        
        # Process any unfinished records
        current_time = time.time()
        final_record = None
        
        if self.focus_start_time is not None:
            final_record = self.format_time_string(
                self.focus_start_time, 
                current_time, 
                "Focus"
            )
            with self._records_lock:
                self.time_records.append({
                    'type': 'focus',
                    'start': self.focus_start_time,
                    'end': current_time,
                    'formatted': final_record
                })
            
        elif self.leave_start_time is not None:
            final_record = self.format_time_string(
                self.leave_start_time, 
                current_time, 
                "Leave"
            )
            with self._records_lock:
                self.time_records.append({
                    'type': 'leave',
                    'start': self.leave_start_time,
                    'end': current_time,
                    'formatted': final_record
                })
        
        self._release_camera()
        logger.info("Monitoring stopped")
        
        if final_record:
            logger.info(f"Final record: {final_record}")
    
    def get_latest_record(self) -> Optional[str]:
        """Get latest time record from queue"""
        try:
            return self.record_queue.get_nowait()
        except Empty:
            return None
    
    def get_all_records(self) -> List[Dict]:
        """Get all time records (thread-safe)"""
        with self._records_lock:
            return self.time_records.copy()
    
    def get_current_status(self) -> Dict:
        """Get current monitoring status"""
        current_time = time.time()
        status = {
            'is_initialized': self.is_initialized,
            'person_detected': self.previous_person_state,
            'current_session': None,
            'total_records': len(self.time_records)
        }
        
        if self.focus_start_time is not None:
            status['current_session'] = {
                'type': 'focus',
                'duration_minutes': (current_time - self.focus_start_time) / 60,
                'start_time': datetime.fromtimestamp(self.focus_start_time).strftime("%Y-%m-%d %H:%M:%S")
            }
        elif self.leave_start_time is not None:
            status['current_session'] = {
                'type': 'leave',
                'duration_minutes': (current_time - self.leave_start_time) / 60,
                'start_time': datetime.fromtimestamp(self.leave_start_time).strftime("%Y-%m-%d %H:%M:%S")
            }
        
        return status
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        total_focus_time = 0
        total_leave_time = 0
        
        with self._records_lock:
            for record in self.time_records:
                duration = record['end'] - record['start']
                if record['type'] == 'focus':
                    total_focus_time += duration
                else:
                    total_leave_time += duration
        
        # Add current ongoing session
        current_time = time.time()
        if self.focus_start_time is not None:
            total_focus_time += current_time - self.focus_start_time
        elif self.leave_start_time is not None:
            total_leave_time += current_time - self.leave_start_time
        
        return {
            'total_focus_minutes': total_focus_time / 60,
            'total_leave_minutes': total_leave_time / 60,
            'focus_sessions': len([r for r in self.time_records if r['type'] == 'focus']),
            'leave_sessions': len([r for r in self.time_records if r['type'] == 'leave'])
        }

# Global monitor instance with thread-safe access
_monitor_instance = None
_monitor_lock = Lock()

def get_monitor_instance(model_path: Optional[str] = None, camera_index: int = 0) -> PersonMonitor:
    """Get or create monitor instance (thread-safe singleton)"""
    global _monitor_instance
    with _monitor_lock:
        if _monitor_instance is None:
            if model_path is None:
                model_path = r"C:\python-env\YOLOv8-Magic\ultralytics\yolo11m-pose.pt"  # Default model
            _monitor_instance = PersonMonitor(model_path, camera_index)
        return _monitor_instance

# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Person Monitor API")
    yield
    # Cleanup on shutdown
    monitor = get_monitor_instance()
    if monitor.is_running:
        monitor.stop()
    logger.info("Person Monitor API shutdown complete")

app = FastAPI(
    title="Person Monitor API",
    description="Real-time person detection and time tracking using YOLOv11-Pose",
    version="2.0.0",
    lifespan=lifespan
)

# TODO: The below should move to a controller class START
# API Endpoints
# TODO: this endpoint should be deleted. Either we configure the swagger to show the below info and make that exposed merely in non-prod env or we have hoppscotch to have the below info. 
@app.get("/", response_model=Dict[str, Any])
async def root():
    """API information endpoint"""
    return {
        "service": "Person Monitor API",
        "version": "2.0.0",
        "status": "online",
        "endpoints": {
            "/monitor/start": "Start monitoring",
            "/monitor/stop": "Stop monitoring",
            "/monitor/status": "Get monitoring status",
            "/monitor/records": "Get all time records",
            "/monitor/summary": "Get time summary",
            "/monitor/latest": "Get latest record",
            # TODO: websocket is totally not needed for now.
            "/ws/monitor": "WebSocket for real-time updates"
        }
    }

# TODO: duplicated code. This feedback would greatly lower the score of this PR
@app.post("/monitor/start")
async def start_monitoring(config: MonitorConfig):
    """Start person monitoring"""
    try:
        monitor = get_monitor_instance(
            model_path=config.model_path,
            camera_index=config.camera_index
        )
        
        if monitor.is_running:
            return JSONResponse(
                status_code=400,
                content={"error": "Monitoring is already running"}
            )
        
        # Start monitoring in background
        await asyncio.get_event_loop().run_in_executor(
            None, monitor.start, config.show_window
        )
        
        return {
            "status": "started",
            "message": "Monitoring started successfully",
            "config": config.dict()
        }
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# TODO: this is not needed. since the data would be collected in real time during the focus session.
@app.post("/monitor/stop")
async def stop_monitoring():
    """Stop person monitoring"""
    try:
        monitor = get_monitor_instance()
        
        if not monitor.is_running:
            return JSONResponse(
                status_code=400,
                content={"error": "Monitoring is not running"}
            )
        
        # Get final stats before stopping
        final_stats = monitor.get_summary_stats()
        
        # Stop monitoring
        await asyncio.get_event_loop().run_in_executor(
            None, monitor.stop
        )
        
        return {
            "status": "stopped",
            "message": "Monitoring stopped successfully",
            "final_stats": final_stats
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# TODO: need further explantion on what does the total_records mean . My expectation is that the score might be flowed over time ( example: at the start of the session, 13:00, the socre is 5/5. 13:15 3/5. also , according the issue's requirement, status is not needed and merely score is needed. )
@app.get("/monitor/status", response_model=StatusResponse)
async def get_status():
    """Get current monitoring status"""
    try:
        monitor = get_monitor_instance()
        status = monitor.get_current_status()
        return StatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TODO: focus time records would be handled by anchor-app
@app.get("/monitor/records", response_model=List[TimeRecord])
async def get_records():
    """Get all time records"""
    try:
        monitor = get_monitor_instance()
        records = monitor.get_all_records()
        
        # Convert to response model
        return [
            TimeRecord(
                type=record['type'],
                start=record['start'],
                end=record['end'],
                formatted=record['formatted'],
                duration_minutes=(record['end'] - record['start']) / 60
            )
            for record in records
        ]
    except Exception as e:
        logger.error(f"Failed to get records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/summary", response_model=SummaryResponse)
async def get_summary():
    """Get time tracking summary"""
    try:
        monitor = get_monitor_instance()
        summary = monitor.get_summary_stats()
        return SummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/latest")
async def get_latest_record():
    """Get latest time record"""
    try:
        monitor = get_monitor_instance()
        record = monitor.get_latest_record()
        
        if record is None:
            return {"message": "No new records available"}
        
        return {"latest_record": record}
    except Exception as e:
        logger.error(f"Failed to get latest record: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await websocket.accept()
    monitor = get_monitor_instance()
    
    try:
        while True:
            # Check for new records
            record = monitor.get_latest_record()
            if record:
                await websocket.send_json({
                    "type": "new_record",
                    "data": record
                })
            
            # Send current status
            status = monitor.get_current_status()
            await websocket.send_json({
                "type": "status_update",
                "data": status
            })
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        monitor = get_monitor_instance()
        return {
            "status": "healthy",
            "monitoring_active": monitor.is_running,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
# TODO: The above should move to a controller class END

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "get_focus_time:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )