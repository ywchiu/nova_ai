# 範例 3｜FIFO Issue Agent：把模糊需求變成可執行契約

對應投影片：第 110-112 頁

- 第 110 頁：先講舊 Issue 流程的問題
- 第 111 頁：貼下面的 prompt 示範 AI 如何補完整 Issue
- 第 112 頁：用「期望輸出」對照投影片上的範例

---

## 情境

產品或驗證團隊只丟了一句模糊需求：

```text
FIFO overflow behavior 有問題，請修一下。
```

同一份草稿也可從 `fixtures/issue_draft.txt` 載入，方便示範 `@file` 或 MCP 不通時的 fallback。

這種需求不能直接丟給 coding agent，因為規格不明、驗收條件不明、測試也不明。Issue Agent 的責任是先把需求變成可討論、可驗收、可交接的契約。

---

## 可直接貼給 AI 的 Prompt

```text
你現在是 Issue Triage Agent，負責把模糊 Issue 整理成可執行契約。

請根據以下 Issue 草稿，先不要寫 code，也不要假設未定義的設計行為。

Issue 草稿：
FIFO overflow behavior 有問題，請修一下。

請輸出以下內容：

1. 問題描述
2. 可能影響範圍
3. 重現條件草稿
4. Acceptance Criteria 草稿
5. 建議測試項目
6. 需人工確認的規格問題
7. Ready for Coding: yes/no

限制：
- 不要修改任何檔案
- 不要呼叫 Jira / Git / MCP / 外部系統
- 不可以自行決定 overflow 時應該 drop、stall 或 overwrite
- Acceptance Criteria 必須可被測試驗證
- 模糊點要保留在「需人工確認」中
- 最後請列出這張 Issue 還缺哪些資訊
```

---

## 期望輸出範例

```markdown
# Issue Contract Draft

## 問題描述
FIFO overflow 行為可能與規格不一致。目前描述不足，無法判斷 overflow 發生時正確處理方式。

## 可能影響範圍
- write transaction
- overflow_flag
- buffer full handling
- input data retention / drop behavior
- downstream data integrity

## 重現條件草稿
Given FIFO 已經 full
When 額外一筆 write transaction 進入
Then 系統應依規格處理 overflow，並正確反映 overflow_flag

## Acceptance Criteria 草稿
- AC1: FIFO full 時，overflow_flag 應被正確拉起
- AC2: overflow 發生後，既有資料不應被未定義方式覆蓋
- AC3: overflow case 必須有 regression test
- AC4: 若規格未定義 drop / stall / overwrite，實作前必須由設計負責人確認

## 建議測試項目
- FIFO full + extra write case
- overflow_flag assertion timing
- overflow 後 read sequence 是否保留既有資料順序
- reset 後 overflow 狀態是否清除

## 需人工確認
- overflow 發生時，是否允許 drop input？
- 如果不允許 drop，write side 應 stall 還是 backpressure？
- overflow_flag 是 pulse 還是 sticky bit？
- overflow 後資料保留策略是否已有正式 spec？

## Ready for Coding
no

## 缺少資訊
- 正式 FIFO overflow spec
- 相關 RTL / testbench 檔案位置
- 目前失敗 waveform 或 log
- design owner 對 drop / stall / overwrite 的決策
```

---

## 講師提醒

這個例子要強調：AI 不決定需求，AI 幫你把需求整理到「可以被人類決策」的狀態。
