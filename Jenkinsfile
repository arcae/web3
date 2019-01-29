pipeline {
    agent any

    environment {
        VELOX_YAML='/blah/home'
        OUTPUTFILES='/tmp/files'
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
