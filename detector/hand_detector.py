# ==========================================
# 手部关键点提取模块 (detector/hand_detector.py)
# ==========================================
# 适配 MediaPipe 0.10.x 新 API — 用 OpenCV 自绘骨骼线
# ==========================================
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandDetector:
    # ---------- 手部关节点连接关系（21 个点，连线绘制骨架） ----------
    _CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),          # 大拇指
        (0, 5), (5, 6), (6, 7), (7, 8),           # 食指
        (0, 9), (9, 10), (10, 11), (11, 12),      # 中指
        (0, 13), (13, 14), (14, 15), (15, 16),     # 无名指
        (0, 17), (17, 18), (18, 19), (19, 20),    # 小拇指
        (5, 9), (9, 13), (13, 17),                 # 掌心横线
    ]

    _JOINT_COLOR = (0, 255, 0)      # 关节点 — 绿色
    _BONE_COLOR = (0, 200, 0)       # 骨骼线 — 深绿色
    _JOINT_RADIUS = 3

    def __init__(self, model_path, max_hands=1,
                 min_detection_confidence=0.7, min_tracking_confidence=0.6):
        print(f"[INFO] 正在加载 MediaPipe 模型: {model_path} ...")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.detector = vision.HandLandmarker.create_from_options(options)
        self.last_timestamp_ms = 0
        print("[SUCCESS] 手部关键点检测模型加载完成！")

    # ----------------------------------------------------------------
    # 公共接口
    # ----------------------------------------------------------------
    def process(self, frame, draw_skeleton=True):
        """
        输入 BGR 帧，返回 (关键点列表, 标注帧)
        关键点列表中每一项是对应一只手的 21 个 NormalizedLandmark
        """
        # 1. BGR → RGB 后包装为 MediaPipe Image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 2. 递增时间戳（VIDEO 模式要求严格递增）
        current_timestamp_ms = int(time.time() * 1000)
        if current_timestamp_ms <= self.last_timestamp_ms:
            current_timestamp_ms = self.last_timestamp_ms + 1
        self.last_timestamp_ms = current_timestamp_ms

        # 3. 推理
        detection_result = self.detector.detect_for_video(
            mp_image, current_timestamp_ms
        )
        landmarks_list = detection_result.hand_landmarks  # list[list[NormalizedLandmark]]

        # 4. 可视化 — 用 OpenCV 直接绘制（不再依赖 mediapipe.solutions 旧 API）
        annotated_frame = frame.copy()
        if draw_skeleton and landmarks_list:
            for hand_landmarks in landmarks_list:
                self._draw_hand(annotated_frame, hand_landmarks)

        return landmarks_list, annotated_frame

    # ----------------------------------------------------------------
    # 私有：手部骨架绘制
    # ----------------------------------------------------------------
    def _draw_hand(self, img, landmarks):
        h, w = img.shape[:2]

        # 收集 21 个点的像素坐标
        points = []
        for lm in landmarks:
            px, py = int(lm.x * w), int(lm.y * h)
            points.append((px, py))

        # 绘制骨骼连线
        for start_idx, end_idx in self._CONNECTIONS:
            cv2.line(img, points[start_idx], points[end_idx],
                     self._BONE_COLOR, 1, cv2.LINE_AA)

        # 绘制关节点
        for px, py in points:
            cv2.circle(img, (px, py), self._JOINT_RADIUS,
                       self._JOINT_COLOR, -1, cv2.LINE_AA)
