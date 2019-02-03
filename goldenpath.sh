#!/bin/bash

echo 'This is my server:' $Server
echo 'This is my gateway type' $gateway_service_type
echo 'This is my YAMLPath' $YAMLPath
echo 'This is value of WSDLPath' $WSDLPath




if ([ $YAMLPath == "GoodVeloxAPI" ] && [$WSDLPath == "GoodVeloxAPI/SoapWSDL" ])
then
   echo 'Reading file inside GoodVeloxAPI dir' 
   cat $YAMLPath/test.yaml
   echo '+++++++++++Reading wsdl file in subdir+++++++++++++++++++++'
   cat $WSDLPath/anotherfile.wsdl
fi





