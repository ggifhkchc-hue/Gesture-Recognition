# ==========================================
# GestureControl 主入口文件 (main.py)
# ==========================================
import cv2
import time
import config

# --- 1. 导入感知层模块 (严格匹配大小写) ---
# 模块名（文件名）是小写 camera，类名是大写 Camera
from detector.camera import Camera
from detector.hand_detector import HandDetector

# --- 2. 识别层与动作层模块 ---
from recognizer.gesture import GestureEngine
from actions.dispatcher import ActionDispatcher

def main():
    print("[INFO] ---------------------------------------")
    print("[INFO] 正在启动智能手势控制系统...")
    print("[INFO] ---------------------------------------")
    
    # ----------------------------------------------------
    # 第一步：初始化系统组件
    # ----------------------------------------------------
    try:
        # 初始化并启动摄像头（Camera 类实例化）
        camera = Camera().start()
        
        # 初始化 MediaPipe 手部关键点检测器 (HandDetector 类实例化)
        detector = HandDetector(
            model_path=config.MODEL_PATH,
            max_hands=config.MAX_NUM_HANDS,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        
        # 初始化手势识别器和动作分发器
        gesture_engine = GestureEngine()
        action_dispatcher = ActionDispatcher()
        
    except Exception as e:
        print(f"[ERROR] 系统初始化失败: {e}")
        return

    print("[SUCCESS] 所有感知模块加载完毕！")
    print("[INFO] 请将手掌举至摄像头前，按键盘上的 'q' 键可安全退出程序。")

    # 用于计算实时帧率 (FPS) 的时间戳变量
    prev_time = 0

    # ----------------------------------------------------
    # 第二步：主程序循环 (Video Processing Pipeline)
    # ----------------------------------------------------
    try:
        while True:
            # 1. 读取实时视频帧
            success, frame = camera.read_frame()
            if not success:
                print("[WARNING] 无法读取视频流帧，正在尝试重新获取...")
                time.sleep(0.01)
                continue

            # 2. 提取手部关键点并绘制骨骼线
            # landmarks_list 包含检测到的手部 21 个归一化三维坐标 [x, y, z]
            # annotated_frame 是已经画好绿色关节点和连线的画面
            landmarks_list, annotated_frame = detector.process(
                frame, 
                draw_skeleton=config.SHOW_UI
            )
            
            # 3. 手势识别与动作触发生命周期 (暂时挂起，下阶段接入)
            gesture_id = "WAITING..."  # 默认待机状态
            
            if landmarks_list:
                # 获取第一只手的数据（控制系统默认使用主手）
                primary_hand = landmarks_list[0]

                # 在画面上标记当前的识别状态
                cv2.putText(annotated_frame, f"Hands Detected: {len(landmarks_list)}",
                            (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                # 接入核心手势分类与动作分发逻辑
                gesture_id = gesture_engine.recognize(primary_hand)
                action_dispatcher.execute(gesture_id, primary_hand)

            # 4. 计算并绘制实时系统性能 (FPS)
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time

            if config.SHOW_UI:
                # 绘制 FPS
                cv2.putText(annotated_frame, f"FPS: {int(fps)}", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                # 绘制当前动作指令
                cv2.putText(annotated_frame, f"Action: {gesture_id}", (20, 85), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 200, 0), 2)

            # 5. 渲染展示窗口
            cv2.imshow("Gesture Control System - Live View", annotated_frame)

            # 6. 监听键盘事件：按 'q' 键退出主循环
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n[INFO] 接收到退出指令，正在终止程序...")
                break

    except KeyboardInterrupt:
        print("\n[INFO] 用户强制中断程序 (Ctrl+C)...")
    except Exception as e:
        print(f"\n[ERROR] 运行时发生异常: {e}")
    finally:
        # ----------------------------------------------------
        # 第三步：安全释放硬件资源
        # ----------------------------------------------------
        camera.release()
        cv2.destroyAllWindows()
        print("[INFO] 摄像头及窗口资源已彻底释放，程序安全关闭。")

if __name__ == '__main__':
    main()