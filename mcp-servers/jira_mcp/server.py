#!/usr/bin/env python3
"""
MCP Server for Jira（同時支援 Data Center 和 Cloud）

Data Center 認證：Personal Access Token (PAT)
  → 設定 JIRA_BASE_URL + JIRA_PAT

Cloud 認證：Email + API Token（Basic Auth）
  → 設定 JIRA_BASE_URL + JIRA_EMAIL + JIRA_API_TOKEN
  → API Token 取得：https://id.atlassian.com/manage-profile/security/api-tokens
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
JIRA_BASE_URL   = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
JIRA_PAT        = os.environ.get("JIRA_PAT", "")
JIRA_EMAIL      = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN  = os.environ.get("JIRA_API_TOKEN", "")

# 自動偵測：有 EMAIL + API_TOKEN → Cloud（Basic Auth）；有 PAT → Data Center（Bearer）
if JIRA_EMAIL and JIRA_API_TOKEN:
    _auth_str = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    _auth_header = f"Basic {_auth_str}"
elif JIRA_PAT:
    _auth_header = f"Bearer {JIRA_PAT}"
else:
    raise RuntimeError(
        "請設定 Jira 認證：\n"
        "  Cloud：JIRA_BASE_URL + JIRA_EMAIL + JIRA_API_TOKEN\n"
        "  Data Center：JIRA_BASE_URL + JIRA_PAT"
    )

if not JIRA_BASE_URL:
    raise RuntimeError("請設定 JIRA_BASE_URL（例如 https://xxx.atlassian.net）")

IS_CLOUD = "atlassian.net" in JIRA_BASE_URL
API_BASE = f"{JIRA_BASE_URL}/rest/api/3" if IS_CLOUD else f"{JIRA_BASE_URL}/rest/api/2"
HEADERS  = {
    "Authorization": _auth_header,
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}

mcp = FastMCP("jira_mcp")

# ── 共用工具函數 ──────────────────────────────────────────────────────────────

async def jira_request(method: str, path: str, params: dict | None = None, body: dict | None = None) -> Any:
    """所有 Jira API 呼叫的統一入口，包含錯誤處理。"""
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, headers=HEADERS, params=params, json=body)
        if not resp.is_success:
            raise httpx.HTTPStatusError(f"Jira {resp.status_code}: {resp.text}", request=resp.request, response=resp)
        return resp.json() if resp.text else {}



def handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401: return "錯誤：驗證失敗，請確認認證資訊是否正確。"
        if code == 403: return "錯誤：沒有權限，請確認帳號有存取此資源的權限。"
        if code == 404: return "錯誤：找不到資源，請確認 issue key 或 project key 是否正確。"
        return f"錯誤：Jira API 回傳 {code}，{e.response.text[:200]}"
    if isinstance(e, httpx.TimeoutException):
        return "錯誤：Jira 連線逾時，請確認伺服器是否可連線。"
    return f"錯誤：{type(e).__name__}: {e}"


# ── Pydantic 輸入模型 ─────────────────────────────────────────────────────────

class GetIssueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    issue_key: str = Field(..., description="Jira issue key，例如 PROJ-123")

class SearchIssuesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    jql:         str = Field(..., description='JQL 查詢，例如 project=PROJ AND status="In Progress"')
    max_results: int = Field(default=20, ge=1, le=100, description="最多回傳幾筆")
    start_at:    int = Field(default=0, ge=0, description="分頁起始位置")

class CreateIssueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key:  str            = Field(..., description="Project key，例如 PROJ")
    summary:      str            = Field(..., min_length=1, description="Issue 標題")
    issue_type:   str            = Field(default="Task", description="類型：Bug / Task / Story / Epic")
    description:  Optional[str] = Field(default=None, description="描述內容")
    priority:     Optional[str] = Field(default=None, description="優先度：Highest / High / Medium / Low / Lowest")
    assignee:     Optional[str] = Field(default=None, description="指派給（username）")
    labels:       list[str]     = Field(default_factory=list, description="標籤清單")

class UpdateIssueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    issue_key:    str                 = Field(..., description="Issue key，例如 PROJ-123")
    summary:      Optional[str]      = Field(default=None)
    description:  Optional[str]      = Field(default=None)
    priority:     Optional[str]      = Field(default=None)
    assignee:     Optional[str]      = Field(default=None, description="Username，空字串表示取消指派")
    labels:       Optional[list[str]]= Field(default=None)

class AddCommentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    issue_key: str = Field(..., description="Issue key")
    body:      str = Field(..., min_length=1, description="留言內容（支援 Jira wiki markup）")

class TransitionIssueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    issue_key:     str           = Field(..., description="Issue key")
    transition_id: str           = Field(..., description="Transition ID（從 jira_get_transitions 取得）")
    comment:       Optional[str] = Field(default=None, description="轉換時附加留言")

class GetTransitionsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    issue_key: str = Field(..., description="Issue key")

class SprintIssuesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str = Field(..., description="Project key，例如 PROJ")


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(name="jira_get_issue")
async def jira_get_issue(params: GetIssueInput) -> str:
    """取得單一 Jira issue 的詳細資訊（狀態、指派人、描述、留言數）。"""
    try:
        issue = await jira_request("GET", f"/issue/{params.issue_key}")
        f = issue["fields"]
        return json.dumps({
            "key":         issue["key"],
            "summary":     f.get("summary"),
            "status":      f.get("status", {}).get("name"),
            "priority":    f.get("priority", {}).get("name"),
            "assignee":    (f.get("assignee") or {}).get("displayName", "未指派"),
            "reporter":    (f.get("reporter") or {}).get("displayName"),
            "created":     f.get("created"),
            "updated":     f.get("updated"),
            "description": f.get("description"),
            "labels":      f.get("labels", []),
            "comments":    f.get("comment", {}).get("total", 0),
            "sprint":      ((f.get("customfield_10020") or [{}])[0]).get("name"),
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_search_issues")
async def jira_search_issues(params: SearchIssuesInput) -> str:
    """用 JQL 搜尋 Jira issues，支援分頁。

    JQL 範例:
    - project=PROJ AND status="In Progress"
    - assignee=currentUser() ORDER BY updated DESC
    - sprint in openSprints() AND priority=High
    """
    try:
        search_path = "/search/jql" if IS_CLOUD else "/search"
        data = await jira_request("GET", search_path, params={
            "jql": params.jql, "maxResults": params.max_results,
            "startAt": params.start_at,
            "fields": "summary,status,assignee,priority,updated",
        })
        return json.dumps({
            "total":      data.get("total", len(data.get("issues", []))),
            "startAt":    data.get("startAt", params.start_at),
            "maxResults": data.get("maxResults", params.max_results),
            "issues": [
                {
                    "key":      i["key"],
                    "summary":  i["fields"].get("summary"),
                    "status":   (i["fields"].get("status") or {}).get("name"),
                    "assignee": (i["fields"].get("assignee") or {}).get("displayName", "未指派"),
                    "priority": (i["fields"].get("priority") or {}).get("name"),
                    "updated":  i["fields"].get("updated"),
                }
                for i in data.get("issues", [])
            ],
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_create_issue")
async def jira_create_issue(params: CreateIssueInput) -> str:
    """建立新的 Jira issue。"""
    try:
        fields: dict[str, Any] = {
            "project":   {"key": params.project_key},
            "summary":   params.summary,
            "issuetype": {"name": params.issue_type},
        }
        if params.description: fields["description"] = params.description
        if params.priority:    fields["priority"]    = {"name": params.priority}
        if params.assignee:
            # Cloud 用 accountId，Data Center 用 name
            fields["assignee"] = {"accountId": params.assignee} if IS_CLOUD else {"name": params.assignee}
        if params.labels:      fields["labels"]      = params.labels

        result = await jira_request("POST", "/issue", body={"fields": fields})
        key = result["key"]
        return f"建立成功：{key}\nURL: {JIRA_BASE_URL}/browse/{key}"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_update_issue")
async def jira_update_issue(params: UpdateIssueInput) -> str:
    """更新 Jira issue 的欄位（標題、描述、優先度、指派人、標籤），只更新有填的欄位。"""
    try:
        fields: dict[str, Any] = {}
        if params.summary     is not None: fields["summary"]     = params.summary
        if params.description is not None: fields["description"] = params.description
        if params.priority    is not None: fields["priority"]    = {"name": params.priority}
        if params.labels      is not None: fields["labels"]      = params.labels
        if params.assignee    is not None:
            if params.assignee:
                fields["assignee"] = {"accountId": params.assignee} if IS_CLOUD else {"name": params.assignee}
            else:
                fields["assignee"] = None

        await jira_request("PUT", f"/issue/{params.issue_key}", body={"fields": fields})
        return f"成功更新 {params.issue_key}"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_add_comment")
async def jira_add_comment(params: AddCommentInput) -> str:
    """在 Jira issue 新增留言（支援 Jira wiki markup）。"""
    try:
        result = await jira_request("POST", f"/issue/{params.issue_key}/comment", body={"body": params.body})
        return f"留言新增成功，ID: {result.get('id')}"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_get_transitions")
async def jira_get_transitions(params: GetTransitionsInput) -> str:
    """取得 issue 可執行的狀態轉換清單，在呼叫 jira_transition_issue 前先用這個確認 transition ID。"""
    try:
        data = await jira_request("GET", f"/issue/{params.issue_key}/transitions")
        return json.dumps([
            {"id": t["id"], "name": t["name"], "to": t.get("to", {}).get("name")}
            for t in data.get("transitions", [])
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_transition_issue")
async def jira_transition_issue(params: TransitionIssueInput) -> str:
    """執行 Jira issue 狀態轉換（例如：待辦 → 進行中 → 完成）。
    請先用 jira_get_transitions 取得 transition ID。
    """
    try:
        body: dict[str, Any] = {"transition": {"id": params.transition_id}}
        if params.comment:
            body["update"] = {"comment": [{"add": {"body": params.comment}}]}
        await jira_request("POST", f"/issue/{params.issue_key}/transitions", body=body)
        return f"{params.issue_key} 狀態轉換成功"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_list_projects")
async def jira_list_projects() -> str:
    """列出所有可存取的 Jira 專案（key、name、type）。"""
    try:
        projects = await jira_request("GET", "/project")
        return json.dumps([
            {"key": p["key"], "name": p["name"], "type": p.get("projectTypeKey")}
            for p in projects
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="jira_get_sprint_issues")
async def jira_get_sprint_issues(params: SprintIssuesInput) -> str:
    """取得某專案目前 active sprint 的所有 issues。"""
    try:
        jql = f'project="{params.project_key}" AND sprint in openSprints() ORDER BY status ASC'
        search_path = "/search/jql" if IS_CLOUD else "/search"
        data = await jira_request("GET", search_path, params={
            "jql": jql, "maxResults": 100,
            "fields": "summary,status,assignee,priority",
        })
        return json.dumps({
            "total": data.get("total", len(data.get("issues", []))),
            "issues": [
                {
                    "key":      i["key"],
                    "summary":  i["fields"].get("summary"),
                    "status":   (i["fields"].get("status") or {}).get("name"),
                    "assignee": (i["fields"].get("assignee") or {}).get("displayName", "未指派"),
                    "priority": (i["fields"].get("priority") or {}).get("name"),
                }
                for i in data.get("issues", [])
            ],
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


if __name__ == "__main__":
    mcp.run()
