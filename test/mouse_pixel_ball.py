# ==============================================================================
# 3D 炫彩物理粒子弹性球 - 纯净微粒与独立鼠标拖尾粒子完整版
# ==============================================================================
import cv2
import numpy as np
import math
import random
import app
# ==========================================
# 🎛️ 核心可调参数配置面板（全局常量）
# ==========================================
# 1. 基础视效与画布配置
WINDOW_WIDTH = 1200         # 窗口宽度 (像素)
WINDOW_HEIGHT = 800         # 窗口高度 (像素)
NUM_PARTICLES = 3500        # 3D 球体粒子总数 (决定球体微粒的整体密度)
BALL_RADIUS = 240           # 球体的基础半径 (像素尺寸)
AUTO_ROTATE_SPEED = 0.0     # 自动 3D 自转速度 (0.0 为静态不旋转，可设为 0.01 体验自转)

# 2. 🎛️ 滚轮体积调节参数限制
SCALE_STEP = 0.8           # 每次滚动滚轮时的体积缩放比例步长 (每下滚动变化 8%)
MIN_SCALE = 0.2             # 球体全方位压缩的最小极限体积比例 (原始大小的 20%)
MAX_SCALE = 3.0             # 球体全方位拉伸的最大极限体积比例 (原始大小的 300%)

# 3. 核心磁吸拉扯感参数
SPRING_K = 0.35             # 弹性恢复系数 (值越大，粒子离开鼠标后回弹到原位越果断)
DAMPING = 0.2               # 临界阻尼系数 (高阻尼，消除粒子在原位的任何晃动和颤抖)
INFLUENCE_RADIUS = 400      # 鼠标磁吸的超大影响半径范围 (进入此区域即受引力影响)

# 4. 两段式引力系数
PULL_STRENGTH_DEFAULT = 0.2  # 鼠标【不按左键】时的基础引力强度 (柔和拉伸)
PULL_STRENGTH_CLICK = 2.8    # 鼠标【按下左键】时的强力吸附引力强度 (极速抽吸)

# 5. 💫 鼠标独立拖尾微粒限制参数
TRAIL_MAX_LIFE = 20         # 鼠标粒子最大寿命 (帧数，越短拖尾越短)
TRAIL_SPAWN_DIST = 5        # 距离限制：鼠标单次移动超过5像素才释放新拖尾粒子 (防止原地堆积)
TRAIL_RANDOM_SPREAD = 8     # 扩散限制：粒子在鼠标周围随机溅射的最大半径范围


# --- 1. 3D 物理粒子类 (球体专用) ---
class Particle3D:
    def __init__(self, x, y, z, hue):
        """
        单个球体粒子的物理与视效属性初始化
        """
        # 3D 纯初始相对位置：用于保存球体最初的几何形态，作为自转和缩放的绝对基准
        self.ox, self.oy, self.oz = x, y, z
        
        # 3D 动态锚点位置：经过滚轮缩放和自转计算后，粒子“理想中”应该回到的平衡点位置
        self.ax, self.ay, self.az = x, y, z 
        
        # 3D 当前物理实际位置：粒子当前在空间中的实时坐标，受鼠标引力和弹簧力拉扯而动态变化
        self.x, self.y, self.z = x, y, z     
        
        # 三维速度分量：用于物理引擎的动量积分计算
        self.vx, self.vy, self.vz = 0.0, 0.0, 0.0
        
        # 粒子的颜色色调 (HSV空间的H分量)
        self.hue = hue


# --- 2. 💫 鼠标独立拖尾粒子类 (鼠标专用) ---
class TrailParticle:
    def __init__(self, x, y):
        """
        鼠标拖尾粒子初始化：在鼠标周围带限制地随机生成
        """
        # 扩散限制：在鼠标坐标基础上，做轻微的随机中心扰动散射
        self.x = x + random.uniform(-TRAIL_RANDOM_SPREAD, TRAIL_RANDOM_SPREAD)
        self.y = y + random.uniform(-TRAIL_RANDOM_SPREAD, TRAIL_RANDOM_SPREAD)
        
        # 飘移限制：赋予粒子微弱的随机初始速度，使其产生像流星散落的微弱动态效果
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        
        # 寿命控制 (逐帧递减)
        self.life = TRAIL_MAX_LIFE  
        
        # 颜色控制：选择冷色调（青蓝-紫罗兰色系）突出鼠标轨迹，与球体的全彩虹色进行视觉分离
        self.hue = random.choice([90, 100, 110, 120, 130]) 


# --- 3. 💫 鼠标拖尾粒子管理器 ---
class MouseTrailSystem:
    def __init__(self):
        self.particles = []
        self.last_x = 0
        self.last_y = 0

    def update_and_spawn(self, mx, my):
        """
        更新鼠标粒子状态，并根据距离限制判定是否生成新粒子（实现两模块互不干扰）
        """
        # 1. 更新已有粒子的物理位置，并衰减寿命
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.life -= 1  
            
        # 过滤机制：只保留还活着（寿命 > 0）的粒子
        self.particles = [p for p in self.particles if p.life > 0]

        # 2. 距离限制判定：计算当前鼠标与上一帧鼠标的平面物理距离
        move_dist = math.hypot(mx - self.last_x, my - self.last_y)
        
        # 限制机制：只有当鼠标移动距离超过阈值时，才分裂出新拖尾，防止鼠标静止时粒子在原地无限堆积
        if move_dist > TRAIL_SPAWN_DIST:
            # 动态生成数量：移动速度越快，产生的微粒越多，丰富速度感
            spawn_count = min(3, int(move_dist / 4))
            for _ in range(spawn_count):
                self.particles.append(TrailParticle(mx, my))
                
        # 更新鼠标坐标历史缓存
        self.last_x = mx
        self.last_y = my

    def draw(self, frame):
        """
        在画布上单独绘制清晰的鼠标拖尾粒子 (随寿命淡出、变小)
        """
        for p in self.particles:
            # 视口边缘裁剪边界检查
            if not (0 <= int(p.x) < WINDOW_WIDTH and 0 <= int(p.y) < WINDOW_HEIGHT):
                continue
                
            # 计算当前寿命百分比 (从 1.0 逐步递减到 0.0)
            life_pct = p.life / TRAIL_MAX_LIFE
            
            # 限制1：尺寸随寿命缩水，最老的时候收缩为 1 像素的微尘
            size = max(1, int(3 * life_pct))
            
            # 限制2：亮度随寿命淡出 (通过控制 HSV 空间的明度 Brightness 实现无缝渐隐)
            brightness = int(255 * life_pct)
            
            # 颜色空间转换
            hsv_color = np.uint8([[[p.hue, 255, brightness]]])
            bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
            color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))
            
            # 独立在画布上绘制硬边鼠标点，不影响球体数据结构
            cv2.circle(frame, (int(p.x), int(p.y)), size, color, -1)


# --- 4. 3D 弹性球体物理引擎 ---
class PixelBall3D:
    def __init__(self, cx, cy, radius, num_particles):
        """
        3D 弹性球初始化
        """
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.particles = []
        self.color_shift = 0
        self.current_scale = 1.0  # 实时体积缩放系数 (滚轮控制)

        # 斐波那契球面均匀采样生成立体球体分布
        golden_ratio = (1 + math.sqrt(5)) / 2
        for i in range(num_particles):
            z = 1 - (i / float(num_particles - 1)) * 2
            radius_at_z = math.sqrt(1 - z * z)
            theta = 2 * math.pi * i / golden_ratio

            x = radius_at_z * math.cos(theta) * radius
            y = radius_at_z * math.sin(theta) * radius
            z_val = z * radius
            
            hue = int(((z_val + radius) / (2 * radius)) * 180)
            self.particles.append(Particle3D(x, y, z_val, hue))

    def change_scale(self, direction):
        """
        滚轮触发：全方位拉伸（放大）或压缩（缩小）体积系数
        """
        if direction > 0:
            self.current_scale = min(self.current_scale + SCALE_STEP, MAX_SCALE)
        else:
            self.current_scale = max(self.current_scale - SCALE_STEP, MIN_SCALE)

    def update(self, mouse_pos, is_left_clicked):
        """
        核心物理控制层：处理 3D 旋转、基于滚轮系数的体积自适应拉伸、以及防越界锁定
        """
        self.color_shift = (self.color_shift + 1) % 180
        cos_y = math.cos(AUTO_ROTATE_SPEED)
        sin_y = math.sin(AUTO_ROTATE_SPEED)
        current_pull = PULL_STRENGTH_CLICK if is_left_clicked else PULL_STRENGTH_DEFAULT

        for p in self.particles:
            # 1. 基础原始锚点在空间中绕 Y 轴自转变换
            new_ox = p.ox * cos_y - p.oz * sin_y
            new_oz = p.ox * sin_y + p.oz * cos_y
            p.ox, p.oz = new_ox, new_oz

            # 2. 全方位同步应用滚轮带来的实时体积缩放系数，计算出最新目标锚点位置
            p.ax = new_ox * self.current_scale
            p.ay = p.oy * self.current_scale
            p.az = new_oz * self.current_scale

            # 3. 胡克定律弹簧恢复力计算
            fx = SPRING_K * (p.ax - p.x)
            fy = SPRING_K * (p.ay - p.y)
            fz = SPRING_K * (p.az - p.z)

            # 4. 鼠标磁吸力计算
            if mouse_pos is not None:
                mx, my = mouse_pos
                screen_x = p.x + self.cx
                screen_y = p.y + self.cy

                dx = mx - screen_x
                dy = my - screen_y
                dz = 0 - p.z  

                dist_2d = math.hypot(dx, dy)
                dist_3d = math.sqrt(dx*dx + dy*dy + dz*dz)

                if dist_2d < INFLUENCE_RADIUS and dist_3d > 0:
                    ndx = dx / dist_3d
                    ndy = dy / dist_3d
                    ndz = dz / dist_3d

                    # 距离渐进衰减机制
                    drop_off = (INFLUENCE_RADIUS - dist_2d) / INFLUENCE_RADIUS
                    force = current_pull * drop_off * 15.0
                    
                    fx += ndx * force
                    fy += ndy * force
                    fz += ndz * force

            # 5. 欧拉积分物理更新 (引入高阻尼，消除微粒回弹时的任何抖动)
            p.vx = (p.vx + fx) * (1 - DAMPING)
            p.vy = (p.vy + fy) * (1 - DAMPING)
            p.vz = (p.vz + fz) * (1 - DAMPING)
            
            p.x += p.vx
            p.y += p.vy
            p.z += p.vz

            # 6. 防越界严苛限距锁：极度贴近鼠标坐标时直接截断速度，稳稳吸附
            if mouse_pos is not None:
                mx, my = mouse_pos
                rx = (p.x + self.cx) - mx
                ry = (p.y + self.cy) - my
                dist_to_mouse = math.hypot(rx, ry)
                if dist_to_mouse < 5:  
                    p.vx = 0
                    p.vy = 0

    def draw(self, frame):
        """
        三维透视渲染层：深度排序后绘制纯净清晰的硬边微粒，移除外氲朦胧感
        """
        # 深度排序（由远及近渲染，保证正确的三维遮挡关系）
        sorted_particles = sorted(self.particles, key=lambda p: p.z)
        dynamic_radius = self.radius * self.current_scale

        for p in sorted_particles:
            screen_x = int(p.x + self.cx)
            screen_y = int(p.y + self.cy)

            if not (0 <= screen_x < WINDOW_WIDTH and 0 <= screen_y < WINDOW_HEIGHT):
                continue

            # 3D 纵深归一化 [0.0, 1.0]
            z_normalized = (p.z + dynamic_radius) / (2 * dynamic_radius + 1e-5)
            z_normalized = max(0.0, min(1.0, z_normalized))

            # 彩虹色彩与近明远暗的空间明暗度转换
            hue = (p.hue + self.color_shift) % 180
            saturation = int(180 + 75 * z_normalized)   
            brightness = int(120 + 135 * z_normalized)  
            
            hsv_color = np.uint8([[[hue, saturation, brightness]]])
            bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
            color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))

            # 精细近大远小控制 (去除了发光外氲，最大粒径只有 4 像素，小巧而具有实体感)
            particle_size = max(1, int(1 + 3 * z_normalized))

            # 在画布直接绘制清晰的硬边实心点
            cv2.circle(frame, (screen_x, screen_y), particle_size, color, -1)


# --- 5. 鼠标交互事件流监听 ---
mouse_x, mouse_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
is_left_clicked = False
pixel_ball = None

def mouse_callback(event, x, y, flags, param):
    """
    OpenCV 鼠标事件核心回调：高频拦截轨迹、点击以及滚轮状态
    """
    global mouse_x, mouse_y, is_left_clicked, pixel_ball
    mouse_x, mouse_y = x, y
    
    if event == cv2.EVENT_LBUTTONDOWN:
        is_left_clicked = True
    elif event == cv2.EVENT_LBUTTONUP:
        is_left_clicked = False
        
    elif event == cv2.EVENT_MOUSEWHEEL:
        # flags > 0 代表向前滚动滚轮 (全方位拉伸增大体积)
        # flags < 0 代表向后滚动滚轮 (全方位压缩减小体积)
        if flags > 0:
            pixel_ball.change_scale(1)   
        else:
            pixel_ball.change_scale(-1)  


# --- 6. 主程序入口 ---
def main():
    global mouse_x, mouse_y, is_left_clicked, pixel_ball
    
    # 🚀 在主程序启动前，先在后台拉起手机网页服务器
    app.start_control_server()
    
    window_name = "3D Ball & Phone Remote Control"
    cv2.namedWindow(window_name)
    # 保留鼠标回调，这样你手机和电脑鼠标能同时控制它！
    cv2.setMouseCallback(window_name, mouse_callback)

    # 初始化 3D 球体引擎系统
    pixel_ball = PixelBall3D(cx=WINDOW_WIDTH // 2, cy=WINDOW_HEIGHT // 2, radius=BALL_RADIUS, num_particles=NUM_PARTICLES)
    
    # 初始化 💫 独立的鼠标轨迹流星拖尾系统
    trail_system = MouseTrailSystem()

    print("[SUCCESS] 手机联动版本已就绪！")

    while True:
        # 每一帧重置创建纯黑色背景画布
        frame = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)

        # --------------------------------------------------------
        # 📲 核心桥接：将手机传过来的百分比数据映射回电脑屏幕像素坐标
        # --------------------------------------------------------
        p_data = app.phone_data
        
        # 如果手机有滑屏事件，更新电脑控制坐标
        if p_data["is_touching"]:
            target_x = int(p_data["x_pct"] * WINDOW_WIDTH)
            target_y = int(p_data["y_pct"] * WINDOW_HEIGHT)
            # 平滑过渡当前控制点
            mouse_x = int(mouse_x + (target_x - mouse_x) * 0.4)
            mouse_y = int(mouse_y + (target_y - mouse_y) * 0.4)
            is_left_clicked = True
        else:
            is_left_clicked = False

        # 如果手机发出了双指缩放信号
        if p_data["scale_change"] != 0:
            pixel_ball.change_scale(p_data["scale_change"])
            p_data["scale_change"] = 0 # 消费掉这一次缩放输入

        # --------------------------------------------------------
        # 渲染层 (保持原样不变)
        # --------------------------------------------------------
        # 1. 独立运行并绘制：鼠标拖尾粒子系统
        trail_system.update_and_spawn(mouse_x, mouse_y)
        trail_system.draw(frame)

        # 2. 独立运行并绘制：3D 弹性球体粒子系统
        pixel_ball.update((mouse_x, mouse_y), is_left_clicked)
        pixel_ball.draw(frame)

        # HUD 信息看板
        cv2.putText(frame, f"VOLUME SCALE: {pixel_ball.current_scale * 100:.0f}%", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"CONTROL MODE: PHONE REMOTE", (20, 65), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(15) & 0xFF == 27:  
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()