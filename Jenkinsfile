// Jenkinsfile — target-project 流水线配置
//
// 触发条件:
//   - PR 创建/更新时：执行 PR 审查 Agent + 跑测试 + 失败分类
//   - 合并到 main 时：额外执行测试用例维护 Agent
//   - 手动触发发布时：执行影响评估 Agent

pipeline {
    agent any

    parameters {
        string(name: 'PR_NUMBER', defaultValue: '', description: 'GitHub PR 编号（PR 触发时自动填入）')
        string(name: 'BASE_TAG',  defaultValue: '', description: '上一个版本 tag，发布时填写，如 v1.0.0')
        string(name: 'HEAD_TAG',  defaultValue: 'main', description: '本次发布版本')
    }

    environment {
        PYTHON       = 'python'
        AGENTS_DIR   = 'agents'
        // TODO: 在 Jenkins Credentials 中配置后取消注释
        // DOUBAO_API_KEY = credentials('DOUBAO_API_KEY')
        // GITHUB_TOKEN   = credentials('GITHUB_TOKEN')
    }

    stages {

        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Install Dependencies') {
            steps {
                sh '${PYTHON} -m pip install -r requirements.txt'
            }
        }

        stage('Agent: PR Review') {
            when { expression { params.PR_NUMBER != '' } }
            steps {
                sh "${PYTHON} ${AGENTS_DIR}/agent_pr_review.py ${params.PR_NUMBER}"
            }
            post {
                failure { echo 'PR 审查 Agent 失败，跳过（不影响构建）' }
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    ${PYTHON} -m pytest tests/ \
                        --json-report --json-report-file=report.json \
                        --cov=app --cov-report=xml:coverage.xml \
                        -v || true
                '''
            }
        }

        stage('Agent: Failure Triage') {
            steps {
                script {
                    def exitCode = sh(
                        script: "${PYTHON} ${AGENTS_DIR}/agent_failure_triage.py report.json ${BUILD_URL}",
                        returnStatus: true
                    )
                    if (exitCode != 0) {
                        error('检测到代码 Bug，流水线已拦截，请查看飞书通知')
                    }
                }
            }
        }

        stage('Agent: Coverage') {
            steps {
                sh "${PYTHON} ${AGENTS_DIR}/agent_coverage.py coverage.xml || true"
            }
        }

        stage('Agent: Impact Evaluation') {
            when { expression { params.BASE_TAG != '' } }
            steps {
                script {
                    def exitCode = sh(
                        script: "${PYTHON} ${AGENTS_DIR}/agent_impact.py ${params.BASE_TAG} ${params.HEAD_TAG}",
                        returnStatus: true
                    )
                    if (exitCode != 0) {
                        input message: '⚠️ 高风险发布，是否继续？', ok: '确认发布'
                    }
                }
            }
        }

        stage('Agent: Update Tests After Merge') {
            when {
                allOf {
                    branch 'main'
                    expression { params.PR_NUMBER != '' }
                }
            }
            steps {
                sh "${PYTHON} ${AGENTS_DIR}/agent_test_updater.py ${params.PR_NUMBER} || true"
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'report.json, coverage.xml', allowEmptyArchive: true
        }
    }
}
