# 範例 1｜Bug Report：先整理可重現資訊，不要直接亂改

對應投影片：第 27-30 頁

- 第 27 頁：以 Bug Report 為例
- 第 28 頁：示範 Vibe Coding 的限制
- 第 29-30 頁：引出 regression 與 Agentic Engineering

---

## 情境

使用者只丟一句很模糊的 bug report：

```text
幫我修這個 data_out 偶爾為 0 的 bug。你覺得怎麼改就直接改。
```

同一份稍微完整的 bug report 草稿也可從 `fixtures/bug_report.txt` 載入，方便示範 `@file` 或複製外部 bug report 時的做法。

這種指令容易讓 Agent 直接改很多檔案，卻沒有重現條件、沒有 regression test，也沒有保留設計行為邊界。這個範例的重點是：先把 bug report 整理成可驗證的 debug contract。

---

## 可直接貼給 AI 的 Prompt

```text
你現在是 Debug Triage Agent。請先整理 bug report，不要修改任何檔案。

Bug report:
data_out 偶爾為 0，請修一下。

如果使用 @file 示範，請改讀：
fixtures/bug_report.txt

請輸出：
1. 已知現象
2. 缺少的重現資訊
3. 可能影響範圍
4. 需要先檢查的 signal / module / log
5. 最小重現步驟草稿
6. 建議新增的 regression test
7. 不應該直接修改的設計行為
8. 下一步需要人工確認的問題

限制：
- 不要修改任何檔案
- 不要自行決定 data_out = 0 是否一定是錯
- 不要假設 reset / enable / busy 的規格未明確行為
- 如果資訊不足，請明確標示「目前不可直接修」
```

---

## 期望輸出範例

```markdown
# Bug Triage Draft

## 已知現象
`data_out` 偶爾變成 `0`，但目前缺少觸發條件、波形、log 與預期行為，因此尚不能判斷是設計 bug、testbench 問題或合法狀態。

## 缺少的重現資訊
- 發生時的 `reset_n` / `enable` / `busy` / `valid` 狀態
- 觸發前後至少 5 個 cycle 的 waveform
- input transaction sequence
- 預期 `data_out` 應維持、清零、或輸出上一筆資料的正式規格

## 可能影響範圍
- output data path
- reset handling
- enable gating
- busy / start command handshake
- testbench scoreboard

## 最小重現步驟草稿
1. 使用已知會觸發問題的 seed 或 transaction sequence
2. 記錄 `data_out` 變 0 前後的控制訊號
3. 比對 spec 中 reset、enable、busy 狀態下的輸出定義

## 建議 regression test
- `test_data_out_not_cleared_during_valid_transaction`
- `test_data_out_reset_behavior`
- `test_data_out_busy_rejects_new_start`

## 不應直接修改
- 不應在未確認規格前強制讓 `data_out` 保持上一筆資料
- 不應移除 reset 清零邏輯
- 不應弱化現有 assertion 或 scoreboard

## Ready to Fix
no
```

---

## 講師提醒

這個例子要強調：Bug Report 的第一步不是修 code，而是建立可重現、可驗證、可回歸的問題描述。
