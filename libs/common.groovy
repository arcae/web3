

def run_test(){
    try {
        echo "The value of DEPLOY is deploy"
        sh 'exit 1'
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
        // throw new Exception ("$cause")
        throw
    } finally {
        echo "From Finally in lib method"
    }
}

return this;
