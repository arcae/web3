
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

            echo "Hello from web3"


    }
}
