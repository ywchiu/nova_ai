# 範例 3｜CI/CD Agent：失敗摘要與下一步建議

對應投影片：第 119-121 頁

- 第 119 頁：先講舊 CI/CD 失敗處理方式
- 第 120 頁：貼下面的 prompt 示範 Agent 如何分析 CI failure
- 第 121 頁：講 Jenkins / CI 與 Cline 的雙向流程

---

## 情境

Jenkins 跑完 regression 後失敗。舊流程是工程師自己翻 console log；新流程是 Agent 先整理失敗摘要、證據、可能根因與下一步，但不自動 deploy、不自動改 pipeline。

---

## 模擬 CI Log

也可用 `fixtures/jenkins_failure.log` 當 `@file` 載入。

```text
Jenkins job: chip-validator-ci-fail
Build: #42
Result: FAILURE

[Stage] Inject Bug
sed -i.bak 's/CLOCK_MAX_MHZ = 800.0/CLOCK_MAX_MHZ = 100.0/' chip_validator/validator.py

[Stage] Test
FAILED tests/test_validator.py::TestClockFrequency::test_valid_clock_frequency
FAILED tests/test_validator.py::TestClockFrequency::test_clock_boundary_max

E AssertionError: expected no validation error for 200 MHz
E ValidationError(rule='clock_frequency', message='clock 200 MHz exceeds max 100 MHz')

[Stage] Cleanup
restored chip_validator/validator.py from .bak
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
- 如涉及 spec 上限變更，必須要求人工確認
```

---

## 期望輸出範例

```markdown
## CI Failure Summary

Build `chip-validator-ci-fail #42` 失敗，失敗集中在 clock frequency validation。

## Failed Tests
- `tests/test_validator.py::TestClockFrequency::test_valid_clock_frequency`
- `tests/test_validator.py::TestClockFrequency::test_clock_boundary_max`

## Likely Root Cause
`CLOCK_MAX_MHZ` 在 build 過程中從 `800.0` 被改成 `100.0`，導致原本合法的 `200 MHz` 設定被誤判為超出上限。

## Evidence
- Log 顯示 `sed` 將 `CLOCK_MAX_MHZ = 800.0` 改為 `CLOCK_MAX_MHZ = 100.0`
- Assertion error 顯示 `clock 200 MHz exceeds max 100 MHz`
- 失敗測試都集中在 `TestClockFrequency`
- Cleanup stage 顯示檔案已從 `.bak` 還原

## Recommended Next Action
1. 確認 `CLOCK_MAX_MHZ` 正式 spec 是否仍為 `800.0`
2. 若是注入測試用 bug，確認 fail job 行為符合預期
3. 若這是實際 PR 變更，要求作者補 spec update 與 boundary tests
4. 不要自動 deploy，需要人工確認上限規格

## Requires Human Approval
yes
```

```json
{
  "status": "failed",
  "job": "chip-validator-ci-fail",
  "build": 42,
  "failed_tests": [
    "tests/test_validator.py::TestClockFrequency::test_valid_clock_frequency",
    "tests/test_validator.py::TestClockFrequency::test_clock_boundary_max"
  ],
  "likely_root_cause": "CLOCK_MAX_MHZ changed from 800.0 to 100.0 during build",
  "evidence": [
    "sed command changed CLOCK_MAX_MHZ",
    "200 MHz rejected because max became 100 MHz",
    "failures concentrated in TestClockFrequency"
  ],
  "recommended_action": "confirm clock max spec; restore constant or update spec/tests if the limit changed",
  "confidence": 0.86,
  "requires_human_approval": true
}
```

---

## 講師提醒

這個例子要強調：CI/CD Agent 初期最好只做「診斷與通知」。觸發 build、改 pipeline、rollback、deploy 都應該有更嚴格的權限與人工確認。
