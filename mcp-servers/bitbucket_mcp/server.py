#!/usr/bin/env python3
"""
MCP Server for BitBucket 8.19.8 (Data Center / Self-hosted)

Auth: Personal Access Token (PAT)
取得方式: BitBucket → 右上角頭像 → Manage Account → HTTP Access Tokens → Create token
注意：Data Center REST API 用 /rest/api/1.0/（不是 cloud 的 v2）
"""

import json
import os
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
import httpx
from mcp.server.fastmcp import FastMCP

# ── 設定 ─────────────────────────────────────────────────────────────────────
BB_BASE_URL = os.environ.get("BB_BASE_URL", "").rstrip("/")
BB_PAT      = os.environ.get("BB_PAT", "")

if not BB_BASE_URL or not BB_PAT:
    raise RuntimeError("請設定環境變數 BB_BASE_URL 和 BB_PAT")

API_BASE = f"{BB_BASE_URL}/rest/api/1.0"
HEADERS  = {
    "Authorization": f"Bearer {BB_PAT}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}

mcp = FastMCP("bitbucket_mcp")

# ── 共用工具函數 ──────────────────────────────────────────────────────────────

async def bb_request(method: str, path: str, params: dict | None = None, body: dict | None = None, raw_url: str | None = None) -> Any:
    """所有 BitBucket API 呼叫的統一入口。"""
    url = raw_url or f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, headers=HEADERS, params=params, json=body)
        if not resp.is_success:
            raise httpx.HTTPStatusError(f"BitBucket {resp.status_code}: {resp.text}", request=resp.request, response=resp)
        if "application/json" in resp.headers.get("content-type", ""):
            return resp.json()
        return resp.text


async def bb_paginate(path: str, limit: int = 25) -> list[Any]:
    """自動處理 BitBucket 分頁，把所有結果合併回傳。"""
    results: list[Any] = []
    start = 0
    while True:
        sep = "&" if "?" in path else "?"
        data = await bb_request("GET", f"{path}{sep}start={start}&limit={limit}")
        results.extend(data.get("values", []))
        if data.get("isLastPage", True):
            break
        start = data.get("nextPageStart", start + limit)
    return results


def handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401: return "錯誤：PAT 驗證失敗，請確認 BB_PAT 是否正確。"
        if code == 403: return "錯誤：沒有權限存取此資源。"
        if code == 404: return "錯誤：找不到資源，請確認 project key、repo slug 是否正確。"
        return f"錯誤：BitBucket API 回傳 {code}，{e.response.text[:200]}"
    if isinstance(e, httpx.TimeoutException):
        return "錯誤：BitBucket 連線逾時。"
    return f"錯誤：{type(e).__name__}: {e}"


# ── Pydantic 輸入模型 ─────────────────────────────────────────────────────────

class ListReposInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str = Field(..., description="BitBucket project key，例如 NOVA")

class ListPRsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str = Field(..., description="Project key")
    repo_slug:   str = Field(..., description="Repository slug")
    state:       str = Field(default="OPEN", description="PR 狀態：OPEN / MERGED / DECLINED / ALL")

class GetPRInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str = Field(..., description="Project key")
    repo_slug:   str = Field(..., description="Repository slug")
    pr_id:       int = Field(..., description="Pull request ID")

class CreatePRInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key:  str            = Field(..., description="Project key")
    repo_slug:    str            = Field(..., description="Repository slug")
    title:        str            = Field(..., min_length=1, description="PR 標題")
    description:  Optional[str] = Field(default=None, description="PR 描述")
    from_branch:  str            = Field(..., description="來源分支名稱")
    to_branch:    str            = Field(default="main", description="目標分支名稱")
    reviewers:    list[str]      = Field(default_factory=list, description="Reviewer usernames")

class PRCommentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str = Field(..., description="Project key")
    repo_slug:   str = Field(..., description="Repository slug")
    pr_id:       int = Field(..., description="PR ID")
    text:        str = Field(..., min_length=1, description="留言內容")

class ListBranchesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key:  str           = Field(..., description="Project key")
    repo_slug:    str           = Field(..., description="Repository slug")
    filter_text:  Optional[str] = Field(default=None, description="分支名稱過濾字串")

class GetFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str           = Field(..., description="Project key")
    repo_slug:   str           = Field(..., description="Repository slug")
    file_path:   str           = Field(..., description="檔案路徑，例如 src/main/App.java")
    branch:      Optional[str] = Field(default=None, description="分支名稱（不填則用預設分支）")

class ListCommitsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str           = Field(..., description="Project key")
    repo_slug:   str           = Field(..., description="Repository slug")
    branch:      Optional[str] = Field(default=None, description="分支名稱")
    limit:       int           = Field(default=20, ge=1, le=50, description="最多幾筆")


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(name="bitbucket_list_repos")
async def bitbucket_list_repos(params: ListReposInput) -> str:
    """列出 BitBucket project 底下的所有 repository（slug、name、state、cloneUrl）。"""
    try:
        repos = await bb_paginate(f"/projects/{params.project_key}/repos")
        return json.dumps([
            {
                "slug":          r["slug"],
                "name":          r["name"],
                "state":         r.get("state"),
                "defaultBranch": r.get("defaultBranch", {}).get("displayId"),
                "cloneUrl":      next(
                    (c["href"] for c in r.get("links", {}).get("clone", []) if c["name"] == "http"),
                    None
                ),
            }
            for r in repos
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_list_prs")
async def bitbucket_list_prs(params: ListPRsInput) -> str:
    """列出 BitBucket repository 的 Pull Requests（可依 OPEN/MERGED/DECLINED/ALL 過濾）。"""
    try:
        prs = await bb_paginate(
            f"/projects/{params.project_key}/repos/{params.repo_slug}/pull-requests?state={params.state}"
        )
        return json.dumps([
            {
                "id":          pr["id"],
                "title":       pr["title"],
                "state":       pr["state"],
                "author":      pr.get("author", {}).get("user", {}).get("displayName"),
                "fromBranch":  pr.get("fromRef", {}).get("displayId"),
                "toBranch":    pr.get("toRef", {}).get("displayId"),
                "createdDate": pr.get("createdDate"),
                "reviewers": [
                    {"name": r["user"]["displayName"], "approved": r["approved"], "status": r["status"]}
                    for r in pr.get("reviewers", [])
                ],
            }
            for pr in prs
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_get_pr")
async def bitbucket_get_pr(params: GetPRInput) -> str:
    """取得指定 PR 的詳細資訊（描述、Reviewer 狀態）與最近 5 筆活動。"""
    try:
        pr_path   = f"/projects/{params.project_key}/repos/{params.repo_slug}/pull-requests/{params.pr_id}"
        pr        = await bb_request("GET", pr_path)
        acts_data = await bb_request("GET", f"{pr_path}/activities", params={"limit": 10})
        return json.dumps({
            "id":          pr["id"],
            "title":       pr["title"],
            "description": pr.get("description"),
            "state":       pr["state"],
            "author":      pr.get("author", {}).get("user", {}).get("displayName"),
            "fromBranch":  pr.get("fromRef", {}).get("displayId"),
            "toBranch":    pr.get("toRef", {}).get("displayId"),
            "reviewers": [
                {"name": r["user"]["displayName"], "approved": r["approved"]}
                for r in pr.get("reviewers", [])
            ],
            "recentActivity": [
                {"action": a["action"], "user": a.get("user", {}).get("displayName"), "date": a.get("createdDate")}
                for a in acts_data.get("values", [])[:5]
            ],
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_create_pr")
async def bitbucket_create_pr(params: CreatePRInput) -> str:
    """建立 BitBucket Pull Request。"""
    try:
        body: dict[str, Any] = {
            "title":       params.title,
            "description": params.description or "",
            "fromRef": {
                "id":         f"refs/heads/{params.from_branch}",
                "repository": {"slug": params.repo_slug, "project": {"key": params.project_key}},
            },
            "toRef": {
                "id":         f"refs/heads/{params.to_branch}",
                "repository": {"slug": params.repo_slug, "project": {"key": params.project_key}},
            },
            "reviewers": [{"user": {"name": name}} for name in params.reviewers],
        }
        pr = await bb_request(
            "POST",
            f"/projects/{params.project_key}/repos/{params.repo_slug}/pull-requests",
            body=body,
        )
        url = next(
            (link["href"] for link in pr.get("links", {}).get("self", [])),
            f"{BB_BASE_URL}/projects/{params.project_key}/repos/{params.repo_slug}/pull-requests/{pr['id']}"
        )
        return f"建立成功：PR #{pr['id']} - {pr['title']}\nURL: {url}"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_add_pr_comment")
async def bitbucket_add_pr_comment(params: PRCommentInput) -> str:
    """在 BitBucket PR 新增留言。"""
    try:
        result = await bb_request(
            "POST",
            f"/projects/{params.project_key}/repos/{params.repo_slug}/pull-requests/{params.pr_id}/comments",
            body={"text": params.text},
        )
        return f"留言新增成功，ID: {result.get('id')}"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_list_branches")
async def bitbucket_list_branches(params: ListBranchesInput) -> str:
    """列出 repository 的分支，可用 filter_text 依名稱過濾。"""
    try:
        path = (
            f"/projects/{params.project_key}/repos/{params.repo_slug}/branches?orderBy=MODIFICATION"
            + (f"&filterText={params.filter_text}" if params.filter_text else "")
        )
        branches = await bb_paginate(path)
        return json.dumps([
            {"name": b["displayId"], "isDefault": b.get("isDefault", False), "latestCommit": b.get("latestCommit", "")[:8]}
            for b in branches
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_get_file")
async def bitbucket_get_file(params: GetFileInput) -> str:
    """取得 BitBucket repository 中某檔案的原始文字內容。"""
    try:
        at_param = f"?at=refs/heads/{params.branch}" if params.branch else ""
        raw_url  = f"{BB_BASE_URL}/rest/api/1.0/projects/{params.project_key}/repos/{params.repo_slug}/raw/{params.file_path}{at_param}"
        content  = await bb_request("GET", "", raw_url=raw_url)
        return str(content)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_list_commits")
async def bitbucket_list_commits(params: ListCommitsInput) -> str:
    """列出 repository 分支的最近 commits（id 前 8 碼、commit message 第一行、作者、時間）。"""
    try:
        at_param = f"&until=refs/heads/{params.branch}" if params.branch else ""
        data = await bb_request(
            "GET",
            f"/projects/{params.project_key}/repos/{params.repo_slug}/commits?limit={params.limit}{at_param}",
        )
        return json.dumps([
            {
                "id":      c["id"][:8],
                "message": c.get("message", "").split("\n")[0],
                "author":  c.get("author", {}).get("name"),
                "date":    c.get("authorTimestamp"),
            }
            for c in data.get("values", [])
        ], ensure_ascii=False, indent=2)
    except Exception as e:
        return handle_error(e)


if __name__ == "__main__":
    mcp.run()
