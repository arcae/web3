#! groovy

// Load shared pipeline library
//@Library('velox') _

properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '14', numToKeepStr: '32')),
    durabilityHint('PERFORMANCE_OPTIMIZED'),
    parameters([
        string(name: "Server", defaultValue: "myserver",description: "Server type"),
        choice(name: "gateway_service_type", choices:['datapower-gateway','V6-gateway'],defaultValue:'datapower-gateway',description: "Type of gateway used"),
        choice(name: "YAMLPath", choices:["GoodVeloxAPI","V6VeloxAPI"], defaultValue: "GoodVeloxAPI", description: "Path to the YAML files"),
        string(name: "WSDLPath", choices:["GoodVeloxAPI/SoapWSDL", "V6VeloxAPI/SoapWSDL"], defaultValue: "GoodVeloxAPI/SoapWSDL", description: "Path to WDSL file")
    ])
])



node {
        stage('Build') {

                git credentialsId: '8b721918-37dd-4695-931e-85dc9cf1a630', url: 'https://github.com/arcae/web3.git'
                //sh 'touch test.txt'
                //echo 'Building..'
                //writeFile file: 'test.txt', text: "Server=${params.Server}"
                //writeFile file: 'test.txt', text: "YMLPath=${params.YMLPath}"
                //sh 'cat test.txt'
                sh './goldenpath.sh'
        }
}


