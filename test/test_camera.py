import cv2
import time

URL = "http://10.163.93.164:4747/video"

print(f"正在连接: {URL}")
print("等待最多 8 秒...\n")

cap = cv2.VideoCapture()
cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 8000)   # 8秒超时

success = cap.open(URL)

if not success:
    print("❌ 连接失败！")
    print("\n可能原因和解决方案：")
    print("1. 手机和电脑**必须在同一个 WiFi**")
    print("2. DroidCam App 是否完全退出后重新打开？")
    print("3. 尝试用 USB 连接模式（推荐）")
    print("4. 尝试其他地址：http://10.163.93.164:4747/mjpeg")
else:
    print("✅ 连接成功！按 ESC 退出窗口")
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("DroidCam 测试", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()