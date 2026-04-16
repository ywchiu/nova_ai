#!/usr/bin/env python3
"""
Demo #3：Issue 彙整與報表產生（對應課程 AI Agent Design W2）

完整模擬工作流程：
  1. 用自然語言下指令：「收集 KAN 專案的所有 Issue，整理成摘要」
  2. Agent 串接 Jira API 讀取 Issues
  3. AI 進行篩選、分類、風險標註
  4. 自動產生週報（搭配 weekly-report.md Skill 模板）

用法：
  cd mcp-servers
  pytest jira_mcp/test_demo_report.py -v -s
"""

import json
import os
from datetime import datetime
import pytest

from jira_mcp.server import (
    jira_list_projects,
    jira_search_issues,
    SearchIssuesInput,
)

TEST_PROJECT = os.environ.get("TEST_JIRA_PROJECT", "KAN")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 1：Agent 收集專案全部 Issues
# ══════════════════════════════════════════════════════════════════════════════


class TestStep1_收集Issues:

    @pytest.mark.asyncio
    async def test_搜尋專案全部issues(self):
        """Agent 用 JQL 撈出專案所有 issues"""
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f"project={TEST_PROJECT} ORDER BY updated DESC",
            max_results=50,
        )))
        assert result["total"] >= 1
        print(f"\n  {TEST_PROJECT} 專案共 {result['total']} 個 issues")

    @pytest.mark.asyncio
    async def test_依狀態分類統計(self):
        """Agent 依狀態分類，產出統計數字"""
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f"project={TEST_PROJECT}",
            max_results=50,
        )))
        by_status: dict[str, int] = {}
        for issue in result["issues"]:
            status = issue["status"] or "未知"
            by_status[status] = by_status.get(status, 0) + 1

        print(f"\n  === {TEST_PROJECT} 狀態分佈 ===")
        for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
            print(f"    {status}: {count} 個")

        assert sum(by_status.values()) == result["total"]


# ══════════════════════════════════════════════════════════════════════════════
#  Step 2：Agent 篩選分類與風險標註
# ══════════════════════════════════════════════════════════════════════════════


class TestStep2_篩選分類:

    @pytest.mark.asyncio
    async def test_找出Bug類型的Issues(self):
        """Agent 篩選標題含 [Bug] 的 issues"""
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "Bug"',
            max_results=50,
        )))
        print(f"\n  Bug issues: {result['total']} 個")
        for issue in result["issues"]:
            print(f"    {issue['key']}: {issue['summary']}")

    @pytest.mark.asyncio
    async def test_找出Feature類型的Issues(self):
        """Agent 篩選標題含 [Feature] 的 issues"""
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "Feature"',
            max_results=50,
        )))
        print(f"\n  Feature issues: {result['total']} 個")
        for issue in result["issues"]:
            print(f"    {issue['key']}: {issue['summary']}")

    @pytest.mark.asyncio
    async def test_風險標註_超過3天未更新(self):
        """Agent 標註超過 3 天沒更新的 issues 為風險"""
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND updated <= -3d',
            max_results=50,
        )))
        print(f"\n  風險 issues（超過 3 天未更新）: {result['total']} 個")
        for issue in result["issues"]:
            print(f"    ⚠ {issue['key']}: {issue['summary']}（{issue['updated'][:10]}）")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 3：產生完整週報
# ══════════════════════════════════════════════════════════════════════════════


class TestStep3_產生報表:

    @pytest.mark.asyncio
    async def test_產生Markdown週報(self):
        """
        Agent 根據 weekly-report.md Skill 模板，
        將 Jira 資料填入，產生完整的 Markdown 週報。
        """
        # 撈所有 issues
        all_issues = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f"project={TEST_PROJECT} ORDER BY status ASC",
            max_results=50,
        )))

        # 分類
        done = [i for i in all_issues["issues"] if i["status"] and "完成" in i["status"]]
        in_progress = [i for i in all_issues["issues"] if i["status"] and "進行" in i["status"]]
        todo = [i for i in all_issues["issues"] if i["status"] and ("待辦" in i["status"] or "To Do" in (i["status"] or ""))]
        # 風險：標題含 Bug 或超過一定時間
        risk = [i for i in all_issues["issues"] if "Bug" in (i["summary"] or "")]

        # 產生週報
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        report = f"""# {TEST_PROJECT} 專案週報

**期間**：本週
**撰寫者**：AI 助理（資料來源：Jira MCP）
**產出時間**：{now}

---

## 摘要

| 指標 | 數量 |
|------|------|
| 總計 | {all_issues['total']} |
| 已完成 | {len(done)} |
| 進行中 | {len(in_progress)} |
| 待辦 | {len(todo)} |
| 風險項目 | {len(risk)} |

---

## 進行中

| Issue | 標題 | 負責人 | 狀態 |
|-------|------|--------|------|
"""
        for i in in_progress:
            report += f"| {i['key']} | {i['summary']} | {i['assignee']} | {i['status']} |\n"

        report += f"""
---

## 待辦事項

| Issue | 標題 | 負責人 |
|-------|------|--------|
"""
        for i in todo:
            report += f"| {i['key']} | {i['summary']} | {i['assignee']} |\n"

        if risk:
            report += f"""
---

## 風險與卡關

| Issue | 標題 | 風險原因 |
|-------|------|---------|
"""
            for i in risk:
                report += f"| {i['key']} | {i['summary']} | 標記為 Bug |\n"

        print(f"\n{report}")

        # 驗證報表結構
        assert f"# {TEST_PROJECT} 專案週報" in report
        assert "## 摘要" in report
        assert "## 進行中" in report
        assert "## 待辦事項" in report


# ══════════════════════════════════════════════════════════════════════════════
#  端對端：完整報表產生流程
# ══════════════════════════════════════════════════════════════════════════════


class TestE2E_報表產生:

    @pytest.mark.asyncio
    async def test_完整流程_從指令到週報(self):
        """
        模擬課堂 Demo W2 的完整對話：

        使用者：「收集 KAN 專案的 Issue，整理成週報」
        Agent：
          1. 列出專案確認存在
          2. 搜尋所有 issues
          3. 分類統計
          4. 產生結構化報表
        """
        print("\n  ═══════════════════════════════════════")
        print("  Issue 彙整報表 — 完整流程 Demo")
        print("  ═══════════════════════════════════════")

        # 1. 確認專案存在
        projects = json.loads(await jira_list_projects())
        project_keys = [p["key"] for p in projects]
        assert TEST_PROJECT in project_keys
        print(f"\n  [Step 1] 確認專案 {TEST_PROJECT} 存在 ✓")

        # 2. 搜尋所有 issues
        all_data = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f"project={TEST_PROJECT} ORDER BY updated DESC",
            max_results=50,
        )))
        total = all_data["total"]
        print(f"  [Step 2] 搜尋到 {total} 個 issues")

        # 3. 分類統計
        by_status: dict[str, list] = {}
        by_type: dict[str, list] = {}  # 從 summary prefix 推斷
        for issue in all_data["issues"]:
            status = issue["status"] or "未知"
            by_status.setdefault(status, []).append(issue)
            # 從 summary 推斷類型
            summary = issue["summary"] or ""
            if "[Bug]" in summary:
                by_type.setdefault("Bug", []).append(issue)
            elif "[Feature]" in summary:
                by_type.setdefault("Feature", []).append(issue)
            elif "[Done]" in summary:
                by_type.setdefault("已完成", []).append(issue)
            else:
                by_type.setdefault("其他", []).append(issue)

        print(f"  [Step 3] 分類完成：")
        print(f"    依狀態：{', '.join(f'{k}({len(v)})' for k, v in by_status.items())}")
        print(f"    依類型：{', '.join(f'{k}({len(v)})' for k, v in by_type.items())}")

        # 4. 產生摘要報表
        now = datetime.now().strftime("%Y-%m-%d")
        print(f"\n  [Step 4] 產生報表：")
        print(f"    ┌─────────────────────────────────────┐")
        print(f"    │  {TEST_PROJECT} 專案週報 — {now}          │")
        print(f"    ├─────────────────────────────────────┤")
        print(f"    │  總計 issues：{total:>3} 個                 │")
        for status, issues in by_status.items():
            print(f"    │    {status}：{len(issues):>3} 個                    │")
        print(f"    ├─────────────────────────────────────┤")
        if by_type.get("Bug"):
            print(f"    │  ⚠ Bug：{len(by_type['Bug'])} 個                       │")
            for b in by_type["Bug"]:
                print(f"    │    • {b['key']}: {b['summary'][:30]}│")
        print(f"    └─────────────────────────────────────┘")

        print("\n  ═══════════════════════════════════════")
        print("  Demo 完成！")
        print("  ═══════════════════════════════════════")
