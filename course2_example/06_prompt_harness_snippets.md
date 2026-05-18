# 範例 6｜Prompt / Harness Snippets：把短指令整理成可執行流程

對應投影片：第 15-17、31、34、72、89、93、96 頁

- 第 15-17 頁：從「只問問題」到「設計 AI 怎麼做事」
- 第 31、34 頁：讓 AI 先協助理解與規劃，而不是直接改 code
- 第 72 頁：給規格、給範例、給規則
- 第 89 頁：Model + Harness，讓工作有軌道
- 第 93 頁：Project Memory 的規則範例
- 第 96 頁：Guardrails，規格不明時停下來

---

## 使用情境

投影片中有一些短短的 prompt、memory、guardrails、流程片段。它們不是完整 bug report、test plan 或 FIFO 流程，但很適合課堂上拿來示範：同一句「幫我做」如果補上 context、規則和停止條件，AI 的行為會穩定很多。

這份範例可以在第 65 頁講完 role-play 後補充，也可以在第 89、93、96 頁講 harness 零件時使用。

### 白話說明

可以把 AI 想成一位新同事。你只說「幫我寫 test plan」，他可能不知道公司格式、命名習慣、哪些規格不能猜、遇到風險要不要先問。

Harness snippets 就是把這些「工作規則」先寫清楚：要看哪些資料、要輸出什麼格式、不能做哪些事、什麼情況要停下來問人。這不是 IC 設計專有知識，而是一般團隊協作也會做的事。

---

## 範例資料

也可用 `fixtures/harness_context_package.txt` 當 `@file` 載入。

```text
Task:
根據 reset / enable / busy 三段規格，整理 test plan 初稿。

Spec:
- reset_n = 0 時，所有輸出應回到預設值
- enable = 1 時，模組開始處理輸入資料
- busy = 1 時，不應接受新的 start command

Existing naming examples:
- test_dut_reset_outputs_default
- test_dut_enable_starts_processing
- test_dut_busy_rejects_start_command

Project memory:
- reset 行為必須有獨立 test case
- busy 狀態下的 start command 必須測試
- 規格未定義的 timing 不可自行腦補
- 設計行為變更必須人工確認

Guardrails:
- 不要修改 RTL
- 不要修改正式 testbench
- 不要把模糊規格寫成確定行為
- 模糊點必須標記為「需人工確認」
```

---

## 可直接貼給 AI 的 Prompt

```text
你現在是協助整理 test plan 的 verification assistant。

請根據以下 context package，整理一份「可交給人類 review 的 test plan 初稿」。
不要修改任何檔案，不要寫 RTL，不要寫 testbench code，也不要呼叫外部系統。

Context package:
Task:
根據 reset / enable / busy 三段規格，整理 test plan 初稿。

Spec:
- reset_n = 0 時，所有輸出應回到預設值
- enable = 1 時，模組開始處理輸入資料
- busy = 1 時，不應接受新的 start command

Existing naming examples:
- test_dut_reset_outputs_default
- test_dut_enable_starts_processing
- test_dut_busy_rejects_start_command

Project memory:
- reset 行為必須有獨立 test case
- busy 狀態下的 start command 必須測試
- 規格未定義的 timing 不可自行腦補
- 設計行為變更必須人工確認

Guardrails:
- 不要修改 RTL
- 不要修改正式 testbench
- 不要把模糊規格寫成確定行為
- 模糊點必須標記為「需人工確認」

請輸出：
1. 你讀到的任務目標
2. 你會使用的 context
3. Test plan 初稿表格
4. 需要人工確認的問題
5. Stop conditions：哪些情況你會停下來，不繼續產生測試或改 code
```

如果使用 `@file` 示範，可改成：

```text
請讀取 @course2_example/fixtures/harness_context_package.txt。
根據檔案中的 Task / Spec / Existing naming examples / Project memory / Guardrails，產生 test plan 初稿。
限制同上：不要修改檔案、不要寫 RTL、不要寫 testbench code、不要呼叫外部系統。
```

---

## 期望輸出範例

```markdown
## 1. 任務目標

根據 reset / enable / busy 三段規格，整理 test plan 初稿，並標出需要人工確認的規格模糊點。

## 2. 使用的 Context

- Spec: reset_n、enable、busy 三段需求
- Naming examples: test_dut_<behavior>
- Project memory: reset 必須獨立測、busy + start command 必須測
- Guardrails: 不改 RTL、不改正式 testbench、不腦補規格

## 3. Test Plan 初稿

| Test Case | 測試目的 | 前置條件 | 測試步驟 | 預期結果 | 需人工確認 |
|---|---|---|---|---|---|
| `test_dut_reset_outputs_default` | 確認 reset_n = 0 時輸出回到預設值 | DUT 正常初始化 | 1. 將 reset_n 拉低 2. 等待至少一個 clock cycle 3. 觀察輸出 | 所有輸出回到預設值 | 預設值清單、reset 是 sync 或 async |
| `test_dut_enable_starts_processing` | 確認 enable = 1 時模組開始處理輸入 | reset_n = 1 且 DUT idle | 1. 提供合法 input 2. 將 enable 拉高 3. 觀察狀態或輸出 | 模組開始處理輸入資料 | 「開始處理」應看哪個 observable signal |
| `test_dut_busy_rejects_start_command` | 確認 busy = 1 時不接受新 start command | DUT busy = 1 | 1. 在 busy 期間送 start 2. 觀察 transaction 是否被接受 | 新 start command 不應改變目前交易 | 拒收時是否要拉 error flag 或 ready/valid backpressure |

## 4. 需要人工確認

- reset 預設值清單在哪裡
- reset release 後第一個 cycle 是否有特殊行為
- busy 拒收 start 時是否需要錯誤訊號

## 5. Stop Conditions

- 需要決定 reset timing 或 busy handshake 語意時，先停下來問人
- 需要修改 RTL 或正式 testbench 時，先停下來問人
- 發現 spec 與既有 test naming / project memory 衝突時，先列出衝突，不自行決定
```
