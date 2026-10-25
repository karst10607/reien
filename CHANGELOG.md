# 📋 Reien (霊園) ‧ 版本更新日誌 (Changelog)

所有重要的專案版本演進、功能變更、測試案例與問題修復皆詳細記錄於此文件。  
本專案遵循 [Semantic Versioning (語意化版本 2.0.0)](https://semver.org/lang/zh-TW/) 規範。

---

## [1.3.0] - 2026-10-25

### ✨ 新增功能 (Added)
* **手遊風格「頂部 HUD 沉浸式收合/展開」系統 (`window.toggleTopHUD()`)**：
  * 在頂部標題卡右側新增 `[ ▲ 收合 ]` / `[ ▼ 選單 ]` 手遊折疊按鈕（`#btn-top-hud-toggle`）。
  * 點擊收合或在手機直立模式下，頂部時間、天氣、視角與造鎮按鈕會平滑摺疊隱藏，頂部高度縮減至 `< 36px`，**釋放 95% 以上全螢幕無遮擋視野**。
  * 支援點擊 3D 畫面任意處自動收合，重現手遊全螢幕沉浸遊玩體驗。
* **iOS Safari「Web Audio 聲學低頻實體震動脈衝」(`playHapticAudioImpulse()`)**：
  * 針對 Apple WebKit (iOS Safari) 系統級限制不開放 `navigator.vibrate` API 的問題，研發出基於 Web Audio 的 44Hz 超低頻正弦波脈衝。
  * 瞬間驅動 iPhone 底部實體揚聲器震膜振幅，在玩家手掌中產生真實的實體反饋微震感，克服 iOS 網頁無法震動的硬限制。
* **藍牙手把與有線手把支援增強（Bluetooth & USB Gamepads）**：
  * 支援 Xbox Wireless、PS4/PS5 DualSense、Switch Pro、八位堂 (8BitDo) 等各式藍牙與 USB 有線手把。
  * 實裝自動連線廣播橫幅 (`#gamepad-banner`)，提示連線狀態與按鍵映射。
  * 手把按鍵映射：
    - **左搖桿**：角色 3D 移動（依當前視角自動換算方向）
    - **右搖桿**：旋轉 3D 視角
    - **A 鍵**：摸摸豆豆（伴隨手把雙馬達震動）
    - **B 鍵**：祈願／打坐
    - **X 鍵**：**一鍵測試手把強弱雙馬達震動 (Dual-Rumble)**
    - **Y 鍵**：收合／展開頂部手遊選單
* **一鍵「📳 震動/手把測試」按鈕與環境診斷 (`window.testHapticsAndGamepad()`)**：
  * 點擊立即檢測 Android 實體震動馬達、iOS 聲學實體震動，以及當前連接之藍牙／有線手把，並顯示詳細診斷 Toast。
* **自動化測試擴充至 12 項 (CI/CD Test Suite)**：
  * 新增 `TC-11`: 手機直立模式頂部選單手遊風格收合與展開驗證。
  * 新增 `TC-12`: 藍牙與有線手把 `vibrationActuator.playEffect('dual-rumble')` 雙馬達強弱震動測試。

### 🐛 問題修復 (Fixed)
* **手機直立模式操作說明遮擋修復**：
  * 修正切換庭園建造模式時 `nHelp.style.display` 誤設行內 `display: flex` 覆蓋 `@media` 規則的問題，加入 `!important` 樣式層與點擊畫面任意處自動關閉說明框機制，徹底杜絕文字遮擋畫面。
* **手機震動未生效修復**：
  * 修正 Android Chrome 下 `navigator.vibrate` 因角色尋路走動延遲（脫離了原始點擊手勢事件鏈）被瀏覽器安全機制（User Activation Policy）阻擋的問題；改為在使用者按鈕點擊當下立即同步觸發。
* **虛擬搖桿跨瀏覽器拖曳修復**：
  * 修正手指滑出 `#joystick-zone` 外圈時 `PointerCapture` 遺失問題，加入 `window` 全域指標監聽與 `touchstart`/`touchmove`/`touchend` 觸控事件相容層。

### 🔬 實測驗證
* 執行 CDP 12 項端到端自動檢測套件：**12/12 測試案例全部通過（耗時 21.55s）**。
* 截圖留存：`docs/screenshots/mobile_portrait_collapsed_immersive.png`（直立手機沉浸模式實拍）。

---

## [1.2.0] - 2026-10-25

### ✨ 新增功能 (Added)
* **白天多層次色溫光影升級**：
  * 壓低白天主太陽仰角，拉長立體斜射陰影；主光強化至 `2.15`，環境光壓低至 `0.24`（主光/環境光對比度達 **8.95x**）。
  * 增設背光側冷青色天空補光（`0x0ea5e9`）、櫻花粉逆光透射光（`0xfda4af`）與 4 組區域環境反彈光源（聖壇暖金、清溪水波、櫻花林珊瑚光、木橋斜照）。
* **自訂 GLSL「木漏れ日（Komorebi）樹影碎光與漂浮雲影」Shader**：
  * 即時渲染緩慢流動的大氣冷靛雲影與金黃葉隙碎光斑，消除平淡單一綠色。
* **3 階層立體樹冠漸層受光 ＋ 4096 鏤空葉影 (`MeshDepthMaterial`)**：
  * 櫻花與青松配置向陽頂冠、中層、背光底層 3 套獨立材質，並投射細緻鏤空樹葉陰影。
* **自動化 CI/CD 端到端檢測流水線 (`.github/workflows/ci-deploy.yml`)**：
  * 建立零外部套件依賴的 Chrome DevTools Protocol 測試套件 (`tests/e2e_ci_suite.py`)，涵蓋靜態語法、WebGL 啟動、手機直橫向排版、虛擬搖桿、震動引擎、透視遮擋等 10 項測試。

---

## [1.1.0] - 2026-10-25

### ✨ 新增功能 (Added)
* **手機直立／橫放自適應排版 ＋ 手遊虛擬搖桿 (`#joystick-zone`)**：支援觸控與多點觸控拖曳移動角色。
* **守護犬「豆豆」3D 互動模型 (`companionDog`)**：靠近或點擊即觸發開心地跳躍、快速搖尾巴、撒嬌汪汪音效與愛心粒子。
* **跨平台觸覺震動回饋引擎 (`window.triggerHaptics`)**：支援雷雨閃電驚雷雙馬達強震與摸狗心跳震動。
* **樹下與進入室內自動 X-Ray 透視（See-Through Occlusion）**：遮擋物自動平滑降至 14%~16% 半透明。
* **GLSL 丁達爾體積光束散射 (God-Rays)**。

---

## [1.0.0] - 2026-10-24

### ✨ 初始發布 (Initial Release)
* 2.5D RO 動漫風格斜俯視角（Isometric 45°）線上靈園原型。
* PBR 凹凸法線貼圖石板路徑、日式清溪拱橋、高低起伏地形與中央星空守護聖壇。
* 完整庭園小鎮建造模式（自由擺放千本櫻、青松木、日式祈福木舍、教堂、石燈籠與供桌）。
* 聖壇獻花點燈供奉面板與親友留言信箱。
