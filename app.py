# ==========================================
# 网页版服务启动入口 (app.py)
# ==========================================
from flask import Flask, render_template, Response
import cv2
import time
import config

# 导入你原有的感知与控制模块
from detector.camera import Camera
from detector.hand_detector import HandDetector
from recognizer.gesture import GestureEngine
from actions.dispatcher import ActionDispatcher

app = Flask(__name__)

# --- 初始化核心组件 (只初始化一次，避免多线程冲突) ---
camera = Camera().start()
detector = HandDetector(
    model_path=config.MODEL_PATH,
    max_hands=config.MAX_NUM_HANDS,
    min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
)
gesture_engine = GestureEngine()
action_dispatcher = ActionDispatcher()

def gen_frames():
    """视频流生成器：持续抓取画面，处理手势，并编码为 JPEG 推送给前端"""
    prev_time = 0
    while True:
        # 1. 读取摄像头画面
        success, frame = camera.read_frame()
        if not success:
            time.sleep(0.01)
            continue
        
        # 2. 识别手部关键点
        landmarks_list, annotated_frame = detector.process(
            frame, 
            draw_skeleton=config.SHOW_UI
        )
        
        gesture_id = "WAITING..."
        if landmarks_list:
            primary_hand = landmarks_list[0]
            # 3. 识别手势并触发鼠标动作
            gesture_id = gesture_engine.recognize(primary_hand)
            action_dispatcher.execute(gesture_id, primary_hand)
            
            # 在画面上绘制手部数量
            cv2.putText(annotated_frame, f"Hands: {len(landmarks_list)}", 
                        (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # 4. 计算实时 FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        
        if config.SHOW_UI:
            # 在推送到网页的画面中绘制调试信息
            cv2.putText(annotated_frame, f"FPS: {int(fps)}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Action: {gesture_id}", (20, 85), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 200, 0), 2)
            
        # 5. 将 OpenCV 图像格式（Matrix）压缩编码为 JPEG 格式
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        
        # 6. 使用 multipart 格式生成响应体分块
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """渲染前端主页面"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """视频流路由：浏览器访问此接口会直接收到持续更新的图片流"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # 注意：千万不要开启 debug=True！因为 Flask 的 Debug 模式会启动双进程，
    # 导致摄像头（Camera）被初始化两次进而因资源抢占而报错。
    print("[INFO] Web 服务器正在启动，请在浏览器中访问 http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)