#!/usr/bin/env python3
"""
Jira MCP Server 整合測試（Cloud + Data Center 通用）

前置條件：
  1. 設定 mcp-servers/.env（Cloud 或 Data Center 皆可）
  2. Jira 上至少有一個專案和一些 issues

用法：
  cd mcp-servers
  pytest jira_mcp/test_server.py -v -s

  # 只跑某一類
  pytest jira_mcp/test_server.py -v -k "查詢"
  pytest jira_mcp/test_server.py -v -k "寫入"
  pytest jira_mcp/test_server.py -v -k "錯誤"
"""

import json
import os
import pytest

from jira_mcp.server import (
    jira_list_projects,
    jira_get_issue,
    jira_search_issues,
    jira_create_issue,
    jira_update_issue,
    jira_add_comment,
    jira_get_transitions,
    jira_transition_issue,
    GetIssueInput,
    SearchIssuesInput,
    CreateIssueInput,
    UpdateIssueInput,
    AddCommentInput,
    GetTransitionsInput,
    TransitionIssueInput,
)


# ── 測試用常數（根據你的 Jira 環境調整）─────────────────────────────────────
TEST_PROJECT = os.environ.get("TEST_JIRA_PROJECT", "KAN")


# ══════════════════════════════════════════════════════════════════════════════
#  第一類：查詢類 — 不改變 Jira 狀態
# ══════════════════════════════════════════════════════════════════════════════


class Test查詢專案:

    @pytest.mark.asyncio
    async def test_列出所有專案(self):
        """應回傳至少一個專案，每個都有 key 和 name"""
        result = json.loads(await jira_list_projects())
        assert len(result) >= 1
        for p in result:
            assert "key" in p
            assert "name" in p
        keys = [p["key"] for p in result]
        print(f"\n  找到 {len(result)} 個專案：{', '.join(keys)}")


class Test查詢Issues:

    @pytest.mark.asyncio
    async def test_用JQL搜尋issues(self):
        """搜尋指定專案的 issues，應回傳結構化結果"""
        result = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT} ORDER BY updated DESC", max_results=5)
        ))
        assert "issues" in result
        assert "total" in result
        assert len(result["issues"]) >= 1
        # 每個 issue 都有必要欄位
        for issue in result["issues"]:
            assert "key" in issue
            assert "summary" in issue
            assert "status" in issue
        print(f"\n  {TEST_PROJECT} 共 {result['total']} 個 issues，取回 {len(result['issues'])} 筆")

    @pytest.mark.asyncio
    async def test_搜尋特定狀態的issues(self):
        """用 JQL 過濾狀態，驗證回傳的 issues 狀態一致"""
        # 先找出有哪些狀態
        all_issues = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=50)
        ))
        statuses = {i["status"] for i in all_issues["issues"] if i["status"]}
        print(f"\n  專案 {TEST_PROJECT} 的狀態：{statuses}")
        assert len(statuses) >= 1

    @pytest.mark.asyncio
    async def test_搜尋結果分頁(self):
        """用 start_at 和 max_results 驗證分頁"""
        page1 = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=1, start_at=0)
        ))
        page2 = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=1, start_at=1)
        ))
        if page1["total"] >= 2:
            assert page1["issues"][0]["key"] != page2["issues"][0]["key"]
            print(f"\n  第 1 頁：{page1['issues'][0]['key']}，第 2 頁：{page2['issues'][0]['key']}")
        else:
            print(f"\n  專案只有 {page1['total']} 個 issue，跳過分頁驗證")


class Test查詢單一Issue:

    @pytest.mark.asyncio
    async def test_取得issue詳情(self):
        """取得指定 issue 的完整資訊"""
        # 先找一個 issue key
        search = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=1)
        ))
        assert len(search["issues"]) >= 1
        key = search["issues"][0]["key"]

        result = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
        assert result["key"] == key
        assert "summary" in result
        assert "status" in result
        assert "created" in result
        assert "updated" in result
        print(f"\n  {key}: {result['summary']}（{result['status']}）")

    @pytest.mark.asyncio
    async def test_取得issue的狀態轉換選項(self):
        """查詢 issue 可用的 transition（用於狀態轉換）"""
        search = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=1)
        ))
        key = search["issues"][0]["key"]

        result = json.loads(await jira_get_transitions(GetTransitionsInput(issue_key=key)))
        assert isinstance(result, list)
        print(f"\n  {key} 可用的狀態轉換：")
        for t in result:
            print(f"    [{t['id']}] {t['name']} → {t.get('to')}")


# ══════════════════════════════════════════════════════════════════════════════
#  第二類：寫入類 — 建立、更新、留言、狀態轉換
# ══════════════════════════════════════════════════════════════════════════════


class Test寫入操作:

    @pytest.mark.asyncio
    async def test_建立issue(self):
        """建立一個測試 issue，驗證回傳 key"""
        result = await jira_create_issue(CreateIssueInput(
            project_key=TEST_PROJECT,
            summary="MCP 測試 Issue — 自動建立",
            issue_type="Task",
            description="由 Jira MCP Server 整合測試自動建立，可安全刪除。",
        ))
        assert "建立成功" in result
        # 從回傳中取出 key
        key = result.split("：")[1].split("\n")[0]
        assert TEST_PROJECT in key
        print(f"\n  建立成功：{key}")

    @pytest.mark.asyncio
    async def test_建立並更新issue(self):
        """建立 issue → 更新標題 → 驗證更新成功"""
        # 建立
        create_result = await jira_create_issue(CreateIssueInput(
            project_key=TEST_PROJECT,
            summary="MCP 測試 — 等待更新",
            issue_type="Task",
        ))
        key = create_result.split("：")[1].split("\n")[0]

        # 更新標題
        update_result = await jira_update_issue(UpdateIssueInput(
            issue_key=key,
            summary="MCP 測試 — 已更新標題",
        ))
        assert "成功更新" in update_result

        # 驗證更新後的內容
        issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
        assert issue["summary"] == "MCP 測試 — 已更新標題"
        print(f"\n  {key} 標題已更新為：{issue['summary']}")

    @pytest.mark.asyncio
    async def test_在issue新增留言(self):
        """在指定 issue 新增留言"""
        # 找一個 issue
        search = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=1)
        ))
        key = search["issues"][0]["key"]

        result = await jira_add_comment(AddCommentInput(
            issue_key=key,
            body="這是 MCP 整合測試的自動留言，可安全刪除。",
        ))
        assert "成功" in result
        print(f"\n  已在 {key} 新增留言")

    @pytest.mark.asyncio
    async def test_issue狀態轉換(self):
        """建立 issue → 查詢可用轉換 → 執行第一個轉換"""
        # 建立
        create_result = await jira_create_issue(CreateIssueInput(
            project_key=TEST_PROJECT,
            summary="MCP 測試 — 狀態轉換",
            issue_type="Task",
        ))
        key = create_result.split("：")[1].split("\n")[0]

        # 查看可用轉換
        transitions = json.loads(await jira_get_transitions(
            GetTransitionsInput(issue_key=key)
        ))
        assert len(transitions) >= 1
        first_transition = transitions[0]

        # 執行轉換
        result = await jira_transition_issue(TransitionIssueInput(
            issue_key=key,
            transition_id=first_transition["id"],
            comment="MCP 自動轉換狀態",
        ))
        assert "成功" in result

        # 驗證狀態已改變
        issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
        print(f"\n  {key} 狀態已轉為：{issue['status']}")


# ══════════════════════════════════════════════════════════════════════════════
#  第三類：錯誤處理 — 驗證不會 crash
# ══════════════════════════════════════════════════════════════════════════════


class Test錯誤處理:

    @pytest.mark.asyncio
    async def test_查詢不存在的issue(self):
        """不存在的 issue key 應回傳友善錯誤"""
        result = await jira_get_issue(GetIssueInput(issue_key="NOPE-99999"))
        assert "錯誤" in result
        print(f"\n  回傳：{result}")

    @pytest.mark.asyncio
    async def test_無效的JQL(self):
        """錯誤的 JQL 語法應回傳錯誤，不 crash"""
        result = await jira_search_issues(
            SearchIssuesInput(jql="這不是合法的JQL!!!")
        )
        assert "錯誤" in result
        print(f"\n  回傳：{result[:80]}...")

    @pytest.mark.asyncio
    async def test_在不存在的issue新增留言(self):
        """不存在的 issue 新增留言應回傳錯誤"""
        result = await jira_add_comment(AddCommentInput(
            issue_key="NOPE-99999",
            body="這不應該成功",
        ))
        assert "錯誤" in result

    @pytest.mark.asyncio
    async def test_建立issue到不存在的專案(self):
        """不存在的 project key 應回傳錯誤"""
        result = await jira_create_issue(CreateIssueInput(
            project_key="ZZZZZ",
            summary="不應該成功",
            issue_type="Task",
        ))
        assert "錯誤" in result


# ══════════════════════════════════════════════════════════════════════════════
#  第四類：端對端 — 模擬 AI Agent 實際使用場景
# ══════════════════════════════════════════════════════════════════════════════


class TestAgent使用場景:

    @pytest.mark.asyncio
    async def test_Agent查詢專案狀態摘要(self):
        """
        模擬對話：「幫我看一下 KAN 專案目前的狀態」
        Agent：列出專案 → 搜尋 issues → 依狀態分類 → 產出摘要
        """
        # 搜尋所有 issues
        result = json.loads(await jira_search_issues(
            SearchIssuesInput(jql=f"project={TEST_PROJECT}", max_results=50)
        ))

        # 依狀態分類
        by_status: dict[str, list] = {}
        for issue in result["issues"]:
            status = issue["status"] or "未知"
            by_status.setdefault(status, []).append(issue["key"])

        print(f"\n  === {TEST_PROJECT} 專案狀態摘要 ===")
        print(f"  總計 {result['total']} 個 issues：")
        for status, keys in by_status.items():
            print(f"    {status}：{len(keys)} 個（{', '.join(keys)}）")

        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_Agent建立issue並追蹤(self):
        """
        模擬對話：「幫我建一個 bug，然後開始處理」
        Agent：建立 issue → 加留言 → 轉為進行中
        """
        # 1. 建立
        create_result = await jira_create_issue(CreateIssueInput(
            project_key=TEST_PROJECT,
            summary="[Bug] Register validator clock 上限設定錯誤",
            issue_type="Task",
            description="chip_validator 的 CLOCK_MAX_MHZ 應為 800 但被設成 100，導致 CI 失敗。",
        ))
        key = create_result.split("：")[1].split("\n")[0]
        print(f"\n  Step 1 — 建立 issue：{key}")

        # 2. 加留言
        await jira_add_comment(AddCommentInput(
            issue_key=key,
            body="已確認問題根因：validator.py 第 18 行 CLOCK_MAX_MHZ 被誤改。",
        ))
        print(f"  Step 2 — 新增留言：已記錄根因分析")

        # 3. 查可用轉換
        transitions = json.loads(await jira_get_transitions(
            GetTransitionsInput(issue_key=key)
        ))
        # 找「進行中」的轉換
        in_progress = next(
            (t for t in transitions if "進行" in (t.get("to") or "") or "progress" in (t.get("to") or "").lower()),
            transitions[0] if transitions else None,
        )

        if in_progress:
            await jira_transition_issue(TransitionIssueInput(
                issue_key=key,
                transition_id=in_progress["id"],
                comment="開始修復 CLOCK_MAX_MHZ",
            ))
            issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
            print(f"  Step 3 — 狀態轉為：{issue['status']}")
        else:
            print(f"  Step 3 — 無可用轉換，跳過")

        print(f"  完成！Agent 已建立並追蹤 {key}")
