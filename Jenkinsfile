pipeline {
    agent any

    environment {
        VELOX_YAML='/blah/home'
        OUTPUTFILES='/tmp/files'
     }
     
     parameters {
         choice(name: 'Choose_Build',
           choices: '1234\n2345\n9876',
	   description: 'What is the Build number?')
         booleanParam(name: 'Should_we_cleanup?',
            defaultValue: true,
            description: 'Checkbox parameter')
         string(name: 'GW_hostname',
             defaultValue: 'Blah GW.com',
             description: 'What is the GW hostname')
     }

    stages {
        stage('Build') {
            steps {
                echo 'Building..'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
            }
        }
        stage('Deploy') {
            steps {
                sh '''#!/bin/bash
                     sh script.sh
                   '''
                        echo 'blahhhhh'
                        echo $VELOX_YAML
                        echo $OUTPUTFILES
                        echo "The Build number is: ${params.Choose_Build}"
                        echo "The Should we clean is: ${params.Should_we_cleanup}"
			echo "The GW hostname is: ${params.GW_hostname}"
                
            }
 
        }
    }
}
