pipeline {
    agent any

    environment {
        VELOX_YAML='/blah/home'
        OUTPUTFILES='/tmp/files'
     }
     
     parameters {
         choice(name: 'Choose Build',
           choices: '1234\n2345\n9876',
	   description: 'What is the Build number?')
         booleanParam(name: 'Should we cleanup?',
            defaultValue: true,
            description: 'Checkbox parameter')
         string(name: 'GW hostname',
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
                        echo 'blahhhhh'
                        echo $VELOX_YAML
                        echo $OUTPUTFILES
                '''
            }
 
        }
    }
}
