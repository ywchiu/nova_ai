#!/usr/bin/env python3
"""
Jenkins MCP Server — Pipeline 整合測試（對應課程 M4：CI/CD Pipeline 整合）

本檔測試 Pipeline Job 的完整場景，涵蓋課程大綱中 M4 的所有操作：
  - Agent 與 Jenkins Pipeline 的整合模式
  - 觸發條件與流程設計
  - 錯誤處理與通知機制
  - PR → Agent Review → Jenkins Build

前置條件：
  1. docker compose up -d jenkins
  2. python jenkins_mcp/setup_test_jobs.py

用法：
  JENKINS_URL=http://localhost:9090 \
  JENKINS_USER=admin \
  JENKINS_API_TOKEN=<token> \
  pytest jenkins_mcp/test_pipeline.py -v
"""

import json
import os
import asyncio
import pytest

os.environ.setdefault("JENKINS_URL", "http://localhost:9090")
os.environ.setdefault("JENKINS_USER", "admin")
os.environ.setdefault("JENKINS_API_TOKEN", "")

from jenkins_mcp.server import (
    jenkins_get_job,
    jenkins_trigger_build,
    jenkins_get_build,
    jenkins_get_build_log,
    jenkins_list_builds,
    jenkins_get_job_config,
    JobPathInput,
    TriggerBuildInput,
    GetBuildInput,
    GetBuildLogInput,
    ListBuildsInput,
)


# ── 共用工具 ─────────────────────────────────────────────────────────────────

async def _取得目前最新build編號(job_path: str) -> int | None:
    """取得目前最新的 build number，用來判斷新 build 是否已開始"""
    raw = await jenkins_get_build(GetBuildInput(job_path=job_path, build_number=-1))
    if raw.startswith("錯誤"):
        return None
    return json.loads(raw).get("number")


async def _等待_build_完成(job_path: str, timeout_secs: int = 60, after_build: int | None = None) -> dict:
    """
    輪詢等待 build 完成，回傳 build 結果 dict。
    after_build: 若指定，等待 build number > after_build 的那一筆完成。
    """
    for _ in range(timeout_secs // 2):
        await asyncio.sleep(2)
        raw = await jenkins_get_build(GetBuildInput(job_path=job_path, build_number=-1))
        if raw.startswith("錯誤"):
            continue
        build = json.loads(raw)
        # 如果指定了 after_build，跳過舊的 build
        if after_build is not None and build.get("number", 0) <= after_build:
            continue
        if not build.get("building"):
            return build
    pytest.fail(f"Job '{job_path}' 超過 {timeout_secs} 秒未完成")


async def _確保參數已註冊(job_path: str):
    """
    Pipeline 的 parameters {} 在第一次 build 前不會生效。
    先觸發一次空 build 讓 Jenkins 註冊參數定義。
    """
    raw = await jenkins_get_build(GetBuildInput(job_path=job_path, build_number=-1))
    if not raw.startswith("錯誤"):
        return  # 已有 build，參數已註冊
    await jenkins_trigger_build(TriggerBuildInput(job_path=job_path))
    await _等待_build_完成(job_path)


# ══════════════════════════════════════════════════════════════════════════════
#  場景一：Pipeline 多階段 CI/CD 流程
#  對應課程：M4「Agent 與 Jenkins Pipeline 的整合模式」
# ══════════════════════════════════════════════════════════════════════════════


class TestPipeline多階段CICD:
    """
    模擬真實 CI/CD：Checkout → Build → Test → Deploy
    這是課程中最核心的 demo，展示 AI Agent 如何觸發並監控 Pipeline。
    """

    @pytest.mark.asyncio
    async def test_觸發Pipeline_預設參數_全階段通過(self):
        """
        情境：開發者 push 到 main，觸發完整 CI/CD Pipeline。
        預期：Checkout → Build → Test → Deploy 四個 stage 全部通過。
        """
        # 確保參數已註冊；註冊後必須用帶參數的方式觸發（用預設值即可）
        await _確保參數已註冊("pipeline-cicd")
        prev_build = await _取得目前最新build編號("pipeline-cicd")

        trigger = await jenkins_trigger_build(
            TriggerBuildInput(
                job_path="pipeline-cicd",
                parameters={"BRANCH": "main", "PR_ID": ""},
            )
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("pipeline-cicd", after_build=prev_build)
        assert build["result"] == "SUCCESS"

        # 驗證 log 中包含所有 stage 的輸出
        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="pipeline-cicd", build_number=build["number"])
        )
        assert "Checking out branch" in log
        assert "Compiling project" in log
        assert "Running unit tests" in log
        assert "Deploying to staging" in log  # main branch → Deploy 會執行
        assert "Pipeline 完成" in log

    @pytest.mark.asyncio
    async def test_觸發Pipeline_非main分支_跳過Deploy(self):
        """
        情境：開發者 push 到 feature branch，不應觸發 Deploy。
        預期：Checkout → Build → Test 通過，Deploy 被跳過。
        這演示 Pipeline 的 when 條件判斷。
        """
        # 確保參數已註冊（Pipeline 第一次跑才會註冊 parameters 區塊）
        await _確保參數已註冊("pipeline-cicd")

        # 記住目前最新 build 編號，避免拿到舊的結果
        prev_build = await _取得目前最新build編號("pipeline-cicd")

        trigger = await jenkins_trigger_build(
            TriggerBuildInput(
                job_path="pipeline-cicd",
                parameters={"BRANCH": "feature/new-api", "PR_ID": ""},
            )
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("pipeline-cicd", after_build=prev_build)
        assert build["result"] == "SUCCESS"

        log = await jenkins_get_build_log(
            GetBuildLogInput(job_path="pipeline-cicd", build_number=build["number"])
        )
        assert "feature/new-api" in log
        # Deploy 階段有 when { branch == 'main' } 條件，feature branch 不會跑
        assert "Deploying to staging" not in log


# ══════════════════════════════════════════════════════════════════════════════
#  場景二：Pipeline 錯誤處理
#  對應課程：M4「錯誤處理與通知機制」
# ══════════════════════════════════════════════════════════════════════════════


class TestPipeline錯誤處理:
    """
    課堂重點：當 Pipeline 某個 stage 失敗時，
    AI Agent 如何找出失敗點、讀取錯誤 log、給出修復建議。
    """

    @pytest.mark.asyncio
    async def test_Pipeline在Test階段失敗(self):
        """
        情境：Build 成功但 Test 失敗（常見的 CI 場景）。
        預期：result=FAILURE，log 中可看到是 Test stage 失敗，
              Deploy stage 不會執行。
        """
        await jenkins_trigger_build(
            TriggerBuildInput(job_path="pipeline-fail-stage")
        )

        build = await _等待_build_完成("pipeline-fail-stage")
        assert build["result"] == "FAILURE"

        log = await jenkins_get_build_log(
            GetBuildLogInput(
                job_path="pipeline-fail-stage", build_number=build["number"]
            )
        )
        # Build stage 有跑
        assert "Build OK" in log
        # Test stage 失敗了
        assert "Running tests" in log
        # Deploy stage 不應該被執行
        assert "This stage should NOT run" not in log
        # post { failure } 區塊有執行
        assert "Pipeline 失敗" in log

    @pytest.mark.asyncio
    async def test_從失敗build的log定位錯誤(self):
        """
        情境：AI Agent 讀取失敗的 build log，分析錯誤原因。
        這是課堂的核心演練——讓學員理解 Agent 如何「看懂」 log。
        """
        # 確保有一筆失敗的 build
        await jenkins_trigger_build(
            TriggerBuildInput(job_path="pipeline-fail-stage")
        )
        build = await _等待_build_完成("pipeline-fail-stage")

        # Agent 取得 job 資訊，確認有失敗記錄
        job_info = json.loads(
            await jenkins_get_job(JobPathInput(job_path="pipeline-fail-stage"))
        )
        assert job_info["lastFailed"] is not None
        assert job_info["color"] == "red"  # 紅燈 = 最近一次 build 失敗

        # Agent 列出最近 builds，找出失敗的那一筆
        builds = json.loads(
            await jenkins_list_builds(
                ListBuildsInput(job_path="pipeline-fail-stage", limit=5)
            )
        )
        failed_builds = [b for b in builds if b["result"] == "FAILURE"]
        assert len(failed_builds) >= 1

        # Agent 讀取失敗 log 來診斷問題
        log = await jenkins_get_build_log(
            GetBuildLogInput(
                job_path="pipeline-fail-stage",
                build_number=failed_builds[0]["number"],
            )
        )
        # log 中應有 exit code 資訊，Agent 可據此判斷原因
        assert "exit" in log.lower() or "ERROR" in log or "FAILURE" in log


# ══════════════════════════════════════════════════════════════════════════════
#  場景三：PR → Agent Review → Jenkins Build
#  對應課程：M4「PR → Agent Review → Jenkins Build」
# ══════════════════════════════════════════════════════════════════════════════


class TestPR驅動的Build流程:
    """
    完整模擬課程 M4 的核心流程：
    1. 從 Bitbucket 收到 PR
    2. AI Agent 進行 Code Review
    3. 觸發 Jenkins Pipeline Build
    4. 回報結果
    """

    @pytest.mark.asyncio
    async def test_PR觸發完整審查流程(self):
        """
        情境：PR #42 從 feature/new-api 分支提交，由 developer 發起。
        Agent 觸發 pipeline-pr-review，帶入 PR 資訊。
        """
        # Pipeline 的 parameters 需要第一次 build 後才會生效
        await _確保參數已註冊("pipeline-pr-review")
        prev_build = await _取得目前最新build編號("pipeline-pr-review")

        trigger = await jenkins_trigger_build(
            TriggerBuildInput(
                job_path="pipeline-pr-review",
                parameters={
                    "PR_ID": "42",
                    "PR_BRANCH": "feature/new-api",
                    "PR_AUTHOR": "david",
                },
            )
        )
        assert "已觸發" in trigger

        build = await _等待_build_完成("pipeline-pr-review", after_build=prev_build)
        assert build["result"] == "SUCCESS"

        # 驗證 PR 資訊有正確帶入
        log = await jenkins_get_build_log(
            GetBuildLogInput(
                job_path="pipeline-pr-review", build_number=build["number"]
            )
        )
        assert "PR #42" in log
        assert "feature/new-api" in log
        assert "david" in log
        # 驗證 review 流程有跑完
        assert "Code Review" in log
        assert "建置成功" in log
        assert "最終結果" in log

    @pytest.mark.asyncio
    async def test_PR的build帶有參數記錄(self):
        """
        情境：Agent 需要回查某次 PR build 的參數（誰發的、哪個分支）。
        這對 AI 自動回報 PR 狀態很重要。
        """
        await _確保參數已註冊("pipeline-pr-review")
        prev_build = await _取得目前最新build編號("pipeline-pr-review")

        await jenkins_trigger_build(
            TriggerBuildInput(
                job_path="pipeline-pr-review",
                parameters={
                    "PR_ID": "99",
                    "PR_BRANCH": "hotfix/urgent-fix",
                    "PR_AUTHOR": "alice",
                },
            )
        )
        build = await _等待_build_完成("pipeline-pr-review", after_build=prev_build)

        # 用 get_build 回查這筆 build 的參數
        assert build["params"]["PR_ID"] == "99"
        assert build["params"]["PR_BRANCH"] == "hotfix/urgent-fix"
        assert build["params"]["PR_AUTHOR"] == "alice"


# ══════════════════════════════════════════════════════════════════════════════
#  場景四：讀取 Pipeline 設定檔（config.xml）
#  對應課程：M4「Agent 與 Jenkins Pipeline 的整合模式」
#           M6「讓 AI 能讀取 Issue、存取 Repo」的延伸
# ══════════════════════════════════════════════════════════════════════════════


class Test讀取Pipeline設定:
    """
    AI Agent 讀取 Job 的 config.xml，理解 Pipeline 結構。
    課堂用途：讓 Agent 能分析現有 Pipeline、建議修改方向。
    """

    @pytest.mark.asyncio
    async def test_讀取Pipeline的Jenkinsfile內容(self):
        """Agent 讀取 pipeline-cicd 的設定，應包含 Pipeline script"""
        config = await jenkins_get_job_config(
            JobPathInput(job_path="pipeline-cicd")
        )
        assert "pipeline" in config.lower()
        assert "stage" in config.lower()
        # 應包含我們定義的參數
        assert "BRANCH" in config
        assert "PR_ID" in config

    @pytest.mark.asyncio
    async def test_讀取Freestyle_vs_Pipeline設定差異(self):
        """
        Agent 能區分 Freestyle 和 Pipeline job。
        Freestyle 的 config 是 <project>，Pipeline 是 <flow-definition>。
        """
        freestyle_config = await jenkins_get_job_config(
            JobPathInput(job_path="mcp-test-job")
        )
        pipeline_config = await jenkins_get_job_config(
            JobPathInput(job_path="pipeline-cicd")
        )

        assert "<project>" in freestyle_config
        assert "flow-definition" in pipeline_config

    @pytest.mark.asyncio
    async def test_讀取PR_Review_Pipeline的階段設計(self):
        """Agent 讀取 PR review pipeline，理解 PR → Review → Build → Report 流程"""
        config = await jenkins_get_job_config(
            JobPathInput(job_path="pipeline-pr-review")
        )
        # 應包含完整的 PR review 流程定義
        assert "PR Info" in config
        assert "Code Review" in config
        # XML 中 & 被轉義為 &amp;
        assert "Build &amp; Test" in config or "Build & Test" in config
        assert "Report" in config
        # 應包含 PR 相關參數
        assert "PR_ID" in config
        assert "PR_BRANCH" in config
        assert "PR_AUTHOR" in config


# ══════════════════════════════════════════════════════════════════════════════
#  場景五：Build 歷史比較與趨勢
#  對應課程：M4「觸發條件與流程設計」
# ══════════════════════════════════════════════════════════════════════════════


class TestBuild歷史與趨勢:
    """
    AI Agent 分析多次 build 的趨勢，找出不穩定的 Pipeline。
    課堂用途：展示 Agent 如何作為 CI/CD 的智能助理。
    """

    @pytest.mark.asyncio
    async def test_比較成功與失敗Pipeline的build歷史(self):
        """
        情境：Agent 比對兩個 Pipeline 的健康狀態。
        pipeline-cicd 應全是 SUCCESS，pipeline-fail-stage 應全是 FAILURE。
        """
        # 確保兩個 Pipeline 都有 build 紀錄
        await jenkins_trigger_build(TriggerBuildInput(job_path="pipeline-cicd"))
        await jenkins_trigger_build(TriggerBuildInput(job_path="pipeline-fail-stage"))
        await _等待_build_完成("pipeline-cicd")
        await _等待_build_完成("pipeline-fail-stage")

        # 查詢兩個 job 的健康狀態
        good_job = json.loads(
            await jenkins_get_job(JobPathInput(job_path="pipeline-cicd"))
        )
        bad_job = json.loads(
            await jenkins_get_job(JobPathInput(job_path="pipeline-fail-stage"))
        )

        assert good_job["color"] == "blue"   # 藍燈 = 健康
        assert bad_job["color"] == "red"      # 紅燈 = 不健康

        assert good_job["lastSuccess"] is not None
        assert bad_job["lastFailed"] is not None

    @pytest.mark.asyncio
    async def test_列出Pipeline的所有builds統計(self):
        """
        情境：Agent 列出 pipeline-cicd 最近 builds，計算成功率。
        """
        builds = json.loads(
            await jenkins_list_builds(
                ListBuildsInput(job_path="pipeline-cicd", limit=10)
            )
        )
        assert len(builds) >= 1

        success_count = sum(1 for b in builds if b["result"] == "SUCCESS")
        total = len(builds)
        success_rate = success_count / total

        # pipeline-cicd 的 builds 應全部成功
        assert success_rate == 1.0, f"成功率 {success_rate:.0%}，預期 100%"
