// Jenkins declarative pipeline (alternative to GitHub Actions).
// Plugins: Pipeline, Docker Pipeline, JUnit, HTML Publisher, (optional) Allure Jenkins Plugin.
// Credentials: "Username with password" id 'orangehrm-credentials'
//              (optional) "Secret text" id 'reqres-api-key'
pipeline {
    agent {
        docker {
            // Keep this tag equal to the playwright version in requirements.txt
            image 'mcr.microsoft.com/playwright/python:v1.63.0-noble'
            args '--ipc=host'
        }
    }

    parameters {
        choice(name: 'SUITE', choices: ['all', 'api', 'ui-hybrid'], description: 'Suites to run')
        string(name: 'BROWSERS', defaultValue: 'chromium firefox', description: 'Browsers for UI tests (space separated)')
        choice(name: 'WORKERS', choices: ['2', '1', '4', 'auto'], description: 'Parallel workers (pytest-xdist)')
        choice(name: 'DATA_SOURCE', choices: ['json', 'csv'], description: 'Employee test data source')
    }

    triggers { cron('H 2 * * *') }

    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        ORANGEHRM = credentials('orangehrm-credentials')
        ORANGEHRM_USERNAME = "${ORANGEHRM_USR}"
        ORANGEHRM_PASSWORD = "${ORANGEHRM_PSW}"
        DATA_SOURCE = "${params.DATA_SOURCE}"
        HOME = "${WORKSPACE}"
    }

    stages {
        stage('Install') {
            steps {
                sh 'python -m pip install --user -r requirements.txt'
            }
        }
        stage('API tests') {
            when { expression { params.SUITE in ['all', 'api'] } }
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''python -m pytest -m api --reruns 1 \
                          --html=reports/html/api-report.html \
                          --junitxml=reports/junit/api-results.xml \
                          --alluredir=reports/allure-results-api'''
                }
            }
        }
        stage('UI + Hybrid tests') {
            when { expression { params.SUITE in ['all', 'ui-hybrid'] } }
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''BROWSER_ARGS=""; for b in $BROWSERS; do BROWSER_ARGS="$BROWSER_ARGS --browser $b"; done
                          python -m pytest -m "ui or hybrid" $BROWSER_ARGS -n "$WORKERS" --reruns 1 \
                          --html=reports/html/ui-hybrid-report.html \
                          --junitxml=reports/junit/ui-hybrid-results.xml \
                          --alluredir=reports/allure-results-ui'''
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit/*.xml'
            publishHTML(target: [
                reportDir: 'reports/html', reportFiles: 'api-report.html,ui-hybrid-report.html',
                reportName: 'Automation HTML Reports', keepAll: true,
                alwaysLinkToLastBuild: true, allowMissing: true
            ])
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
    }
}
