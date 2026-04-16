#!/usr/bin/env python3
"""
Demo #2：自動化測試與 Code Review（對應課程 AI Agent Design W1）

完整模擬 Multi-Agent 工作流程：
  1. Planner Agent：從 BitBucket 讀取程式碼，分析結構
  2. Coder Agent：根據程式結構，自動產生測試策略
  3. Reviewer Agent：用 novatek-coding-style.md 規範做 Code Review
  4. 產生 Coverage 報告與 Review 意見

用法：
  cd mcp-servers
  pytest bitbucket_mcp/test_demo_review.py -v -s
"""

import json
import os
import re
import pytest

from bitbucket_mcp.server import (
    bitbucket_list_repos,
    bitbucket_list_branches,
    bitbucket_list_commits,
    bitbucket_get_file,
    ListReposInput,
    ListBranchesInput,
    ListCommitsInput,
    GetFileInput,
)

WS = os.environ.get("TEST_BB_WORKSPACE", "nova_ai_test")
REPO = os.environ.get("TEST_BB_REPO", "chip-validator")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 1：Planner Agent — 分析 Repo 結構
#  對應課程：M3「Planner Agent 分析程式結構」
# ══════════════════════════════════════════════════════════════════════════════


class TestStep1_Planner分析結構:

    @pytest.mark.asyncio
    async def test_列出Repo與分支(self):
        """Planner 先確認 repo 存在，查看分支狀態"""
        repos = json.loads(await bitbucket_list_repos(ListReposInput(project_key=WS)))
        repo_slugs = [r["slug"] for r in repos]
        assert REPO in repo_slugs
        print(f"\n  Planner：找到 repo {WS}/{REPO}")

        branches = json.loads(await bitbucket_list_branches(
            ListBranchesInput(project_key=WS, repo_slug=REPO)
        ))
        print(f"  分支：{[b['name'] for b in branches]}")

    @pytest.mark.asyncio
    async def test_讀取最近commits了解變更(self):
        """Planner 看最近的 commits，了解開發動態"""
        commits = json.loads(await bitbucket_list_commits(
            ListCommitsInput(project_key=WS, repo_slug=REPO, limit=5)
        ))
        assert len(commits) >= 1
        print(f"\n  Planner：最近 {len(commits)} 筆 commit：")
        for c in commits:
            print(f"    [{c['id']}] {c['message']}")

    @pytest.mark.asyncio
    async def test_讀取原始碼分析模組結構(self):
        """
        Planner 讀取各檔案，分析：
        - models.py：有哪些 dataclass
        - validator.py：有哪些驗證函數
        - test_validator.py：現有測試涵蓋哪些規則
        """
        # 分析 models.py
        models_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="models.py")
        )
        dataclasses = re.findall(r"class (\w+)", models_src)
        print(f"\n  Planner 分析 models.py：")
        print(f"    Data classes: {dataclasses}")

        # 分析 validator.py
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )
        functions = re.findall(r"def (validate_\w+)", validator_src)
        constants = re.findall(r"^([A-Z_]+)\s*=", validator_src, re.MULTILINE)
        print(f"\n  Planner 分析 validator.py：")
        print(f"    驗證函數: {functions}")
        print(f"    常數: {constants}")

        # 分析 test_validator.py
        test_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="tests/test_validator.py")
        )
        test_classes = re.findall(r"class (Test\w+)", test_src)
        test_methods = re.findall(r"def (test_\w+)", test_src)
        print(f"\n  Planner 分析 test_validator.py：")
        print(f"    測試類別: {test_classes}")
        print(f"    測試方法: {len(test_methods)} 個")

        # Planner 的結論
        assert len(functions) >= 6, "應有至少 6 個驗證函數"
        assert len(test_methods) >= 20, "應有至少 20 個測試"
        print(f"\n  Planner 結論：{len(functions)} 個驗證規則，{len(test_methods)} 個測試")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 2：Coder Agent — 分析測試覆蓋率缺口
#  對應課程：M3「Coder Agent 自動產生測試程式碼」
# ══════════════════════════════════════════════════════════════════════════════


class TestStep2_Coder分析測試缺口:

    @pytest.mark.asyncio
    async def test_比對驗證規則與測試的覆蓋率(self):
        """
        Coder Agent 比對 validator.py 的規則和 test_validator.py 的測試，
        找出哪些規則的測試不夠完整。
        """
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )
        test_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="tests/test_validator.py")
        )

        # 提取驗證規則名稱
        rules = re.findall(r"def (validate_\w+)", validator_src)
        # 提取 rule 字串（ValidationError 裡的 rule= 值）
        rule_names = re.findall(r'rule="(\w+)"', validator_src)

        # 分析測試覆蓋了哪些 rule
        covered_rules = set()
        for rule in rule_names:
            if rule in test_src:
                covered_rules.add(rule)

        uncovered = set(rule_names) - covered_rules

        print(f"\n  Coder Agent 測試覆蓋分析：")
        print(f"    驗證規則：{len(rule_names)} 個")
        print(f"    已覆蓋：{len(covered_rules)} 個 — {covered_rules}")
        if uncovered:
            print(f"    未覆蓋：{len(uncovered)} 個 — {uncovered}")
        else:
            print(f"    所有規則都有對應測試 ✓")

    @pytest.mark.asyncio
    async def test_找出缺少邊界值測試的規則(self):
        """
        Coder Agent 檢查每個驗證規則是否有邊界值測試：
        - 最小值通過 / 最小值-1 失敗
        - 最大值通過 / 最大值+1 失敗
        """
        test_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="tests/test_validator.py")
        )

        boundary_keywords = ["邊界", "boundary", "最小", "最大", "min", "max"]
        has_boundary = any(kw in test_src.lower() for kw in boundary_keywords)

        print(f"\n  Coder Agent 邊界值測試分析：")
        if has_boundary:
            boundary_tests = [
                line.strip() for line in test_src.split("\n")
                if "def test_" in line and any(kw in line for kw in boundary_keywords)
            ]
            print(f"    找到 {len(boundary_tests)} 個邊界值測試：")
            for t in boundary_tests:
                print(f"      {t}")
        else:
            print(f"    警告：未發現邊界值測試，建議補上")

        # 建議新增的測試
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )
        suggestions = []
        if "ADDR_MAX = 0xFFFF" in validator_src and "0xFFFF" not in test_src:
            suggestions.append("位址上限邊界：address=0xFFFF 應通過")
        if "VOLTAGE_MIN_MV" in validator_src and "750" in validator_src:
            if "749" not in test_src:
                suggestions.append("電壓下限邊界：voltage_mv=749 應失敗")

        if suggestions:
            print(f"\n    建議新增的測試：")
            for s in suggestions:
                print(f"      + {s}")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 3：Reviewer Agent — Code Review
#  對應課程：M3「Reviewer Agent 進行 Code Review」
# ══════════════════════════════════════════════════════════════════════════════


class TestStep3_Reviewer做CodeReview:

    @pytest.mark.asyncio
    async def test_檢查命名規範(self):
        """
        Reviewer 依據 novatek-coding-style.md 檢查命名：
        - 函數：snake_case
        - 類別：PascalCase
        - 常數：UPPER_SNAKE_CASE
        """
        models_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="models.py")
        )
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )

        issues = []

        # 檢查類別名稱是否 PascalCase
        classes = re.findall(r"class (\w+)", models_src + validator_src)
        for cls in classes:
            if cls[0].islower() and not cls.startswith("_"):
                issues.append(f"類別 '{cls}' 不是 PascalCase")

        # 檢查函數名稱是否 snake_case
        functions = re.findall(r"def (\w+)", validator_src)
        for fn in functions:
            if fn != fn.lower() and not fn.startswith("_"):
                issues.append(f"函數 '{fn}' 不是 snake_case")

        # 檢查常數是否 UPPER_SNAKE_CASE
        constants = re.findall(r"^([A-Z][A-Z_0-9]*)\s*=", validator_src, re.MULTILINE)
        for const in constants:
            if const != const.upper():
                issues.append(f"常數 '{const}' 不是 UPPER_SNAKE_CASE")

        print(f"\n  Reviewer 命名規範檢查：")
        print(f"    類別：{len(classes)} 個")
        print(f"    函數：{len(functions)} 個")
        print(f"    常數：{len(constants)} 個")
        if issues:
            print(f"    ⚠ 發現 {len(issues)} 個命名問題：")
            for i in issues:
                print(f"      • {i}")
        else:
            print(f"    ✓ 命名規範全部通過")

    @pytest.mark.asyncio
    async def test_檢查docstring(self):
        """
        Reviewer 檢查每個公開函數是否有 docstring
        （novatek-coding-style.md：函數必須有 docstring）
        """
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )

        # 找出所有 def，檢查下一行是否有 docstring
        lines = validator_src.split("\n")
        missing_docstring = []
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and not line.strip().startswith("def _"):
                # 檢查下一行是否是 docstring
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if not (next_line.startswith('"""') or next_line.startswith("'''")):
                    func_name = re.search(r"def (\w+)", line)
                    if func_name:
                        missing_docstring.append(func_name.group(1))

        print(f"\n  Reviewer Docstring 檢查：")
        if missing_docstring:
            print(f"    ⚠ {len(missing_docstring)} 個函數缺少 docstring：")
            for fn in missing_docstring:
                print(f"      • {fn}()")
        else:
            print(f"    ✓ 所有公開函數都有 docstring")

    @pytest.mark.asyncio
    async def test_檢查錯誤處理(self):
        """
        Reviewer 檢查：
        - 有沒有裸 except:（novatek-coding-style 禁止）
        - 有沒有用 print() 而非 logging
        """
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )

        issues = []
        lines = validator_src.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "except:" or stripped == "except :":
                issues.append(f"Line {i+1}: 裸 except:（應指定例外類型）")
            if "print(" in stripped and not stripped.startswith("#"):
                issues.append(f"Line {i+1}: 使用 print()（應使用 logging）")

        print(f"\n  Reviewer 錯誤處理檢查：")
        if issues:
            for i in issues:
                print(f"    ⚠ {i}")
        else:
            print(f"    ✓ 無裸 except，無 print()，符合規範")


# ══════════════════════════════════════════════════════════════════════════════
#  Step 4：產生 Review 報告
#  對應課程：W1「產生 Coverage 報告與 Review 意見」
# ══════════════════════════════════════════════════════════════════════════════


class TestStep4_產生Review報告:

    @pytest.mark.asyncio
    async def test_產生完整Review報告(self):
        """
        整合所有 Agent 的分析結果，產生結構化的 Review 報告。
        """
        # 讀取所有原始碼
        models_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="models.py")
        )
        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )
        test_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="tests/test_validator.py")
        )

        # 統計
        total_lines = len(models_src.split("\n")) + len(validator_src.split("\n"))
        test_lines = len(test_src.split("\n"))
        functions = re.findall(r"def (validate_\w+)", validator_src)
        test_methods = re.findall(r"def (test_\w+)", test_src)
        classes = re.findall(r"class (\w+)", models_src)
        rule_names = set(re.findall(r'rule="(\w+)"', validator_src))
        covered = {r for r in rule_names if r in test_src}

        # Review 評分
        coverage_pct = len(covered) / len(rule_names) * 100 if rule_names else 0
        has_docstrings = '"""' in validator_src
        has_type_hints = "->" in validator_src
        no_bare_except = "except:" not in validator_src.replace("except Exception", "")

        score = 0
        score += 30 if coverage_pct == 100 else int(coverage_pct * 0.3)
        score += 20 if has_docstrings else 0
        score += 20 if has_type_hints else 0
        score += 15 if no_bare_except else 0
        score += 15 if len(test_methods) >= 20 else int(len(test_methods) * 0.75)

        report = f"""
  ╔══════════════════════════════════════════════════╗
  ║       Code Review Report — chip-validator        ║
  ╠══════════════════════════════════════════════════╣
  ║  Repo:   {WS}/{REPO:<30s}    ║
  ║  Branch: main                                    ║
  ║  Score:  {score}/100                                    ║
  ╠══════════════════════════════════════════════════╣
  ║  程式碼統計                                       ║
  ║    產品程式碼：{total_lines:>4} 行                          ║
  ║    測試程式碼：{test_lines:>4} 行                          ║
  ║    Data Classes：{len(classes)} 個                           ║
  ║    驗證函數：{len(functions)} 個                              ║
  ║    測試方法：{len(test_methods)} 個                             ║
  ╠══════════════════════════════════════════════════╣
  ║  測試覆蓋                                         ║
  ║    規則覆蓋率：{coverage_pct:.0f}% ({len(covered)}/{len(rule_names)})                       ║
  ║    Docstrings：{'✓' if has_docstrings else '✗'}                                   ║
  ║    Type Hints：{'✓' if has_type_hints else '✗'}                                   ║
  ║    無裸 except：{'✓' if no_bare_except else '✗'}                                  ║
  ╠══════════════════════════════════════════════════╣
  ║  Review 結論                                      ║
  ║    {'✅ APPROVED — 程式碼品質良好，可合併' if score >= 80 else '⚠️  NEEDS WORK — 請修正後重新提交'}           ║
  ╚══════════════════════════════════════════════════╝"""

        print(report)
        assert score >= 70, f"Review 分數 {score} 低於 70"


# ══════════════════════════════════════════════════════════════════════════════
#  端對端：完整 Multi-Agent Code Review 流程
# ══════════════════════════════════════════════════════════════════════════════


class TestE2E_MultiAgent_CodeReview:

    @pytest.mark.asyncio
    async def test_完整流程(self):
        """
        模擬課堂 Demo W1 完整對話：

        使用者：「幫我 review chip-validator 這個 repo 的程式碼」

        Planner Agent：分析 repo 結構
        Coder Agent：檢查測試覆蓋率
        Reviewer Agent：依 coding style 做 review
        → 產出最終報告
        """
        print("\n  ═══════════════════════════════════════")
        print("  Multi-Agent Code Review — 完整流程 Demo")
        print("  ═══════════════════════════════════════")

        # === Planner Agent ===
        print(f"\n  [Planner] 分析 {WS}/{REPO} 結構...")
        commits = json.loads(await bitbucket_list_commits(
            ListCommitsInput(project_key=WS, repo_slug=REPO, limit=3)
        ))
        print(f"    最近 commit：{commits[0]['message']}")

        validator_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="validator.py")
        )
        functions = re.findall(r"def (validate_\w+)", validator_src)
        print(f"    找到 {len(functions)} 個驗證函數")

        # === Coder Agent ===
        print(f"\n  [Coder] 分析測試覆蓋率...")
        test_src = await bitbucket_get_file(
            GetFileInput(project_key=WS, repo_slug=REPO, file_path="tests/test_validator.py")
        )
        test_count = len(re.findall(r"def test_", test_src))
        rule_names = set(re.findall(r'rule="(\w+)"', validator_src))
        covered = {r for r in rule_names if r in test_src}
        print(f"    {test_count} 個測試，覆蓋 {len(covered)}/{len(rule_names)} 個規則")

        # === Reviewer Agent ===
        print(f"\n  [Reviewer] 依 novatek-coding-style 檢查...")
        naming_ok = all(fn == fn.lower() for fn in functions)
        has_docstrings = '"""' in validator_src
        no_print = "print(" not in validator_src
        print(f"    命名規範：{'✓' if naming_ok else '✗'}")
        print(f"    Docstrings：{'✓' if has_docstrings else '✗'}")
        print(f"    無 print()：{'✓' if no_print else '✗'}")

        # === 最終結論 ===
        all_pass = naming_ok and has_docstrings and no_print and len(covered) == len(rule_names)
        verdict = "APPROVED" if all_pass else "NEEDS WORK"
        print(f"\n  [結論] Review 結果：{verdict}")
        print(f"    規則覆蓋 {len(covered)}/{len(rule_names)}，{test_count} 個測試")

        print("\n  ═══════════════════════════════════════")
        print("  Demo 完成！")
        print("  ═══════════════════════════════════════")
