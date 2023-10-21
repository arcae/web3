import org.jenkinsci.plugins.pipeline.modeldefinition.Utils
import hudson.tasks.test.AbstractTestResultAction

def isFailed = false
def errMsg = ""

node ('agent1') {
    try {
        timeout(time:1, unit:'MINUTES') {
            stage('sleep') {
                // Git checkout before load source the file
                checkout scm
                // To know files are checked out or not
                sh '''
                    ls -lhrt
                '''
                def rootDir = pwd()
                println("Current Directory: " + rootDir)
                // point to exact source file
                def example = load "${rootDir}/libs/common.groovy"

                // example.run_test()
                sh 'sleep 300'
                
            }
        }
    } catch(Exception e) {
        isFailed = true
        cause = ""
        echo "This is in main Jenkinsfile: {$e}"
        if (e.hasProperty('causes')) {
            echo "{$e}"
            cause = e.causes.get(0)
            echo "${cause}"
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
