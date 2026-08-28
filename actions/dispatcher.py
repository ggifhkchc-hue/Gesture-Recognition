# ==========================================
# 动作分发调度器 (actions/dispatcher.py)
# ==========================================
import config
from actions.mouse_action import MouseAction
from actions.ball_action import BallAction   # 新增

class ActionDispatcher:
    def __init__(self):
        # 1. 注册并初始化所有可用的动作控制插件
        # 这里的 key 对应 config.py 的 mapping 值，value 是动作插件的实例化对象[cite: 1]
        self.actions_registry = {
            'mouse_move': MouseAction(),
            'mouse_click': MouseAction(),
            # 后面新增 PPT 或音量插件后，直接在这里实例化挂载：
            # 'volume_control': VolumeAction(),
            # 'ppt_control': PPTAction(),
            'ball_control': BallAction(),   # 新增
        }

    def execute(self, gesture_id, landmarks):
        """
        核心分发：根据 config 中的配置关系，将手势 ID 派发到具体的插件[cite: 1]
        """
        # 从配置中查找该手势映射到了哪个动作
        action_name = config.GESTURE_ACTION_MAPPING.get(gesture_id)
        
        if not action_name:
            return  # 如果该手势未绑定任何动作，忽略

        # 获取对应的插件对象
        action_plugin = self.actions_registry.get(action_name)
        
        if action_plugin:
            try:
                # 驱动该插件干活[cite: 1]
                action_plugin.execute(gesture_id, landmarks)
            except Exception as e:
                print(f"[DISPATCHER ERROR] 插件 {action_name} 执行失败: {e}")
