# IC 設計流程工作台

一個完整的 IC (積體電路) 設計流程互動式工作台，用於視覺化和追蹤晶片設計的各個階段。

## 功能特色

### 📋 流程總覽 (Flow Overview)
- **8 個設計階段**：Spec → Architecture → RTL → Simulation → Synthesis → P&R → STA → Tape-out
- 互動式時間軸，點擊查看每個階段的輸入、輸出與常見風險
- 每個階段包含專屬的 EDA 工具列表

### 🔌 Block Diagram (晶片系統架構圖)
- 完整的 AXI4 匯流排架構圖
- 包含 CPU、SRAM、DMA、Peripheral、IO Ring、Clock & Reset
- 點擊區塊查看詳細規格資訊

### ✅ 驗證檢查清單 (Verification Checklist)
- 18 項驗證檢查點，分為 Simulation、Coverage、Lint、STA、DRC/LVS 五大類
- 即時進度追蹤與百分比顯示

### 📊 Sign-off Dashboard (簽核儀表板)
- 9 項簽核指標：Timing、Area、Power、Coverage、DRC、LVS、ERC
- 執行簽核檢查並匯出報告

### 📐 GDSII 預覽區
- 支援拖放上載 GDSII/OASIS 檔案
- 縮放與適應視窗功能

### 🛠️ 側邊欄工具
- **專案資訊**：製程節點、封裝類型、Tape-out 日期
- **流程進度**：即時追蹤各階段狀態
- **EDA 工具管理**：管理 Synopsys、Cadence、Siemens 等工具
- **檔案管理**：專案檔案樹狀結構
- **團隊管理**：成員角色與線上狀態

### 🎨 其他功能
- 深色/亮色主題切換
- 響應式設計（桌面/平板/手機）
- 鍵盤導航支援

## 技術架構

- **HTML5**：語意化結構
- **CSS3**：CSS 變數、Flexbox、Grid、Media Queries
- **JavaScript**：原生 ES6 (無框架依賴)

## 使用方式

直接於瀏覽器開啟 `index.html` 即可使用。

## 適用對象

- IC 設計工程師
- 驗證工程師
- 專案經理
- 教學用途