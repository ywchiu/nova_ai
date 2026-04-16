#!/usr/bin/env python3
"""
建立 Jenkins 測試用 Jobs

在跑整合測試之前，先執行這個腳本來建立所需的測試 Jobs：
  - mcp-test-job          ：簡單的 freestyle job（echo hello）
  - mcp-param-job         ：帶參數的 job（BRANCH, ENV）
  - mcp-fail-job          ：永遠會失敗的 job（測試錯誤處理）
  - mcp-slow-job          ：跑 30 秒的 job（測試取消 build）
  - TestFolder/nested-job ：放在 folder 裡的 job（測試路徑處理）

用法：
  JENKINS_URL=http://localhost:9090 \
  JENKINS_USER=admin \
  JENKINS_API_TOKEN=<token> \
  python jenkins_mcp/setup_test_jobs.py
"""

import os
import sys
import httpx

JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:9090")
JENKINS_USER = os.environ.get("JENKINS_USER", "admin")
JENKINS_API_TOKEN = os.environ.get("JENKINS_API_TOKEN", "")

if not JENKINS_API_TOKEN:
    print("錯誤：請設定 JENKINS_API_TOKEN 環境變數")
    sys.exit(1)

AUTH = (JENKINS_USER, JENKINS_API_TOKEN)


def get_crumb(client: httpx.Client) -> dict[str, str]:
    resp = client.get(f"{JENKINS_URL}/crumbIssuer/api/json", auth=AUTH)
    data = resp.json()
    return {data["crumbRequestField"]: data["crumb"]}


def create_job(client: httpx.Client, name: str, config_xml: str, folder: str | None = None):
    """建立 job，如果已存在則跳過"""
    crumb = get_crumb(client)

    if folder:
        # 先確保 folder 存在
        folder_xml = """<?xml version="1.0" encoding="UTF-8"?>
<com.cloudbees.hudson.plugins.folder.Folder>
  <description>測試用 Folder</description>
</com.cloudbees.hudson.plugins.folder.Folder>"""
        resp = client.post(
            f"{JENKINS_URL}/createItem",
            params={"name": folder},
            headers={"Content-Type": "application/xml", **crumb},
            content=folder_xml,
            auth=AUTH,
        )
        if resp.status_code == 200:
            print(f"  ✓ Folder '{folder}' 建立成功")
        elif resp.status_code == 400 and "already exists" in resp.text:
            print(f"  - Folder '{folder}' 已存在，跳過")
        else:
            print(f"  ✗ Folder '{folder}' 建立失敗：{resp.status_code}")
            return

        base_url = f"{JENKINS_URL}/job/{folder}"
        crumb = get_crumb(client)
    else:
        base_url = JENKINS_URL

    resp = client.post(
        f"{base_url}/createItem",
        params={"name": name},
        headers={"Content-Type": "application/xml", **crumb},
        content=config_xml,
        auth=AUTH,
    )
    full_name = f"{folder}/{name}" if folder else name
    if resp.status_code == 200:
        print(f"  ✓ Job '{full_name}' 建立成功")
    elif resp.status_code == 400 and "already exists" in resp.text:
        print(f"  - Job '{full_name}' 已存在，跳過")
    else:
        print(f"  ✗ Job '{full_name}' 建立失敗：{resp.status_code} {resp.text[:200]}")


# ── Job 定義 ─────────────────────────────────────────────────────────────────

SIMPLE_JOB = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <description>MCP 測試用：簡單 Job</description>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "Hello from MCP test job"</command>
    </hudson.tasks.Shell>
  </builders>
</project>"""

PARAM_JOB = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <description>MCP 測試用：帶參數的 Job</description>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <defaultValue>main</defaultValue>
          <description>Git branch 名稱</description>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>ENV</name>
          <defaultValue>staging</defaultValue>
          <description>部署環境（staging / production）</description>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "部署分支 ${BRANCH} 到 ${ENV} 環境"</command>
    </hudson.tasks.Shell>
  </builders>
</project>"""

FAIL_JOB = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <description>MCP 測試用：一定會失敗的 Job</description>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "即將失敗..." &amp;&amp; exit 1</command>
    </hudson.tasks.Shell>
  </builders>
</project>"""

SLOW_JOB = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <description>MCP 測試用：長時間執行的 Job（用來測試取消功能）</description>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "開始長時間任務..." &amp;&amp; sleep 30 &amp;&amp; echo "完成"</command>
    </hudson.tasks.Shell>
  </builders>
</project>"""

NESTED_JOB = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <description>MCP 測試用：放在 Folder 裡的 Job</description>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "來自 TestFolder 裡的 nested job"</command>
    </hudson.tasks.Shell>
  </builders>
</project>"""


# ── 課程 M4 CI/CD Pipeline 場景 ──────────────────────────────────────────────

PIPELINE_CICD = """<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>課程 M4：模擬完整 CI/CD Pipeline（Build → Test → Deploy）</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
pipeline {
    agent any
    parameters {
        string(name: 'BRANCH', defaultValue: 'main', description: 'Git branch')
        string(name: 'PR_ID', defaultValue: '', description: 'Pull Request ID（空值表示非 PR 觸發）')
    }
    stages {
        stage('Checkout') {
            steps {
                echo "Checking out branch: ${params.BRANCH}"
                echo "PR ID: ${params.PR_ID ?: 'N/A (direct push)'}"
            }
        }
        stage('Build') {
            steps {
                echo '--- Compiling project ---'
                sh 'sleep 2'
                echo 'Build completed successfully'
            }
        }
        stage('Test') {
            steps {
                echo '--- Running unit tests ---'
                sh 'sleep 1'
                echo 'All 42 tests passed'
            }
        }
        stage('Deploy') {
            when {
                expression { return params.BRANCH == 'main' }
            }
            steps {
                echo '--- Deploying to staging ---'
                sh 'sleep 1'
                echo 'Deployment successful'
            }
        }
    }
    post {
        success { echo '✅ Pipeline 完成：所有階段通過' }
        failure { echo '❌ Pipeline 失敗：請檢查錯誤 log' }
    }
}
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""

PIPELINE_FAIL_STAGE = """<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>課程 M4：Pipeline 在 Test 階段失敗（錯誤處理演練）</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Build OK'
            }
        }
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh 'exit 1'
            }
        }
        stage('Deploy') {
            steps {
                echo 'This stage should NOT run'
            }
        }
    }
    post {
        failure { echo '❌ Pipeline 失敗於 Test 階段' }
    }
}
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""

PIPELINE_PR_REVIEW = """<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>課程 M4：PR → Agent Review → Jenkins Build 流程</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
pipeline {
    agent any
    parameters {
        string(name: 'PR_ID', defaultValue: '1', description: 'Bitbucket PR 編號')
        string(name: 'PR_BRANCH', defaultValue: 'feature/new-api', description: 'PR 來源分支')
        string(name: 'PR_AUTHOR', defaultValue: 'developer', description: 'PR 作者')
    }
    stages {
        stage('PR Info') {
            steps {
                echo "=== PR #${params.PR_ID} 審查報告 ==="
                echo "分支: ${params.PR_BRANCH}"
                echo "作者: ${params.PR_AUTHOR}"
            }
        }
        stage('Code Review') {
            steps {
                echo '--- AI Agent 正在進行 Code Review ---'
                sh 'sleep 1'
                echo 'Code Review 結果: 符合規範，建議合併'
            }
        }
        stage('Build & Test') {
            steps {
                echo '--- 建置與測試 ---'
                sh 'sleep 2'
                echo '建置成功，所有測試通過'
            }
        }
        stage('Report') {
            steps {
                echo "=== PR #${params.PR_ID} 最終結果 ==="
                echo '狀態: ✅ 通過'
                echo 'Code Review: 通過'
                echo 'Build: 成功'
                echo 'Test: 全部通過'
            }
        }
    }
}
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""


# ── CI/CD Demo：chip_validator 真實專案 ──────────────────────────────────────

CHIP_VALIDATOR_PIPELINE = """<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>CI/CD Demo：晶片暫存器設定驗證器（真實 pytest）</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                echo '=== 建立虛擬環境並安裝 pytest ==='
                sh 'python3 -m venv /var/jenkins_home/.venv-ci || true'
                sh '/var/jenkins_home/.venv-ci/bin/pip install --quiet pytest'
            }
        }
        stage('Lint') {
            steps {
                echo '=== 程式碼風格檢查 ==='
                sh '/var/jenkins_home/.venv-ci/bin/python -m py_compile /var/jenkins_home/chip_validator/models.py'
                sh '/var/jenkins_home/.venv-ci/bin/python -m py_compile /var/jenkins_home/chip_validator/validator.py'
                echo 'Lint 通過：無語法錯誤'
            }
        }
        stage('Test') {
            steps {
                echo '=== 執行單元測試 ==='
                sh '/var/jenkins_home/.venv-ci/bin/python -m pytest /var/jenkins_home/chip_validator/tests/test_validator.py -v --tb=short --no-header --junitxml=/var/jenkins_home/test-results.xml'
            }
        }
        stage('Report') {
            steps {
                echo '=== 測試報告 ==='
                sh 'cat /var/jenkins_home/test-results.xml | head -20 || true'
                echo '✅ CI Pipeline 完成'
            }
        }
    }
    post {
        success { echo '✅ chip_validator CI 通過：所有驗證規則的測試均正確' }
        failure { echo '❌ chip_validator CI 失敗：請檢查 Test 階段的錯誤輸出' }
    }
}
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""

CHIP_VALIDATOR_FAIL = """<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>CI/CD Demo：chip_validator 測試失敗版（演示 Agent 診斷流程）</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'python3 -m venv /var/jenkins_home/.venv-ci || true'
                sh '/var/jenkins_home/.venv-ci/bin/pip install --quiet pytest'
            }
        }
        stage('Inject Bug') {
            steps {
                echo '=== 模擬：有人改壞了 clock 頻率上限 ==='
                echo '修改 CLOCK_MAX_MHZ 從 800.0 → 100.0'
                sh 'cp /var/jenkins_home/chip_validator/validator.py /var/jenkins_home/chip_validator/validator.py.bak'
                sh "sed -i 's/CLOCK_MAX_MHZ = 800.0/CLOCK_MAX_MHZ = 100.0/' /var/jenkins_home/chip_validator/validator.py"
            }
        }
        stage('Test') {
            steps {
                echo '=== 執行單元測試（預期會失敗）==='
                sh '/var/jenkins_home/.venv-ci/bin/python -m pytest /var/jenkins_home/chip_validator/tests/test_validator.py -v --tb=short --no-header'
            }
        }
    }
    post {
        always {
            echo '=== 還原被修改的檔案 ==='
            sh 'cp /var/jenkins_home/chip_validator/validator.py.bak /var/jenkins_home/chip_validator/validator.py || true'
        }
        failure { echo '❌ CI 失敗：clock 頻率驗證規則被改壞了' }
    }
}
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>"""


def main():
    print("=== 建立 Jenkins 測試 Jobs ===\n")

    with httpx.Client(timeout=15.0) as client:
        # 基礎測試 Jobs
        create_job(client, "mcp-test-job", SIMPLE_JOB)
        create_job(client, "mcp-param-job", PARAM_JOB)
        create_job(client, "mcp-fail-job", FAIL_JOB)
        create_job(client, "mcp-slow-job", SLOW_JOB)
        create_job(client, "nested-job", NESTED_JOB, folder="TestFolder")

        # 課程 M4 Pipeline Jobs
        create_job(client, "pipeline-cicd", PIPELINE_CICD)
        create_job(client, "pipeline-fail-stage", PIPELINE_FAIL_STAGE)
        create_job(client, "pipeline-pr-review", PIPELINE_PR_REVIEW)

        # CI/CD Demo：chip_validator 真實專案
        create_job(client, "chip-validator-ci", CHIP_VALIDATOR_PIPELINE)
        create_job(client, "chip-validator-ci-fail", CHIP_VALIDATOR_FAIL)

    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
