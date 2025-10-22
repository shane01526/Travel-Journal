# 🌍 Travel Journal - 旅行日誌

一個優雅的旅行日誌應用程式，讓你記錄每一段旅程，並在互動式地圖上追蹤你的足跡。

## ✨ 主要功能

- 📝 **日誌記錄**：撰寫詳細的旅行日誌
- 🗺️ **互動地圖**：在地圖上標記並查看所有旅行地點
- 📍 **座標搜尋**：內建地點搜尋功能，輕鬆找到座標
- 🌏 **國家統計**：追蹤造訪過的國家數量
- 🔐 **用戶認證**：安全的登入註冊系統
- 📱 **響應式設計**：支援手機、平板、電腦

## 🚀 快速開始

### 1. 環境需求

- Python 3.11+
- PostgreSQL 資料庫（推薦 Supabase）

### 2. 安裝步驟

```bash
# 克隆專案
git clone https://github.com/your-username/Travel-Journal.git
cd Travel-Journal

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，填入你的資料庫密碼
```

### 3. 設定 Supabase 資料庫

在 `.env` 檔案中設定：

```bash
SUPABASE_DB_PASSWORD=your-actual-password-here
```

或直接使用完整連接字串：

```bash
DATABASE_URL=postgresql://postgres:your-password@db.rtfdfsvqigdiadnffcxs.supabase.co:5432/postgres
```

### 4. 執行應用程式

```bash
# 本地開發
python app.py

# 或使用 gunicorn（生產環境）
gunicorn app:app
```

訪問 `http://localhost:5000`

## 🌐 部署到 Render

### 方式 1：使用 render.yaml（推薦）

1. 將專案推送到 GitHub
2. 在 Render 建立新的 Web Service
3. 連接你的 GitHub 儲存庫
4. Render 會自動偵測 `render.yaml` 並建立服務

### 方式 2：手動設定

1. **建立 Web Service**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

2. **建立 PostgreSQL 資料庫**
   - 或使用 Supabase

3. **設定環境變數**
   ```
   SECRET_KEY=自動生成
   DATABASE_URL=你的資料庫連接字串
   或
   SUPABASE_DB_PASSWORD=你的 Supabase 密碼
   ```

## 📁 專案結構

```
Travel-Journal/
├── app.py                 # 主應用程式
├── requirements.txt       # Python 依賴
├── runtime.txt           # Python 版本
├── Procfile              # Heroku/Render 設定
├── .env.example          # 環境變數範例
├── templates/            # HTML 模板
│   ├── welcome.html      # 歡迎頁面
│   ├── login.html        # 登入頁面
│   ├── register.html     # 註冊頁面
│   ├── dashboard.html    # 主控台（互動地圖）
│   ├── add_journal.html  # 新增日誌
│   ├── 404.html          # 404 錯誤頁
│   └── 500.html          # 500 錯誤頁
└── README.md             # 專案說明
```

## 🔧 主要技術

- **後端**：Flask 3.0, SQLAlchemy
- **資料庫**：PostgreSQL (Supabase)
- **前端**：TailwindCSS, Leaflet.js
- **地圖**：OpenStreetMap
- **地點搜尋**：Nominatim API

## 📝 功能說明

### 1. 歡迎頁面優化
- 文藝風格的宣傳文字
- 清晰的登入/註冊入口
- 快速 Google 登入選項

### 2. 新增日誌功能
- **座標搜尋**：輸入地點名稱自動查詢經緯度
- **互動地圖**：點擊地圖直接選擇位置
- **外部連結**：提供 LatLong.net 和 Google Maps 連結
- 自動儲存日期、地點、國家和內容

### 3. 互動式地圖
- 自動標記所有日誌地點
- 點擊標記查看日誌詳細內容
- 地圖彈窗顯示：
  - 地點名稱
  - 日期和國家
  - 日誌內容預覽
- 從日誌列表直接定位到地圖標記

### 4. 資料庫連接
- 支援 Supabase PostgreSQL
- 使用環境變數安全管理密碼
- 自動連線池管理

## 🎨 使用範例

### 新增一篇日誌

1. 登入後點擊「新增日誌」
2. 填寫日期、地點、國家
3. 使用座標搜尋功能：
   - 輸入 "Eiffel Tower, Paris" 
   - 點擊「搜尋」按鈕
   - 自動填入經緯度
4. 或直接在地圖上點擊位置
5. 撰寫日誌內容
6. 點擊「儲存日誌」

### 查看日誌

1. 在主控台地圖上查看所有標記
2. 點擊標記查看日誌彈窗
3. 或在下方列表瀏覽所有日誌
4. 點擊「定位」按鈕跳轉到地圖標記

## 🔒 安全性

- 密碼使用 Werkzeug 加密儲存
- Session 管理用戶狀態
- 環境變數保護敏感資訊
- CSRF 保護（Flask 內建）

## 🐛 常見問題

### Q: 座標搜尋找不到地點？
A: 
- 使用英文地點名稱
- 加入城市或國家（例如：Tokyo Tower, Japan）
- 使用提供的外部連結查詢

### Q: 地圖沒有顯示標記？
A: 
- 確認日誌有填寫座標（非 0,0）
- 檢查瀏覽器主控台是否有錯誤
- 重新整理頁面

### Q: 資料庫連接失敗？
A: 
- 檢查 `.env` 檔案設定
- 確認 Supabase 密碼正確
- 查看應用程式日誌

### Q: 日誌無法新增？
A: 
- 檢查所有必填欄位
- 查看瀏覽器主控台錯誤訊息
- 確認已登入

## 📈 未來功能規劃

- [ ] 圖片上傳功能
- [ ] 日誌標籤和分類
- [ ] 匯出 PDF 功能
- [ ] 社群分享功能
- [ ] 多語言支援
- [ ] 行程規劃功能

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

## 📄 授權

MIT License

## 👨‍💻 開發者

由 shane01526 開發

---

## 🚨 重要更新說明

### 最新版本功能

✅ **已完成**
1. 優化歡迎頁面設計
2. 整合 Supabase PostgreSQL 資料庫
3. 修復日誌新增功能
4. 新增座標搜尋功能（Nominatim API）
5. 互動式地圖標記點擊查看日誌
6. 從日誌列表定位到地圖標記

### 環境變數設定重點

在 Render 或本地 `.env` 檔案中設定：

```bash
# 方式 1：使用 Supabase 密碼
SUPABASE_DB_PASSWORD=你的密碼

# 方式 2：使用完整連接字串
DATABASE_URL=postgresql://postgres:你的密碼@db.rtfdfsvqigdiadnffcxs.supabase.co:5432/postgres
```

應用程式會自動選擇合適的連接方式。

## 📞 聯絡方式

如有問題或建議，歡迎聯絡！
