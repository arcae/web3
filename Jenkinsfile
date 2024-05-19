import org.jenkinsci.plugins.pipeline.modeldefinition.Utils
import hudson.tasks.test.AbstractTestResultAction

def isFailed = false
def errMsg = ""

node ('agent1') {
    withCredentials([ usernameColonPassword(credentialsId: 'docker-job-cred', variable: 'jenkins') ])
    try {
        timeout(time:1, unit:'HOURS') {
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

                example.run_test()
                // sh 'scripts/testscript.sh'
                // sh 'sleep 300'
                
            }
            stage('Call gitlab job'){
                build 'gitlab-proj'
            }
            stage('Call docker param job'){
                // build job: 'docker', parameters: [string(name: 'PARAM1', value: 'No')]
                def jobUrl = "http://9.46.95.28:8080/job/docker"
                def PARAM1 = "No"
                triggerRemoteJob (job: jobUrl,
                    blockBuildUntilComplete: true,
                    pollInterval: 120,
                    shouldNotFailBuild: true,
                    parameters: "${PARAM1}\n",
                    auth: CredentialsAuth(credentials: 'docker-job-cred'))
                    

                // triggerRemoteJob job: 'http://9.46.95.28:8080/job/docker', parameters: StringParameters(parameters: 'PARAM1=\'No\''), useCrumbCache: true, useJobInfoCache: true
            }
            // stage('Deploy'){
            //     echo 'Sleeping for 60 sec in stage Deploy'
            //     sh 'sleep 10'
            // }
            // stage('Test'){
            //     catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE'){
            //     echo "This is stage Test"
            //     sh 'scripts/testscript.sh'
            //     }
            // }
            // stage('Returnstatus'){
            //     def retstatus = sh(returnStatus: true, script: 'scripts/testscript.sh')
            //     if (retstatus != 0) {
            //         echo "Error: Command exited with status ${retstatus}"
            //     } else {
            //         echo "Command executed successfully"
            //     }

            // }
            stage('Topo'){

                echo 'This is Topo stage'
            }

        }
    } catch(Exception e) {
        echo "Printing Error"
        unstable('Encountered errors in the run.......')
        cause = ""
        errstr = "$e"
        if (e.hasProperty('causes')) {
            cause = e.causes.get(0)
        } else if (errstr.contains('ExceededTimeout')){
            cause = "Timed out in pytest stage"
        } 
        else {
            cause = "Runtime error"
        }
        if (cause == "Runtime error") {
            errMsg = "Runtime error"
            // currentBuild.result = "FAILED"
        } else if (cause instanceof org.jenkinsci.plugins.workflow.steps.TimeoutStepExecution.ExceededTimeout) {
            errMsg = "Run timed out"
            // currentBuild.result = "UNSTABLE"
        } else if ( cause == "Timed out in pytest stage"){
            errMsg = "Timed out when running pytests"
            // currentBuild.result = "UNSTABLE"
        } 
        else {
            errMsg = "Build aborted by user"
            // currentBuild.result = "UNSTABLE"
        }
        echo errMsg
            
    }
}
