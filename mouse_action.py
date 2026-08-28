# ==========================================
# 优化版：鼠标控制插件 (actions/mouse_action.py)
# ==========================================
import pyautogui
import config
from actions.base_action import BaseAction

# --- 核心优化 1：解除 PyAutoGUI 的默认运行延迟 ---
pyautogui.PAUSE = 0.001     # 默认为 0.1 秒，改为极小值后，鼠标移动帧率直接翻倍！
pyautogui.FAILSAFE = False

class MouseAction(BaseAction):
    def __init__(self):
        super().__init__()
        # 获取屏幕分辨率[cite: 10]
        self.screen_w, self.screen_h = pyautogui.size()
        
        # 记录上一帧的坐标[cite: 10]
        self.prev_x, self.prev_y = None, None
        
        # --- 核心优化 2：定义“虚拟操作框”（DPI 灵敏度） ---
        # 限制手部在摄像头中央的 35% ~ 65% 区域移动即可填满整张电脑屏幕，操作省力
        self.x_min, self.x_max = 0.35, 0.65
        self.y_min, self.y_max = 0.30, 0.60

    def execute(self, gesture_id, landmarks):
        if not landmarks:
            # 手丢了的时候重置前一帧坐标，防止下次出现时鼠标瞬移[cite: 10]
            self.prev_x, self.prev_y = None, None  
            return

        # 1. 鼠标移动逻辑 (当手势为 'POINT_UP' 伸出食指时)[cite: 2, 5, 10]
        if gesture_id == 'POINT_UP':
            finger_tip = landmarks[8]  # 食指指尖[cite: 10]
            
            # --- 核心优化 3：区域限制与比例映射（DPI 灵敏度转换） ---
            # 限制手尖的坐标在虚拟框内
            x_clipped = max(self.x_min, min(finger_tip.x, self.x_max))
            y_clipped = max(self.y_min, min(finger_tip.y, self.y_max))
            
            # 将虚拟框内的坐标归一化到 0.0 ~ 1.0[cite: 10]
            normalized_x = (x_clipped - self.x_min) / (self.x_max - self.x_min)
            normalized_y = (y_clipped - self.y_min) / (self.y_max - self.y_min)
            
            # 映射到真实的屏幕像素[cite: 10]
            target_x = normalized_x * self.screen_w
            target_y = normalized_y * self.screen_h

            # --- 核心优化 4：智能平滑过滤 ---
            if self.prev_x is None or self.prev_y is None:
                # 第一帧直接定位，拒绝“拉扯感”[cite: 10]
                curr_x, curr_y = target_x, target_y
            else:
                # 动态调节：如果平滑系数还是偏大，可以通过调整 config.py 降低[cite: 2]
                smooth_coef = config.MOUSE_SMOOTHING
                curr_x = self.prev_x + (target_x - self.prev_x) / smooth_coef
                curr_y = self.prev_y + (target_y - self.prev_y) / smooth_coef

            # 移动鼠标[cite: 10]
            pyautogui.moveTo(int(curr_x), int(curr_y))
            
            # 记录上一帧坐标[cite: 10]
            self.prev_x, self.prev_y = curr_x, curr_y

        # 2. 鼠标点击逻辑 (当手势为 'FIST' 握拳时)[cite: 2, 5, 10]
        elif gesture_id == 'FIST':
            # 点击时暂时不更新移动坐标[cite: 10]
            self.prev_x, self.prev_y = None, None  
            pyautogui.click()
            print("[ACTION] 触发：鼠标左键点击")  #[cite: 10]