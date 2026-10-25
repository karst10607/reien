# 🌸 Reien (霊園) ‧ 2.5D 溫馨線上靈園 & 庭園小鎮

> 一個重現《仙境傳說 RO》與《動物森友會》溫暖治癒風格的 2.5D 偽 3D 線上靈園、虛擬追思園與自建庭園小鎮。  
> 具備免安裝瀏覽器秒開、點擊走動、聖壇獻花點燈、親友追思信箱、以及完整的**自由建造庭園小鎮系統**。

[![Live Demo](https://img.shields.io/badge/Live%20Demo-%E7%8F%BE%E5%9C%A8%E5%85%8D%E5%AE%89%E8%A3%9D%E5%85%A5%E5%9C%92%E5%8F%83%E8%A8%AA-10b981?style=for-the-badge&logo=googlechrome&logoColor=white)](https://karst10607.github.io/reien/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Online-blue?style=for-the-badge)](https://karst10607.github.io/reien/)

### 🌐 線上即時參訪網址 (Live Visit Link)
👉 **[https://karst10607.github.io/reien/](https://karst10607.github.io/reien/)**  
*(手機、平板、電腦打開瀏覽器 3 秒內直接進入，免下載任何 App 即可漫步、獻花、點燈與自建花園)*

---

## 📸 實機畫面 (Live Screenshots)

### 1. 靈園與小鎮全景 (World Overview)
![靈園主世界全景](docs/screenshots/memorial_ui_full.png)
* **RO 經典 45° 斜俯視角 (Isometric)**：低多邊形（Low-poly）溫馨造景、石板路徑、中央守護聖壇、靜心蓮池與千本櫻花樹。
* **動態粒子氛圍**：空中飄拂的粉白落櫻花瓣粒子與螢火蟲。
* **RO 操作模式**：滑鼠點擊地面顯示經典綠色脈衝光圈，角色平滑前往；右下角具備坐下休息 (`/sit`)、祈願與思念表情。
* **雷達小地圖**：右上角即時顯示周圍景點與漫步旅人。

### 2. 庭園與小鎮建造模式 (Town & Garden Builder)
![庭園建造模式](docs/screenshots/town_builder_mode.png)
* **對齊網格系統 (Grid Snap)**：開啟建造模式後，地面亮起綠色網格，滑鼠游標帶有半透明預覽模型。
* **物件目錄庫 (Object Palette)**：
  * 🌸 **千本櫻花樹**（自帶花瓣飄落粒子）
  * 🌲 **高聳青松木**
  * ⛩️ **日式祈福木舍**（面向鏡頭半開放，內有暖心微光）
  * ⛪ **溫馨小教堂 / 靈骨紀念堂**
  * 🏮 **古樸石燈籠**（自帶夜間照明點光源）
  * 🪑 **原木休憩椅**
  * 🌷 **五彩花圃壇**
  * 🕯️ **室內榻榻米供桌**
* **操作與保存**：按鍵盤 <kbd>R</kbd> 旋轉方向，左鍵放置，右鍵拆除回收，所有擺放進度自動持久化儲存。

### 3. 中央守護聖壇追思面板 (Memorial Interaction Modal)
![中央守護聖壇互動面板](docs/screenshots/memorial_modal_full.png)
* **供奉互動**：供奉鮮花（聖壇前生成 3D 盛開花朵）、點燃長明燈（增加跳動暖光）、心香敬拜。
* **親友思念信箱**：親友可在此輸入暱稱並留下一句心底話，資料永久釘在雲端回憶牆上。

---

## 🚀 快速開始 (Quick Start)

### 方式 1：本地快速運行
本專案為零依賴原生 Web 架構，只需要 Python 即可在本地啟動：

```bash
# 1. 複製專案
git clone https://github.com/karst10607/reien.git
cd reien

# 2. 啟動本機伺服器
python server.py

# 3. 在瀏覽器打開
http://localhost:8088
```

### 方式 2：GitHub Pages 免費全球線上託管 (1 鍵上線)
1. 前往 GitHub 本專案頁面的 **Settings** -> **Pages**。
2. 在 **Branch** 選取 `main`，資料夾選取 `/ (root)`，點擊 **Save**。
3. 稍候片刻，全世界的親友即可透過 `https://karst10607.github.io/reien/` 免安裝直接進入靈園！

---

## 🛠️ 技術架構與規劃

本專案採用 **Monorepo（單一多模組儲存庫）** 策略設計，以便未來進行 Three.js 與 Godot 4 的跨框架比較與無痛遷移：

```
reien/
├── index.html               # Three.js 2.5D 前端客戶端 (支援 GitHub Pages 秒開)
├── server.py                # 本機測試伺服器腳本
├── docs/
│   ├── architecture_and_evaluation.md   # 完整技術選型、Godot/Rust 對比與 Oracle VPS 評估
│   └── screenshots/                     # 實機展示截圖
│
├── client-godot/            # (規劃中) Godot 4 原生遊戲客戶端 (匯出 PC .exe / Android APK)
└── server/                  # (規劃中) PocketBase / Rust 即時狀態與留言簿後端
```

### 核心技術特點：
1. **WebGL / Three.js 原生秒開**：整包前端核心體積小於 3MB，手機 4G 點開 3 秒內進入，無任何安裝門檻。
2. **PBR 物理材質與電影級調色**：採用 ACES Filmic Tone Mapping 與 PCF 柔和陰影。
3. **Web Audio 原生合成音效**：內建免下載的放鬆環境琶音和弦（點擊右上角隨開即聽）。
4. **多人在線架構**：支援 `BroadcastChannel` 本機多開同步，未來可無縫掛載 PocketBase 或 Colyseus 房廳伺服器。

---

## ☁️ Oracle VPS 伺服器部署指南

* **硬體需求**：
  * **Oracle Cloud Always Free (永久免費層)**：
    * **Ampere A1 (4 OCPU, 24GB RAM, 10TB/月流量)**：可支撐 1,500 ~ 3,000 人同時在線漫步祈願。
* **動靜分離最佳架構**：
  * 靜態 3D 模型與前端託管於 **Cloudflare CDN / GitHub Pages**。
  * Oracle VPS 僅負責處理 **PocketBase / WebSocket** 數據傳輸，VPS 頻寬消耗接近 0。

詳細評估與技術報告請參閱 [docs/architecture_and_evaluation.md](docs/architecture_and_evaluation.md)。

---

## 📜 開源許可
MIT License.
