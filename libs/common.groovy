

def run_test(){
    try {
        echo "The value of DEPLOY is deploy"
        sh 'sleep 300'
    } catch (error) {
        echo "Suite:  -- test failed"
        echo "${error}"
    } finally {
        echo "From Finally in lib method"
        // junit '*.xml'
    }
}

return this;
