import json
import os
import requests
import time # [新增] 導入 time 模組以獲取時間戳

CONFIG_FILE = "config.json"

def get_existing_config():
    """載入現有設定，如果不存在則返回範本"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "push_method": "",
        "push_config": {},
        "token": "",
        "token_update_timestamp": 0, # [新增] 為新設定檔增加預設值
        "interval": 5,
        "spaces": []
    }

def prompt_for_new_space():
    """提示使用者輸入一個新的監控 Space 資訊"""
    space_name = input("請輸入此任務的名稱（例如 'Project Alpha'）: ").strip()
    space_id = input(f"請輸入 '{space_name}' 的 Galxe Space ID: ").strip()
    return {"name": space_name, "id": space_id}

def test_access_token(token, space_id):
    """檢測 Access Token 是否有效"""
    url = "https://graphigo.prd.galaxy.eco/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": """query($id: Int!) {
            space(id: $id) {
                id
                name
            }
        }""",
        "variables": {
            "id": int(space_id)
        }
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "data" in data and "space" in data.get("data", {}) and data["data"]["space"] is not None:
             return True
        else:
             print(f"❌ Galxe API 返回錯誤: {data.get('errors')}")
             return False
    except requests.exceptions.Timeout:
        print("❌ 請求逾時，請檢查網路或稍後再試。")
        return False
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ 發生 HTTP 錯誤: {http_err} - 回應內容: {http_err.response.text}")
        return False
    except ValueError:
        print(f"❌ 無法解析伺服器回應，請檢查 Galxe API 狀態。")
        return False
    except Exception as e:
        print(f"❌ 驗證請求期間發生未知錯誤: {e}")
        return False

def main():
    print("=== Galxe 監控任務設定精靈 ===")
    config = get_existing_config()

    # 推送方式 (您的原始邏輯)
    print("\n請選擇或確認推送方式：")
    print(f"  (當前: {config.get('push_method') or '未設定'})")
    print("  1. Telegram")
    print("  2. Discord")
    print("  3. 不推送（僅網頁查看）")
    print("  (直接按 Enter 跳過)")
    choice = input("輸入數字選擇: ").strip()
    
    if choice == "1":
        config["push_method"] = "telegram"
        config["push_config"] = {
            "bot_token": input("請輸入 Telegram Bot Token: ").strip(),
            "chat_id": input("請輸入 Telegram Chat ID: ").strip()
        }
    elif choice == "2":
        config["push_method"] = "discord"
        config["push_config"] = {
            "webhook_url": input("請輸入 Discord Webhook URL: ").strip()
        }
    elif choice == "3":
        config["push_method"] = "none"
        config["push_config"] = {}

    # Access Token (您的原始邏輯)
    print("\n請提供 Galxe Access Token（Bearer 後面的字串）")
    token_input = input(f"(直接按 Enter 使用現有Token): ").replace("Bearer ", "").strip()
    if token_input:
        config["token"] = token_input
        # --- 這是唯一增加的功能 ---
        config["token_update_timestamp"] = int(time.time())
        print("✅ Token 已更新，24 小時倒數計時器已重設。")
        # ------------------------

    # 檢查間隔 (您的原始邏輯)
    try:
        interval_input = input(f"請輸入檢查間隔（分鐘，當前 {config.get('interval', 5)}，直接按 Enter 跳過）: ").strip()
        if interval_input:
            config["interval"] = int(interval_input)
    except ValueError:
        print(f"輸入無效，將使用之前的間隔 {config['interval']} 分鐘。")

    # Space 管理 (您的原始邏輯)
    while True:
        print("\n=== 當前監控的 Space 列表 ===")
        if not config["spaces"]:
            print("（空）")
        else:
            for i, sp in enumerate(config["spaces"], start=1):
                print(f"{i}. {sp['name']} - ID: {sp['id']}")

        print("\n操作選項：")
        print("  1. 新增 Space")
        print("  2. 刪除 Space")
        print("  3. 完成並儲存配置")
        action = input("請選擇操作: ").strip()

        if action == "1":
            if not config.get("token"):
                print("❌ 請先設定 Access Token 再新增 Space。")
                time.sleep(2)
                continue
            sp = prompt_for_new_space()
            if not sp['name'] or not sp['id'] or not sp['id'].isdigit():
                print("❌ 名稱不能為空，ID 必須為純數字。")
                time.sleep(2)
                continue
            print("正在驗證 Access Token 與 Space ID...")
            if test_access_token(config["token"], sp["id"]):
                config["spaces"].append(sp)
                print(f"✅ 新增成功: {sp['name']}")
            else:
                print("❌ 新增失敗，請仔細檢查 Access Token 和 Space ID 是否正確且匹配。")
            time.sleep(1.5)
        elif action == "2":
            if not config["spaces"]:
                print("沒有可刪除的 Space。")
                time.sleep(1.5)
                continue
            try:
                idx = int(input("請輸入要刪除的編號: ").strip()) - 1
                if 0 <= idx < len(config["spaces"]):
                    removed = config["spaces"].pop(idx)
                    print(f"已刪除 {removed['name']}")
                else:
                    print("❌ 編號無效")
            except ValueError:
                print("❌ 請輸入數字")
            time.sleep(1.5)
        elif action == "3":
            break
        else:
            print("❌ 無效輸入")

    # 儲存配置 (您的原始邏輯)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"\n✅ 設定已儲存到 {CONFIG_FILE}")
    print("你可以運行主監控程式了。")

if __name__ == "__main__":
    main()
