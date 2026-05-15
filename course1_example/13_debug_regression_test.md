# Debug：先補 regression test，再修

> 對應投影片：Part 9｜舊專案維護與 Debug（Regression Test Prompt）

確認 root cause 之後，下一步不是改實作，是先把 regression test 補上。

---

承上題的 bug。請先新增 regression test，行為要求：

- 同一個錯誤訊息，大小寫不同
- 預期被合併成同一個 signature，count = 2
- related test names 要同時包含兩個 test

新增測試之後，執行 pytest，貼出結果。若目前程式仍有 bug，這時候應該 fail；若測試已經 pass，請回報 bug 目前無法重現，保留 regression test，並不要為了製造 RED 而改壞程式。

如果測試確實 fail，再做最小修改讓測試通過。修改時只動 normalization 那段，不要順手重構別的地方。

完成之後執行全部 pytest，回報以下四點：

1. **Root cause**：問題出在哪一個 function 的哪一行
2. **修改內容**：實際改了什麼
3. **測試結果**：pytest pass/fail 數量
4. **是否有剩餘風險**：例如：這個 normalization 改動會不會影響到別的測試？

如果使用者已開啟 auto-act，可以連續完成「新增 regression test -> 確認 fail -> 最小修正 -> 全部 pytest」四步。最後報告每一步的實際結果與 pytest output 摘要。

如果使用者沒有要求 auto-act，才每一步先停下來等我確認，不要連跑。
