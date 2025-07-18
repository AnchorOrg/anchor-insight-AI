#!/usr/bin/env python3

import cv2
import time
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from typing import Optional, Tuple, List, Dict
import threading
import queue

class PersonMonitor:
    def __init__(self, model_path: str = 'yolov11n-pose.pt', camera_index: int = 0):
        self.model = YOLO(model_path)

        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Tracking
        self.person_detected = False
        self.previous_person_state = None  # init
        self.is_initialized = False  
        
        # Time record
        self.focus_start_time = None
        self.leave_start_time = None
        self.time_records = []  
        
        # Threading Control
        self.is_running = False
        self.monitor_thread = None
        self.record_queue = queue.Queue() 
        
        # show
        self.window_name = "YOLOv11-Pose Person Monitor"
        self.show_window = False
        
    def format_time_string(self, start_time: float, end_time: float, time_type: str) -> str:
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        
        # format date
        date_str = start_dt.strftime("%d/%m/%Y")
        
        # format start time
        start_hour = start_dt.strftime("%I").lstrip('0') 
        start_minute = start_dt.strftime("%M")
        start_period = start_dt.strftime("%p").lower()
        
        # format end time
        end_hour = end_dt.strftime("%I").lstrip('0')
        end_minute = end_dt.strftime("%M")
        end_period = end_dt.strftime("%p").lower()
        
        return f"{date_str} {time_type} time: {start_hour}:{start_minute} {start_period} - {end_hour}:{end_minute} {end_period}"
    
    def detect_person(self, frame: np.ndarray) -> Tuple[bool, np.ndarray]:
        results = self.model(frame, stream=True, verbose=False, save=False, conf=0.7, iou=0.45)
        person_found = False
        rendered_frame = frame.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    if box.cls == 0:  # label of person
                        person_found = True
                        break
                if person_found:
                    break
            rendered_frame = result.plot()
        
        return person_found, rendered_frame
    
    def update_time_tracking(self, person_detected: bool) -> Optional[str]:
        current_time = time.time()
        time_record = None
        
        # init
        if not self.is_initialized:
            if person_detected:
                # start recording time
                self.is_initialized = True
                self.focus_start_time = current_time
                self.previous_person_state = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] System Format Successful! Now Recording Time.")
            return None
        
        # State Change
        if self.previous_person_state is not None:
            if person_detected and not self.previous_person_state:
                # End leave time, start focus time
                if self.leave_start_time is not None:
                    time_record = self.format_time_string(
                        self.leave_start_time, 
                        current_time, 
                        "Leave"
                    )
                    self.time_records.append({
                        'type': 'leave',
                        'start': self.leave_start_time,
                        'end': current_time,
                        'formatted': time_record
                    })
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {time_record}")
                
                self.focus_start_time = current_time
                self.leave_start_time = None
                
            elif not person_detected and self.previous_person_state:
                # End focus time, start leave time
                if self.focus_start_time is not None:
                    time_record = self.format_time_string(
                        self.focus_start_time, 
                        current_time, 
                        "Focus"
                    )
                    self.time_records.append({
                        'type': 'focus',
                        'start': self.focus_start_time,
                        'end': current_time,
                        'formatted': time_record
                    })
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {time_record}")
                
                self.leave_start_time = current_time
                self.focus_start_time = None
        
        self.previous_person_state = person_detected
        return time_record
    
    def monitor_loop(self):
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # detect person
                person_detected, rendered_frame = self.detect_person(frame)
                
                # upload time
                time_record = self.update_time_tracking(person_detected)
                if time_record:
                    self.record_queue.put(time_record)
                
                # show window
                if self.show_window:
                    display_frame = self.draw_info(rendered_frame)
                    cv2.imshow(self.window_name, display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
                
                time.sleep(0.1)  # avoid use more cpu resource
                
        except Exception as e:
            print(f"CCTV circulate Error: {e}")
        finally:
            if self.show_window:
                cv2.destroyAllWindows()
    
    def draw_info(self, frame: np.ndarray) -> np.ndarray:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # draw
        if not self.is_initialized:
            status_text = "Waiting for first detection..."
            status_color = (255, 255, 0)
        else:
            status_text = "Person: Detected" if self.previous_person_state else "Person: Not Detected"
            status_color = (0, 255, 0) if self.previous_person_state else (0, 0, 255)
        
        cv2.putText(frame, status_text, (10, 30), font, font_scale, status_color, thickness)
        
        # show now record type of time
        if self.focus_start_time is not None:
            elapsed = (time.time() - self.focus_start_time) / 60  # transf to min
            cv2.putText(frame, f"Focus time: {elapsed:.1f} min", (10, 60), font, font_scale, (0, 255, 0), thickness)
        elif self.leave_start_time is not None:
            elapsed = (time.time() - self.leave_start_time) / 60  # transf to min
            cv2.putText(frame, f"Leave time: {elapsed:.1f} min", (10, 60), font, font_scale, (0, 165, 255), thickness)
        
        # show numbers of recording 
        cv2.putText(frame, f"Records: {len(self.time_records)}", (10, 90), font, font_scale, (255, 255, 255), thickness)
        
        return frame
    
    def start(self, show_window: bool = False):
        if self.is_running:
            return
        
        self.is_running = True
        self.show_window = show_window
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Monitor Begin")
    
    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        current_time = time.time()
        final_record = None
        
        if self.focus_start_time is not None:
            final_record = self.format_time_string(
                self.focus_start_time, 
                current_time, 
                "Focus"
            )
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
            self.time_records.append({
                'type': 'leave',
                'start': self.leave_start_time,
                'end': current_time,
                'formatted': final_record
            })
        
        self.cap.release()
        print("Monitor Ending")
        
        if final_record:
            print(f"Final record: {final_record}")
    
    def get_latest_record(self) -> Optional[str]:
        try:
            return self.record_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_all_records(self) -> List[Dict]:
        return self.time_records.copy()
    
    def get_current_status(self) -> Dict:
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
        total_focus_time = 0
        total_leave_time = 0
        
        for record in self.time_records:
            duration = record['end'] - record['start']
            if record['type'] == 'focus':
                total_focus_time += duration
            else:
                total_leave_time += duration
        
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

_monitor_instance = None

def get_monitor_instance(model_path: str = r'C:\python-env\YOLOv8-Magic\ultralytics\yolo11s-pose.pt', 
                        camera_index: int = 0) -> PersonMonitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PersonMonitor(model_path, camera_index)
    return _monitor_instance

# API
def start_monitoring(show_window: bool = False):
    monitor = get_monitor_instance()
    monitor.start(show_window)

def stop_monitoring():
    monitor = get_monitor_instance()
    monitor.stop()

def get_latest_time_record() -> Optional[str]:
    monitor = get_monitor_instance()
    return monitor.get_latest_record()

def get_all_time_records() -> List[Dict]:
    monitor = get_monitor_instance()
    return monitor.get_all_records()

def get_monitoring_status() -> Dict:
    monitor = get_monitor_instance()
    return monitor.get_current_status()

def get_time_summary() -> Dict:
    monitor = get_monitor_instance()
    return monitor.get_summary_stats()

def main():
    try:
        monitor = PersonMonitor(model_path=r'C:\python-env\YOLOv8-Magic\ultralytics\yolo11s-pose.pt', camera_index=0)
        monitor.start(show_window=True)
        
        print("Monitor Starting")
        print("Press Ctrl+C to Stop the Monitor")
        
        # main while
        try:
            while True:
                # check the new time record
                record = monitor.get_latest_record()
                if record:
                    print(f"\n New recording: {record}")
                
                time.sleep(10)
                status = monitor.get_current_status()
                print(f"\n Now State: {status}")
                
        except KeyboardInterrupt:
            print("\n Ending the monitor, Please wait...")
            
        finally:
            monitor.stop()
            
            # Print Final record
            print("\n=== Final statisticians ===")
            stats = monitor.get_summary_stats()
            print(f"All focus time: {stats['total_focus_minutes']:.1f} min")
            print(f"All leave time: {stats['total_leave_minutes']:.1f} min")
            print(f"Focus frequency: {stats['focus_sessions']}")
            print(f"Leave frequency: {stats['leave_sessions']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
