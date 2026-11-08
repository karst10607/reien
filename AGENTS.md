# Multi-Agent Collaboration Protocol & Quality Gates (AGENTS.md)

歡迎所有參與 **Reien (星塵彼岸 ‧ 2.5D 線上靈園 & 湖光小鎮)** 開發的 AI Agents。為確保分散式、非同步的多 Agent 協作流暢並防範衝突，所有 Agent 必須嚴格遵守以下治理規範。

---

## 1. Agent 命名規範 (Agent Identity Scheme)

每位 Agent 在執行任何 GitHub 操作前，必須確定自身唯一識別標識：
```
agent-{model}-{host_or_env}
```
- 本機當前 Agent 標識：`antigravity-thinkpad-x395`
- 範例：`agent-gemini-thinkpad-x395`, `agent-claude-cloud-runner`

Git Commit Author 統一規範：
```bash
git config user.name "Howl"
git config user.email "karst10607@gmail.com"
```

---

## 2. CAS 取單與搶單防護協議 (Claim-Check Protocol)

為防範不同機器上的 Agent 覆蓋同一 Issue 或重複工作，遵循 CAS（Check-And-Set）樂觀鎖機制：

1. **查核 (Check)**：
   - 檢視 Issue 的留言紀錄。
   - 若已有其他 Agent 留言 `🤖 [Claimed by: <agent_name>]` 且最後活躍在 2 小時內，視為已被認領，禁止搶單。
2. **認領 (Claim)**：
   - 取單時立即留言鎖定：
     ```markdown
     🤖 [Claimed by: <agent_name>]
     - **Target Branch**: agent/<agent_name>/issue-<issue_number>
     - **Status**: In Progress
     - **Scope**: <簡要工作範圍>
     ```
3. **分支命名規範**：
   - 分支必須為：`agent/<agent_name>/issue-<issue_number>`
   - 禁止直接 Push 至 `main`。

---

## 3. 品質閘門 (Quality Gates & DoD)

所有 Pull Request 必須滿足以下驗收標準（Definition of Done），方可進行 Squash Merge：

### 靜態與語法檢查
```bash
# TC-01: HTML 結構與 JavaScript 語法檢查
python -m unittest tests/e2e_ci_suite.py  # 或直接執行 e2e_ci_suite.py
```

### 動態 E2E 與 CDP 渲染驗證
```bash
python tests/e2e_ci_suite.py
```
- 驗證包含：
  - WebGL 場景與攝影機啟動無拋錯
  - 水岸木棧道、錦鯉水波與群聚反應
  - 手機直橫屏 UI 佈局適配與手遊虛擬搖桿
  - 觸覺回饋（手機震動與手把雙馬達震動）
  - 聖壇追思面板與自由建造模式

### Pull Request 內容規範
PR 內文必須附帶：
1. **關聯 Issue**：`Closes #<issue_number>`
2. **變更清單**
3. **測試與驗證證據**（包含終端機輸出摘要與截圖路徑）

---

## 4. 自動合併與合併後作業 (Post-Merge Protocol)

1. 當 CI 檢查全數通過時，執行 Squash and Merge：
   ```bash
   gh pr merge <pr_number> --squash --delete-branch
   ```
2. 切回 `main` 並同步：
   ```bash
   git checkout main && git pull origin main
   ```
3. 確認關聯 Issue 已關閉，並附上最終驗收留言。

---

## 5. 跨專案關聯與架構定位 (Cross-Project Integration)

依據 `mabi` 專案之 **ADR 0001 (AuraPet 桌面夥伴與線上靈園跨專案整合架構策略)**：
1. **儲存庫獨立原則**：
   - `karst10607/reien`：專注於 WebGL / Three.js 2.5D 網頁客戶端，提供零安裝、秒開之湖光小鎮與追思體驗。
   - `karst10607/reien-godot`：Godot 4 原生遊戲客戶端原型。
   - `karst10607/mabi`：AuraPet 桌面伴侶。
   - **禁止擅自將三者直接合併為單一儲存庫**。
2. **通訊與資產共享**：
   - 未來透過 WebSocket / MCP / Shared Profile (`pet-profile.json`) 與桌面端桌寵進行互動聯動。
