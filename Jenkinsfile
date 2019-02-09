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
        file(name: "hilo", description: "Path to hilo file"),
        choice(name: "WSDLPath", choices:["GoodVeloxAPI/SoapWSDL", "V6VeloxAPI/SoapWSDL"], defaultValue: "GoodVeloxAPI/SoapWSDL", description: "Path to WDSL file")
    ])
])

try {
        // do something that fails
        if (Server == null || Server == ""){ 
        currentBuild.result = 'ABORTED'
        echo "ABORTING build since parameters are missing"
        echo "Result inside try if cond: ${currentBuild.result}"
        return
    }
    } catch (Exception err) {
        currentBuild.result = 'FAILURE'
    }
    echo "RESULT outside try block: ${currentBuild.result}"



node {
        stage('Build') {
                echo " Workspace is $workspace"
                git credentialsId: '8b721918-37dd-4695-931e-85dc9cf1a630', url: 'https://github.com/arcae/web3.git'
                echo "The value of Server param is ${params.Server}"
                def filename = 'hilo.yaml'
                def data = readYaml file: filename
                
                data.cloud.name = "${params.Server}"
                data.cloud.topology.database_node_name = "Heeelleelle"
            
                sh "rm $filename"
                writeYaml file: filename, data: data
                 
                //sh 'touch test.txt'
                echo 'Building..'
                //writeFile file: 'test.txt', text: "Server=${params.Server}"
                //writeFile file: 'test.txt', text: "YMLPath=${params.YMLPath}"
                //sh 'cat test.txt'
                //echo 'CMSetup value is' ${params.CMSetup}
                sh './goldenpath.sh'
        }
}


