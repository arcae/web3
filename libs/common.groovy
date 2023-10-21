

def run_test(){
    try {
        echo "The value of DEPLOY is deploy"
        sh 'sleep 300'
    } catch (error) {
        echo "Suite:  -- test failed"
        echo "${error}"
        throw new Exception ('Hit timout exception')
    } finally {
        echo "From Finally in lib method"
    }
}

return this;
