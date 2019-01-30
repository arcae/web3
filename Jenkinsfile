#! groovy

// Load shared pipeline library
//@Library('velox') _

properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '14', numToKeepStr: '32')),
    durabilityHint('PERFORMANCE_OPTIMIZED'),
    parameters([
        string(name: "Server", description: "The Ingress URL of the System under Test"),
        string(name: "YMLPath", defaultValue: "GoodVeloxAPIs", description: "Path to the YAML files"),
        string(name: "WSDLPath", defaultValue: "GoodVeloxAPIs/Soap_APIs", description: "Path to the WSDL files"),
        string(name: "Gateway Service", defaultValue: "datapower-gateway", description: "Gateway Type"),
        string(name: "GW_Endpoint", description: "The Ingress URL of the Gateway endpoint"),
        string(name: "GW_API_Endpoint", description: "The Ingress URL of the Gateway API endpoint"),
        string(name: "Portal_Endpoint", description: "The Ingress URL of the Portal endpoint"),
        string(name: "Portal_API_Endpoint", description: "The Ingress URL of the Portal API endpoint"),
        string(name: "Analytics_Endpoint", description: "The Ingress URL of the Analytics endpoint"),
        string(name: "Consumer_Endpoint", description: "The Ingress URL of the Consumer endpoint"),
        string(name: "APIC_Release", description: "Input release version"),
        string(name: "Build#", description: "Input build number"),
        string(name: "datapowerVersion", defaultValue: "latest", description: "The Datapower version to deploy (e.g. '2018.4.1.0') or 'latest'."),
        booleanParam(name: "datapowerV5Compat", defaultValue: false, description: "Use v5 compatibility in Datapower's API Connect Gateway Service."),
        string(name: "publicKey", defaultValue: "none", description: "Contents of your id_rsa.pub file (i.e. your public key, prefixed with key type). Required to SSH into the velox appliances.")

    ])
])


        stage('Build') {
                echo 'Building..'
        }


//sh "mkdir -p output"
//echo "Server=${params.Server}" >> UserInput
//echo "YMLPath=${params.YMLPath}" >> UserInput
//echo "WSDLPath=${params.WSDLPath}" >> UserInput





