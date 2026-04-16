# Skills 說明文件

本目錄包含課程用的自訂 Skill 範例，搭配 [Superpowers](https://github.com/obra/superpowers) 框架使用。

---

## 什麼是 Skill？

Skill 是一份 Markdown 文件，定義 AI 助理在特定場景下的行為規範和操作流程。
跟 MCP 的差異：

| | Skill | MCP |
|---|---|---|
| **本質** | 靜態知識 + 流程定義 | 動態 API 連接 |
| **格式** | Markdown 文件 | Python Server |
| **能做什麼** | 告訴 AI「你應該知道什麼、怎麼做」 | 讓 AI「能呼叫外部系統」 |
| **組合使用** | Skill 可以指定「在 Step 3 用 jenkins_trigger_build」 | MCP 提供工具，Skill 定義流程 |

---

## Superpowers 框架

[Superpowers](https://github.com/obra/superpowers) 是一套完整的 AI 開發流程框架，
包含 14 個內建 Skill，涵蓋從構思到上線的完整開發流程。

### 安裝方式

#### Claude Code（官方 Marketplace）

```bash
/plugin install superpowers@claude-plugins-official
```

#### Claude Code（Plugin Marketplace）

```bash
# 註冊 marketplace
/plugin marketplace add obra/superpowers-marketplace

# 安裝
/plugin install superpowers@superpowers-marketplace
```

#### Cursor

在 Cursor Agent 對話框：

```
/add-plugin superpowers
```

#### 驗證安裝

啟動新的對話，輸入「help me plan this feature」或「let's debug this issue」，
Agent 應該會自動觸發對應的 Skill。

### 更新

```bash
/plugin update superpowers
```

### Superpowers 內建 Skills

| Skill | 觸發時機 | 說明 |
|-------|---------|------|
| **brainstorming** | 開始做新功能之前 | 釐清需求、探索方案、產出設計文件 |
| **writing-plans** | 設計確認後 | 拆成 2~5 分鐘的小任務，每個有明確的檔案和驗證步驟 |
| **using-git-worktrees** | 開始實作前 | 建立隔離的 git worktree，乾淨的開發環境 |
| **test-driven-development** | 實作中 | 強制 RED→GREEN→REFACTOR 循環 |
| **subagent-driven-development** | 有多個獨立任務時 | 派子 Agent 平行處理，雙階段 review |
| **executing-plans** | 按計畫執行 | 分批執行，每批有人工確認點 |
| **dispatching-parallel-agents** | 2+ 個獨立任務 | 平行派發子 Agent |
| **systematic-debugging** | 遇到 bug 時 | 4 階段根因分析法 |
| **requesting-code-review** | 任務完成後 | 自動 review，依嚴重度分類 |
| **receiving-code-review** | 收到 review 回饋 | 技術性回應，不盲目同意 |
| **verification-before-completion** | 宣告完成前 | 跑測試、確認 output、不靠聲稱 |
| **finishing-a-development-branch** | 所有任務完成 | 驗證測試、決定 merge/PR/丟棄 |
| **writing-skills** | 要建新 Skill 時 | 建立 Skill 的最佳實踐 |
| **using-superpowers** | 每次對話開始 | 自動偵測適用的 Skill |

### 核心工作流程

```
brainstorming（構思）
  → writing-plans（規劃）
    → using-git-worktrees（建環境）
      → test-driven-development（TDD 實作）
        → requesting-code-review（Review）
          → finishing-a-development-branch（完成）
```

---

## 本專案的自訂 Skills

以下是本課程建立的 Skill，與 Superpowers 互補：

### 靜態知識型

| Skill | 用途 | 搭配的 MCP |
|-------|------|-----------|
| [`novatek-coding-style.md`](novatek-coding-style.md) | 聯詠 C/Perl/Python 命名規範、Code Review checklist | 無 |
| [`register-spec.md`](register-spec.md) | 暫存器規格 — 位址、bit field、時脈、電壓 | 無 |

### 流程型（串接 MCP）

| Skill | 用途 | 搭配的 MCP |
|-------|------|-----------|
| [`weekly-report.md`](weekly-report.md) | 自動產生週報（帶 5 個參數） | Jira |
| [`fix-pr.md`](fix-pr.md) | 修復 PR 的完整流程（診斷→修復→CI→回報） | Jira + BitBucket + Jenkins |
| [`develop-feature.md`](develop-feature.md) | 從 Issue 到上線的完整開發流程 | Jira + BitBucket + Jenkins |

### Skill + MCP + Superpowers 如何組合

```
使用者：「幫我做 KAN-10」

Superpowers 自動觸發：
  → brainstorming（探索需求）
    → 呼叫 Jira MCP 讀 Issue    ← MCP
    → 參考 register-spec.md      ← 自訂 Skill（知識）
    → 按 develop-feature.md 流程  ← 自訂 Skill（流程）

  → writing-plans（規劃實作）
    → 呼叫 BitBucket MCP 讀原始碼  ← MCP
    → 參考 novatek-coding-style.md ← 自訂 Skill（規範）

  → test-driven-development（TDD 實作）

  → verification-before-completion（驗證）
    → 呼叫 Jenkins MCP 跑 CI      ← MCP

  → finishing-a-development-branch（完成）
    → 呼叫 Jira MCP 回報結果       ← MCP
```

---

## 如何在課堂使用

### 安裝順序

1. **先裝 Superpowers**（提供框架和內建 Skills）
2. **再設定 MCP Server**（提供 Jira/BB/Jenkins 連接）
3. **最後載入自訂 Skills**（提供公司特定知識和流程）

### 載入自訂 Skill 到 Cline

在 Cline 對話中直接貼入 Skill 內容，或在 Project Rules 裡引用：

```
請參考以下 Skill 文件來處理這個需求：
@file:skills/develop-feature.md
```

### 課堂 Demo 建議

| 順序 | Demo | 觸發方式 |
|------|------|---------|
| 1 | Superpowers 基本流程 | 「幫我規劃一個新功能」→ brainstorming 自動觸發 |
| 2 | MCP 連線測試 | 「列出所有 Jira 專案」→ jira_list_projects |
| 3 | 知識型 Skill | 「review 這段 code」→ 自動參考 novatek-coding-style |
| 4 | 流程型 Skill | 「幫我做 KAN-10」→ develop-feature.md 完整流程 |
| 5 | 三合一整合 | 「CI 掛了幫我修」→ fix-pr.md 串接三個 MCP |
