#!/bin/bash

echo 'This is my server:' $Server
echo 'This is my gateway type' $gateway_service_type
echo 'This is my YAMLPath' $YAMLPath
echo 'This is value of WSDLPath' $WSDLPath
echo 'This is value of CMSetip' $CMSetup



CloudManager(){

  echo 'Inside CloudManager function'

}


if [ $YAMLPath == "GoodVeloxAPI" ]
then
   echo 'Reading file inside GoodVeloxAPI dir' 
   cat $YAMLPath/test.yaml
   echo '+++++++++++Reading wsdl file in GoodVelox  subdir+++++++++++++++++++++'
   cat $WSDLPath/anotherfile.wsdl
elif [ $YAMLPath == "V6VeloxAPI" ]
then
   echo 'Reading file inside V6Velox dir'
   cat $YAMLPath/another.yaml
   echo '********************** Reading wsdl file in V6Velox subdir***********'
   cat $WSDLPath/test.wsdl
else
   echo 'IF failed!!!'
fi

echo 'After first if statement'


if [ $CMSetup == "true" ]
then 
   echo 'CMSetup is true'
   CloudManager()
fi
