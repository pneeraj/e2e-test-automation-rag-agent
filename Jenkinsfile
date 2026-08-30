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

    parameters {
        choice(name: 'SUITE', choices: ['all', 'ui', 'api', 'mobile'], description: 'Which test suite to run')
        string(name: 'SAUCE_BASE_URL', defaultValue: 'https://www.saucedemo.com', description: 'UI target')
        string(name: 'BOOKING_API_BASE_URL', defaultValue: 'https://restful-booker.herokuapp.com', description: 'API target')
        booleanParam(name: 'RUN_TRIAGE', defaultValue: true, description: 'Run the RAG defect-triage agent on failures')
    }

    environment {
        CI = 'true'
        SAUCE_BASE_URL = "${params.SAUCE_BASE_URL}"
        BOOKING_API_BASE_URL = "${params.BOOKING_API_BASE_URL}"
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
            when { expression { params.SUITE in ['all', 'ui'] } }
            steps { bat 'py ci\\run_tests.py --suite ui' }
        }
        stage('API tests') {
            when { expression { params.SUITE in ['all', 'api'] } }
            steps { bat 'py ci\\run_tests.py --suite api' }
        }
        stage('Mobile tests') {
            when { expression { params.SUITE in ['all', 'mobile'] } }
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
                allOf {
                    expression { params.RUN_TRIAGE }
                    expression { fileExists('test-results/failures.json') }
                }
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
