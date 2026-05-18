# 範例 2｜PR Review Agent：AI 預審 + 人類確認

對應投影片：第 108、113-118 頁

- 第 108 頁：先講「PR Diff → Review Checklist」
- 第 113-114 頁：講舊 PR Review 與新流程
- 第 115 頁：貼下面的 prompt
- 第 116 頁：對照 Review Checklist
- 第 118 頁：對照 Summary-first 的輸出格式

---

## 情境

PR 修改了 FIFO overflow 行為，但 reviewer 不確定：

- 是否改變設計語意
- 是否補 regression test
- 是否同步更新 spec / test plan
- 哪些地方需要人類 reviewer 判斷

---

## 模擬 PR Diff

也可用 `fixtures/fifo_overflow_pr.diff` 當 `@file` 載入。

```diff
diff --git a/rtl/fifo_controller.sv b/rtl/fifo_controller.sv
@@
-assign overflow_flag = write_en && fifo_full;
+assign overflow_flag = write_en && fifo_full && !read_en;

@@
-if (write_en && fifo_full) begin
-  drop_input <= 1'b1;
-end
+if (write_en && fifo_full && read_en) begin
+  write_ptr <= write_ptr + 1'b1;
+end
```

---

## 可直接貼給 AI 的 Prompt

```text
你現在是 PR Review Agent。請只做 Review，不要修改檔案。

請根據下面的 PR diff，產生 review checklist。

PR diff:
<貼上上方 diff>

請判斷：
1. 是否修改設計行為
2. 是否需要同步更新 test plan
3. 是否需要補 regression test
4. 是否需要更新 spec / design doc
5. 哪些地方需要 reviewer 特別確認

輸出格式：

## Summary
## Design Behavior
## Test Gaps
## Documentation Gaps
## Reviewer Notes
## Verdict

限制：
- 不要修改任何檔案
- 不要呼叫 Git / BitBucket / MCP / 外部系統
- 不可以自行決定 overflow 正確行為
- 不可以批准 merge
- 不可以把模糊規格寫成確定結論
- 每個風險都要附上 diff evidence
```

---

## 期望輸出範例

```markdown
## Summary
本 PR 修改 FIFO overflow 判斷邏輯，可能改變 full 狀態下 write/read 同時發生時的資料處理語意。

## Design Behavior
- [must] `overflow_flag` 從 `write_en && fifo_full` 改為 `write_en && fifo_full && !read_en`
  - Evidence: overflow_flag 在 read_en=1 時不再拉起
  - 需要確認：這是否符合最新 FIFO overflow spec？
- [must] full + write + read 同時發生時，新的邏輯會推進 `write_ptr`
  - Evidence: 新增 `write_ptr <= write_ptr + 1'b1`
  - 需要確認：此時 input data 應該 drop、stall，還是允許寫入？

## Test Gaps
- 未看到 full buffer + extra write 的 regression test
- 未看到 full + write_en + read_en 同 cycle 的測試
- 建議補 overflow_flag pulse / sticky 行為測試

## Documentation Gaps
- 若 overflow 行為改變，需同步更新 FIFO spec
- test plan 應新增 overflow boundary case

## Reviewer Notes
- 請設計負責人確認 overflow 時資料保留策略
- 請 verification owner 確認 regression test 是否覆蓋 full + simultaneous read/write

## Verdict
需要人工 review 後才能 merge。目前不建議直接批准。
```

---

## 講師提醒

這個例子要強調：AI Review 的定位是「預審」與「整理證據」，不是取代 reviewer。真正的設計取捨仍然由人決定。
