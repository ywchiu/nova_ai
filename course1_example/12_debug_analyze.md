# Debug：先分析，不要先改

> 對應投影片：Part 9｜舊專案維護與 Debug（Debug Prompt）

接手一個有 bug 的舊專案，第一步永遠不是「叫 AI 直接修」。先讓 AI 把現況講清楚。

情境：Repeated Error Signatures 遇到大小寫不同的訊息會被分成兩類，預期應該視為同一類。

---

目前 Repeated Error Signatures 有一個 bug：

大小寫不同的相同錯誤訊息應視為同一個 signature，但目前被分成兩類。

範例：

```
ERROR: Timeout waiting for tx_done
ERROR: timeout waiting for tx_done
```

這兩筆應該被聚合成同一個 signature，count = 2。但目前 count = 1, 1。

請先不要修改程式碼。請先：

1. 閱讀相關 spec、tests、src 三邊的內容
2. 找出目前 normalization 的邏輯在哪裡實作
3. 說明可能的 root cause（兩到三個假設都要列）
4. 提出 debug 計畫（要先看哪幾個地方、要新增什麼 log/print 來驗證）
5. 建議應該新增哪一個 regression test 才能在修復後守住這個行為
6. 如果目前程式已經正確把大小寫不同的訊息合併，請明確回報「bug 無法重現」，並指出還缺哪個 regression test 來防止未來退化

回報之後等我確認再進入下一步。
