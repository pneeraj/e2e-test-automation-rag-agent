// Windows-native pipeline (bat steps, no Docker - blocked by IT policy on
// this machine): install deps, run the three Playwright suites in sequence,
// always publish the HTML report, then hand failures (if any) to the Python
// RAG agent for automated Jira triage.
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    triggers {
        // nightly full run in addition to the usual "build on push" webhook
        cron('H 2 * * *')
    }

    environment {
        CI = 'true'
        // Jenkins credential bindings, not literal values.
        JIRA_API_TOKEN = credentials('jira-api-token')
        OPENAI_API_KEY = credentials('openai-api-key')
        RAG_DRY_RUN = 'true'
    }

    stages {
        stage('Install') {
            steps {
                bat 'npm ci'
                bat 'npx playwright install chromium webkit'
                bat 'py -m pip install -r rag-defect-agent\\requirements.txt'
            }
        }

        // Suites run sequentially: on a single Windows box, three parallel
        // Playwright runs would fight over CPU and write to the same
        // playwright-report/ folder.
        stage('UI tests') {
            steps { bat 'py ci\\run_tests.py --suite ui' }
        }
        stage('API tests') {
            steps { bat 'py ci\\run_tests.py --suite api' }
        }
        stage('Mobile tests') {
            steps { bat 'py ci\\run_tests.py --suite mobile' }
        }

        stage('Summarize') {
            steps {
                // non-zero exit means "there were failures" - keep the build
                // going so the report + defect-triage stages still run.
                bat script: 'py ci\\summarize_report.py', returnStatus: true
            }
        }

        stage('Triage failures') {
            when {
                expression { fileExists('test-results/failures.json') }
            }
            steps {
                bat 'py rag-defect-agent\\analyze_failures.py'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'playwright-report/**, test-results/*.json', allowEmptyArchive: true
            publishHTML(target: [
                reportDir: 'playwright-report',
                reportFiles: 'index.html',
                reportName: 'Playwright Report',
                keepAll: true,
                alwaysLinkToLastBuild: true,
            ])
        }
        failure {
            echo 'Build failed - see the Playwright report and any auto-filed Jira defects above.'
        }
    }
}
