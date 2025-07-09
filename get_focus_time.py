#!/usr/bin/env python3
"""
YOLOv11-Pose 人体监测脚本
功能：
1. 获取摄像头画面
2. 使用YOLOv11-pose进行人体姿态检测
3. 记录集中时间和离开时间
4. 提供接口供外部调用
"""
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
        """
        Args:
            model_path: YOLOv11-pose模型路径
            camera_index: 摄像头索引
        """
        # 加载YOLOv11-pose模型
        self.model = YOLO(model_path)
        
        # 初始化摄像头
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 状态跟踪
        self.person_detected = False
        self.previous_person_state = None  # None表示初始状态
        self.is_initialized = False  # 是否已初始化（第一次检测到人）
        
        # 时间记录
        self.focus_start_time = None
        self.leave_start_time = None
        self.time_records = []  # 存储所有时间记录
        
        # 线程控制
        self.is_running = False
        self.monitor_thread = None
        self.record_queue = queue.Queue()  # 用于线程间传递记录
        
        # 显示相关
        self.window_name = "YOLOv11-Pose Person Monitor"
        self.show_window = False
        
    def format_time_string(self, start_time: float, end_time: float, time_type: str) -> str:
        """
        格式化时间字符串
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            time_type: "Focus" 或 "Leave"
        Returns:
            格式化的时间字符串
        """
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        
        # 格式化日期
        date_str = start_dt.strftime("%d/%m/%Y")
        
        # 格式化开始时间
        start_hour = start_dt.strftime("%I").lstrip('0')  # 移除前导0
        start_minute = start_dt.strftime("%M")
        start_period = start_dt.strftime("%p").lower()
        
        # 格式化结束时间
        end_hour = end_dt.strftime("%I").lstrip('0')
        end_minute = end_dt.strftime("%M")
        end_period = end_dt.strftime("%p").lower()
        
        return f"{date_str} {time_type} time: {start_hour}:{start_minute} {start_period} - {end_hour}:{end_minute} {end_period}"
    
    def detect_person(self, frame: np.ndarray) -> Tuple[bool, np.ndarray]:
        """
        检测画面中是否有人
        Args:
            frame: 输入图像帧
        Returns:
            (是否检测到人, 渲染后的图像)
        """
        results = self.model(frame, stream=True, verbose=False, save=False, conf=0.7, iou=0.45)
        person_found = False
        rendered_frame = frame.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    if box.cls == 0:  # 人的类别
                        person_found = True
                        break
            rendered_frame = result.plot()
        
        return person_found, rendered_frame
    
    def update_time_tracking(self, person_detected: bool) -> Optional[str]:
        """
        更新时间跟踪
        Args:
            person_detected: 是否检测到人
        Returns:
            如果有时间记录完成，返回格式化的时间字符串
        """
        current_time = time.time()
        time_record = None
        
        # 初始状态处理
        if not self.is_initialized:
            if person_detected:
                # 第一次检测到人，开始记录集中时间
                self.is_initialized = True
                self.focus_start_time = current_time
                self.previous_person_state = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 系统初始化完成，开始记录集中时间")
            return None
        
        # 状态变化检测
        if self.previous_person_state is not None:
            if person_detected and not self.previous_person_state:
                # 人回来了，结束离开时间，开始集中时间
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
                # 人离开了，结束集中时间，开始离开时间
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
        """监控循环（在独立线程中运行）"""
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # 检测人体
                person_detected, rendered_frame = self.detect_person(frame)
                
                # 更新时间跟踪
                time_record = self.update_time_tracking(person_detected)
                if time_record:
                    self.record_queue.put(time_record)
                
                # 如果需要显示窗口
                if self.show_window:
                    display_frame = self.draw_info(rendered_frame)
                    cv2.imshow(self.window_name, display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
                
                time.sleep(0.1)  # 避免过度占用CPU
                
        except Exception as e:
            print(f"监控循环错误: {e}")
        finally:
            if self.show_window:
                cv2.destroyAllWindows()
    
    def draw_info(self, frame: np.ndarray) -> np.ndarray:
        """绘制信息到图像上"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # 绘制状态信息
        if not self.is_initialized:
            status_text = "Waiting for first detection..."
            status_color = (255, 255, 0)
        else:
            status_text = "Person: Detected" if self.previous_person_state else "Person: Not Detected"
            status_color = (0, 255, 0) if self.previous_person_state else (0, 0, 255)
        
        cv2.putText(frame, status_text, (10, 30), font, font_scale, status_color, thickness)
        
        # 显示当前记录的时间类型
        if self.focus_start_time is not None:
            elapsed = (time.time() - self.focus_start_time) / 60  # 转换为分钟
            cv2.putText(frame, f"Focus time: {elapsed:.1f} min", (10, 60), font, font_scale, (0, 255, 0), thickness)
        elif self.leave_start_time is not None:
            elapsed = (time.time() - self.leave_start_time) / 60  # 转换为分钟
            cv2.putText(frame, f"Leave time: {elapsed:.1f} min", (10, 60), font, font_scale, (0, 165, 255), thickness)
        
        # 显示记录数量
        cv2.putText(frame, f"Records: {len(self.time_records)}", (10, 90), font, font_scale, (255, 255, 255), thickness)
        
        return frame
    
    def start(self, show_window: bool = False):
        """启动监控"""
        if self.is_running:
            return
        
        self.is_running = True
        self.show_window = show_window
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("监控已启动")
    
    def stop(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        # 处理未完成的记录
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
        print("监控已停止")
        
        if final_record:
            print(f"最终记录: {final_record}")
    
    def get_latest_record(self) -> Optional[str]:
        """获取最新的时间记录（非阻塞）"""
        try:
            return self.record_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_all_records(self) -> List[Dict]:
        """获取所有时间记录"""
        return self.time_records.copy()
    
    def get_current_status(self) -> Dict:
        """获取当前状态"""
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
        """获取统计摘要"""
        total_focus_time = 0
        total_leave_time = 0
        
        for record in self.time_records:
            duration = record['end'] - record['start']
            if record['type'] == 'focus':
                total_focus_time += duration
            else:
                total_leave_time += duration
        
        # 添加当前进行中的会话
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

# 全局监控实例
_monitor_instance = None

def get_monitor_instance(model_path: str = r'C:\python-env\YOLOv8-Magic\ultralytics\yolo11s-pose.pt', 
                        camera_index: int = 0) -> PersonMonitor:
    """获取或创建监控实例（单例模式）"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PersonMonitor(model_path, camera_index)
    return _monitor_instance

# API 接口函数
def start_monitoring(show_window: bool = False):
    """启动监控"""
    monitor = get_monitor_instance()
    monitor.start(show_window)

def stop_monitoring():
    """停止监控"""
    monitor = get_monitor_instance()
    monitor.stop()

def get_latest_time_record() -> Optional[str]:
    """获取最新的时间记录"""
    monitor = get_monitor_instance()
    return monitor.get_latest_record()

def get_all_time_records() -> List[Dict]:
    """获取所有时间记录"""
    monitor = get_monitor_instance()
    return monitor.get_all_records()

def get_monitoring_status() -> Dict:
    """获取监控状态"""
    monitor = get_monitor_instance()
    return monitor.get_current_status()

def get_time_summary() -> Dict:
    """获取时间统计摘要"""
    monitor = get_monitor_instance()
    return monitor.get_summary_stats()

def main():
    """
    主函数 - 用于测试
    """
    try:
        monitor = PersonMonitor(model_path=r'C:\python-env\YOLOv8-Magic\ultralytics\yolo11s-pose.pt', camera_index=0)
        monitor.start(show_window=True)
        
        print("监控系统已启动")
        print("按 Ctrl+C 停止监控")
        
        # 主循环
        try:
            while True:
                # 检查新的时间记录
                record = monitor.get_latest_record()
                if record:
                    print(f"\n新记录: {record}")
                
                # 每10秒打印一次状态
                time.sleep(10)
                status = monitor.get_current_status()
                print(f"\n当前状态: {status}")
                
        except KeyboardInterrupt:
            print("\n正在停止监控...")
            
        finally:
            monitor.stop()
            
            # 打印最终统计
            print("\n=== 最终统计 ===")
            stats = monitor.get_summary_stats()
            print(f"总集中时间: {stats['total_focus_minutes']:.1f} 分钟")
            print(f"总离开时间: {stats['total_leave_minutes']:.1f} 分钟")
            print(f"集中次数: {stats['focus_sessions']}")
            print(f"离开次数: {stats['leave_sessions']}")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()