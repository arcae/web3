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



node {
        stage('Build') {

                git credentialsId: '8b721918-37dd-4695-931e-85dc9cf1a630', url: 'https://github.com/arcae/web3.git'
                sh 'touch test.txt'
                echo 'Building..'
                writeFile file: 'test.txt', text: "Server=${params.Server}"
                sh 'cat test.txt'
                sh './goldenpath.sh'
        }
}


