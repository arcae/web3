

def run_test(){
    try {
        echo "The value of DEPLOY is deploy"
    } catch (error) {
        echo "Suite:  -- test failed"
        return error
    } finally {
        echo "From Finally in lib method"
        // junit '*.xml'
    }
}

return this;
