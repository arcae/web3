echo 'This is my' $Server
echo 'This is my gateway type' $gateway_service_type
echo 'This is my YAMLPath' $YAMLPath



echo 'Reading file inside GoodVeloxAPI dir' 
cat $YAMLPath/test.yaml


echo '+++++++++++Reading wsdl file in subdir+++++++++++++++++++++'
cat $WSDLPath/anotherfile.wsdl



