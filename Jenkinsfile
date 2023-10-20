import org.jenkinsci.plugins.pipeline.modeldefinition.Utils
import hudson.tasks.test.AbstractTestResultAction

def isFailed = false
def errMsg = ""

def commonlib = load('Libs/common.groovy')

node ('agent1') {
    try {
        timeout(time:1, unit:'MINUTES') {
            stage('sleep') {
                commonlib.run_test()
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
}
