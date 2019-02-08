#! groovy

// Load shared pipeline library
//@Library('velox') _

properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '14', numToKeepStr: '32')),
    durabilityHint('PERFORMANCE_OPTIMIZED'),
    parameters([
        string(name: "Server", description: "Server type"),
        choice(name: "gateway_service_type", choices:['datapower-gateway','V6-gateway'],defaultValue:'datapower-gateway',description: "Type of gateway used"),
        choice(name: "YAMLPath", choices:["GoodVeloxAPI","V6VeloxAPI"], defaultValue: "GoodVeloxAPI", description: "Path to the YAML files"),
        booleanParam(name: "CMSetup", defaultValue:false, description: "Cloud manager setup needed"),
        choice(name: "WSDLPath", choices:["GoodVeloxAPI/SoapWSDL", "V6VeloxAPI/SoapWSDL"], defaultValue: "GoodVeloxAPI/SoapWSDL", description: "Path to WDSL file")
    ])
])

environment{
   Server = ${params.Server}
}

node {
      echo "Server env value is" env.Server
      echo "Server param value is " ${params.Server}
      try {
        // do something that fails
        if("${params.Server}" == null){
        echo "My server param is " ${params.Server}
    }
    } catch (ex) {
        echo "Result from inside catch block  ${currentBuild.result}"
        currentBuild.result = 'ABORTED'
        return
        
    }
    echo "RESULT outside try: ${currentBuild.result}"


        stage('Build') {

                git credentialsId: '8b721918-37dd-4695-931e-85dc9cf1a630', url: 'https://github.com/arcae/web3.git'
                //sh 'touch test.txt'
                echo 'Building..'
                //writeFile file: 'test.txt', text: "Server=${params.Server}"
                //writeFile file: 'test.txt', text: "YMLPath=${params.YMLPath}"
                //sh 'cat test.txt'
                //echo 'CMSetup value is' ${params.CMSetup}
                sh './goldenpath.sh'
        }
}


