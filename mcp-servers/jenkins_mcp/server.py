#!/usr/bin/env python3
"""
MCP Server for Jenkins (最新版)

Auth: 用戶名 + API Token（Basic Auth）
取得 API Token: Jenkins → 右上角帳號 → Configure → API Token → Add new Token → Generate
注意：Jenkins 每個 POST 都需要 CSRF crumb，本 server 自動處理。
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict
import httpx
from mcp.server.fastmcp import FastMCP

# ── 載入 .env（從 mcp-servers/ 根目錄讀取，環境變數優先）────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── 設定 ─────────────────────────────────────────────────────────────────────
JENKINS_URL       = os.environ.get("JENKINS_URL", "").rstrip("/")
JENKINS_USER      = os.environ.get("JENKINS_USER", "")
JENKINS_API_TOKEN = os.environ.get("JENKINS_API_TOKEN", "")

if not JENKINS_URL or not JENKINS_USER or not JENKINS_API_TOKEN:
    raise RuntimeError("請設定環境變數 JENKINS_URL、JENKINS_USER、JENKINS_API_TOKEN")

_auth_str = base64.b64encode(f"{JENKINS_USER}:{JENKINS_API_TOKEN}".encode()).decode()
HEADERS   = {"Authorization": f"Basic {_auth_str}"}

mcp = FastMCP("jenkins_mcp")

# ── 共用工具函數 ──────────────────────────────────────────────────────────────

def _encode_job_path(job_path: str) -> str:
    """把 'Folder/JobName' 轉換成 Jenkins URL 格式 'Folder/job/JobName'。"""
    parts = job_path.strip("/").split("/")
    return "/job/".join(parts)


async def jenkins_request(method: str, path: str, params: dict | None = None, data: str | None = None, extra_headers: dict | None = None) -> Any:
    """所有 Jenkins API 呼叫的統一入口。"""
    url = path if path.startswith("http") else f"{JENKINS_URL}{path}"
    headers = {**HEADERS, **(extra_headers or {})}
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.request(method, url, headers=headers, params=params, content=data)
        if not resp.is_success:
            raise httpx.HTTPStatusError(f"Jenkins {resp.status_code}: {resp.text[:300]}", request=resp.request, response=resp)
        if "application/json" in resp.headers.get("content-type", ""):
            return resp.json()
        return resp.text


async def get_crumb() -> dict[str, str]:
    """取得 Jenkins CSRF crumb（每次 POST 前必須取得）。"""
    data = await jenkins_request("GET", "/crumbIssuer/api/json")
    return {data["crumbRequestField"]: data["crumb"]}


async def jenkins_post(path: str, body: str = "", content_type: str = "application/x-www-form-urlencoded") -> Any:
    """POST 請求：自動取得 crumb 附在 header，避免 CSRF 403。"""
    crumb = await get_crumb()
    return await jenkins_request(
        "POST", path,
        data=body,
        extra_headers={"Content-Type": content_type, **crumb},
    )


def handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401: return "錯誤：驗證失敗，請確認 JENKINS_USER 和 JENKINS_API_TOKEN 是否正確。"
        if code == 403: return "錯誤：沒有權限，或 CSRF crumb 失效，請確認帳號權限。"
        if code == 404: return "錯誤：找不到 Job，請確認 job_path 是否正確（例如 MyFolder/my-pipeline）。"
        return f"錯誤：Jenkins API 回傳 {code}，{e.response.text[:200]}"
    if isinstance(e, httpx.TimeoutException):
        return "錯誤：Jenkins 連線逾時，請確認伺服器是否可連線。"
    return f"錯誤：{type(e).__name__}: {e}"


# ── Pydantic 輸入模型 ─────────────────────────────────────────────────────────

class ListJobsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    folder: Optional[str] = Field(default=None, description="Folder 路徑，例如 MyFolder，不填則列出根目錄")

class JobPathInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_path: str = Field(..., description="Job 路徑，例如 MyFolder/my-pipeline 或 my-job")

class TriggerBuildInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_path:   str             = Field(..., description="Job 路徑，例如 MyFolder/my-pipeline")
    parameters: dict[str, str] = Field(default_factory=dict, description="Build 參數，例如 {BRANCH: 'main', ENV: 'staging'}")

class GetBuildInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_path:     str = Field(..., description="Job 路徑")
    build_number: int = Field(..., description="Build 編號，-1 表示最新一次")

class GetBuildLogInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_path:     str = Field(..., description="Job 路徑")
    build_number: int = Field(..., description="Build 編號，-1 表示最新一次")
    last_chars:   int = Field(default=5000, ge=500, le=50000, description="回傳 log 最後幾個字元（預設 5000）")

class ListBuildsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_path: str = Field(..., description="Job 路徑")
    limit:    int = Field(default=10, ge=1, le=50, description="最多幾筆")

class CancelBuildInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    job_path:     str = Field(..., description="Job 路徑")
    build_number: int = Field(..., description="要取消的 Build 編號")


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(name="jenkins_list_jobs")
async def jenkins_list_jobs(params: ListJobsInput) -> str:
    """列出 Jenkins jobs，可指定 folder。回傳 name、color（blue=成功/red=失敗）、最近一次 build 結果。"""
    try:
        if params.folder:
            path = f"/job/{_encode_job_path(params.folder)}/api/json"
        else:
            path = "/api/json?tree=jobs[name,url,color,buildable,lastBuild[number,result,timestamp]]"

        data = await jenkins_request("GET", path)
        return json.dumps([
            {
                "name":      j["name"],
                "color":     j.get("color"),   # blue=通過, red=失敗, disabled=停用
                "buildable": j.get("buildable"),
                "lastBuild": {
                    "number":    j["lastBuild"]["number"],
                    "result":    j["lastBuild"].get("result"),
                    "timestamp": j["lastBuild"].get("timestamp"),
                } if j.get("lastBuild") else None,
            }
            for j in data.get("jobs", [])
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_get_job")
async def jenkins_get_job(params: JobPathInput) -> str:
    """取得 Jenkins job 詳細資訊（健康狀態、最近成功/失敗的 build 編號）。"""
    try:
        data = await jenkins_request("GET", f"/job/{_encode_job_path(params.job_path)}/api/json")
        return json.dumps({
            "name":         data["name"],
            "description":  data.get("description"),
            "buildable":    data.get("buildable"),
            "color":        data.get("color"),
            "healthReport": data.get("healthReport", [{}])[0].get("description") if data.get("healthReport") else None,
            "lastBuild":    (data.get("lastBuild") or {}).get("number"),
            "lastSuccess":  (data.get("lastSuccessfulBuild") or {}).get("number"),
            "lastFailed":   (data.get("lastFailedBuild") or {}).get("number"),
            "recentBuilds": [b["number"] for b in (data.get("builds") or [])[:10]],
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_trigger_build")
async def jenkins_trigger_build(params: TriggerBuildInput) -> str:
    """觸發 Jenkins job build。有 parameters 時自動走 buildWithParameters endpoint。

    parameters 範例：{"BRANCH": "main", "ENV": "staging"}
    觸發後請用 jenkins_list_builds 查看 build 編號和狀態。
    """
    try:
        encoded_path = _encode_job_path(params.job_path)
        if params.parameters:
            qs = "&".join(f"{k}={v}" for k, v in params.parameters.items())
            await jenkins_post(f"/job/{encoded_path}/buildWithParameters", body=qs)
        else:
            await jenkins_post(f"/job/{encoded_path}/build")
        return f"Build 已觸發：{params.job_path}。請稍後用 jenkins_list_builds 確認 build 狀態。"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_get_build")
async def jenkins_get_build(params: GetBuildInput) -> str:
    """取得指定 Jenkins build 的詳細結果（狀態、時間、參數、測試報告摘要）。
    build_number 填 -1 表示最新一次 build。
    """
    try:
        num = "lastBuild" if params.build_number == -1 else params.build_number
        data = await jenkins_request("GET", f"/job/{_encode_job_path(params.job_path)}/{num}/api/json")

        # 從 actions 撈出參數和測試結果
        actions    = data.get("actions", [])
        build_params = next((a.get("parameters") for a in actions if a.get("parameters")), [])
        test_action  = next((a for a in actions if "totalCount" in a), None)

        return json.dumps({
            "number":    data.get("number"),
            "result":    "進行中" if data.get("building") else data.get("result"),
            "building":  data.get("building"),
            "duration":  f"{round(data.get('duration', 0) / 1000)}秒",
            "timestamp": data.get("timestamp"),
            "url":       data.get("url"),
            "causes":    [c.get("shortDescription") for a in actions for c in a.get("causes", [])],
            "params":    {p["name"]: p.get("value") for p in build_params},
            "testResult": {
                "total":   test_action.get("totalCount"),
                "failed":  test_action.get("failCount"),
                "passed":  test_action.get("passCount"),
                "skipped": test_action.get("skipCount"),
            } if test_action else None,
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_get_build_log")
async def jenkins_get_build_log(params: GetBuildLogInput) -> str:
    """取得 Jenkins build 的 console log，只回傳最後 N 個字元避免 log 太大。
    build_number 填 -1 表示最新一次 build。
    """
    try:
        num  = "lastBuild" if params.build_number == -1 else params.build_number
        log  = await jenkins_request("GET", f"/job/{_encode_job_path(params.job_path)}/{num}/consoleText")
        text = str(log)
        if len(text) > params.last_chars:
            text = f"...[已截斷，顯示最後 {params.last_chars} 個字元]...\n" + text[-params.last_chars:]
        return text
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_list_builds")
async def jenkins_list_builds(params: ListBuildsInput) -> str:
    """列出 Jenkins job 最近幾次 build 的結果和執行時間。"""
    try:
        data = await jenkins_request(
            "GET",
            f"/job/{_encode_job_path(params.job_path)}/api/json"
            f"?tree=builds[number,result,duration,timestamp,building]{{0,{params.limit}}}"
        )
        return json.dumps([
            {
                "number":    b["number"],
                "result":    "進行中" if b.get("building") else b.get("result"),
                "duration":  f"{round(b.get('duration', 0) / 1000)}秒",
                "timestamp": b.get("timestamp"),
            }
            for b in data.get("builds", [])
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_get_queue")
async def jenkins_get_queue() -> str:
    """查看 Jenkins build queue（等待執行的 jobs），包含等待原因。"""
    try:
        data = await jenkins_request("GET", "/queue/api/json")
        return json.dumps([
            {
                "id":       item["id"],
                "job":      item.get("task", {}).get("name"),
                "why":      item.get("why"),   # 等待原因，例如 "Waiting for next executor"
                "stuck":    item.get("stuck"),
                "inQueue":  item.get("inQueueSince"),
            }
            for item in data.get("items", [])
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_cancel_build")
async def jenkins_cancel_build(params: CancelBuildInput) -> str:
    """終止（abort）正在執行的 Jenkins build。這是破壞性操作，請確認後再執行。"""
    try:
        await jenkins_post(f"/job/{_encode_job_path(params.job_path)}/{params.build_number}/stop")
        return f"Build #{params.build_number} 終止請求已送出（{params.job_path}）"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_get_nodes")
async def jenkins_get_nodes() -> str:
    """取得 Jenkins 所有 agent nodes 的狀態（online/offline、執行中/空閒 executor 數量）。"""
    try:
        data = await jenkins_request("GET", "/computer/api/json")
        return json.dumps([
            {
                "name":          n.get("displayName"),
                "offline":       n.get("offline"),
                "offlineCause":  n.get("offlineCauseReason"),
                "numExecutors":  n.get("numExecutors"),
                "busyExecutors": n.get("busyExecutors", 0),
                "idleExecutors": n.get("idleExecutors", 0),
            }
            for n in data.get("computer", [])
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jenkins_get_job_config")
async def jenkins_get_job_config(params: JobPathInput) -> str:
    """取得 Jenkins job 的 config.xml（Pipeline script、參數定義、觸發條件等完整設定）。
    用途：讓 AI 理解 Pipeline 的結構、修改建議、或產生新的 Pipeline script。
    """
    try:
        xml = await jenkins_request("GET", f"/job/{_encode_job_path(params.job_path)}/config.xml")
        return str(xml)
    except Exception as e:
        return handle_error(e)


if __name__ == "__main__":
    mcp.run()
