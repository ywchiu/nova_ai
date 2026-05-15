# Workshop：Issue 驅動開發完整流程

> 對應投影片：Part 8｜Workshop

把下面整段貼進 Cline。會跑完整個 Issue → Spec → AC → Tests → Code → Report 的鏈路。

---

## Issue #128：Improve log summary report

目前 Log Error Summarizer 只支援 ERROR 訊息。

希望新增兩個功能：

1. **支援 WARNING：**
   - WARNING 不影響 PASS / FAIL 狀態
   - summary.md 要顯示 warning 總數與明細

2. **新增 Repeated Error Signatures：**
   - 相同的 error_message 出現在兩個以上 failed tests 時要聚合
   - summary.md 列出 message、count、test names

---

請根據 Issue #128，使用 /sdd-feature workflow 開發功能。

要求：

1. 先用一段話摘要 Issue 的需求
2. 更新 specs/log-error-summarizer.md
3. 更新 specs/acceptance-criteria.md
4. 先新增或更新 pytest（這時候執行應該會 fail）
5. 再實作功能
6. 執行 pytest 並貼出結果
7. 最後產生一段可以回覆 Issue 的開發摘要，格式如下：

```
## Update Summary
（一句話總結）

### Changes
- spec
- AC
- tests
- code

### Test Result
- pytest: passed X / X

### Notes
- 行為保證
- 已知限制
```

限制：

- 不可修改 sample_logs/
- 不可弱化既有測試
- 只做最小必要變更，不重構無關區塊
