#!/usr/bin/env python3
"""
Jenkins MCP Server 整合測試

前置條件：
  1. docker compose up -d jenkins
  2. Jenkins 已完成初始設定
  3. 執行 setup_test_jobs.py 建立測試用 Jobs
  4. 設定環境變數 JENKINS_URL / JENKINS_USER / JENKINS_API_TOKEN

用法：
  # 建立測試 Jobs（只需跑一次）
  python jenkins_mcp/setup_test_jobs.py

  # 跑全部測試
  pytest jenkins_mcp/test_server.py -v

  # 只跑某一類測試
  pytest jenkins_mcp/test_server.py -v -k "查詢"
  pytest jenkins_mcp/test_server.py -v -k "觸發"
  pytest jenkins_mcp/test_server.py -v -k "錯誤"
"""

import json
import os
import asyncio
import pytest

# ── 環境變數（在 import server 之前設定）────────────────────────────────────
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
    jenkins_get_queue,
    jenkins_cancel_build,
    jenkins_get_nodes,
    ListJobsInput,
    JobPathInput,
    TriggerBuildInput,
    GetBuildInput,
    GetBuildLogInput,
    ListBuildsInput,
    CancelBuildInput,
)


# ── 共用工具 ─────────────────────────────────────────────────────────────────

async def _等待_build_完成(job_path: str, timeout_secs: int = 30) -> dict:
    """觸發 build 後，輪詢等待完成，回傳 build 結果 dict"""
    build = None
    for _ in range(timeout_secs // 2):
        await asyncio.sleep(2)
        raw = await jenkins_get_build(GetBuildInput(job_path=job_path, build_number=-1))
        if raw.startswith("錯誤"):
            continue
        build = json.loads(raw)
        if not build.get("building"):
            return build
    pytest.fail(f"Job '{job_path}' 超過 {timeout_secs} 秒未完成")


# ══════════════════════════════════════════════════════════════════════════════
#  第一類：查詢類測試 — 不會改變 Jenkins 狀態
# ══════════════════════════════════════════════════════════════════════════════


class Test查詢Jobs:
    """測試 jenkins_list_jobs / jenkins_get_job"""

    @pytest.mark.asyncio
    async def test_列出根目錄所有jobs(self):
        """呼叫 list_jobs（不帶 folder），應回傳包含 mcp-test-job 的清單"""
        result = json.loads(await jenkins_list_jobs(ListJobsInput()))
        names = [j["name"] for j in result]
        assert "mcp-test-job" in names
        # 每個 job 都應該有 name 和 color 欄位
        for job in result:
            assert "name" in job
            assert "color" in job

    @pytest.mark.asyncio
    async def test_列出Folder內的jobs(self):
        """指定 folder=TestFolder，應回傳 nested-job"""
        result = json.loads(await jenkins_list_jobs(ListJobsInput(folder="TestFolder")))
        names = [j["name"] for j in result]
        assert "nested-job" in names

    @pytest.mark.asyncio
    async def test_取得job詳細資訊(self):
        """取得 mcp-test-job 的詳情，確認 name / buildable 等欄位"""
        result = json.loads(await jenkins_get_job(JobPathInput(job_path="mcp-test-job")))
        assert result["name"] == "mcp-test-job"
        assert result["buildable"] is True
        # 應有這些欄位（值可能是 None）
        assert "healthReport" in result
        assert "lastBuild" in result
        assert "recentBuilds" in result

    @pytest.mark.asyncio
    async def test_取得Folder內job詳情(self):
        """路徑含 Folder：TestFolder/nested-job"""
        result = json.loads(
            await jenkins_get_job(JobPathInput(job_path="TestFolder/nested-job"))
        )
        assert result["name"] == "nested-job"
        assert result["buildable"] is True


class Test查詢節點:
    """測試 jenkins_get_nodes"""

    @pytest.mark.asyncio
    async def test_列出所有節點(self):
        """至少有 Built-In Node"""
        result = json.loads(await jenkins_get_nodes())
        assert len(result) >= 1
        node = result[0]
        assert "name" in node
        assert "offline" in node
        assert "numExecutors" in node

    @pytest.mark.asyncio
    async def test_內建節點是上線狀態(self):
        """Built-In Node 不應該是 offline"""
        result = json.loads(await jenkins_get_nodes())
        builtin = next(
            n for n in result if "Built-In" in n["name"] or "master" in n["name"]
        )
        assert builtin["offline"] is False


class Test查詢Queue:
    """測試 jenkins_get_queue"""

    @pytest.mark.asyncio
    async def test_查詢build佇列(self):
        """queue API 應回傳 list（閒置時為空）"""
        result = json.loads(await jenkins_get_queue())
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════════════════════
#  第二類：觸發與執行 — 會實際執行 build
# ══════════════════════════════════════════════════════════════════════════════


class Test觸發Build:
    """測試 jenkins_trigger_build + jenkins_get_build + jenkins_get_build_log"""

    @pytest.mark.asyncio
    async def test_觸發簡單job並檢查結果(self):
        """觸發 mcp-test-job → 等完成 → 驗證 SUCCESS + log 內容"""
        trigger = await jenkins_trigger_build(
            TriggerBuildInput(job_path="mcp-test-job")
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("mcp-test-job")
        assert build["result"] == "SUCCESS"

        # 驗證 log 包含預期輸出
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="mcp-test-job", build_number=build["number"])
        )
        assert "Hello from MCP test job" in log

    @pytest.mark.asyncio
    async def test_觸發帶參數的job(self):
        """傳入 BRANCH=develop, ENV=production，log 應包含這些參數值"""
        trigger = await jenkins_trigger_build(
            TriggerBuildInput(
                job_path="mcp-param-job",
                parameters={"BRANCH": "develop", "ENV": "production"},
            )
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("mcp-param-job")
        assert build["result"] == "SUCCESS"

        # 驗證參數有被帶入
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="mcp-param-job", build_number=build["number"])
        )
        assert "develop" in log
        assert "production" in log

    @pytest.mark.asyncio
    async def test_觸發會失敗的job(self):
        """mcp-fail-job 的 build result 應為 FAILURE"""
        await jenkins_trigger_build(TriggerBuildInput(job_path="mcp-fail-job"))

        build = await _等待_build_完成("mcp-fail-job")
        assert build["result"] == "FAILURE"

        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="mcp-fail-job", build_number=build["number"])
        )
        assert "即將失敗" in log

    @pytest.mark.asyncio
    async def test_觸發Folder內的job(self):
        """觸發 TestFolder/nested-job，驗證路徑轉換正確"""
        trigger = await jenkins_trigger_build(
            TriggerBuildInput(job_path="TestFolder/nested-job")
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("TestFolder/nested-job")
        assert build["result"] == "SUCCESS"


class Test查詢Build紀錄:
    """測試 jenkins_list_builds / jenkins_get_build（需要先有 build 紀錄）"""

    @pytest.mark.asyncio
    async def test_列出最近builds(self):
        """mcp-test-job 應有至少一筆 build 紀錄"""
        # 先確保至少跑過一次
        await jenkins_trigger_build(TriggerBuildInput(job_path="mcp-test-job"))
        await _等待_build_完成("mcp-test-job")

        builds = json.loads(
            await jenkins_list_builds(ListBuildsInput(job_path="mcp-test-job", limit=5))
        )
        assert len(builds) >= 1
        # 每筆都有必要欄位
        for b in builds:
            assert "number" in b
            assert "result" in b
            assert "duration" in b

    @pytest.mark.asyncio
    async def test_用負一取得最新build(self):
        """build_number=-1 應回傳最新一筆"""
        raw = await jenkins_get_build(
            GetBuildInput(job_path="mcp-test-job", build_number=-1)
        )
        build = json.loads(raw)
        assert build["number"] >= 1
        assert build["result"] in ("SUCCESS", "FAILURE", "UNSTABLE", "進行中")

    @pytest.mark.asyncio
    async def test_指定log截斷長度(self):
        """設定 last_chars=500，確認 log 不超過合理長度"""
        raw = await jenkins_get_build(
            GetBuildInput(job_path="mcp-test-job", build_number=-1)
        )
        build = json.loads(raw)
        log = await jenkins_get_build_log(
            GetBuildLogInput(
                job_path="mcp-test-job",
                build_number=build["number"],
                last_chars=500,
            )
        )
        assert isinstance(log, str)
        assert len(log) <= 600  # 500 + 截斷提示文字的長度


# ══════════════════════════════════════════════════════════════════════════════
#  第三類：取消 Build — 測試 cancel 功能
# ══════════════════════════════════════════════════════════════════════════════


class Test取消Build:
    """測試 jenkins_cancel_build（需要一個跑很久的 job）"""

    @pytest.mark.asyncio
    async def test_取消執行中的build(self):
        """觸發 mcp-slow-job（sleep 30s）→ 立即取消 → 結果應為 ABORTED"""
        await jenkins_trigger_build(TriggerBuildInput(job_path="mcp-slow-job"))

        # 等 build 真正開始（不再是 queue 狀態）
        build_number = None
        for _ in range(10):
            await asyncio.sleep(2)
            raw = await jenkins_get_build(
                GetBuildInput(job_path="mcp-slow-job", build_number=-1)
            )
            if raw.startswith("錯誤"):
                continue
            build = json.loads(raw)
            if build.get("building"):
                build_number = build["number"]
                break

        assert build_number is not None, "mcp-slow-job 未在 20 秒內開始執行"

        # 送出取消請求
        cancel_result = await jenkins_cancel_build(
            CancelBuildInput(job_path="mcp-slow-job", build_number=build_number)
        )
        assert "終止請求已送出" in cancel_result

        # 等待 build 真正停止
        final_build = None
        for _ in range(10):
            await asyncio.sleep(2)
            raw = await jenkins_get_build(
                GetBuildInput(job_path="mcp-slow-job", build_number=build_number)
            )
            final_build = json.loads(raw)
            if not final_build.get("building"):
                break

        assert final_build is not None
        assert final_build["result"] == "ABORTED"


# ══════════════════════════════════════════════════════════════════════════════
#  第四類：錯誤處理 — 驗證 server 不會 crash
# ══════════════════════════════════════════════════════════════════════════════


class Test錯誤處理:
    """驗證錯誤的輸入會回傳友善錯誤訊息，而非 exception"""

    @pytest.mark.asyncio
    async def test_查詢不存在的job(self):
        """不存在的 job 應回傳 404 錯誤訊息"""
        result = await jenkins_get_job(JobPathInput(job_path="不存在的job"))
        assert "錯誤" in result
        assert "找不到" in result

    @pytest.mark.asyncio
    async def test_觸發不存在的job(self):
        """觸發不存在的 job 應回傳錯誤，不應 raise exception"""
        result = await jenkins_trigger_build(
            TriggerBuildInput(job_path="absolutely-no-such-job")
        )
        assert "錯誤" in result

    @pytest.mark.asyncio
    async def test_取得不存在的build(self):
        """build_number=99999 不存在，應回傳錯誤"""
        result = await jenkins_get_build(
            GetBuildInput(job_path="mcp-test-job", build_number=99999)
        )
        assert "錯誤" in result

    @pytest.mark.asyncio
    async def test_列出不存在Folder的jobs(self):
        """不存在的 folder 應回傳錯誤"""
        result = await jenkins_list_jobs(ListJobsInput(folder="NoSuchFolder"))
        assert "錯誤" in result
