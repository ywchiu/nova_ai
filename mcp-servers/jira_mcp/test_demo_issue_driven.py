#!/usr/bin/env python3
"""
Demo #1：Issue 驅動程式開發（對應課程 Vibe Coding W1）

完整模擬工作流程：
  1. 從 Jira 讀取一張 Feature Request Issue
  2. AI 解析需求 → 產生新的驗證規則程式碼
  3. AI 產生對應的測試程式碼
  4. 執行測試確認通過
  5. 產生 commit message 和 PR 描述
  6. 回 Jira 更新狀態並留言

用法：
  cd mcp-servers
  pytest jira_mcp/test_demo_issue_driven.py -v -s
"""

import json
import os
import pytest

from jira_mcp.server import (
    jira_get_issue,
    jira_search_issues,
    jira_add_comment,
    jira_get_transitions,
    jira_transition_issue,
    GetIssueInput,
    SearchIssuesInput,
    AddCommentInput,
    GetTransitionsInput,
    TransitionIssueInput,
)

TEST_PROJECT = os.environ.get("TEST_JIRA_PROJECT", "KAN")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 1：從 Jira 讀取需求
# ══════════════════════════════════════════════════════════════════════════════


class TestStep1_從Jira讀取需求:

    @pytest.mark.asyncio
    async def test_搜尋Feature類型的Issue(self):
        """
        Agent 收到：「幫我看看有什麼新的 feature request」
        → 用 JQL 搜尋標題含 [Feature] 的 issues
        """
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "Feature" ORDER BY updated DESC',
            max_results=10,
        )))
        assert result["total"] >= 1
        features = result["issues"]
        print(f"\n  找到 {len(features)} 個 Feature Request：")
        for issue in features:
            print(f"    {issue['key']}: {issue['summary']}（{issue['status']}）")

    @pytest.mark.asyncio
    async def test_讀取Issue詳情取得需求描述(self):
        """
        Agent 讀取特定 Issue 的 description，從中解析出：
        - 要做什麼（新增位址對齊驗證）
        - 驗證規則（address % 4 == 0）
        - 嚴重度（ERROR）
        """
        # 找到位址對齊的 issue
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "位址對齊"',
            max_results=1,
        )))
        assert result["total"] >= 1
        key = result["issues"][0]["key"]

        issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
        desc = issue["description"]

        print(f"\n  === {key}: {issue['summary']} ===")
        print(f"  狀態：{issue['status']}")
        print(f"  描述：{desc[:200]}...")

        # Agent 能從 description 解析出關鍵資訊
        assert "address" in desc.lower() or "位址" in desc
        assert "4" in desc  # 4 的倍數
        assert "ERROR" in desc or "error" in desc.lower()


# ══════════════════════════════════════════════════════════════════════════════
#  Step 2：根據 Issue 需求，產生驗證規則
# ══════════════════════════════════════════════════════════════════════════════


class TestStep2_AI產生程式碼:

    @pytest.mark.asyncio
    async def test_根據Issue產生驗證規則(self):
        """
        模擬 Agent 根據 Issue description 產生新的驗證規則。
        實際上這裡驗證「程式碼邏輯正確性」。
        """
        # 模擬 AI 根據 Issue 產生的驗證函數
        from chip_validator.models import ChipConfig, Register
        from chip_validator.validator import ValidationError

        def validate_address_alignment(config: ChipConfig) -> list[ValidationError]:
            """（AI 產生）驗證暫存器位址是否對齊"""
            errors = []
            for reg in config.registers:
                alignment = 4 if reg.width == 32 else 2
                if reg.address % alignment != 0:
                    errors.append(ValidationError(
                        rule="address_alignment",
                        message=f"位址 0x{reg.address:04X} 未對齊（{reg.width}-bit 暫存器需對齊到 {alignment} bytes）",
                        register=reg.name,
                    ))
            return errors

        # 測試 1：對齊的位址 → 無錯誤
        good_config = ChipConfig(
            chip_name="TEST",
            registers=[
                Register(name="CTRL_REG", address=0x0000, width=32),
                Register(name="STATUS_REG", address=0x0004, width=32),
            ],
            clock_freq_mhz=200.0,
            voltage_mv=900,
        )
        assert validate_address_alignment(good_config) == []
        print("\n  測試 1 通過：對齊的位址 → 零錯誤")

        # 測試 2：未對齊的位址 → 應偵測到
        bad_config = ChipConfig(
            chip_name="TEST",
            registers=[
                Register(name="CTRL_REG", address=0x0000, width=32),
                Register(name="BAD_REG", address=0x0003, width=32),  # 未對齊
            ],
            clock_freq_mhz=200.0,
            voltage_mv=900,
        )
        errors = validate_address_alignment(bad_config)
        assert len(errors) == 1
        assert errors[0].rule == "address_alignment"
        assert "BAD_REG" in errors[0].register
        print(f"  測試 2 通過：未對齊位址 → {errors[0].message}")

        # 測試 3：16-bit 暫存器用 2-byte 對齊
        config_16bit = ChipConfig(
            chip_name="TEST",
            registers=[
                Register(name="CTRL_REG", address=0x0000, width=32),
                Register(name="STATUS_REG", address=0x0004, width=32),
                Register(name="SMALL_REG", address=0x0006, width=16),  # 2-byte 對齊 OK
                Register(name="BAD_16", address=0x0007, width=16),    # 未對齊
            ],
            clock_freq_mhz=200.0,
            voltage_mv=900,
        )
        errors = validate_address_alignment(config_16bit)
        assert len(errors) == 1
        assert "BAD_16" in errors[0].register
        print(f"  測試 3 通過：16-bit 暫存器 2-byte 對齊 → {errors[0].message}")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 3：產生 Commit Message 和 PR 描述
# ══════════════════════════════════════════════════════════════════════════════


class TestStep3_產生CommitMessage:

    @pytest.mark.asyncio
    async def test_根據Issue產生commit_message(self):
        """
        Agent 根據 Issue key 和實作內容，產生結構化的 commit message。
        """
        # 取得 issue 資訊
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "位址對齊"',
            max_results=1,
        )))
        key = result["issues"][0]["key"]
        summary = result["issues"][0]["summary"]

        # Agent 產生的 commit message
        commit_msg = f"feat(validator): 新增暫存器位址對齊驗證規則\n\n" \
                     f"- 32-bit 暫存器位址必須是 4 的倍數\n" \
                     f"- 16-bit 暫存器位址必須是 2 的倍數\n" \
                     f"- 新增 validate_address_alignment() 函數\n" \
                     f"- 新增 3 個對應的單元測試\n\n" \
                     f"Closes {key}"

        # 驗證 commit message 格式
        assert key in commit_msg
        assert "feat" in commit_msg
        assert "validator" in commit_msg
        print(f"\n  === Commit Message ===\n{commit_msg}")

        # Agent 產生的 PR 描述
        pr_body = f"## Summary\n\n" \
                  f"根據 {key}（{summary}）的需求，新增暫存器位址對齊驗證規則。\n\n" \
                  f"## Changes\n\n" \
                  f"- `chip_validator/validator.py`：新增 `validate_address_alignment()`\n" \
                  f"- `chip_validator/tests/test_validator.py`：新增 3 個測試案例\n\n" \
                  f"## Test Plan\n\n" \
                  f"- [x] 對齊位址 → 零錯誤\n" \
                  f"- [x] 32-bit 未對齊 → 偵測到 ERROR\n" \
                  f"- [x] 16-bit 暫存器用 2-byte 對齊\n\n" \
                  f"Closes {key}"

        assert key in pr_body
        print(f"\n  === PR Description ===\n{pr_body}")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 4：回 Jira 更新狀態
# ══════════════════════════════════════════════════════════════════════════════


class TestStep4_回Jira更新:

    @pytest.mark.asyncio
    async def test_完成後回Jira留言並更新狀態(self):
        """
        Agent 完成實作後：
        1. 在 Issue 留言記錄做了什麼
        2. 轉換狀態為「進行中」
        """
        # 找到 issue
        result = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "位址對齊"',
            max_results=1,
        )))
        key = result["issues"][0]["key"]

        # 留言
        comment_result = await jira_add_comment(AddCommentInput(
            issue_key=key,
            body="AI Agent 已完成實作：\n"
                 "- 新增 validate_address_alignment() 驗證規則\n"
                 "- 新增 3 個單元測試，全部通過\n"
                 "- PR 已建立，等待 Code Review",
        ))
        assert "成功" in comment_result
        print(f"\n  已在 {key} 留言：實作完成通知")

        # 查可用轉換
        transitions = json.loads(await jira_get_transitions(
            GetTransitionsInput(issue_key=key)
        ))
        # 找「進行中」
        in_progress = next(
            (t for t in transitions if "進行" in (t.get("to") or "") or "progress" in (t.get("to") or "").lower()),
            None,
        )

        if in_progress:
            await jira_transition_issue(TransitionIssueInput(
                issue_key=key,
                transition_id=in_progress["id"],
                comment="AI Agent 開始處理此 Issue",
            ))
            issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
            print(f"  {key} 狀態已轉為：{issue['status']}")
        else:
            print(f"  {key} 無「進行中」轉換可用，跳過")


# ══════════════════════════════════════════════════════════════════════════════
#  端對端：完整 Issue 驅動開發流程
# ══════════════════════════════════════════════════════════════════════════════


class TestE2E_Issue驅動開發:

    @pytest.mark.asyncio
    async def test_完整流程_從Issue到程式碼(self):
        """
        模擬課堂 Demo 的完整對話：

        使用者：「幫我看 KAN 專案有什麼 feature request，挑一個來做」
        Agent：
          1. 搜尋 Feature issues
          2. 讀取需求描述
          3. 根據需求產生程式碼和測試
          4. 確認測試通過
          5. 產生 commit message
          6. 回 Jira 留言
        """
        print("\n  ═══════════════════════════════════════")
        print("  Issue 驅動程式開發 — 完整流程 Demo")
        print("  ═══════════════════════════════════════")

        # 1. 搜尋 Feature issues
        features = json.loads(await jira_search_issues(SearchIssuesInput(
            jql=f'project={TEST_PROJECT} AND summary ~ "Feature" AND status != "完成" ORDER BY updated DESC',
            max_results=5,
        )))
        print(f"\n  [Step 1] 找到 {features['total']} 個待處理的 Feature Request")
        for f in features["issues"]:
            print(f"    • {f['key']}: {f['summary']}")

        # 2. 讀取第一個 feature 的詳情
        target_key = features["issues"][0]["key"]
        issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=target_key)))
        print(f"\n  [Step 2] 選擇 {target_key}: {issue['summary']}")
        desc = issue["description"] or ""
        print(f"    需求摘要：{desc[:100]}...")

        # 3. 模擬 AI 根據需求產生程式碼
        print(f"\n  [Step 3] AI 分析需求，產生驗證規則...")
        from chip_validator.models import ChipConfig, Register
        from chip_validator.validator import ValidationError

        # AI 產生的新規則（根據 Issue 描述）
        def new_rule(config: ChipConfig) -> list[ValidationError]:
            errors = []
            for reg in config.registers:
                alignment = 4 if reg.width == 32 else 2
                if reg.address % alignment != 0:
                    errors.append(ValidationError(
                        rule="address_alignment",
                        message=f"位址 0x{reg.address:04X} 未對齊",
                        register=reg.name,
                    ))
            return errors

        print("    產生 validate_address_alignment() 函數")

        # 4. 跑測試
        test_config = ChipConfig(
            chip_name="TEST", clock_freq_mhz=200.0, voltage_mv=900,
            registers=[
                Register(name="CTRL_REG", address=0x0000, width=32),
                Register(name="STATUS_REG", address=0x0004, width=32),
            ],
        )
        assert new_rule(test_config) == []

        bad_config = ChipConfig(
            chip_name="TEST", clock_freq_mhz=200.0, voltage_mv=900,
            registers=[
                Register(name="CTRL_REG", address=0x0000, width=32),
                Register(name="STATUS_REG", address=0x0004, width=32),
                Register(name="BAD", address=0x0003, width=32),
            ],
        )
        assert len(new_rule(bad_config)) == 1
        print("    測試全部通過 ✓")

        # 5. 產生 commit message
        commit = f"feat(validator): 新增位址對齊驗證 — Closes {target_key}"
        print(f"\n  [Step 4] Commit: {commit}")

        # 6. 回 Jira 留言
        await jira_add_comment(AddCommentInput(
            issue_key=target_key,
            body=f"AI Agent 完成實作：\n"
                 f"- 新增 validate_address_alignment() 規則\n"
                 f"- 2 個測試通過\n"
                 f"- Commit: {commit}",
        ))
        print(f"  [Step 5] 已在 {target_key} 留言通知完成")

        print("\n  ═══════════════════════════════════════")
        print("  Demo 完成！")
        print("  ═══════════════════════════════════════")
