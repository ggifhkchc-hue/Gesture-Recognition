# test/app.py
from flask import Flask, render_template_string
from flask_sock import Sock
import json
import socket
import qrcode
import threading

app = Flask(__name__)
sock = Sock(app)

# 全局存储最新的手机控制数据
phone_data = {
    "x_pct": 0.5,      # 手指在手机屏幕X轴的百分比位置
    "y_pct": 0.5,      # 手指在手机屏幕Y轴的百分比位置
    "is_touching": False, # 是否触摸（相当于鼠标左键按下）
    "scale_change": 0  # 缩放变化量（双指放大缩小）
}

# 手机访问的摇杆/触摸板网页 HTML  const
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>手机粒子控制器</title>
    <style>
        body { margin: 0; overflow: hidden; background: #111; font-family: sans-serif; color: #fff; touch-action: none; }
        #pad { width: 100vw; height: 85vh; background: #222; border-bottom: 2px solid #444; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #666; position: relative;}
        #info { height: 15vh; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 14px; }
        #status { color: #0f0; }
    </style>
</head>
<body>
    <div id="pad">【 触摸板：在此处滑动/单指按压/双指缩放 】</div>
    <div id="info">
        <div>连接状态: <span id="status">连接中...</span></div>
        <div id="debug">X: 0, Y: 0</div>
    </div>

    <script>
        // 自动建立 WebSocket 连接
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(protocol + '//' + location.host + '/control');
        
        ws.onopen = () => { document.getElementById('status').innerText = '已连接电脑'; };
        ws.onclose = () => { document.getElementById('status').innerText = '已断开'; };

        const pad = document.getElementById('pad');
        const debug = document.getElementById('debug');
        
        let initialDist = 0; // 用于双指缩放记录

        function sendData(xPct, yPct, isTouching, scaleChange = 0) {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(json = JSON.stringify({
                    x_pct: xPct,
                    y_pct: yPct,
                    is_touching: isTouching,
                    scale_change: scaleChange
                }));
            }
        }

        // 监听单指滑动与按压
        pad.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                let touch = e.touches[0];
                let xPct = touch.clientX / window.innerWidth;
                let yPct = touch.clientY / pad.clientHeight;
                debug.innerText = `X: ${Math.round(xPct*100)}%, Y: ${Math.round(yPct*100)}%`;
                sendData(xPct, yPct, true, 0);
            } 
            // 监听双指手势（缩放球体）
            else if (e.touches.length === 2) {
                let dist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                if (initialDist > 0) {
                    let change = (dist - initialDist) > 0 ? 1 : -1;
                    // 只有显著变化才发送缩放信号
                    if (Math.abs(dist - initialDist) > 5) {
                        sendData(0.5, 0.5, false, change);
                        initialDist = dist; 
                    }
                } else {
                    initialDist = dist;
                }
            }
        });

        pad.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                initialDist = 0;
                sendData(e.touches[0].clientX / window.innerWidth, e.touches[0].clientY / pad.clientHeight, true, 0);
            }
        });

        pad.addEventListener('touchend', () => {
            initialDist = 0;
            sendData(0.5, 0.5, false, 0); // 手指抬起，粒子回弹
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@sock.route('/control')
def control(ws):
    global phone_data
    while True:
        msg = ws.receive()
        try:
            data = json.loads(msg)
            phone_data["x_pct"] = data.get("x_pct", 0.5)
            phone_data["y_pct"] = data.get("y_pct", 0.5)
            phone_data["is_touching"] = data.get("is_touching", False)
            
            # 滚轮缩放数据做累加缓冲
            sc = data.get("scale_change", 0)
            if sc != 0:
                phone_data["scale_change"] = sc
        except:
            pass

def get_local_ip():
    """获取电脑在局域网的本地IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def run_server():
    local_ip = get_local_ip()
    port = 5000
    url = f"http://{local_ip}:{port}"
    
    print("\n" + "="*50)
    print(f" 📱 手机局域网控制器已启动！")
    print(f" 请确保手机和电脑连接了【同一个家庭网络/WiFi】")
    print(f" 请使用手机浏览器访问： {url}")
    print("="*50 + "\n")
    
    # 终端直接打印二维码，手机扫码即可
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# 暴露给主程序调用的接口
def start_control_server():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()