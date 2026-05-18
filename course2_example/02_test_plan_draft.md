# 範例 2｜Test Plan：把規格片段整理成測試初稿

對應投影片：第 59-65 頁

- 第 59 頁：請 Cline 幫忙整理 Test Plan 初稿
- 第 60 頁：說明「幫我寫 test plan」太粗會產生的問題
- 第 62-65 頁：明確輸出格式、few-shot、角色設定

---

## 規格片段

```text
當 reset_n = 0 時，所有輸出應回到預設值。
當 enable = 1 時，模組開始處理輸入資料。
當 busy = 1 時，不應接受新的 start command。
```

同一份規格片段也可從 `fixtures/test_plan_spec.txt` 載入，方便示範 `@file` 或從規格文件摘錄段落時的做法。

---

## 可直接貼給 AI 的 Prompt

```text
你現在是資深 verification engineer。

請根據以下規格片段整理 test plan 初稿，不要寫 RTL，不要寫 testbench code。

規格片段：
當 reset_n = 0 時，所有輸出應回到預設值。
當 enable = 1 時，模組開始處理輸入資料。
當 busy = 1 時，不應接受新的 start command。

如果使用 @file 示範，請改讀：
fixtures/test_plan_spec.txt

請用表格輸出：
1. Test Case 名稱
2. 測試目的
3. 前置條件
4. 測試步驟
5. 預期結果
6. 需要人工確認的規格模糊點

命名規則：
- test_<module>_<behavior>
- 若 module 名稱未知，先用 test_dut_<behavior>

限制：
- 不要自行補完規格沒有說的 timing
- 不要假設 busy 是 pulse 還是 sticky
- 不要假設 reset release 後第一個 cycle 的行為
- 規格不明處必須放在「需要人工確認」欄位
```

---

## 期望輸出範例

```markdown
| Test Case | 測試目的 | 前置條件 | 測試步驟 | 預期結果 | 需要人工確認 |
|---|---|---|---|---|---|
| `test_dut_reset_outputs_default` | 確認 `reset_n = 0` 時輸出回到預設值 | DUT 已完成初始化 | 1. 將 `reset_n` 拉低 2. 等待至少一個 clock cycle 3. 觀察所有輸出 | 所有輸出等於預設值 | 預設值列表是否已有正式 spec？reset 是 async 還是 sync？ |
| `test_dut_enable_starts_processing` | 確認 `enable = 1` 時模組開始處理輸入 | `reset_n = 1` 且 DUT idle | 1. 提供合法 input 2. 將 `enable` 拉高 3. 觀察處理狀態與輸出 | 模組開始處理輸入資料 | 「開始處理」應由哪個 observable signal 判斷？ |
| `test_dut_busy_rejects_start_command` | 確認 `busy = 1` 時不接受新的 start command | DUT 處於 busy 狀態 | 1. 在 `busy = 1` 時送出新的 `start` 2. 觀察 transaction 是否被接受 | 新 start command 不應改變目前處理中的 transaction | 拒收時是否需要 error flag 或 ready/valid backpressure？ |
```

---

## 講師提醒

這個例子要強調：Test Plan 的價值不是產生很多測項，而是把「可測的行為」與「規格模糊點」分開。
