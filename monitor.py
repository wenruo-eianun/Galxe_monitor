import json
import os
import time
import requests
from datetime import datetime, timedelta # [新增] 導入 timedelta 用於時間計算
import threading
from flask import Flask, render_template_string
import sys # [新增] 導入 sys 以便在出錯時安全退出

# --- 您原有的全域變數 ---
CONFIG_FILE = "config.json"
PUSH_LOG_FILE = "pushed_campaigns.json"
GRAPHQL_URL = "https://graphigo.prd.galaxy.eco/query"

# --- [新增] 用於在後台和網頁間共享數據 ---
campaign_data_store = {}
token_status_store = {
    "expires_in_str": "未設定時間",
    "is_expiring_soon": False
}

# --- Flask 應用定義 ---
app = Flask(__name__)
HTML_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="90">
    <title>Galxe 任务监控面板 by eianun</title>
    <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg-dark: #12121b; --primary-dark: #1d1d2b; --secondary-dark: #2a2a3e; --primary-purple: #9333ea; --secondary-purple: #a855f7; --text-light: #e5e7eb; --text-muted: #9ca3af; --border-color: #374151; --warning-yellow: #facc15; }
        body { font-family: 'Noto Sans SC', sans-serif; line-height: 1.6; background-color: var(--bg-dark); color: var(--text-light); margin: 0; padding: 2rem 1rem; }
        .container { max-width: 1400px; margin: auto; }
        .header h1 { font-size: 2.5rem; font-weight: 700; color: white; background: -webkit-linear-gradient(45deg, var(--primary-purple), var(--secondary-purple)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { font-size: 1rem; color: var(--text-muted); }
        .grid-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 2rem; }
        .space-card, .token-card { background-color: var(--primary-dark); border-radius: 12px; border: 1px solid var(--border-color); transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .space-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.2), 0 0 20px var(--primary-purple); }
        .card-header { height: 150px; background-size: cover; background-position: center; position: relative; display: flex; align-items: flex-end; padding: 1rem; color: white; }
        .card-header::after { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%); }
        .card-header-content { display: flex; align-items: center; z-index: 1; }
        .card-header-content img { width: 48px; height: 48px; border-radius: 50%; margin-right: 1rem; border: 2px solid var(--border-color); }
        .card-header-content h2 { margin: 0; font-size: 1.75rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.7); }
        .campaign-count { font-size: 1rem; font-weight: 500; margin-left: 0.75rem; opacity: 0.8; }
        .card-body { padding: 1.5rem; }
        .token-card { padding: 1.5rem; text-align: center; margin-bottom: 2rem; }
        .token-card h3 { margin-top: 0; color: var(--text-muted); font-weight: 500; }
        .token-timer { font-size: 2rem; font-weight: 700; color: var(--text-light); }
        .token-timer.expiring { color: var(--warning-yellow); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; }
        a { color: var(--secondary-purple); text-decoration: none; } a:hover { text-decoration: underline; }
        .status-Active { color: #22c55e; font-weight: bold; } .status-NotStarted { color: #f97316; font-weight: bold; }
        .footer { text-align: center; margin-top: 3rem; padding: 1rem; color: var(--text-muted); font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header" style="text-align: center; margin-bottom: 2rem;">
            <h1>Galxe 任务监控面板</h1> <p>由 eianun 搭建测试</p>
        </div>
        <div class="token-card">
            <h3>Access Token 剩餘有效時間</h3>
            <div class="token-timer {{ 'expiring' if token_status.is_expiring_soon else '' }}">
                {{ token_status.expires_in_str }}
            </div>
        </div>
        <div class="grid-container">
        {% for space_id, data in spaces_data.items() %}
            <div class="space-card">
                <div class="card-header" style="background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), {% if data.thumbnail %}url('{{ data.thumbnail }}'){% else %}linear-gradient(45deg, #2d3748, #4a5568){% endif %};">
                    <div class="card-header-content">
                        <img src="{{ data.thumbnail }}" alt="{{ data.name }}">
                        <h2>{{ data.name }} <span class="campaign-count">({{ data.campaigns|length }} 個活動)</span></h2>
                    </div>
                </div>
                <div class="card-body">
                    <table>
                        <thead><tr><th>活動名稱</th><th>狀態</th><th>結束時間 (UTC)</th></tr></thead>
                        <tbody>
                        {% for c in data.campaigns %}
                            <tr>
                                <td><a href="https://galxe.com/{{ space_id }}/campaign/{{ c.id }}" target="_blank" title="{{c.name}}">{{ c.name[:30] }}{% if c.name|length > 30 %}...{% endif %}</a></td>
                                <td class="status-{{ c.status }}">{{ c.status }}</td>
                                <td>{{ format_time(c.endTime) }}</td>
                            </tr>
                        {% else %}
                            <tr><td colspan="3" style="text-align: center; color: var(--text-muted);">暫無進行中的活動</td></tr>
                        {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        {% endfor %}
        </div>
        <div class="footer">頁面每 90 秒自動刷新 | Powered by eianun</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, spaces_data=campaign_data_store, token_status=token_status_store, format_time=format_time)

# --- 您原有的函式 (僅在 query 中增加 thumbnail) ---

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("❌ 未找到 config.json，请先运行 setup.py")
        sys.exit(1)
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_push_log():
    if os.path.exists(PUSH_LOG_FILE):
        with open(PUSH_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_push_log(log):
    with open(PUSH_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=4, ensure_ascii=False)

def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        # [修改] 將 parse_mode 改為 HTML 以支援提醒訊息中的粗體和程式碼格式
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    except Exception as e:
        print(f"❌ Telegram 推送失败: {e}")

def send_discord(webhook_url, message):
    try:
        requests.post(webhook_url, json={"content": message})
    except Exception as e:
        print(f"❌ Discord 推送失败: {e}")

def query_space_campaigns(token, space_id):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    # [修改] 為了顯示圖片，在 space 查詢中增加了 thumbnail 欄位
    payload = {
        "query": """query($id: Int!, $input: ListCampaignInput!) {
            space(id: $id) {
                id
                name
                thumbnail
                campaigns(input: $input) {
                    list { id name status startTime endTime }
                }
            }
        }""",
        "variables": {
            "id": int(space_id),
            "input": {"first": 20, "statuses": ["Active", "NotStarted"]}
        }
    }
    try:
        r = requests.post(GRAPHQL_URL, headers=headers, json=payload, timeout=10)
        return r.json().get("data", {}).get("space", {})
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return {}

def format_time(ts):
    if ts is None: return "N/A"
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

# [修改] 您原有的 main 函式被重新命名為 monitor_loop，並增加了新功能
def monitor_loop():
    global campaign_data_store, token_status_store
    config = load_config()
    push_log = load_push_log()

    token = config["token"] if config["token"].startswith("Bearer ") else "Bearer " + config["token"]
    interval_sec = config.get("interval", 5) * 60

    # [新增] Token 過期計時變數
    token_update_ts = config.get("token_update_timestamp", 0)
    expiration_notified = False

    print("✅ Galxe 后台监控线程已启动")
    print(f"推送方式: {config.get('push_method', 'N/A')}")
    print(f"检查间隔: {config.get('interval', 5)} 分钟")

    while True:
        # --- [新增] Token 倒數計時與提醒邏輯 ---
        if token_update_ts > 0:
            now_ts = int(time.time())
            expire_ts = token_update_ts + (24 * 3600) # 24小時有效期
            remaining_seconds = expire_ts - now_ts
            
            if remaining_seconds > 0:
                hours = remaining_seconds // 3600
                minutes = (remaining_seconds % 3600) // 60
                token_status_store["expires_in_str"] = f"{hours} 小時 {minutes} 分鐘"
                token_status_store["is_expiring_soon"] = remaining_seconds < 3600 # 小於 1 小時
                
                # 檢查是否需要發送提醒
                if token_status_store["is_expiring_soon"] and not expiration_notified:
                    print("🟡 Token 即將在一小時內過期，準備發送提醒...")
                    alert_msg = "⚠️ <b>Galxe 監控提醒</b> ⚠️\n\nAccess Token 即將在 <b>1 小時</b>內過期，請運行 <code>setup.py</code> 更新以確保服務不中斷。"
                    if config.get("push_method") == "telegram":
                        send_telegram(config.get("push_config", {}).get("bot_token"), config.get("push_config", {}).get("chat_id"), alert_msg)
                    expiration_notified = True
            else:
                token_status_store["expires_in_str"] = "已過期"
                token_status_store["is_expiring_soon"] = True
        else:
            token_status_store["expires_in_str"] = "未設定時間"

        # --- 以下是您原有的監控邏輯 ---
        for sp in config["spaces"]:
            space_id = sp["id"]
            space_name = sp["name"]

            data = query_space_campaigns(token, space_id)
            if not data:
                print(f"🟡 未能獲取到 Space '{space_name}' ({space_id}) 的數據，跳過本次檢查。")
                continue
            
            campaigns = data.get("campaigns", {}).get("list", [])
            campaign_data_store[space_id] = {
                "name": data.get("name", space_name),
                "thumbnail": data.get("thumbnail"),
                "campaigns": campaigns,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if space_id not in push_log:
                push_log[space_id] = [c['id'] for c in campaigns]
                save_push_log(push_log)
                continue

            for c in campaigns:
                if c["id"] not in push_log[space_id]:
                    msg = (
                        f"📢 *{data.get('name', space_name)}* 有新活動！\n\n"
                        f"**名稱**: {c['name']}\n"
                        f"**狀態**: {c['status']}\n"
                        f"**結束**: {format_time(c['endTime'])} (UTC)\n\n"
                        f"🔗 [點擊參與](https://galxe.com/{space_id}/campaign/{c['id']})"
                    )

                    print(f"✔️ 檢測到新活動: {space_name} - {c['name']}，準備推送...")
                    if config["push_method"] == "telegram":
                        send_telegram(config["push_config"]["bot_token"], config["push_config"]["chat_id"], msg)
                    elif config["push_method"] == "discord":
                        discord_msg = msg.replace("*", "**") 
                        send_discord(config["push_config"]["webhook_url"], discord_msg)
                    else:
                        print(f"[新活動] {space_name} - {c['name']}")

                    push_log[space_id].append(c["id"])
                    save_push_log(push_log)
        
        print(f"--- 所有 Space 檢查完畢，休眠 {config.get('interval', 5)} 分鐘 ---")
        time.sleep(interval_sec)

# [修改] 新的程式啟動入口
if __name__ == "__main__":
    # 將您原有的 main 函式放入後台執行緒
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()

    print("✅ eianun 網頁服務已啟動")
    print("👉 請在瀏覽器中打開 http://您的伺服器IP:5001")
    app.run(host='0.0.0.0', port=5001)
