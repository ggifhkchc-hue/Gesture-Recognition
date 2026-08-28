# ==========================================
# 核心手势识别逻辑 (recognizer/gesture.py)
# ==========================================

class GestureEngine:
    def __init__(self):
        pass

    def recognize(self, landmarks):
        """
        输入单只手 21 个关键点归一化坐标列表
        返回识别出的手势标签字符串，例如：'FIST', 'POINT_UP', 'OPEN_PALM', 'UNKNOWN'
        """
        if not landmarks:
            return "UNKNOWN"

        # 1. 判断各个手指的伸直（Up）/ 弯曲（Down）状态
        # 0:大拇指, 1:食指, 2:中指, 3:无名指, 4:小拇指
        finger_states = [False] * 5

        # --- 大拇指 (Thumb) ---
        # 比较大拇指尖（4）与大拇指关节（3/2）的 X 轴距离（假设右手，左手逻辑镜像）
        # 这里使用简单逻辑：指尖与第2关节的水平距离
        if abs(landmarks[4].x - landmarks[2].x) > 0.05:
            finger_states[0] = True

        # --- 食指 (Index Finger) ---
        # 比较指尖（8）与 PIP 关节（6）的 Y 轴高度。Y 越小代表在屏幕上方。
        if landmarks[8].y < landmarks[6].y:
            finger_states[1] = True

        # --- 中指 (Middle Finger) ---
        # 比较指尖（12）与 PIP 关节（10）的 Y 轴高度
        if landmarks[12].y < landmarks[10].y:
            finger_states[2] = True

        # --- 无名指 (Ring Finger) ---
        # 比较指尖（16）与 PIP 关节（14）的 Y 轴高度
        if landmarks[16].y < landmarks[14].y:
            finger_states[3] = True

        # --- 小拇指 (Pinky Finger) ---
        # 比较指尖（20）与 PIP 关节（18）的 Y 轴高度
        if landmarks[20].y < landmarks[18].y:
            finger_states[4] = True


        # 2. 根据手指状态组合，匹配具体手势
        # [大拇指, 食指, 中指, 无名指, 小拇指]

        # 2.1 握拳 (FIST) -> 全弯曲
        if not any(finger_states):
            return "FIST"

        # 2.2 张开手掌 (OPEN_PALM) -> 全伸直
        if all(finger_states):
            return "OPEN_PALM"

        # 2.3 伸出食指 (POINT_UP) -> 仅食指伸直
        if finger_states[1] and not any([finger_states[0], finger_states[2], finger_states[3], finger_states[4]]):
            return "POINT_UP"

        # 2.4 剪刀手 (VICTORY) -> 仅食指和中指伸直
        if finger_states[1] and finger_states[2] and not any([finger_states[0], finger_states[3], finger_states[4]]):
            return "VICTORY"

        # 2.5 捏合手势 (PINCH) -> 食指和大拇指很近，其他手指弯曲 (特殊判断)
        # 计算大拇指尖（4）与食指尖（8）之间的欧氏距离
        dist_thumb_index = self._calculate_distance(landmarks[4], landmarks[8])
        if dist_thumb_index < 0.05 and not any([finger_states[2], finger_states[3], finger_states[4]]):
            return "PINCH"

        # 未匹配到已知手势
        return "UNKNOWN"

    def _calculate_distance(self, p1, p2):
        """计算两个三维空间点之间的欧氏距离"""
        return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2) ** 0.5