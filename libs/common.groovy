

def run_test(){
    try {
        echo "The value of DEPLOY is deploy"
        sh 'sleep 300'
    } catch (error) {
        echo "Suite:  -- test failed"
        echo "${error}"
        cause = ""
        echo "This is in lib : {$error}"
        if (error.hasProperty('causes')) {
            echo "{$error}"
            cause = error.causes.get(0)
            echo "${cause}"
        } else {
            cause = "Runtime error"
        }
        throw new Exception ("$cause")
    } finally {
        echo "From Finally in lib method"
    }
}

return this;
