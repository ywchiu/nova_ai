#!/usr/bin/env python3
"""
MCP Server for BitBucket（同時支援 Data Center 和 Cloud）

Data Center 認證：Personal Access Token (PAT)
  → 設定 BB_BASE_URL + BB_PAT
  → API: /rest/api/1.0/

Cloud 認證：Username + API Token（Basic Auth）
  → 設定 BB_BASE_URL + BB_USER + BB_API_TOKEN
  → API: https://api.bitbucket.org/2.0/
  → API Token 取得：BitBucket → Personal settings → API tokens
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
BB_BASE_URL     = os.environ.get("BB_BASE_URL", "").rstrip("/")
BB_PAT          = os.environ.get("BB_PAT", "")
BB_USER         = os.environ.get("BB_USER", "")
BB_API_TOKEN    = os.environ.get("BB_API_TOKEN", "")

# 自動偵測 Cloud vs Data Center
IS_CLOUD = "api.bitbucket.org" in BB_BASE_URL or "bitbucket.org" in BB_BASE_URL

if IS_CLOUD and BB_USER and BB_API_TOKEN:
    _auth_str = base64.b64encode(f"{BB_USER}:{BB_API_TOKEN}".encode()).decode()
    _auth_header = f"Basic {_auth_str}"
    API_BASE = BB_BASE_URL.rstrip("/")  # https://api.bitbucket.org/2.0
elif BB_PAT:
    _auth_header = f"Bearer {BB_PAT}"
    API_BASE = f"{BB_BASE_URL}/rest/api/1.0"
else:
    raise RuntimeError(
        "請設定 BitBucket 認證：\n"
        "  Cloud：BB_BASE_URL + BB_USER + BB_API_TOKEN\n"
        "  Data Center：BB_BASE_URL + BB_PAT"
    )

HEADERS = {
    "Authorization": _auth_header,
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
            raise httpx.HTTPStatusError(f"BitBucket {resp.status_code}: {resp.text[:300]}", request=resp.request, response=resp)
        if "application/json" in resp.headers.get("content-type", ""):
            return resp.json()
        return resp.text


async def bb_paginate(path: str, limit: int = 25) -> list[Any]:
    """自動處理 BitBucket 分頁（Cloud 和 DC 分頁機制不同）。"""
    results: list[Any] = []
    if IS_CLOUD:
        # Cloud: 用 ?page=N 或 next URL
        sep = "&" if "?" in path else "?"
        url: str | None = f"{API_BASE}{path}{sep}pagelen={limit}"
        while url:
            data = await bb_request("GET", "", raw_url=url)
            results.extend(data.get("values", []))
            url = data.get("next")
    else:
        # Data Center: 用 start + limit
        start = 0
        while True:
            sep = "&" if "?" in path else "?"
            data = await bb_request("GET", f"{path}{sep}start={start}&limit={limit}")
            results.extend(data.get("values", []))
            if data.get("isLastPage", True):
                break
            start = data.get("nextPageStart", start + limit)
    return results


def _repo_path(project_key: str, repo_slug: str) -> str:
    """根據 Cloud/DC 產生正確的 repo API 路徑"""
    if IS_CLOUD:
        return f"/repositories/{project_key}/{repo_slug}"
    return f"/projects/{project_key}/repos/{repo_slug}"


def handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401: return "錯誤：驗證失敗，請確認認證資訊是否正確。"
        if code == 403: return "錯誤：沒有權限存取此資源。"
        if code == 404: return "錯誤：找不到資源，請確認 workspace、repo slug 是否正確。"
        return f"錯誤：BitBucket API 回傳 {code}，{e.response.text[:200]}"
    if isinstance(e, httpx.TimeoutException):
        return "錯誤：BitBucket 連線逾時。"
    return f"錯誤：{type(e).__name__}: {e}"


# ── Pydantic 輸入模型 ─────────────────────────────────────────────────────────

class ListReposInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    project_key: str = Field(..., description="BitBucket project key（DC）或 workspace（Cloud），例如 NOVA")

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
    """列出 BitBucket project/workspace 底下的所有 repository。"""
    try:
        if IS_CLOUD:
            repos = await bb_paginate(f"/repositories/{params.project_key}")
            return json.dumps([
                {
                    "slug":          r["slug"],
                    "name":          r.get("name", r["slug"]),
                    "full_name":     r.get("full_name"),
                    "defaultBranch": (r.get("mainbranch") or {}).get("name"),
                    "cloneUrl":      next(
                        (c["href"] for c in r.get("links", {}).get("clone", []) if c["name"] == "https"),
                        None
                    ),
                }
                for r in repos
            ], ensure_ascii=False, indent=2)
        else:
            repos = await bb_paginate(f"/projects/{params.project_key}/repos")
            return json.dumps([
                {
                    "slug":          r["slug"],
                    "name":          r["name"],
                    "state":         r.get("state"),
                    "defaultBranch": (r.get("defaultBranch") or {}).get("displayId"),
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
        rp = _repo_path(params.project_key, params.repo_slug)
        state = params.state
        if IS_CLOUD:
            # Cloud 用小寫 state
            prs = await bb_paginate(f"{rp}/pullrequests?state={state}")
            return json.dumps([
                {
                    "id":          pr["id"],
                    "title":       pr["title"],
                    "state":       pr["state"],
                    "author":      (pr.get("author") or {}).get("display_name"),
                    "fromBranch":  (pr.get("source", {}).get("branch") or {}).get("name"),
                    "toBranch":    (pr.get("destination", {}).get("branch") or {}).get("name"),
                    "createdDate": pr.get("created_on"),
                    "reviewers": [
                        {"name": r.get("display_name", r.get("nickname")), "approved": r.get("approved", False)}
                        for r in pr.get("reviewers", [])
                    ],
                }
                for pr in prs
            ], ensure_ascii=False, indent=2)
        else:
            prs = await bb_paginate(f"{rp}/pull-requests?state={state}")
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
    """取得指定 PR 的詳細資訊（描述、Reviewer 狀態）與最近活動。"""
    try:
        rp = _repo_path(params.project_key, params.repo_slug)
        if IS_CLOUD:
            pr_path = f"{rp}/pullrequests/{params.pr_id}"
            pr = await bb_request("GET", pr_path)
            return json.dumps({
                "id":          pr["id"],
                "title":       pr["title"],
                "description": pr.get("description"),
                "state":       pr["state"],
                "author":      (pr.get("author") or {}).get("display_name"),
                "fromBranch":  (pr.get("source", {}).get("branch") or {}).get("name"),
                "toBranch":    (pr.get("destination", {}).get("branch") or {}).get("name"),
                "reviewers": [
                    {"name": r.get("display_name", r.get("nickname")), "approved": r.get("approved", False)}
                    for r in pr.get("reviewers", [])
                ],
            }, ensure_ascii=False, indent=2)
        else:
            pr_path = f"{rp}/pull-requests/{params.pr_id}"
            pr = await bb_request("GET", pr_path)
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
        rp = _repo_path(params.project_key, params.repo_slug)
        if IS_CLOUD:
            body: dict[str, Any] = {
                "title":       params.title,
                "description": params.description or "",
                "source":      {"branch": {"name": params.from_branch}},
                "destination": {"branch": {"name": params.to_branch}},
                "reviewers":   [{"uuid": name} for name in params.reviewers],
            }
            pr = await bb_request("POST", f"{rp}/pullrequests", body=body)
            url = (pr.get("links", {}).get("html", {}).get("href")
                   or f"https://bitbucket.org/{params.project_key}/{params.repo_slug}/pull-requests/{pr['id']}")
        else:
            body = {
                "title":       params.title,
                "description": params.description or "",
                "fromRef": {
                    "id": f"refs/heads/{params.from_branch}",
                    "repository": {"slug": params.repo_slug, "project": {"key": params.project_key}},
                },
                "toRef": {
                    "id": f"refs/heads/{params.to_branch}",
                    "repository": {"slug": params.repo_slug, "project": {"key": params.project_key}},
                },
                "reviewers": [{"user": {"name": name}} for name in params.reviewers],
            }
            pr = await bb_request("POST", f"{rp}/pull-requests", body=body)
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
        rp = _repo_path(params.project_key, params.repo_slug)
        if IS_CLOUD:
            result = await bb_request("POST", f"{rp}/pullrequests/{params.pr_id}/comments",
                                      body={"content": {"raw": params.text}})
        else:
            result = await bb_request("POST", f"{rp}/pull-requests/{params.pr_id}/comments",
                                      body={"text": params.text})
        return f"留言新增成功，ID: {result.get('id')}"
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_list_branches")
async def bitbucket_list_branches(params: ListBranchesInput) -> str:
    """列出 repository 的分支，可用 filter_text 依名稱過濾。"""
    try:
        rp = _repo_path(params.project_key, params.repo_slug)
        if IS_CLOUD:
            q = f'name ~ "{params.filter_text}"' if params.filter_text else ""
            path = f"{rp}/refs/branches" + (f"?q={q}" if q else "")
            branches = await bb_paginate(path)
            return json.dumps([
                {"name": b["name"], "isDefault": b.get("name") == (b.get("target", {}).get("repository", {}).get("mainbranch", {}).get("name")),
                 "latestCommit": (b.get("target") or {}).get("hash", "")[:8]}
                for b in branches
            ], ensure_ascii=False, indent=2)
        else:
            path = (
                f"{rp}/branches?orderBy=MODIFICATION"
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
        rp = _repo_path(params.project_key, params.repo_slug)
        if IS_CLOUD:
            ref = params.branch or "main"
            raw_url = f"{API_BASE}{rp}/src/{ref}/{params.file_path}"
            content = await bb_request("GET", "", raw_url=raw_url)
        else:
            at_param = f"?at=refs/heads/{params.branch}" if params.branch else ""
            raw_url = f"{BB_BASE_URL}/rest/api/1.0/projects/{params.project_key}/repos/{params.repo_slug}/raw/{params.file_path}{at_param}"
            content = await bb_request("GET", "", raw_url=raw_url)
        return str(content)
    except Exception as e:
        return handle_error(e)


@mcp.tool(name="bitbucket_list_commits")
async def bitbucket_list_commits(params: ListCommitsInput) -> str:
    """列出 repository 分支的最近 commits（id 前 8 碼、commit message 第一行、作者、時間）。"""
    try:
        rp = _repo_path(params.project_key, params.repo_slug)
        if IS_CLOUD:
            path = f"{rp}/commits"
            if params.branch:
                path += f"?include={params.branch}"
            data = await bb_request("GET", path, params={"pagelen": params.limit} if not params.branch else {"pagelen": params.limit})
            return json.dumps([
                {
                    "id":      c["hash"][:8],
                    "message": c.get("message", "").split("\n")[0],
                    "author":  (c.get("author") or {}).get("user", {}).get("display_name", (c.get("author") or {}).get("raw", "")),
                    "date":    c.get("date"),
                }
                for c in data.get("values", [])
            ], ensure_ascii=False, indent=2)
        else:
            at_param = f"&until=refs/heads/{params.branch}" if params.branch else ""
            data = await bb_request(
                "GET",
                f"{rp}/commits?limit={params.limit}{at_param}",
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
