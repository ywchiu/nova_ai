#!/usr/bin/env python3
"""
CI/CD Demo 端對端測試 — 模擬 AI Agent 透過 MCP 操作 Jenkins

本檔模擬課程中 AI Agent 的完整工作流程：
  場景 A：Agent 觸發 CI → 全部通過 → 回報成功
  場景 B：有人改壞程式 → CI 失敗 → Agent 讀 log 診斷問題 → 找出根因

專案背景：chip_validator（晶片暫存器設定驗證器）
  - 6 條驗證規則、21 個 pytest 測試
  - Jenkins 裡有真實的 Python 專案、真實的 pytest 執行

用法：
  JENKINS_URL=http://localhost:9090 \
  JENKINS_USER=admin \
  JENKINS_API_TOKEN=<token> \
  pytest jenkins_mcp/test_demo_cicd.py -v -s
"""

import json
import os
import asyncio
import pytest

os.environ.setdefault("JENKINS_URL", "http://localhost:9090")
os.environ.setdefault("JENKINS_USER", "admin")
os.environ.setdefault("JENKINS_API_TOKEN", "")

from jenkins_mcp.server import (
    jenkins_list_jobs,
    jenkins_get_job,
    jenkins_trigger_build,
    jenkins_get_build,
    jenkins_get_build_log,
    jenkins_list_builds,
    jenkins_get_job_config,
    ListJobsInput,
    JobPathInput,
    TriggerBuildInput,
    GetBuildInput,
    GetBuildLogInput,
    ListBuildsInput,
)


# ── 共用 ──────────────────────────────────────────────────────────────────────

async def _等待_build_完成(job_path: str, after_build: int | None = None, timeout: int = 90) -> dict:
    for _ in range(timeout // 3):
        await asyncio.sleep(3)
        raw = await jenkins_get_build(GetBuildInput(job_path=job_path, build_number=-1))
        if raw.startswith("錯誤"):
            continue
        build = json.loads(raw)
        if after_build is not None and build.get("number", 0) <= after_build:
            continue
        if not build.get("building"):
            return build
    pytest.fail(f"Job '{job_path}' 超過 {timeout} 秒未完成")


async def _取得目前最新build編號(job_path: str) -> int | None:
    raw = await jenkins_get_build(GetBuildInput(job_path=job_path, build_number=-1))
    if raw.startswith("錯誤"):
        return None
    return json.loads(raw).get("number")


# ══════════════════════════════════════════════════════════════════════════════
#  場景 A：完整 CI 流程 — Agent 觸發、監控、確認成功
#  課堂示範：「用自然語言請 Agent 跑一次 CI，看到真實的 pytest 結果」
# ══════════════════════════════════════════════════════════════════════════════


class TestAgent觸發CI成功:
    """
    模擬對話：
      使用者：「幫我跑一次 chip-validator 的 CI」
      Agent ：觸發 build → 等待 → 回報結果
    """

    @pytest.mark.asyncio
    async def test_step1_Agent找到chip_validator的CI_job(self):
        """Agent 先列出所有 jobs，確認 chip-validator-ci 存在"""
        result = json.loads(await jenkins_list_jobs(ListJobsInput()))
        job_names = [j["name"] for j in result]
        assert "chip-validator-ci" in job_names
        print(f"\n  Agent 找到 {len(job_names)} 個 jobs，包含 chip-validator-ci")

    @pytest.mark.asyncio
    async def test_step2_Agent讀取Pipeline設定理解CI流程(self):
        """Agent 讀 config.xml 了解 Pipeline 有哪些 stage"""
        config = await jenkins_get_job_config(JobPathInput(job_path="chip-validator-ci"))
        assert "Setup" in config
        assert "Lint" in config
        assert "Test" in config
        assert "Report" in config
        print("\n  Agent 解析 Pipeline：Setup → Lint → Test → Report")

    @pytest.mark.asyncio
    async def test_step3_Agent觸發build並等待結果(self):
        """Agent 觸發 CI，等待完成，確認 21 個測試全部通過"""
        prev = await _取得目前最新build編號("chip-validator-ci")

        trigger = await jenkins_trigger_build(
            TriggerBuildInput(job_path="chip-validator-ci")
        )
        assert "已觸發" in trigger
        print(f"\n  Agent：{trigger}")

        build = await _等待_build_完成("chip-validator-ci", after_build=prev)
        assert build["result"] == "SUCCESS"
        print(f"  Agent：Build #{build['number']} 結果 = {build['result']}")

        # Agent 讀 log 確認測試數量
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="chip-validator-ci", build_number=build["number"])
        )
        assert "21 passed" in log
        assert "FAILED" not in log
        print("  Agent：21 個測試全部 PASSED，CI 流程完整通過")


# ══════════════════════════════════════════════════════════════════════════════
#  場景 B：CI 失敗 → Agent 診斷根因
#  課堂示範：「有人改壞 clock 頻率上限 → Agent 找出哪條規則壞了」
# ══════════════════════════════════════════════════════════════════════════════


class TestAgent診斷CI失敗:
    """
    模擬對話：
      使用者：「CI 掛了，幫我看一下怎麼回事」
      Agent ：查 job 狀態 → 讀失敗 log → 定位失敗的測試 → 找出根因
    """

    @pytest.mark.asyncio
    async def test_step1_Agent觸發失敗版CI(self):
        """Agent 觸發 chip-validator-ci-fail（內含注入的 bug）"""
        prev = await _取得目前最新build編號("chip-validator-ci-fail")

        trigger = await jenkins_trigger_build(
            TriggerBuildInput(job_path="chip-validator-ci-fail")
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("chip-validator-ci-fail", after_build=prev)
        assert build["result"] == "FAILURE"
        print(f"\n  Agent：Build #{build['number']} 結果 = FAILURE（如預期）")

    @pytest.mark.asyncio
    async def test_step2_Agent查看job健康狀態(self):
        """Agent 查 job 狀態：紅燈 = 最近一次 build 失敗"""
        job = json.loads(
            await jenkins_get_job(JobPathInput(job_path="chip-validator-ci-fail"))
        )
        assert job["color"] == "red"
        assert job["lastFailed"] is not None
        print(f"\n  Agent：chip-validator-ci-fail 亮紅燈，最近一次失敗的 build = #{job['lastFailed']}")

    @pytest.mark.asyncio
    async def test_step3_Agent讀取失敗log找出壞掉的測試(self):
        """Agent 讀 log，找出哪些測試 FAILED"""
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="chip-validator-ci-fail", build_number=-1)
        )

        # 找出失敗的測試名稱
        failed_tests = [
            line.strip() for line in log.split("\n")
            if "FAILED" in line and "::" in line
        ]
        assert len(failed_tests) >= 1
        print(f"\n  Agent 從 log 找到 {len(failed_tests)} 個失敗的測試：")
        for t in failed_tests:
            print(f"    ✗ {t}")

        # 應該包含 clock 頻率相關的測試
        failed_text = " ".join(failed_tests)
        assert "Clock" in failed_text or "頻率" in failed_text or "合法設定" in failed_text

    @pytest.mark.asyncio
    async def test_step4_Agent定位根因(self):
        """
        Agent 分析 log，定位到 CLOCK_MAX_MHZ 被改壞：
          - 看到 'sed' 命令把 800.0 改成 100.0
          - TestClock頻率 的測試因此失敗
          - 診斷結論：CLOCK_MAX_MHZ 常數被錯誤修改
        """
        # 需要讀取完整 log（包含 Inject Bug stage 的輸出）
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="chip-validator-ci-fail", build_number=-1, last_chars=20000)
        )

        # Agent 能從 log 找到修改記錄
        assert "CLOCK_MAX_MHZ" in log
        assert "800.0" in log
        assert "100.0" in log

        # Agent 也能確認檔案已被還原（post { always } 區塊）
        assert "還原" in log or ".bak" in log

        print("\n  Agent 根因分析結果：")
        print("    原因：validator.py 中 CLOCK_MAX_MHZ 從 800.0 被改為 100.0")
        print("    影響：200 MHz 的合法設定被誤判為超出範圍")
        print("    建議：還原 CLOCK_MAX_MHZ = 800.0，或確認新的 spec 上限")

    @pytest.mark.asyncio
    async def test_step5_Agent比較成功版與失敗版(self):
        """
        Agent 同時查看正常版和失敗版，比較差異：
          - chip-validator-ci：藍燈、全部通過
          - chip-validator-ci-fail：紅燈、clock 相關測試失敗
        """
        good = json.loads(await jenkins_get_job(JobPathInput(job_path="chip-validator-ci")))
        bad = json.loads(await jenkins_get_job(JobPathInput(job_path="chip-validator-ci-fail")))

        assert good["color"] == "blue"
        assert bad["color"] == "red"

        good_builds = json.loads(
            await jenkins_list_builds(ListBuildsInput(job_path="chip-validator-ci", limit=5))
        )
        bad_builds = json.loads(
            await jenkins_list_builds(ListBuildsInput(job_path="chip-validator-ci-fail", limit=5))
        )

        good_success = sum(1 for b in good_builds if b["result"] == "SUCCESS")
        bad_failure = sum(1 for b in bad_builds if b["result"] == "FAILURE")

        print(f"\n  Agent 比較報告：")
        print(f"    chip-validator-ci      → 🔵 成功 {good_success}/{len(good_builds)} 次")
        print(f"    chip-validator-ci-fail  → 🔴 失敗 {bad_failure}/{len(bad_builds)} 次")
        print(f"    結論：問題出在 clock 頻率驗證規則被改壞，不影響其他規則")
