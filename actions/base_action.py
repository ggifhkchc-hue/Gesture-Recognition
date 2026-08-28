# ==========================================
# 动作插件基类 (actions/base_action.py)
# ==========================================

class BaseAction:
    def __init__(self):
        self.cooldown_tracker = {}  # 用于处理每个手势的动作冷却，防止抖动触发多次

    def execute(self, gesture_id, landmarks):
        """
        子类必须实现此方法以执行具体的动作逻辑
        :param gesture_id: 当前识别到的手势字符串
        :param landmarks: 21个手部关键点数据，便于动作提取精细物理坐标（如鼠标位置）
        """
        raise NotImplementedError("所有的动作插件必须实现 execute 接口！[cite: 1]")