#! groovy

// Load shared pipeline library
//@Library('velox') _

properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '14', numToKeepStr: '32')),
    durabilityHint('PERFORMANCE_OPTIMIZED'),
    parameters([
        string(name: "Server", description: "The Ingress URL of the System under Test"),
        string(name: "YMLPath", defaultValue: "GoodVeloxAPIs", description: "Path to the YAML files")
    ])
])

environment{

	SERVER = ${params.Server}
}


node {
        stage('Build') {
                sh 'touch test.txt'
                echo 'Building..'
                echo "Server=${env.Server}"
                writeFile file: 'test.txt', text: "Server=${params.Server}"
                echo "Server=${params.Server}" 
                echo "YMLPath=${params.YMLPath}" 
                echo "WSDLPath=${params.WSDLPath}" 
                sh ./goldenpath.sh
        }
}


