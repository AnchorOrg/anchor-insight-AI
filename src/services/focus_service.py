"""
Focus monitoring service using YOLOv11-Pose
"""
import cv2
import time
import numpy as np
import logging
from datetime import datetime
from enum import Enum
from ultralytics import YOLO
from typing import Optional, Tuple, List, Dict, Any
from threading import Thread, Lock, Event
from queue import Queue, Empty
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class MonitorStatus(Enum):
    """Enumeration for monitor status messages and colors"""
    WAITING_DETECTION = ("Waiting for first detection...", (255, 255, 0))  # Yellow
    PERSON_DETECTED = ("Person: Detected", (0, 255, 0))  # Green
    PERSON_NOT_DETECTED = ("Person: Not Detected", (0, 0, 255))  # Red
    
    def __init__(self, text: str, color: Tuple[int, int, int]):
        self.text = text
        self.color = color


class PersonMonitorService:
    """Optimized Person Monitor Service with adaptive frame processing"""
    
    def __init__(self, model_path: str = None, camera_index: int = 0, session_id: str = "default"):
        """Initialize the person monitor with performance optimizations"""
        # Session management
        self.session_id = session_id

        # Model and camera
        settings = get_settings()
        self.model = YOLO(model_path or settings.default_model_path)
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
        self.window_name = f"YOLOv11-Pose Person Monitor - {session_id}"
        self.show_window = False

        # Performance optimization
        self.target_fps = settings.target_fps
        self.frame_time = 1.0 / self.target_fps
        self.last_process_time = 0

        # Frame buffer for smooth processing
        self.frame_buffer = Queue(maxsize=settings.frame_buffer_size)
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
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, get_settings().camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, get_settings().camera_height)
            self.cap.set(cv2.CAP_PROP_FPS, 60)  # Set camera FPS
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
            # Use Event.wait instead of time.sleep for better responsiveness
            self._stop_event.wait(timeout=0.001)
    
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
        # Use settings from config
        settings = get_settings()
        results = self.model(
            frame,
            stream=True,
            verbose=False,
            save=False,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            device='cpu',
            half=False
        )
        person_found = False
        rendered_frame = frame.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    if int(box.cls) == 0:  # Person class
                        person_found = True
                        break
            rendered_frame = result.plot()
        
        return person_found, rendered_frame
    
    def _append_record(self, block_type: str, start_ts: float, end_ts: float) -> str:
        """Central helper to append a time block record."""
        formatted = self.format_time_string(start_ts, end_ts, block_type.capitalize())
        with self._records_lock:
            self.time_records.append({
                'type': block_type,
                'start': start_ts,
                'end': end_ts,
                'formatted': formatted,
                'session_id': self.session_id
            })
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Session {self.session_id}: {formatted}")
        return formatted

    def update_time_tracking(self, person_detected: bool) -> Optional[str]:
        """Update time tracking based on person detection state transitions."""
        current_time = time.time()
        # Initial: wait for first detection to start tracking focus block
        if not self.is_initialized:
            if person_detected:
                self.is_initialized = True
                self.focus_start_time = current_time
                self.previous_person_state = True
                logger.info(f"Session {self.session_id} initialized -> focus block started")
            return None

        produced = None
        if self.previous_person_state is not None:
            # Transition: leave -> focus
            if person_detected and not self.previous_person_state and self.leave_start_time is not None:
                produced = self._append_record('leave', self.leave_start_time, current_time)
                self.leave_start_time = None
                self.focus_start_time = current_time
            # Transition: focus -> leave
            elif (not person_detected) and self.previous_person_state and self.focus_start_time is not None:
                produced = self._append_record('focus', self.focus_start_time, current_time)
                self.focus_start_time = None
                self.leave_start_time = current_time

        self.previous_person_state = person_detected
        return produced
    
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
                    # Use Event.wait instead of time.sleep
                    self._stop_event.wait(timeout=self.frame_time - time_since_last)
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
        
        # Draw session info
        cv2.putText(frame, f"Session: {self.session_id}", (10, 20), font, font_scale, (255, 255, 255), thickness)
        
        # Draw status info using enum
        if not self.is_initialized:
            status = MonitorStatus.WAITING_DETECTION
        else:
            status = MonitorStatus.PERSON_DETECTED if self.previous_person_state else MonitorStatus.PERSON_NOT_DETECTED
        
        cv2.putText(frame, status.text, (10, 50), font, font_scale, status.color, thickness)
        
        # Show current time tracking
        if self.focus_start_time is not None:
            elapsed = (time.time() - self.focus_start_time) / 60
            cv2.putText(frame, f"Focus time: {elapsed:.1f} min", (10, 80), font, font_scale, (0, 255, 0), thickness)
        elif self.leave_start_time is not None:
            elapsed = (time.time() - self.leave_start_time) / 60
            cv2.putText(frame, f"Leave time: {elapsed:.1f} min", (10, 80), font, font_scale, (0, 165, 255), thickness)
        
        # Show record count
        cv2.putText(frame, f"Records: {len(self.time_records)}", (10, 110), font, font_scale, (255, 255, 255), thickness)
        
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
        logger.info(f"Monitoring started for session {self.session_id}")
    
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
            final_record = self._append_record('focus', self.focus_start_time, current_time)
            self.focus_start_time = None
        elif self.leave_start_time is not None:
            final_record = self._append_record('leave', self.leave_start_time, current_time)
            self.leave_start_time = None
        
        self._release_camera()
        logger.info(f"Monitoring stopped for session {self.session_id}")
        
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
            'total_records': len(self.time_records),
            'session_id': self.session_id
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
    
    def get_focus_score(self) -> float:
        """Calculate focus score based on current session and overall performance"""
        if not self.is_initialized:
            return 0.0
        
        current_time = time.time()
        total_session_time = 0
        total_focus_time = 0
        
        # Calculate from records
        with self._records_lock:
            for record in self.time_records:
                duration = record['end'] - record['start']
                total_session_time += duration
                if record['type'] == 'focus':
                    total_focus_time += duration
        
        # Add current session
        if self.focus_start_time is not None:
            current_focus_duration = current_time - self.focus_start_time
            total_focus_time += current_focus_duration
            total_session_time += current_focus_duration
        elif self.leave_start_time is not None:
            current_leave_duration = current_time - self.leave_start_time
            total_session_time += current_leave_duration
        
        if total_session_time == 0:
            return 5.0 if self.previous_person_state else 0.0
        
        # Calculate focus ratio and convert to 0-5 scale
        focus_ratio = total_focus_time / total_session_time
        score = min(5.0, max(0.0, focus_ratio * 5.0))
        
        return round(score, 2)


class SessionManagerService:
    """Manages multiple PersonMonitorService instances for different users/sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, PersonMonitorService] = {}
        self._sessions_lock = Lock()
    
    def create_session(self, session_id: str, model_path: Optional[str] = None, camera_index: int = 0) -> PersonMonitorService:
        """Create a new monitoring session"""
        with self._sessions_lock:
            if session_id in self._sessions:
                raise ValueError(f"Session {session_id} already exists")
            
            monitor = PersonMonitorService(
                model_path=model_path,
                camera_index=camera_index,
                session_id=session_id
            )
            self._sessions[session_id] = monitor
            return monitor
    
    def get_session(self, session_id: str) -> Optional[PersonMonitorService]:
        """Get existing session"""
        with self._sessions_lock:
            return self._sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> bool:
        """Remove and cleanup session"""
        with self._sessions_lock:
            if session_id in self._sessions:
                monitor = self._sessions[session_id]
                if monitor.is_running:
                    monitor.stop()
                del self._sessions[session_id]
                return True
            return False
    
    def list_sessions(self) -> List[str]:
        """List all active sessions"""
        with self._sessions_lock:
            return list(self._sessions.keys())
    
    def cleanup_inactive_sessions(self):
        """Remove inactive sessions"""
        with self._sessions_lock:
            inactive_sessions = [
                session_id for session_id, monitor in self._sessions.items()
                if not monitor.is_running
            ]
            for session_id in inactive_sessions:
                del self._sessions[session_id]


# Global session manager
session_manager = SessionManagerService()
