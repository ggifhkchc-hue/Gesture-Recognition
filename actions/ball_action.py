# ==========================================
# 最终版：手势全控 + 持续手掌开合体积缩放 + 永久模式 (actions/ball_action.py)
# ==========================================
import cv2
import numpy as np
import math
import time
from actions.base_action import BaseAction
import config

# ================== 参数 ==================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
NUM_PARTICLES = 1450
BALL_RADIUS = 235

SPRING_K = 0.38
DAMPING = 0.20
INFLUENCE_RADIUS = 480

PULL_NORMAL = 0.30
PULL_PINCH = 3.6
PUSH_FACTOR = 1.9

# 体积缩放参数
SCALE_STEP = 0.018      # 每帧缩放速度（开合手时持续变化）
MIN_SCALE = 0.25
MAX_SCALE = 2.8


class Particle3D:
    def __init__(self, x, y, z, hue):
        self.ox, self.oy, self.oz = x, y, z
        self.ax, self.ay, self.az = x, y, z
        self.x, self.y, self.z = x, y, z
        self.vx = self.vy = self.vz = 0.0
        self.hue = hue


class PixelBall3D:
    def __init__(self):
        self.cx = WINDOW_WIDTH // 2
        self.cy = WINDOW_HEIGHT // 2
        self.radius = BALL_RADIUS
        self.particles = []
        self.color_shift = 0
        self.current_scale = 1.0
        self.momentum_x = 0.0

        golden_ratio = (1 + math.sqrt(5)) / 2
        for i in range(NUM_PARTICLES):
            z = 1 - (i / float(NUM_PARTICLES - 1)) * 2
            r = math.sqrt(1 - z * z)
            theta = 2 * math.pi * i / golden_ratio
            x = r * math.cos(theta) * self.radius
            y = r * math.sin(theta) * self.radius
            z_val = z * self.radius
            hue = int(((z_val + self.radius) / (2 * self.radius)) * 180)
            self.particles.append(Particle3D(x, y, z_val, hue))

    def update_scale(self, gesture_id):
        """手掌开合控制体积"""
        if gesture_id == 'OPEN_PALM':
            self.current_scale = min(self.current_scale + SCALE_STEP, MAX_SCALE)
        elif gesture_id in ('FIST', 'PINCH'):
            self.current_scale = max(self.current_scale - SCALE_STEP, MIN_SCALE)

    def update(self, hand_pos, gesture_id, prev_hand_x=None):
        self.color_shift = (self.color_shift + 1) % 180
        self.update_scale(gesture_id)

        is_pinch = (gesture_id == 'PINCH')
        pull = PULL_PINCH if is_pinch else PULL_NORMAL

        cos_y = math.cos(0.009)
        sin_y = math.sin(0.009)

        for p in self.particles:
            # 自转 + 缩放
            new_ox = p.ox * cos_y - p.oz * sin_y
            new_oz = p.ox * sin_y + p.oz * cos_y
            p.ox, p.oz = new_ox, new_oz

            p.ax = new_ox * self.current_scale
            p.ay = p.oy * self.current_scale
            p.az = new_oz * self.current_scale

            fx = SPRING_K * (p.ax - p.x)
            fy = SPRING_K * (p.ay - p.y)
            fz = SPRING_K * (p.az - p.z)

            if hand_pos:
                hx, hy = hand_pos
                dx = hx - (p.x + self.cx)
                dy = hy - (p.y + self.cy)
                dz = -p.z

                dist_2d = math.hypot(dx, dy)
                if dist_2d < INFLUENCE_RADIUS:
                    dist_3d = math.sqrt(dx*dx + dy*dy + dz*dz) or 1
                    ndx, ndy, ndz = dx/dist_3d, dy/dist_3d, dz/dist_3d
                    drop = (INFLUENCE_RADIUS - dist_2d) / INFLUENCE_RADIUS
                    force = pull * drop * 18.5
                    
                    fx += ndx * force
                    fy += ndy * force
                    fz += ndz * force

                    if prev_hand_x is not None:
                        push = (hx - prev_hand_x) * PUSH_FACTOR
                        self.momentum_x = push * 0.65
                        fx += self.momentum_x * 0.8

            p.vx = (p.vx + fx) * (1 - DAMPING)
            p.vy = (p.vy + fy) * (1 - DAMPING)
            p.vz = (p.vz + fz) * (1 - DAMPING)
            
            p.x += p.vx
            p.y += p.vy
            p.z += p.vz

    def draw(self, frame, gesture_id):
        overlay = frame.copy()
        sorted_p = sorted(self.particles, key=lambda p: p.z)
        dynamic_r = self.radius * self.current_scale

        for p in sorted_p:
            sx = int(p.x + self.cx)
            sy = int(p.y + self.cy)
            if not (0 <= sx < WINDOW_WIDTH and 0 <= sy < WINDOW_HEIGHT):
                continue

            z_norm = max(0, min(1, (p.z + dynamic_r) / (2 * dynamic_r + 1e-5)))
            hue = (p.hue + self.color_shift) % 180
            color = cv2.cvtColor(np.uint8([[[hue, 165 + 90*z_norm, 115 + 140*z_norm]]]), 
                               cv2.COLOR_HSV2BGR)[0][0]

            size = max(2, int(3 + 7.5 * z_norm))
            cv2.circle(frame, (sx, sy), size, (255,255,255), -1)
            cv2.circle(overlay, (sx, sy), max(5, int(6.5 + 13*z_norm)), 
                      (int(color[0]),int(color[1]),int(color[2])), -1)

        cv2.addWeighted(overlay, 0.47, frame, 0.53, 0, frame)

        # HUD
        scale_pct = int(self.current_scale * 100)
        cv2.putText(frame, f"体积: {scale_pct}%", (30, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2)
        cv2.putText(frame, f"手势: {gesture_id} | ESC退出球窗", (30, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 220, 100), 2)


class BallAction(BaseAction):
    def __init__(self):
        super().__init__()
        self.ball = PixelBall3D()
        self.active = False
        self.prev_hand_x = None
        self.hand_pos = None

    def execute(self, gesture_id, landmarks):
        if not landmarks:
            return

        # 手掌中心
        palm = landmarks[0]
        idx = landmarks[5]
        self.hand_pos = (int((palm.x + idx.x)*0.5 * WINDOW_WIDTH), 
                        int((palm.y + idx.y)*0.5 * WINDOW_HEIGHT))

        # VICTORY 切换为永久激活
        if gesture_id == 'VICTORY' and not self.active:
            self.active = True
            print("[BALL] ✅ 永久激活手势球控模式（按 ESC 退出球窗）")

        if not self.active:
            return

        # 更新物理（包含手掌开合体积控制）
        self.ball.update(self.hand_pos, gesture_id, self.prev_hand_x)
        self.prev_hand_x = self.hand_pos[0]

        # 渲染球窗
        frame = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
        self.ball.draw(frame, gesture_id)
        
        cv2.imshow("Gesture 3D Pixel Ball - 永久手势控制", frame)
        
        # 检测 ESC 退出球窗（不影响主程序）
        if cv2.waitKey(1) & 0xFF == 27:
            self.active = False
            print("[BALL] ⛔ 已退出球控模式")
            cv2.destroyWindow("Gesture 3D Pixel Ball - 永久手势控制")