# ==========================================
# 图像采集模块 (detector/camera.py)
# ==========================================
import cv2
import config

class Camera:  # <--- 确保 C 是大写的，且拼写完全一致！
    def __init__(self, camera_id=config.CAMERA_ID, width=config.FRAME_WIDTH, height=config.FRAME_HEIGHT, mirror=config.MIRROR_FRAME):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.mirror = mirror
        self.cap = None

    def start(self):
        """启动摄像头（支持本地ID或手机IP流URL）"""
        # OpenCV 支持直接传入URL作为VideoCapture参数
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"[ERROR] 无法打开摄像头/视频流 (source: {self.camera_id})！\n"
                             f"如果是手机摄像头，请确保App已开启流服务（如DroidCam/IP Webcam），并在config.py中填写正确URL。")
        
        # 尝试设置期望的分辨率（对IP流效果可能有限）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        source_type = "本地摄像头" if isinstance(self.camera_id, int) else f"手机IP流 ({self.camera_id})"
        print(f"[INFO] 摄像头已启动 -> {source_type}, 分辨率: {self.width}x{self.height}")
        return self

    def read_frame(self):
        """读取一帧图像，返回 (成功标记, 帧数据)"""
        if not self.cap or not self.cap.isOpened():
            return False, None
        
        success, frame = self.cap.read()
        if not success:
            return False, None
            
        # 如果开启了镜像显示，进行水平翻转
        if self.mirror:
            frame = cv2.flip(frame, 1)
            
        return True, frame

    def release(self):
        """释放摄像头资源"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print("[INFO] 摄像头资源已安全释放。")