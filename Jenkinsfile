def isFailed = false
def errMsg = ""

node ('agent1') {
    try {
        timeout(time:1, unit:'MINUTES') {
            stage('sleep') {
                sh 'sleep 300'
            }
        }
    } catch(Exception e) {
        isFailed = true
        cause = ""

        if (e.hasProperty('causes')) {
            cause = e.causes.get(0)
        } else {
            cause = "Runtime error"
        }

        if (cause == "Runtime error") {
            errMsg = "Runtime error"
        } else if (cause instanceof org.jenkinsci.plugins.workflow.steps.TimeoutStepExecution.ExceededTimeout) {
            errMsg = "Build timed out"
        } else {
            errMsg = "Build aborted by user"
        }
        echo errMsg
    }

    stage('notify') {
        if (isFailed) {
            emailext body: errMsg, subject: "${currentBuild.fullDisplayName} - FAILED", to: env.NOTIFY_EMAIL

            slackSend channel: '#blah',
                color: 'danger',
                message: "Pipeline job ${currentBuild.fullDisplayName} failed: ${errMsg}"

            error(errMsg)
        }
    }
}
