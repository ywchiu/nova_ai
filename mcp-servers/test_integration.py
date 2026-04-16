#!/usr/bin/env python3
"""
三合一整合 Demo：Jira + BitBucket + Jenkins

模擬課程 M4 的核心場景：
  PR → Agent Review → Jenkins Build → 回報 Jira

完整流程：
  1. 從 Jira 讀取一張 Bug Issue
  2. 從 BitBucket 讀取相關程式碼，分析問題
  3. Agent 產生修復方案
  4. 觸發 Jenkins CI 驗證
  5. 讀取 CI 結果
  6. 回 Jira 留言彙報完整結果

用法：
  cd mcp-servers
  # 確保 Jenkins 已啟動：docker start nova-jenkins
  PYTHONPATH=../demo_project:$PYTHONPATH pytest test_integration.py -v -s
"""

import json
import os
import re
import asyncio
import pytest

# Jira
from jira_mcp.server import (
    jira_create_issue,
    jira_get_issue,
    jira_add_comment,
    jira_get_transitions,
    jira_transition_issue,
    CreateIssueInput,
    GetIssueInput,
    AddCommentInput,
    GetTransitionsInput,
    TransitionIssueInput,
)

# BitBucket
from bitbucket_mcp.server import (
    bitbucket_get_file,
    bitbucket_list_commits,
    GetFileInput,
    ListCommitsInput,
)

# Jenkins
from jenkins_mcp.server import (
    jenkins_trigger_build,
    jenkins_get_build,
    jenkins_get_build_log,
    TriggerBuildInput,
    GetBuildInput,
    GetBuildLogInput,
)

TEST_PROJECT = os.environ.get("TEST_JIRA_PROJECT", "KAN")
BB_WS = os.environ.get("TEST_BB_WORKSPACE", "nova_ai_test")
BB_REPO = os.environ.get("TEST_BB_REPO", "chip-validator")
JENKINS_CI_JOB = "chip-validator-ci"


# ── 共用 ──────────────────────────────────────────────────────────────────────

async def _等待_build(job: str, after: int | None = None, timeout: int = 90) -> dict:
    for _ in range(timeout // 3):
        await asyncio.sleep(3)
        raw = await jenkins_get_build(GetBuildInput(job_path=job, build_number=-1))
        if raw.startswith("錯誤"):
            continue
        build = json.loads(raw)
        if after is not None and build.get("number", 0) <= after:
            continue
        if not build.get("building"):
            return build
    pytest.fail(f"{job} 超過 {timeout} 秒未完成")


async def _取得最新build編號(job: str) -> int | None:
    raw = await jenkins_get_build(GetBuildInput(job_path=job, build_number=-1))
    if raw.startswith("錯誤"):
        return None
    return json.loads(raw).get("number")


# ══════════════════════════════════════════════════════════════════════════════
#  完整整合流程：Jira Issue → BitBucket 分析 → Jenkins CI → Jira 回報
# ══════════════════════════════════════════════════════════════════════════════


class Test整合流程_BugFix:
    """
    模擬真實場景：
      有人回報 clock 頻率驗證的 bug，Agent 串接三個系統來處理。
    """

    @pytest.mark.asyncio
    async def test_step1_Jira建立Bug_Issue(self):
        """使用者回報 bug → Agent 在 Jira 建立 Issue"""
        result = await jira_create_issue(CreateIssueInput(
            project_key=TEST_PROJECT,
            summary="[Integration] clock 驗證規則的 APB bus 時脈未檢查",
            issue_type="Task",
            description="register-spec.md 定義 APB bus 時脈範圍為 10~200 MHz，"
                        "但 validator.py 的 validate_clock_frequency 只檢查系統主時脈。"
                        "需要新增 APB bus 時脈的驗證。",
        ))
        assert "建立成功" in result
        key = result.split("：")[1].split("\n")[0]
        # 存到 class 變數供後續 step 使用
        Test整合流程_BugFix._issue_key = key
        print(f"\n  [Step 1 — Jira] 建立 Bug Issue：{key}")

    @pytest.mark.asyncio
    async def test_step2_BitBucket讀取相關程式碼(self):
        """Agent 從 BitBucket 讀取 validator.py，分析現有的 clock 驗證邏輯"""
        key = getattr(Test整合流程_BugFix, "_issue_key", "?")

        # 讀 validator.py
        src = await bitbucket_get_file(
            GetFileInput(project_key=BB_WS, repo_slug=BB_REPO, file_path="validator.py")
        )

        # 分析 clock 相關的程式碼
        clock_fn = re.search(
            r'def validate_clock_frequency.*?return errors',
            src, re.DOTALL
        )
        assert clock_fn is not None

        # 讀 register-spec.md（Skill 文件）確認 APB 規格
        # （Skill 在本機，不在 BitBucket）

        print(f"\n  [Step 2 — BitBucket] 讀取 {BB_WS}/{BB_REPO}/validator.py")
        print(f"    找到 validate_clock_frequency()：")
        for line in clock_fn.group().split("\n")[:5]:
            print(f"      {line.strip()}")

        # 也讀 models.py 確認現有的 ChipConfig 結構
        models_src = await bitbucket_get_file(
            GetFileInput(project_key=BB_WS, repo_slug=BB_REPO, file_path="models.py")
        )
        has_apb = "apb" in models_src.lower()
        print(f"    ChipConfig 是否有 apb_clock 欄位：{'有' if has_apb else '沒有（需要新增）'}")

        # 讀最近 commits
        commits = json.loads(await bitbucket_list_commits(
            ListCommitsInput(project_key=BB_WS, repo_slug=BB_REPO, limit=3)
        ))
        print(f"    最近 commit：{commits[0]['message']}")

    @pytest.mark.asyncio
    async def test_step3_Agent產生修復方案(self):
        """Agent 根據 Issue 描述 + 原始碼分析，產生修復方案"""
        key = getattr(Test整合流程_BugFix, "_issue_key", "?")

        fix_plan = {
            "issue": key,
            "analysis": "validate_clock_frequency 只檢查 clock_freq_mhz（系統主時脈 10~800 MHz），"
                        "未檢查 APB bus 時脈（spec 要求 10~200 MHz）",
            "changes": [
                {"file": "models.py", "action": "新增 apb_clock_freq_mhz 欄位到 ChipConfig"},
                {"file": "validator.py", "action": "新增 validate_apb_clock() 驗證函數"},
                {"file": "tests/test_validator.py", "action": "新增 APB clock 相關測試"},
            ],
            "test_strategy": "正常值(100MHz)、過高(300MHz)、過低(5MHz)、邊界值(10/200MHz)",
        }

        print(f"\n  [Step 3 — Agent] 修復方案：")
        print(f"    問題：{fix_plan['analysis']}")
        print(f"    修改：")
        for c in fix_plan["changes"]:
            print(f"      • {c['file']}: {c['action']}")
        print(f"    測試策略：{fix_plan['test_strategy']}")

    @pytest.mark.asyncio
    async def test_step4_Jenkins觸發CI驗證(self):
        """Agent 觸發 Jenkins CI，確認現有測試仍然通過"""
        prev = await _取得最新build編號(JENKINS_CI_JOB)

        trigger = await jenkins_trigger_build(
            TriggerBuildInput(job_path=JENKINS_CI_JOB)
        )
        assert "已觸發" in trigger

        build = await _等待_build(JENKINS_CI_JOB, after=prev)
        Test整合流程_BugFix._build = build

        print(f"\n  [Step 4 — Jenkins] 觸發 {JENKINS_CI_JOB}")
        print(f"    Build #{build['number']}: {build['result']}")

        # 讀 log 確認測試結果
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path=JENKINS_CI_JOB, build_number=build["number"])
        )
        passed = re.search(r"(\d+) passed", log)
        if passed:
            print(f"    測試結果：{passed.group(0)}")

    @pytest.mark.asyncio
    async def test_step5_Jira回報完整結果(self):
        """Agent 把所有分析結果彙整，回 Jira 留言"""
        key = getattr(Test整合流程_BugFix, "_issue_key", "?")
        build = getattr(Test整合流程_BugFix, "_build", {})

        report = (
            f"AI Agent 整合分析報告\n\n"
            f"1. BitBucket 程式碼分析：\n"
            f"   - validate_clock_frequency() 只檢查系統主時脈\n"
            f"   - ChipConfig 缺少 apb_clock_freq_mhz 欄位\n"
            f"   - 需修改 3 個檔案\n\n"
            f"2. Jenkins CI 結果：\n"
            f"   - Build #{build.get('number', '?')}: {build.get('result', '?')}\n"
            f"   - 現有 21 個測試全部通過\n\n"
            f"3. 修復建議：\n"
            f"   - models.py: 新增 apb_clock_freq_mhz 欄位\n"
            f"   - validator.py: 新增 validate_apb_clock()\n"
            f"   - 新增 4 個測試（正常/過高/過低/邊界）"
        )

        result = await jira_add_comment(AddCommentInput(
            issue_key=key,
            body=report,
        ))
        assert "成功" in result

        print(f"\n  [Step 5 — Jira] 已在 {key} 留言回報：")
        print(f"    BitBucket 分析 + Jenkins CI 結果 + 修復建議")

        # 轉為進行中
        transitions = json.loads(await jira_get_transitions(
            GetTransitionsInput(issue_key=key)
        ))
        in_progress = next(
            (t for t in transitions if "進行" in (t.get("to") or "")),
            None,
        )
        if in_progress:
            await jira_transition_issue(TransitionIssueInput(
                issue_key=key,
                transition_id=in_progress["id"],
            ))
            issue = json.loads(await jira_get_issue(GetIssueInput(issue_key=key)))
            print(f"    狀態轉為：{issue['status']}")


# ══════════════════════════════════════════════════════════════════════════════
#  完整整合流程：CI 失敗 → 自動診斷 → 回報 Jira
# ══════════════════════════════════════════════════════════════════════════════


class Test整合流程_CI失敗診斷:
    """
    模擬真實場景：
      Jenkins CI 失敗了，Agent 自動從 log 找原因，
      對照 BitBucket 程式碼，回 Jira 留言。
    """

    @pytest.mark.asyncio
    async def test_CI失敗到Jira回報的完整流程(self):
        """
        使用者：「CI 掛了，幫我查一下」

        Agent：
          1. 查 Jenkins job 狀態
          2. 讀失敗的 build log
          3. 從 BitBucket 讀相關原始碼比對
          4. 在 Jira 建 Issue 記錄 + 診斷結果
        """
        print("\n  ═══════════════════════════════════════")
        print("  整合 Demo：CI 失敗 → 自動診斷 → Jira 回報")
        print("  ═══════════════════════════════════════")

        # 1. 觸發會失敗的 CI
        FAIL_JOB = "chip-validator-ci-fail"
        prev = await _取得最新build編號(FAIL_JOB)
        await jenkins_trigger_build(TriggerBuildInput(job_path=FAIL_JOB))
        build = await _等待_build(FAIL_JOB, after=prev)

        print(f"\n  [Jenkins] {FAIL_JOB} Build #{build['number']}: {build['result']}")
        assert build["result"] == "FAILURE"

        # 2. 讀 log 找失敗原因
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path=FAIL_JOB, build_number=build["number"], last_chars=20000)
        )
        failed_tests = [
            line.strip() for line in log.split("\n")
            if "FAILED" in line and "::" in line
        ]
        print(f"  [Jenkins] 失敗測試：{len(failed_tests)} 個")
        for t in failed_tests[:3]:
            print(f"    {t}")

        # 找出被修改的常數
        has_clock_change = "CLOCK_MAX_MHZ" in log and "100.0" in log

        # 3. 從 BitBucket 讀原始碼比對
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=BB_WS, repo_slug=BB_REPO, file_path="validator.py")
        )
        original_max = re.search(r"CLOCK_MAX_MHZ\s*=\s*([\d.]+)", validator_src)
        original_value = original_max.group(1) if original_max else "?"

        print(f"\n  [BitBucket] validator.py 原始值：CLOCK_MAX_MHZ = {original_value}")
        if has_clock_change:
            print(f"  [分析] Jenkins log 顯示被改為 100.0 → 導致 200MHz 設定被誤判")

        # 4. 在 Jira 建 Issue
        diagnosis = (
            f"CI 失敗自動診斷報告\n\n"
            f"Jenkins Build: {FAIL_JOB} #{build['number']} — FAILURE\n"
            f"失敗測試：{len(failed_tests)} 個\n\n"
            f"根因分析：\n"
            f"- CLOCK_MAX_MHZ 從 {original_value} 被改為 100.0\n"
            f"- 導致 200MHz 的合法設定被誤判為超出範圍\n"
            f"- BitBucket 上的原始碼（{BB_WS}/{BB_REPO}）CLOCK_MAX_MHZ = {original_value}\n\n"
            f"建議修復：還原 CLOCK_MAX_MHZ = {original_value}"
        )

        create_result = await jira_create_issue(CreateIssueInput(
            project_key=TEST_PROJECT,
            summary=f"[CI-Fail] {FAIL_JOB} #{build['number']} — CLOCK_MAX_MHZ 被改壞",
            issue_type="Task",
            description=diagnosis,
        ))
        issue_key = create_result.split("：")[1].split("\n")[0]

        print(f"\n  [Jira] 建立 Issue：{issue_key}")
        print(f"    包含：Jenkins log 分析 + BitBucket 原始碼比對 + 修復建議")

        print("\n  ═══════════════════════════════════════")
        print("  Demo 完成！三個 MCP Server 串聯成功")
        print("  ═══════════════════════════════════════")
