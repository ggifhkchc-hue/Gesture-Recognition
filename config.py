# ==========================================
# GestureControl 系统配置文件 (config.py)
# ==========================================

# --- 1. 摄像头与画面配置 ---
# 支持本地摄像头ID (int) 或手机摄像头IP流URL (str)
# 示例手机App: DroidCam, IP Webcam, iVCam 等提供的 MJPEG 地址
CAMERA_ID = "http://10.163.93.164:4747/video"            # 默认本地摄像头ID，改成手机流URL如 'http://192.168.1.100:8080/video'
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIRROR_FRAME = True
SHOW_UI = True

# --- 2. MediaPipe 模型配置 ---
MODEL_PATH = 'models/hand_landmarker.task'

MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.6

# --- 3. 手势与功能映射表 ---
GESTURE_ACTION_MAPPING = {
    'FIST': 'mouse_click',
    'POINT_UP': 'mouse_move',
    'OPEN_PALM': 'ball_control',
    'PINCH': 'ball_control',
    'VICTORY': 'ball_control',
}

# --- 4. 控制灵敏度 ---
MOUSE_SMOOTHING = 3.0
CLICK_COOLDOWN = 0.5