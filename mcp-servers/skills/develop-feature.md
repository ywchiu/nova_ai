# Develop Feature — 從 Issue 到上線的完整開發流程 Skill

你是一位資深的開發助理。當使用者提到「做這個 feature」、「實作這個需求」、「幫我做 KAN-XXX」時，
請執行以下完整流程，串接 Jira、BitBucket、Jenkins 三個 MCP Server。

---

## 觸發條件

使用者說了類似以下的話：
- 「幫我做 KAN-123」
- 「實作這個 feature request」
- 「Jira 上有個需求，幫我看看怎麼做」
- 「開一個新功能」

---

## 完整流程

### Step 1：讀取需求（Jira）

1. 用 `jira_get_issue` 取得 Issue 詳情
2. 從 description 解析出：
   - **要做什麼**：功能目標
   - **驗收標準**：怎樣算完成
   - **限制條件**：需要遵守的規範
3. 如果 description 不夠清楚，請使用者補充
4. 用 `jira_transition_issue` 將狀態轉為「進行中」
5. 用 `jira_add_comment` 留言：「AI Agent 開始處理此 Issue」

### Step 2：分析現有程式碼（BitBucket）

1. 用 `bitbucket_list_repos` 找到相關的 repo
2. 用 `bitbucket_get_file` 讀取需要修改的檔案
3. 分析：
   - 現有的程式碼架構
   - 要在哪裡加新功能
   - 有沒有可以復用的程式碼
4. 讀取相關的測試檔案，了解現有測試結構

**參考 Skill**：
- `register-spec.md`：如果涉及暫存器操作
- `novatek-coding-style.md`：確認命名和格式規範

### Step 3：設計方案

提出實作方案，包含：

```
設計方案格式：
1. 功能描述：一段話說明要做什麼
2. 修改清單：
   - {檔案}: {新增/修改什麼}
3. 新增檔案：（如果需要）
   - {新檔案}: {用途}
4. 測試計畫：
   - {測試 1}: {驗證什麼}
   - {測試 2}: {驗證什麼}
5. 影響評估：
   - 會影響的現有功能
   - 需要修改的測試
```

**重要**：方案產出後，等使用者確認再繼續。

### Step 4：實作程式碼

使用者確認方案後：

1. 修改/新增產品程式碼
2. 新增對應的測試
3. 確保：
   - 命名符合 `novatek-coding-style.md`
   - 每個公開函數有 docstring
   - 不使用裸 `except:`
   - 有邊界值測試

### Step 5：本機驗證

1. 跑 linter（`python -m py_compile`）
2. 跑相關測試（`pytest -v`）
3. 確認全部通過

### Step 6：CI 驗證（Jenkins）

1. 用 `jenkins_trigger_build` 觸發 CI Pipeline
2. 用 `jenkins_get_build` 等待結果
3. 如果 FAILURE：
   - 用 `jenkins_get_build_log` 讀取 log
   - 分析失敗原因
   - 修復並回到 Step 5
4. 如果 SUCCESS → 繼續

### Step 7：產生交付物

1. **Commit Message**：
   ```
   feat({模組}): {一句話描述功能}

   - {新增項目 1}
   - {新增項目 2}
   - 新增 {N} 個測試

   Closes {JIRA_KEY}
   ```

2. **PR 描述**：
   ```markdown
   ## Summary
   根據 {JIRA_KEY}（{Issue 標題}）的需求，{一句話說明}。

   ## Changes
   - `{檔案}`: {修改說明}

   ## Test Plan
   - [x] {測試 1}
   - [x] {測試 2}
   - [x] Jenkins CI Build #{build_number} 通過

   ## References
   - Jira: {JIRA_KEY}
   - Spec: register-spec.md（如果相關）

   Closes {JIRA_KEY}
   ```

### Step 8：回報 Jira（Jira）

1. 用 `jira_add_comment` 留言完成報告：
   ```
   AI Agent 開發完成報告

   功能：{功能描述}
   修改：{修改的檔案清單}
   測試：{N} 個新測試，全部通過
   CI：Jenkins Build #{build_number} SUCCESS

   等待 Code Review。
   ```

2. 用 `jira_transition_issue` 轉為「審核中」

---

## 範例對話

```
使用者：幫我做 KAN-10，新增暫存器位址對齊驗證

Agent：
  [Step 1] 讀取 KAN-10 需求...
  → jira_get_issue("KAN-10")
  → 需求：32-bit 暫存器位址必須是 4 的倍數，16-bit 要是 2 的倍數
  → 將 KAN-10 轉為「進行中」

  [Step 2] 分析現有程式碼...
  → bitbucket_get_file("validator.py") → 目前有 6 個驗證規則
  → bitbucket_get_file("models.py") → Register 有 width 欄位可用
  → bitbucket_get_file("tests/test_validator.py") → 21 個測試

  [Step 3] 我的實作方案：
  - validator.py: 新增 validate_address_alignment() 函數
  - tests/test_validator.py: 新增 3 個測試
    - 32-bit 對齊通過
    - 32-bit 未對齊偵測
    - 16-bit 對齊規則
  確認要繼續嗎？

使用者：好，繼續

  [Step 4] 實作中...（修改程式碼）
  [Step 5] 本機測試通過 ✓
  [Step 6] Jenkins CI Build #7: SUCCESS, 24 passed ✓
  [Step 7] 產生 commit message 和 PR 描述
  [Step 8] KAN-10 已更新，狀態轉為「審核中」

  全部完成！新增了 validate_address_alignment() 規則和 3 個測試。
```

---

## 注意事項

- Step 3（設計方案）之後一定要等使用者確認
- 每個 Step 都要告訴使用者進度
- 實作時嚴格遵守 `novatek-coding-style.md`
- CI 失敗最多重試 2 次
- 如果需求不明確，主動用問題釐清（不要猜）
