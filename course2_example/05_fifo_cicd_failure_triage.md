# 範例 5｜FIFO CI/CD Agent：失敗摘要與下一步建議

對應投影片：第 119-121 頁

- 第 119 頁：先講舊 CI/CD 失敗處理方式
- 第 120 頁：貼下面的 prompt 示範 Agent 如何分析 CI failure
- 第 121 頁：講 Jenkins / CI 與 Cline 的雙向流程

---

## 情境

FIFO overflow 相關 PR 送出後，Jenkins regression 失敗。舊流程是工程師自己翻 console log；新流程是 Agent 先整理失敗摘要、證據、可能根因與下一步，但不自動 deploy、不自動改 pipeline。

---

## 模擬 CI Log

也可用 `fixtures/jenkins_failure.log` 當 `@file` 載入。

```text
Jenkins job: fifo-regression
Build: #42
Result: FAILURE

[Stage] Checkout
Branch: feature/fifo-overflow-behavior
Commit: 9f8a7c1 adjust FIFO overflow behavior when read_en is high

[Stage] Test
FAILED tests/fifo/test_overflow.py::test_fifo_overflow_flag_full_write
FAILED tests/fifo/test_overflow.py::test_fifo_full_write_read_same_cycle

E AssertionError: expected overflow_flag=1 when fifo_full=1 and write_en=1
E Observed overflow_flag=0 because read_en=1

E AssertionError: expected write_ptr to remain stable on overflow
E Observed write_ptr advanced during full + write_en + read_en

[Stage] Artifacts
waveform: artifacts/fifo_overflow_build42.vcd
test_report: artifacts/fifo_regression_build42.xml
```

---

## 可直接貼給 AI 的 Prompt

```text
你現在是 CI/CD Triage Agent。

請根據下面 Jenkins log 產生失敗摘要。只做分析與建議，不要修改程式碼，不要重跑 build，不要部署。

Jenkins log:
<貼上上方 log>

請輸出：
1. build 結果摘要
2. 失敗測試清單
3. 可能 root cause
4. 支持 root cause 的 evidence
5. 建議下一步
6. 是否需要人工確認
7. 可給通知系統使用的 JSON

限制：
- 不要修改任何檔案
- 不要呼叫 Jenkins / Git / MCP / 外部系統
- 低信心不得寫成確定結論
- 必須引用 log evidence
- 不可重跑 build
- 不可建議自動 deploy
- 如涉及 FIFO overflow spec 變更，必須要求人工確認
```

---

## 期望輸出範例

```markdown
## CI Failure Summary

Build `fifo-regression #42` 失敗，失敗集中在 FIFO overflow 行為，特別是 `fifo_full=1` 且 `write_en=1` 的 boundary case。

## Failed Tests
- `tests/fifo/test_overflow.py::test_fifo_overflow_flag_full_write`
- `tests/fifo/test_overflow.py::test_fifo_full_write_read_same_cycle`

## Likely Root Cause
近期 commit 調整 FIFO overflow 行為後，`read_en=1` 時 `overflow_flag` 不再拉起，且 full + write + read 同 cycle 時 `write_ptr` 會前進。這可能與現有 test plan 或 FIFO spec 的 overflow 定義不一致。

## Evidence
- Log 顯示 branch 為 `feature/fifo-overflow-behavior`
- Commit message: `adjust FIFO overflow behavior when read_en is high`
- Assertion error 顯示預期 `overflow_flag=1`，但因 `read_en=1` 觀察到 `overflow_flag=0`
- Assertion error 顯示 overflow 時預期 `write_ptr` 維持不變，但實際有前進
- 失敗測試都集中在 FIFO overflow regression

## Recommended Next Action
1. 請 design owner 確認 full + write + read 同 cycle 時，overflow 應該 drop、stall、overwrite，或允許同 cycle pop/push。
2. 請 verification owner 確認現有 test expectation 是否仍符合最新 FIFO spec。
3. 若 PR 改變設計行為，需同步更新 FIFO spec、test plan 與 regression tests。
4. 不要自動 deploy；需要人工確認 overflow spec 後再決定修 code 或修 test。

## Requires Human Approval
yes
```

```json
{
  "status": "failed",
  "job": "fifo-regression",
  "build": 42,
  "failed_tests": [
    "tests/fifo/test_overflow.py::test_fifo_overflow_flag_full_write",
    "tests/fifo/test_overflow.py::test_fifo_full_write_read_same_cycle"
  ],
  "likely_root_cause": "FIFO overflow behavior changed when read_en is high",
  "evidence": [
    "commit adjusts FIFO overflow behavior when read_en is high",
    "overflow_flag observed 0 while expected 1",
    "write_ptr advanced during full + write_en + read_en",
    "failures concentrated in FIFO overflow regression tests"
  ],
  "recommended_action": "confirm FIFO overflow spec; then update code or tests consistently",
  "confidence": 0.84,
  "requires_human_approval": true
}
```

---

## 講師提醒

這個例子要強調：CI/CD Agent 初期最好只做「診斷與通知」。觸發 build、改 pipeline、rollback、deploy 都應該有更嚴格的權限與人工確認。
