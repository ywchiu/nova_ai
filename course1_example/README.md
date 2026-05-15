# Course 1 範例包｜Log Error Summarizer

下午場投影片用到的 prompt、設定檔與一份已完成的練習 scaffold 都收在這裡。`00_` 到 `13_` 的 `.md` 檔可以直接整段複製到 Cline 對話框；`src/`、`tests/`、`specs/`、`output/` 則是投影片 Project Structure 對應的完成版範例。

## 檔案地圖

```
course1_example/
├── .cline/skills/log-error-analysis/ # Cline Skills：log 錯誤分析能力包
├── .clinerules/                      # Cline Rules 與 Workflows
├── 00_cline_setup_check.md         # Cline：課前環境 smoke test
├── 01_sdd_initial_spec.md          # SDD：第一次建立 spec 的指令
├── 02_sdd_acceptance_criteria.md   # SDD：產生驗收條件的指令
├── 03_tdd_generate_tests.md        # TDD：把驗收條件轉成 pytest 測試
├── 03b_tdd_implement_v1.md         # TDD：最小實作，讓第一版測試通過
├── 04_extension_warning_sdd.md     # 擴充需求一：支援 WARNING
├── 05_extension_repeated_sdd.md    # 擴充需求二：重複錯誤訊息
├── 06_rules_project.md             # Rules：完整專案規則
├── 07_skill_log_analysis.md        # Skills：log 錯誤分析的能力包
├── 08_workflow_sdd_feature.md      # Workflows：通用功能開發 SOP
├── 09_workflow_summarize_logs.md   # Workflows：log 分析 SOP
├── 10_mcp_issue_driven.md          # MCP：Issue 驅動開發指令
├── 11_workshop_issue128.md         # Workshop：完整 Issue 驅動流程
├── 12_debug_analyze.md             # Debug：先分析不要先改的指令
├── 13_debug_regression_test.md     # Debug：先補 regression 測試的指令
├── output/                         # 已用 sample_logs 產生的範例報告
├── sample_logs/                    # 可複製到工作目錄的 demo logs
├── specs/                          # SDD 規格與 Acceptance Criteria
├── src/log_summarizer.py           # 主要實作
└── tests/test_log_summarizer.py    # pytest 測試
```

## 使用方式

1. 投影片講到對應概念時，老師會提示對應檔名
2. 先跑 `00_cline_setup_check.md`，確認 provider / model / workspace 正常
3. 在 Cline 把整個檔案內容貼到對話框
4. Cline 會跟著裡面的步驟跑
5. 過程中如果要客製，自行調整 prompt 內的限制條件

如果只是想看完成版，可以直接打開 `src/log_summarizer.py`、`tests/test_log_summarizer.py`、`specs/` 與 `output/`。這些檔案是跑完整套 SDD / TDD / Rules / Skills / Workflows 後應該長出的樣子。

測試步驟會用到 `pytest`。如果 Cline terminal 顯示 `No module named pytest`，先執行：

```bash
python -m pip install pytest
```

如果使用 `rapid-mlx serve qwen3.6-35b` 作為 OpenAI-compatible provider，Cline 的 Base URL 請先用 `/v1/models` 確認真的看得到 `qwen3.6-35b`。若 `http://localhost:8000/v1/models` 連到其他服務，改用本機 LAN IP，例如 `http://<your-lan-ip>:8000/v1`。

如果你的練習工作目錄還沒有 `sample_logs/`，先把 `course1_example/sample_logs/` 複製到工作目錄根目錄。建立完成後，把 `sample_logs/` 視為唯讀資料，不要讓 Cline 修改。

## 本地驗證

在 `course1_example/` 底下執行：

```bash
python -m pytest -q
```

若上層 `.python-version` 指到本機沒有安裝的 pyenv 版本，可以先改用系統 Python：

```bash
PYENV_VERSION=system python3 -m pytest -q
```

重新產生範例報告：

```bash
python - <<'PY'
from src.log_summarizer import summarize_logs

summarize_logs("sample_logs", "output")
PY
```

## 共同前提

這套範例都是針對「Log Error Summarizer」這個下午場的貫穿案例。你的工作目錄應該長這樣：

```
sample_logs/                # 原始 log（不可改）
src/log_summarizer.py        # 主要實作
tests/test_log_summarizer.py # pytest 測試
output/                      # 報告輸出
specs/                       # 規格文件（SDD）
.clinerules/                 # Cline 專案規則（Rules）
.cline/skills/               # Cline 任務能力包（Skills）
.clinerules/workflows/       # Cline 流程指令（Workflows）
```

## Cline 路徑速查

這份範例已用 Cline 3.82 測過路徑：

```
.clinerules/project.md
.cline/skills/log-error-analysis/SKILL.md
.clinerules/workflows/sdd-feature.md
.clinerules/workflows/summarize-logs.md
```
