# Galxe 活動監控機械人 (Galxe Campaign Monitor Bot)

一個功能強大且高度可自訂的 Galxe 活動監控工具，旨在自動追蹤您喜愛的項目 (Space) 的最新活動 (Campaigns)，並透過 Telegram 和 Discord 即時推送通知。它還內建了一個美觀的網頁監控面板，讓您隨時掌握所有動態。

[專案截圖][https://servootc.iqq.pp.ua/2025/08/13/832548.webp]

---

## ✨ 核心功能

* **多專案監控**: 可同時監控任意數量的 Galxe Space。
* **即時推送通知**:
    * 支援 **Telegram** 推送。
    * 支援 **Discord Webhook** 推送。
* **視覺化網頁面板**:
    * 採用 Galxe 風格的暗色主題，介面美觀。
    * 以卡片形式清晰展示每個 Space 的資訊。
    * 顯示專案 Logo、進行中/未開始的活動總數。
    * 詳細列出每個活動的名稱、狀態和結束時間。
* **Access Token 到期提醒**:
    * 自動記錄 Token 更新時間，並在網頁上顯示 24 小時倒數計時。
    * 在 Token 到期前 1 小時，會透過 Telegram 自動發送提醒，實現半自動化維護。
* **高可設定性**:
    * 透過互動式的設定精靈 (`setup.py`)，輕鬆完成所有配置。
    * 可自訂檢查頻率。
* **穩定可靠**:
    * 透過日誌檔案 (`pushed_campaigns.json`) 防止重複推送通知。
    * 後台執行緒與網頁服務分離，確保穩定運行。

## 🛠️ 技術棧

* **後端**: Python 3
* **網頁框架**: Flask
* **API 互動**: Requests
* **背景任務**: threading

## 🚀 如何開始

### 環境要求

* 一台 Linux VPS (建議使用 Debian/Ubuntu)
* Python 3.x
* pip

### 1. 複製專案

```bash
git clone [您的 GitHub Repo URL]
cd [您的專案資料夾名稱]
```

### 2. 安裝依賴

```bash
pip3 install requests flask
```

### 3. 執行互動式設定

運行設定精靈，並按照提示輸入您的個人配置資訊：

```bash
python3 setup.py
```
您需要準備：
* 您的 Galxe Access Token
* Telegram Bot Token 和 Chat ID (如果您選擇 Telegram 推送)
* Discord Webhook URL (如果您選擇 Discord 推送)
* 您想監控的 Galxe Space ID 和自訂名稱

### 4. 啟動監控服務

建議使用 `nohup` 來讓腳本在背景永久運行。

```bash
nohup python3 monitor.py > monitor.log 2>&1 &
```

### 5. 訪問監控面板

打開您的瀏覽器，訪問 `http://<您的伺服器 IP>:5001`，即可看到您的個人化監控面板。



---
*由 eianun 強力驅動*
