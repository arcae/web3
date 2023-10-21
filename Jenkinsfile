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
            stage('Deploy'){
                echo 'Sleeping for 60 sec in stage Deploy'
                sh 'sleep 60'
            }
            stage('Test'){
                echo "This is stage Test"
            }
        }
    } catch(Exception e) {
        echo "Printing Error"
            cause = ""
            errstr = "$e"
            if (e.hasProperty('causes')) {
                cause = e.causes.get(0)
            } else if (errstr.contains('ExceededTimeout')){
                cause = "Build Timed out in pytest stage"
            } 
            else {
                cause = "Runtime error"
            }
            if (cause == "Runtime error") {
                errMsg = "Runtime error"
            } else if (cause instanceof org.jenkinsci.plugins.workflow.steps.TimeoutStepExecution.ExceededTimeout) {
                errMsg = "Build timed out"
            } else if ( cause == "Build Timed out in pytest stage"){
                errMsg = "Build Timed out when running pytests"
            } 
            else {
                errMsg = "Build aborted by user"
            }
            echo errMsg
            currentBuild.result = "UNSTABLE"
    }
}
