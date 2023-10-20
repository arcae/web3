
node ('agent1') {

    stage ('Checkout repo'){

        echo "checkout repo"
        checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    userRemoteConfigs: [[url: 'https://github.com/arcae/web3.git']]
                ])


    }
    stage ('Test stage') {

        try {
            echo "Hello from web3"
        }
        catch (exception e) {
            echo 'Exception occurred: ' + e.toString()
            sh 'Handle the exception!'
        }


    }
}
