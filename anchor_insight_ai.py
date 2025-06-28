import cv2
import numpy as np
import base64
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
import eventlet

# 初始化Flask应用和SocketIO
app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

try:
    model = YOLO(r'C:\python-env\YOLOv8-Magic\ultralytics\yolo11s-pose.pt')
    print("YOLOv11-pose 模型加载成功。")
except Exception as e:
    print(f"错误：无法加载YOLO模型。请确保 'yolov8n-pose.pt' 文件存在。 {e}")
    model = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('image')
def handle_image(data_image):
    if not model:
        print("模型未加载，跳过处理")
        return

    # 解码图像
    sbuf = data_image.split(',')[1]
    img_bytes = base64.b64decode(sbuf)
    # 转换为numpy数组
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        print("接收到无效的图像帧")
        return

    # YOLO进行姿态估计
    results = model.track(frame, stream=False, save=False)

    # 可视化
    annotated_frame = results[0].plot()
    _, buffer = cv2.imencode('.jpg', annotated_frame)

    processed_img_bytes = buffer.tobytes()
    processed_img_base64 = base64.b64encode(processed_img_bytes).decode('utf-8')
    
    # 发送回客户端的数据URL
    processed_data_url = 'data:image/jpeg;base64,' + processed_img_base64
    emit('response_back', processed_data_url)

if __name__ == '__main__':
    print("服务器启动，http://127.0.0.1:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)