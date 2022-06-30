# IBM Confidential
# OCO Source Materials
#
# (C) Copyright IBM Corporation 2021
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office.

import subprocess
import sys
import time
import argparse
import os
import shutil
import yaml

oc_client = "oc"
kubectl_client = "kubectl"
client = oc_client

pwd = None
DATA_DIR = None
DATA_TEMP_DIR = None

CONFIG_FILE_NAME = "config.yaml"
CONFIG_PORTAL_FILE_NAME = "config_portal.yaml"
config =  None
config_portal =  None
mgmtSubsystemDetails = None
portalSubsystemDetails = None

ocpVersion = None

mgmtCustomApplicationSecrets = ["atm-cred", "ccli-cred", "cui-cred", "dsgr-cred", "juhu-cred", "cli-cred", "ui-cred"]


EUS_CP4I_CHANNEL = "v1.1-eus"
EUS_CP4I_VERSION = "2020.4.1-eus"
EUS_PN_CHANNEL = "v4.1-eus"
EUS_APIC_CHANNEL = "v2.1.5-eus"  # check for correct values before GA
EUS_APIC_VERSION = "10.0.1.5-eus" # check for correct values before GA
EUS_APIC_PROFILES = ["n3xc4.m16", "n12xc4.m12"]

#keep changing this value based on the release
eusRelease = False

CD_CP4I_CHANNEL = "v1.5" # check for correct values before GA
CD_CP4I_VERSION = "2021.4.1" # check for correct values before GA
CD_PN_CHANNEL = "v5.2" # check for correct values before GA
CD_APIC_CHANNEL = "v2.5" # check for correct values before GA
CD_APIC_VERSION = "10.0.4.0-ifix2" # check for correct values before GA
CD_APIC_PROFILES = ["n1xc7.m48", "n1xc10.m48", "n3xc11.m48", "n3xc14.m48"]

cp4iChannel = CD_CP4I_CHANNEL
cp4iVersion = CD_CP4I_VERSION
apicChannel = CD_APIC_CHANNEL
apicVersion = CD_APIC_VERSION
platformNavigatorChannel = CD_PN_CHANNEL
profiles = CD_APIC_PROFILES

if eusRelease:
    cp4iChannel = EUS_CP4I_CHANNEL
    cp4iVersion = EUS_CP4I_VERSION
    apicChannel = EUS_APIC_CHANNEL
    apicVersion = EUS_APIC_VERSION
    platformNavigatorChannel = EUS_PN_CHANNEL
    profiles = EUS_APIC_PROFILES

EUS_OCP_VERSION = "4.6"


#common services for lts/eus
opencloud_operators_catsrc = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "opencloud-operators",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "IBMCS Operators",
    "image": "icr.io/cpopen/ibm-common-service-catalog:latest",
    "publisher": "IBM",
    "sourceType": "grpc",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

#used for cp4i as per kc docs, both same
ibmOperatorCatalog1 = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "ibm-operator-catalog",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "IBM Operator Catalog",
    "image": "icr.io/cpopen/ibm-operator-catalog:latest",
    "publisher": "IBM",
    "sourceType": "grpc",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

#used for ocp as per kc docs, both same
ibmOperatorCatalog2 = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "ibm-operator-catalog",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "IBM Operator Catalog",
    "publisher": "IBM",
    "sourceType": "grpc",
    "image": "icr.io/cpopen/ibm-operator-catalog",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

operator_group = {
  "apiVersion": "operators.coreos.com/v1",
  "kind": "OperatorGroup",
  "metadata": {
    "name": "apic-operator-group",
    "namespace": "TBD"
  },
  "spec": {
    "targetNamespaces": []
  }
}

apiconnect_subscribe = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "Subscription",
  "metadata": {
    "name": "ibm-apiconnect",
    "namespace": "TBD"
  },
  "spec": {
    "channel": apicChannel,
    "installPlanApproval": "Automatic",
    "name": "ibm-apiconnect",
    "source": "ibm-operator-catalog",
    "sourceNamespace": "openshift-marketplace"
  }
}

#platform navigator catalog source
pn_catalog_source_dailybuild = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "platform-nav",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "platform-nav",
    "publisher": "internal",
    "sourceType": "grpc",
    "image": "cp.stg.icr.io/cp/ibm-integration-platform-navigator-catalog:latest",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

#ibm automation foundation core catalog source, needed by PN
iaf_core_catalog_source_dailybuild = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "iaf-core-operators",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "IAF Core Operators",
    "image": "cp.stg.icr.io/cp/ibm-automation-foundation-core-catalog:latest-validated",
    "publisher": "IBM",
    "sourceType": "grpc",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

pn_subscribe = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "Subscription",
  "metadata": {
    "name": "ibm-integration-platform-navigator",
    "namespace": "TBD"
  },
  "spec": {
    "channel": platformNavigatorChannel,
    "installPlanApproval": "Automatic",
    "name": "ibm-integration-platform-navigator",
    "source": "ibm-operator-catalog",
    "sourceNamespace": "openshift-marketplace"
  }
}


topLevelCR = {
  "apiVersion": "apiconnect.ibm.com/v1beta1",
  "kind": "APIConnectCluster",
  "metadata": {
    "name": "minimum",
    "labels": {
      "app.kubernetes.io/instance": "apiconnect",
      "app.kubernetes.io/managed-by": "ibm-apiconnect",
      "app.kubernetes.io/name": "apiconnect-minimum"
    },
    "namespace": "TBD"
  },
  "spec": {
    "license": {
      "accept": True,
      "use": "nonproduction"
    },
    "storageClassName": "TBD",
    "profile": "TBD",
    "version": "TBD",
    "management": {
      "name": "TBD",
      "originalUID": "TBD",
      "customApplicationCredentials": [],
      "siteName": "TBD",
      "encryptionSecret": {},
      "databaseBackup": {}
    },
    "analytics": {
      "storage": {
        "enabled": True,
        "type": "unique"
      }
    },
    "portal": {
      "name": "tbd",
      "originalUID": "TBD",
      "encryptionSecret": {},
      "portalBackup": {},
      "siteName": "TBD"
    }
  }
}

apiconnect_catalog_source = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "ibm-apiconnect-catalog",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "IBM APIConnect catalog",
    "image": "icr.io/cpopen/ibm-apiconnect-catalog:latest",
    "publisher": "IBM",
    "sourceType": "grpc",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

datapower_catalog_source = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "ibm-datapower-operator-catalog",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "DataPower Operator",
    "publisher": "IBM Content",
    "sourceType": "grpc",
    "image": "icr.io/cpopen/datapower-operator-catalog:latest",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

wmltraining_catalog_source = {
  "apiVersion": "operators.coreos.com/v1alpha1",
  "kind": "CatalogSource",
  "metadata": {
    "name": "ibm-ai-wmltraining-catalog",
    "namespace": "openshift-marketplace"
  },
  "spec": {
    "displayName": "ibm-ai-wmltraining-catalog",
    "publisher": "IBM",
    "sourceType": "grpc",
    "image": "icr.io/cpopen/ibm-ai-wmltraining-operator-catalog@sha256:4e88b9f2df60be6af156d188657763dfa4cbe074c40ea85ba82858796e3cd6a3",
    "updateStrategy": {
      "registryPoll": {
        "interval": "45m"
      }
    }
  }
}

pn_instance_yaml = {
  "apiVersion": "integration.ibm.com/v1beta1",
  "kind": "PlatformNavigator",
  "metadata": {
    "name": "integration-navigator",
    "namespace": "TBD"
  },
  "spec": {
    "license": {
      "accept": True,
      "license": "TBD"
    },
    "mqDashboard": True,
    "version": cp4iVersion,
    "storage": {
      "class": "TBD"
    },
    "replicas": 1
  }
}


# runKubernetesCommand
def runKubernetesCommand(command, kubernetesNamespace, silent=False, retry=10, exitOnError=True):
    global client
    fullCommand = None
    
    if kubernetesNamespace == None:
        fullCommand = client + " " + command
    else:
        fullCommand = client + " -n " + kubernetesNamespace + " " + command 
    
    if not silent:
        print ("Kubernetes command : ", fullCommand)
        
    count = 0
    out = None
    err = None
    flag = True
    while flag:
        returnObject = subprocess.Popen(fullCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
        out, err = returnObject.communicate()        
    
        if (command == "version") and (returnObject.returncode != 0):
            print ("Failed to run kubernetes command [{c1}], error code {r1} and error message is [{e1}]".format(c1=fullCommand, r1=returnObject.returncode, e1=err))
            if kubernetesNamespace == None:
                fullCommand = kubectl_client + " " + command
            else:
                fullCommand = kubectl_client + " -n " + kubernetesNamespace + " " + command
            print ("Trying with kubectl and Command is : ", fullCommand)
            returnObject = subprocess.Popen(fullCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
            out, err = returnObject.communicate()
            client = kubectl_client

        if returnObject.returncode == 0:
            flag = False
        else:
            if count < retry:
                count = count + 1
                time.sleep(15)
                print ("Retrying count {}. Command({}) failed with return code {} and error message : {}".format(count, fullCommand, returnObject.returncode, err))
            else:
                if exitOnError == True:
                    sys.exit("ERROR : Failed to run the kubernetes command, [{}], return code {} and error is [{}].  Exiting...".format(fullCommand, returnObject.returncode, err)) 
                else:
                    flag = False  
    if not silent:
        print (out)
    return out

    
def runCommand(command, silent=False, retry=10, exitOnError=True):
    obfuscatedCommand = None
    if "--password" in command or "--apiKey" in command:
        if "--password" in command: obfuscatedCommand = command[0:command.index("--password")] + "--password ********"
        if "--apiKey" in command: obfuscatedCommand = command[0:command.index("--apiKey")] + "--apiKey ********"
    else:
        obfuscatedCommand = command

    print ("Command : ", obfuscatedCommand)
    
    count = 0
    out = None
    err = None
    flag = True
    while flag:
        returnObject = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
        out, err = returnObject.communicate()
    
        if returnObject.returncode == 0:
            flag = False
        else:
            if count < retry:
                count = count + 1
                time.sleep(15)
                print ("Retrying count {}. Command({}) failed with return code {} and error message : {}".format(count, obfuscatedCommand, returnObject.returncode, err))
            else:
                if exitOnError == True:
                    sys.exit("ERROR : Failed to run the command, [{}], return code {} and error is [{}].  Exiting...".format(obfuscatedCommand, returnObject.returncode, err)) 
                else:
                    out = err
                    flag = False  
    if not silent:
        print (out)
        print ()
    return out

#health check for portal and gateway of the target apic system
def healthCheck(subsystem, ns):
    global targetSystemSpecVersion
    global targetSystemReconciledVersion
    if ns != None:
        out = runKubernetesCommand("get " + subsystem, ns)
        outList = out.splitlines()
        k = 0
        for each in outList:
            if k == 0:
                k = k + 1
                #skip header
                continue 
            subsystemName = each[0:each.index(" ")]
            print(subsystem + " subsystem name ::: " + subsystemName)
            crData = runKubernetesCommand("get " + subsystem + " " + subsystemName + " -o yaml", ns, True)
            crData = yaml.safe_load(crData)
            
            if subsystem == "mgmt":
                targetSystemSpecVersion = crData["spec"]["version"]
                targetSystemReconciledVersion = crData["status"]["versions"]["reconciled"]
            
            # check health
            print ("Phase : {} and state : {} for {} subsystem, {}".format(crData["status"]["phase"], crData["status"]["state"], subsystem, subsystemName))
            if not args.ignore_health_check:
                state = crData["status"]["state"]
                if crData["status"]["phase"] != "Running" or state[0:state.index("/")] != state[state.index("/") + 1:]:
                    sys.exit("ERROR : Health check failed for {} subsystem with name {}. Phase : {} and state : {}".format(subsystem, subsystemName, crData["status"]["phase"], crData["status"]["state"]))
                print ("ACTION OUTPUT : {} with name {} is healthy".format(subsystem, subsystemName))
            print ()
    else:
        print ("ACTION OUTPUT : Skipping health check for {} subsytem as namespace is NOT provided in the input. Given namespace is {}".format(subsystem, ns))


def waitForResourceCreation(command1, namespace1, resourceName, resourceType):
    flag = True
    loopCount = 0
    timeout = False
    while flag:
        loopCount = loopCount + 1
        if loopCount >= 30:
            flag = False
            print ("Timeout after Waiting for creation of resource, " + resourceName + " of type " + resourceType)
            timeout = True
            break # safe break after 10 min
        response1 = runKubernetesCommand(command1, namespace1, True, 0, False)
        if response1 != None and response1 != "" and response1.lower().startswith("error") == False:
            response1 = response1.splitlines()
            for r1 in response1:
                if r1.startswith(resourceName):
                    flag = False
                    break

        if flag == True:
            print ("Waiting for creation of resource, " + resourceName + " of type " + resourceType)
            time.sleep(30)
        else:
            break
    
    if timeout == True:
        sys.exit("Try again. Timed out waiting for creation of resource, " + resourceName + " of type " + resourceType)


def installCatalogSourcesAndSubscribe():
    print ("Check and install catalog sources::")

    #common-services
    catalogsources = runKubernetesCommand("get catalogsource", "openshift-marketplace", False)
    catalogsources = catalogsources.splitlines()
    catalogsourcesList = []
    for eachCatSrc in catalogsources:
        catalogsourcesList.append(eachCatSrc[0:eachCatSrc.index(" ")])

    if eusRelease or args.custom_build:
        if "opencloud-operators" in catalogsourcesList:
            print("ACTION OUTPUT : common services catalog source already installed.")
            print()
        else:
            common_services_fileName = DATA_TEMP_DIR + "/catsrc_common_services.yaml"
            with open(common_services_fileName, 'w') as commonServicesFile:
                yaml.dump(opencloud_operators_catsrc, commonServicesFile, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("create -f " + common_services_fileName, "openshift-marketplace", False)
                waitForResourceCreation("get catalogsource", "openshift-marketplace", "opencloud-operators", "catalog source")
                print("ACTION OUTPUT : Created common services catalog source")
                time.sleep(30)
            else:
                print("no_install flag is set to true. Not installing common-services catalog source.")
                print("ACTION OUTPUT : Location of common-services catalog source file : ", common_services_fileName)
                print()
        
        if args.no_install == False:
            runKubernetesCommand("get packagemanifests | grep common-service", "openshift-marketplace", False, 10)
        print()
    
    #ibm operator catalog
    if args.custom_build == False:
        if "ibm-operator-catalog" in catalogsourcesList:
            print("ibm-operator-catalog catalog source already installed.")
        else:
            #both same, one uses icr and another docker as per kc docs.
            if args.cp4i:
                ibmOperatorCatSrcFileName = DATA_TEMP_DIR + "/catsrc_ibm_operator_catalog.yaml"
                with open(ibmOperatorCatSrcFileName, 'w') as file1:
                    yaml.dump(ibmOperatorCatalog1, file1, default_flow_style=False)
                if args.no_install == False:
                    runKubernetesCommand("create -f " +ibmOperatorCatSrcFileName, "openshift-marketplace", False)
                    waitForResourceCreation("get catalogsource", "openshift-marketplace", "ibm-operator-catalog", "catalog source")
                    print("ACTION OUTPUT : Created ibm-operator-catalog catalog source")
                else:
                    print("no_install flag is set to true. Not installing ibm-operator-catalog catalog source.")
                    print("ACTION OUTPUT : Location of ibm-operator-catalog catalog source file : ", ibmOperatorCatSrcFileName)
                    print()
            else:
                ibmOperatorCatSrcFileName = DATA_TEMP_DIR + "/catsrc_ibm_operator_catalog.yaml"
                with open(ibmOperatorCatSrcFileName, 'w') as file2:
                    yaml.dump(ibmOperatorCatalog2, file2, default_flow_style=False)
                if args.no_install == False:
                    runKubernetesCommand("create -f " + ibmOperatorCatSrcFileName, "openshift-marketplace", False)
                    waitForResourceCreation("get catalogsource", "openshift-marketplace", "ibm-operator-catalog", "catalog source")
                    print("ACTION OUTPUT : Created ibm-operator-catalog catalog source")
                else:
                    print("no_install flag is set to true. Not installing ibm-operator-catalog catalog source.")
                    print("ACTION OUTPUT : Location of ibm-operator-catalog catalog source file : ", ibmOperatorCatSrcFileName)
                    print()
        
        if args.no_install == False:
            runKubernetesCommand("get packagemanifests | grep apiconnect", "openshift-marketplace", False)
            runKubernetesCommand("get packagemanifests | grep datapower", "openshift-marketplace", False)
    else:
        #custom build
        #apiconnect catalog source
        if args.apic_catsrc_image == None or args.apic_catsrc_image == "":
            print ("Time when error occurred :", time.asctime())
            sys.exit("Custom build apiconnect catalog source image value not provided. Exiting. Use the flag -apic_catsrc_image to provide it")

        if "ibm-apiconnect-catalog" in catalogsourcesList:
            print("ibm-apiconnect-catalog catalog source already installed. checking if the image matches..")
            res1 = runKubernetesCommand("get catalogsource ibm-apiconnect-catalog -o yaml", "openshift-marketplace", True)
            res1 = yaml.safe_load(res1)
            if res1["spec"]["image"] == args.apic_catsrc_image:
                print("ACTION OUTPUT : Installed ibm-apiconnect-catalog catalog source image value matches the input image value. Proceeding further")
            else:
                print ("Time when error occurred :", time.asctime())
                sys.exit("Installed ibm-apiconnect-catalog catalog source image value({}) does NOT match the input image value({}). Delete the ibm-apiconnect-catalog catalog source and try again.".format(res1["spec"]["image"] , args.apic_catsrc_image))
        else:
            apiconnect_catalog_source["spec"]["image"] = args.apic_catsrc_image
            apiConnectCatSrcFileName = DATA_TEMP_DIR + "/catsrc_apic_connect_catalog.yaml"
            with open(apiConnectCatSrcFileName, 'w') as file2:
                yaml.dump(apiconnect_catalog_source, file2, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("create -f " + apiConnectCatSrcFileName, "openshift-marketplace", False)
                waitForResourceCreation("get catalogsource", "openshift-marketplace", "ibm-apiconnect-catalog", "catalog source")
                print("ACTION OUTPUT : Created ibm-apiconnect-catalog catalog source using custom image : ", args.apic_catsrc_image)
            else:
                print("no_install flag is set to true. Not installing ibm-apiconnect-catalog catalog source.")
                print("ACTION OUTPUT : Location of ibm-apiconnect-catalog catalog source file : ", apiConnectCatSrcFileName)
        print()
        
        #datapower catalog source
        if args.dp_catsrc_image == None or args.dp_catsrc_image == "":
            print ("Time when error occurred :", time.asctime())
            sys.exit("Custom build datapower catalog source image value not provided. Exiting. Use the flag -dp_catsrc_image to provide it")

        if "ibm-datapower-operator-catalog" in catalogsourcesList:
            print("ibm-datapower-operator-catalog catalog source already installed. checking if the image matches..")
            res1 = runKubernetesCommand("get catalogsource ibm-datapower-operator-catalog -o yaml", "openshift-marketplace", True)
            res1 = yaml.safe_load(res1)
            if res1["spec"]["image"] == args.dp_catsrc_image:
                print("ACTION OUTPUT : Installed ibm-datapower-operator-catalog catalog source image value matches the input image value. Proceeding further")
            else:
                print ("Time when error occurred :", time.asctime())
                sys.exit("Installed ibm-datapower-operator-catalog catalog source image value({}) does NOT match the input image value({}). Delete the ibm-datapower-operator-catalog catalog source and try again".format(res1["spec"]["image"] , args.apic_catsrc_image))
        else:
            datapower_catalog_source["spec"]["image"] = args.dp_catsrc_image
            dpConnectCatSrcFileName = DATA_TEMP_DIR + "/catsrc_datapower_catalog.yaml"
            with open(dpConnectCatSrcFileName, 'w') as file2:
                yaml.dump(datapower_catalog_source, file2, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("create -f " + dpConnectCatSrcFileName, "openshift-marketplace", False)
                waitForResourceCreation("get catalogsource", "openshift-marketplace", "ibm-datapower-operator-catalog", "catalog source")
                print("ACTION OUTPUT : Created ibm-datapower-operator-catalog catalog source using custom image : ", args.dp_catsrc_image)
            else:
                print("no_install flag is set to true. Not installing ibm-datapower-operator-catalog catalog source.")
                print("ACTION OUTPUT : Location of ibm-datapower-operator-catalog catalog source file : ", dpConnectCatSrcFileName)
        print()
        
        if eusRelease == False:
            wmlTrainingConnectCatSrcFileName = DATA_TEMP_DIR + "/catsrc_wmltraining_catalog.yaml"
            with open(wmlTrainingConnectCatSrcFileName, 'w') as file2:
                yaml.dump(wmltraining_catalog_source, file2, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("apply -f " + wmlTrainingConnectCatSrcFileName, "openshift-marketplace", False)
                time.sleep(30)
                print("ACTION OUTPUT : wmltraining catalog source created/applied.")
            else:
                print("no_install flag is set to true. Not installing wmltraining catalog source.")
                print("ACTION OUTPUT : Location of wmltraining catalog source file : ", wmlTrainingConnectCatSrcFileName)
            print()
    
    namespace = None
    if args.operator_in_specific_namespace:
        namespace = args.ns
    else:
        namespace = "openshift-operators"
    
    if args.cp4i and args.custom_build:
        # for PN : iaf-core-operators catalog source
        if "iaf-core-operators" in catalogsourcesList:
            print("ACTION OUTPUT : iaf-core-operators (IBM Automation Foundation Core Operators) catalog source already installed. Proceeding further.")
        else:
            iafCoreCatSrcFileName = DATA_TEMP_DIR + "/catsrc_iaf_core_operators.yaml"
            with open(iafCoreCatSrcFileName, 'w') as file1:
                yaml.dump(iaf_core_catalog_source_dailybuild, file1, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("create -f " +iafCoreCatSrcFileName, "openshift-marketplace", False)
                waitForResourceCreation("get catalogsource", "openshift-marketplace", "iaf-core-operators", "catalog source")
                print("ACTION OUTPUT : Created iaf-core-operators (IAF Core Operators) catalog source needed for Platform Navigator.")
            else:
                print("no_install flag is set to true. Not installing iaf-core-operators catalog source.")
                print("ACTION OUTPUT : Location of iaf-core-operators catalog source file : ", iafCoreCatSrcFileName)
                print()

        # PN catalog source
        if "platform-nav" in catalogsourcesList:
            print("ACTION OUTPUT : platform-nav catalog source already installed. Proceeding further.")
        else:
            pnCatSrcFileName = DATA_TEMP_DIR + "/catsrc_platform_nav.yaml"
            with open(pnCatSrcFileName, 'w') as file1:
                yaml.dump(pn_catalog_source_dailybuild, file1, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("create -f " +pnCatSrcFileName, "openshift-marketplace", False)
                waitForResourceCreation("get catalogsource", "openshift-marketplace", "platform-nav", "catalog source")
                print("ACTION OUTPUT : Created platform-nav catalog source needed for Platform Navigator.")
            else:
                print("no_install flag is set to true. Not installing platform-nav catalog source.")
                print("ACTION OUTPUT : Location of platform-nav catalog source file : ", pnCatSrcFileName)
                print()

    #platform navigator subscription
    if args.cp4i:
        #check if platform navigator subscription exists
        #namespace will be same as what apic is subscribed to.
        subscriptions = runKubernetesCommand("get subscription", namespace, False)
        subscriptions = subscriptions.splitlines()
        subscriptionExists = False
        for eachSubscription in subscriptions:
            if "ibm-integration-platform-navigator" in eachSubscription:
                pnSubscriptionName = eachSubscription[0:eachSubscription.index(" ")]
                pnSubscription = runKubernetesCommand("get subscription " + pnSubscriptionName + " -o yaml", namespace, True)
                pnSubscription = yaml.safe_load(pnSubscription)
                channel = pnSubscription["spec"]["channel"]
                if channel == platformNavigatorChannel:
                    subscriptionExists = True
                    print("ACTION OUTPUT : Platform navigator already subscribed for channel number, " + platformNavigatorChannel + " Not installing again. Proceeding further.")
                    print()
                else:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("Platform navigator already subscribed for different channel number, " + channel + " Uninstall it and try again. This script uses PN channel " + platformNavigatorChannel)

        if subscriptionExists == False:
            if args.custom_build:
                pn_subscribe["spec"]["source"] = "platform-nav"

            pn_subscribe["metadata"]["namespace"] = namespace
            subscribe_pn_FileName = DATA_TEMP_DIR + "/subscription_pn.yaml"
            with open(subscribe_pn_FileName, 'w') as file2:
                yaml.dump(pn_subscribe, file2, default_flow_style=False)
            if args.no_install == False:
                runKubernetesCommand("create -f " + subscribe_pn_FileName, namespace, False)
                time.sleep(120)
                print("ACTION OUTPUT : Created subscription for platform navigator.")
            else:
                print("no_install flag is set to true. Not installing platform navigator.")
                print("ACTION OUTPUT : Location of platform navigator subscription file : ", subscribe_pn_FileName)
                print()
        
        # check if PN subscription is created
        if args.no_install == False:
            flag = True
            loopCount = 0
            timeout = False
            pnSubscribed = False
            while flag:
                loopCount = loopCount + 1
                if loopCount >= 60:
                    flag = False
                    print ("Timeout after waiting for platform navigator subscription. Current time : ", time.asctime())
                    timeout = True
                    break # safe break after 1 hr
                if pnSubscribed == False:
                    res1 = runKubernetesCommand("get subscription ibm-integration-platform-navigator -o yaml", namespace, True, 0, False)
                    if res1 != None and res1 != "" and res1.lower().startswith("error") == False:
                        res1 = yaml.safe_load(res1)
                        if "status" in res1 and "conditions" in res1["status"]:
                            conditions = res1["status"]["conditions"]
                            for eachCondition in conditions:
                                if eachCondition["type"] == "CatalogSourcesUnhealthy" and eachCondition["status"] == "False":
                                    print("ACTION OUTPUT : Platform navigator is subscribed and ready.")
                                    pnSubscribed = True

                if pnSubscribed:
                    flag = False
                else:
                    print ("Waiting for platform navigator subscription to be ready. Current time : ", time.asctime())
                    time.sleep(60)
            
            if timeout:
                print ("Time when error occurred :", time.asctime())
                sys.exit("ERROR : Timedout waiting for platform navigator subscription in namespace, {}. Manually check the status of PN subscription and try again.")
            
        pnInstanceName = None
        pnInstanceExists = False
        pn_instances = None
        count5 = 0
        while True:
            count5 = count5 + 1
            if count5 > 60: 
                sys.exit("Platform navigator and dependencies not ready. Timed out after 1 hour.")

            pn_instances = runKubernetesCommand("get platformnavigator", args.ns, False, 0, False)
            if pn_instances != None and pn_instances != "" and (pn_instances.lower().startswith("error") or "no matches for kind" in pn_instances.lower() or "error" in pn_instances.lower()):
                print("Waiting for platform navigator and its dependencies to be ready..", time.asctime())
                time.sleep(60)
            else:
                break
        
        # create instance of PN
        #check if platform navigator instance exists
        #namespace will be same as what apic is will be installed.
        if pn_instances != None and pn_instances != "":
            pn_instances = pn_instances.splitlines()
            for eachPNInstance in pn_instances:
                if eachPNInstance.startswith("NAME"): continue
                pnInstanceName = eachPNInstance[0:eachPNInstance.index(" ")]
                pnInstance = runKubernetesCommand("get platformnavigator " + pnInstanceName + " -o yaml", args.ns)
                if pnInstance != None and pnInstance != "" and pnInstance.lower().startswith("error") == False:
                    pnInstance = yaml.safe_load(pnInstance)
                    if "spec" in pnInstance and "version" in pnInstance["spec"]:
                        version = pnInstance["spec"]["version"]
                        if version == cp4iVersion:
                            pnInstanceExists = True
                            print("ACTION OUTPUT : Platform navigator instance already exists for version, " + cp4iVersion + " Not installing again. Proceeding further.")
                            print()
                        else:
                            print ("Time when error occurred :", time.asctime())
                            sys.exit("Platform navigator already exists for a different version, " + version + " Uninstall it and try again. This script uses version " + cp4iVersion)
        
        if pnInstanceExists == False:
            pn_instance_yaml["metadata"]["namespace"] = args.ns
            pn_instance_yaml["spec"]["license"]["license"] = args.license_pn
            pn_instance_yaml["spec"]["storage"]["class"] = args.storageclass_pn
            if eusRelease:
                pn_instance_yaml["spec"]["replicas"] = 2
                del pn_instance_yaml["spec"]["storage"]
            createPNInstanceFileName = DATA_TEMP_DIR + "/pn_create_instance.yaml"
            with open(createPNInstanceFileName, 'w') as file2:
                yaml.dump(pn_instance_yaml, file2, default_flow_style=False)
            if args.no_install == False:
                pnInstanceName = pn_instance_yaml["metadata"]["name"]
                runKubernetesCommand("create -f " + createPNInstanceFileName, args.ns, False)
                time.sleep(60)
                print("ACTION OUTPUT : Created platform navigator instance.")
            else:
                print("no_install flag is set to true. Not installing platform navigator instance.")
                print("ACTION OUTPUT : Location of platform navigator instance creation yaml file : ", createPNInstanceFileName)
                print()
        
        # check if PN instance is created
        if args.no_install == False:
            flag = True
            loopCount = 0
            timeout = False
            pnInstanceCreated = False
            while flag:
                loopCount = loopCount + 1
                if loopCount >= 40:
                    flag = False
                    print ("Timeout after waiting for platform navigator instance. Current time : ", time.asctime())
                    timeout = True
                    break # safe break after 2 hr
                if pnInstanceCreated == False:
                    res1 = runKubernetesCommand("get platformnavigator " + pnInstanceName + " -o yaml", args.ns, True, 0, False)
                    if res1 != None and res1 != "" and res1.lower().startswith("error") == False:
                        res1 = yaml.safe_load(res1)
                        if "status" in res1 and "conditions" in res1["status"]:
                            conditions = res1["status"]["conditions"]
                            for eachCondition in conditions:
                                if eachCondition["type"] == "Ready" and eachCondition["status"] == "True":
                                    pnInstanceCreated = True
                
                if pnInstanceCreated:
                    flag = False
                else:
                    print ("Waiting for platform navigator instance to be ready. Current time : ", time.asctime())
                    time.sleep(180)
            
            if timeout:
                print ("Time when error occurred :", time.asctime())
                sys.exit("ERROR : Timedout waiting for platform navigator instance in namespace, {}. Manually check the status of PN instance and try again.")
            
    print()
    print()
    #operator group
    operator_group["metadata"]["namespace"] = args.ns
    operator_group["spec"]["targetNamespaces"].append(args.ns)
    apicOperatorGroupFileName = DATA_TEMP_DIR + "/apic_operator_group.yaml"
    with open(apicOperatorGroupFileName, 'w') as file2:
        yaml.dump(operator_group, file2, default_flow_style=False)
    if args.no_install == False:
        runKubernetesCommand("apply -f " + apicOperatorGroupFileName, args.ns, False)
        print("ACTION OUTPUT : Created/applied apic operator group")
    else:
        print("no_install flag is set to true. Not installing apic operator group.")
        print("ACTION OUTPUT : Location of apic operator group file : ", apicOperatorGroupFileName)
    print()

    #subscribe    
    apiconnect_subscribe["metadata"]["namespace"] = namespace

    #check if apiconnect subscription exists
    subscriptions = runKubernetesCommand("get subscription", namespace, False)
    subscriptions = subscriptions.splitlines()
    subscriptionExists = False
    for eachSubscription in subscriptions:
        if "apiconnect" in eachSubscription:
            apicSubscriptionName = eachSubscription[0:eachSubscription.index(" ")]
            apicSubscription = runKubernetesCommand("get subscription " + apicSubscriptionName + " -o yaml", namespace, True)
            apicSubscription = yaml.safe_load(apicSubscription)
            channel = apicSubscription["spec"]["channel"]
            if channel == apicChannel:
                subscriptionExists = True
                print("ACTION OUTPUT : API Connect operator already subscribed for channel number, " + apicChannel + " Not installing again. Proceeding further.")
                print()
            else:
                print ("Time when error occurred :", time.asctime())
                sys.exit("API Connect operator already subscribed for different channel number, " + channel + " Uninstall it and try again. This script uses API Connect channel " + apicChannel)
    
    if subscriptionExists == False:
        if args.custom_build:
            apiconnect_subscribe["spec"]["source"] = "ibm-apiconnect-catalog"
            
        subscribeAPICFileName = DATA_TEMP_DIR + "/subscription_apic.yaml"
        with open(subscribeAPICFileName, 'w') as file2:
            yaml.dump(apiconnect_subscribe, file2, default_flow_style=False)
        if args.no_install == False:
            runKubernetesCommand("create -f " + subscribeAPICFileName, namespace, False)
            time.sleep(120)
            print("ACTION OUTPUT : Created APIC subscription")
        else:
            print("no_install flag is set to true. Not installing apic operator.")
            print("ACTION OUTPUT : Location of APIC subscription file : ", subscribeAPICFileName)
        print()
    
    if args.no_install == False:
        flag = True
        loopCount = 0
        timeout = False
        apicDeployed = False
        dpDeployed = False
        while flag:
            loopCount = loopCount + 1
            if loopCount >= 60:
                flag = False
                print ("Timeout after waiting for apic and datapower operators to get deployed. Current time : ", time.asctime())
                timeout = True
                break # safe break after 1 hr
            if apicDeployed == False:
                res1 = runKubernetesCommand("get deployment ibm-apiconnect", namespace, True, 0, False)
                if res1 != None and res1 != "" and res1.lower().startswith("error") == False:
                    res11 = res1.splitlines()
                    for each in res11:
                        if each.startswith("ibm-apiconnect") and "1/1" in each:
                            print("ACTION OUTPUT : API Connect deployment is ready. \n", res1)
                            apicDeployed = True
                            break
            if dpDeployed == False:
                res2 = runKubernetesCommand("get deployment datapower-operator", namespace, True, 0, False)
                if res2 != None and res2 != "" and res2.lower().startswith("error") == False:
                    res22 = res2.splitlines()
                    for each2 in res22:
                        if each2.startswith("datapower-operator") and "1/1" in each2:
                            print("ACTION OUTPUT : DataPower deployment is ready. \n", res2)
                            dpDeployed = True
                            break
            if apicDeployed and dpDeployed:
                flag = False
            else:
                print ("Waiting for apic and data power operators to be ready. Current time : ", time.asctime())
                time.sleep(60)
        
        if timeout:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Timedout waiting for apic and datapower operators to be deployed in namespace, {}. Manually check the status of installed operators and try again.")


def validateNamespaces(listOfInputNamespaces):
    namespaceOutput = runKubernetesCommand("get ns", None, True)
    namespaceOutput = namespaceOutput.splitlines()
    existingNamespaceList = []
    skipHeader = True
    for x in namespaceOutput:
        if skipHeader == True:
            skipHeader = False
            continue
        existingNamespaceList.append(x[0:x.index(" ")])
    #print ("Valid namespaces are : ", existingNamespaceList)
    print()
        
    for eachGivenNS in listOfInputNamespaces:
        if eachGivenNS != None:
            giveNamespacesforSubsys = None
            giveNamespacesforSubsys = eachGivenNS.split("|")
            for each in giveNamespacesforSubsys:
                if each != "" and each not in existingNamespaceList:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : Invalid namespace, {} provided. Namespace(s) given as input for this subsystem : {}. Exiting...".format(each, eachGivenNS))


def validateInputs():   
    global mgmtSubsystemDetails
    global portalSubsystemDetails

    # for eus release (10.0.1 or 2020.4), ocp version must be 4.6.x
    if eusRelease and ocpVersion.startswith(EUS_OCP_VERSION) == False:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR :Extended Update Support (EUS) release is getting installed But the OCP version({}) is not valid for EUS release. Exiting...".format(ocpVersion))
    
    if eusRelease == False and (args.license == None or args.license == ""):
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Need license value for CD release. Refer https://www.ibm.com/docs/en/api-connect/10.0.x?topic=requirements-api-connect-licenses. Use -license flag. Exiting...".format(ocpVersion))

    #check if storageclass exists
    validStorageClasses = []
    storageclasses = runKubernetesCommand("get storageclass", args.ns, False)
    storageclasses = storageclasses.splitlines()
    for eachsc in storageclasses:
        validStorageClasses.append(eachsc[0:eachsc.index(" ")])
    print("Valid storage classes : ", validStorageClasses)
    
    if args.storageclass_apic == None or args.storageclass_apic not in validStorageClasses:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR :Invalid storage class provided for APIC installation. use -storageclass_apic flag. Given value is {}. Exiting...".format(args.storageclass_apic))
        
    if args.cp4i and eusRelease == False and (args.storageclass_pn == None or args.storageclass_pn not in validStorageClasses):
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR :Invalid storage class provided for platform navigator in CP4I installation. Given value is {}. Exiting...".format(args.storageclass_pn))
    
    if args.cp4i and (args.license_pn == None or args.license_pn == ""):
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR :Invalid license provided to install platform navigator instance. Given value is {}. Exiting...".format(args.license_pn))
    
    # check if block storage for apic and filesystem storage for pn as WELL. TBD
    
    #check if apic is installed or not
    getapic_out = runKubernetesCommand("get apiconnectcluster.apiconnect.ibm.com", args.ns, False, 0, False)
    if getapic_out.startswith("error") == False and len(getapic_out.splitlines()) > 1:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Resource of type apiconnectcluster.apiconnect.ibm.com(top level CR) already exist in the namespace. Exiting...")
    
    getmgmt_out = runKubernetesCommand("get managementcluster.management.apiconnect.ibm.com", args.ns, False, 0, False)
    if getmgmt_out.startswith("error") == False and len(getmgmt_out.splitlines()) > 1:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Resource of type managementcluster.management.apiconnect.ibm.com already exist in the namespace. Exiting...")

    if args.no_portal == False:
        getptl_out = runKubernetesCommand("get portalcluster.portal.apiconnect.ibm.com", args.ns, False, 0, False)
        if getptl_out.startswith("error") == False and len(getptl_out.splitlines()) > 1:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Resource of type portalcluster.portal.apiconnect.ibm.com already exist in the namespace. Exiting...")

    if args.no_gateway == False:
        getgw_out = runKubernetesCommand("get gatewaycluster.gateway.apiconnect.ibm.com", args.ns, False, 0, False)
        if getgw_out.startswith("error") == False and len(getgw_out.splitlines()) > 1:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Resource of type gatewaycluster.gateway.apiconnect.ibm.com already exist in the namespace. Exiting...")
 
    if args.no_analytics == False:
        geta7sout = runKubernetesCommand("get analyticscluster.analytics.apiconnect.ibm.com", args.ns, False, 0, False)
        if geta7sout.startswith("error") == False and len(geta7sout.splitlines()) > 1:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Resource of type analyticscluster.analytics.apiconnect.ibm.com already exist in the namespace. Exiting...")
    
    mgmtSubsystemNames = config["management_subsystem"].keys()
    selectedManagementSubsystem = None
    if len(mgmtSubsystemNames) > 1:
        print ()
        print ("List of management subsystems from the saved configuration(source system) : ", list(mgmtSubsystemNames))
        if args.silent:
            selectedManagementSubsystem = args.mgmt_subsystem_name
        else:
            selectedManagementSubsystem = input("SELECT THE SUBSYSTEM FROM THE LIST which you want to use for top level cr : ")
            
        if selectedManagementSubsystem != None: selectedManagementSubsystem = selectedManagementSubsystem.strip()
        if selectedManagementSubsystem not in config["management_subsystem"]:
            if args.silent and selectedManagementSubsystem == None:
                print("Multiple management subsystems found in the saved configuration. You need to select one by using -mgmt_subsys_name or --mgmt_subsystem_name flag")
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : The selected subsystem({}) does not exist in the configuration. Exiting...".format(selectedManagementSubsystem))
    elif len(mgmtSubsystemNames) == 1:
        selectedManagementSubsystem = list(mgmtSubsystemNames)[0]
    

    if selectedManagementSubsystem != None and args.ns != None:
        mgmtSubsystemDetails = config["management_subsystem"][selectedManagementSubsystem]
        print ("selected management subsystem from the source configuration : ", selectedManagementSubsystem)
    else:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Invalid management subsystem from source. Check values for source management subsystem name : {} and target namespace : {}".format(selectedManagementSubsystem, args.ns))
    
    versionReconciled = mgmtSubsystemDetails["versionReconciled"]
    if versionReconciled != None and versionReconciled.startswith("10."):
        if "customApplicationCredentials" in mgmtSubsystemDetails:
            customApplicationCredentials = mgmtSubsystemDetails["customApplicationCredentials"]
            for each in customApplicationCredentials:
                runKubernetesCommand("get secret " + each["secretName"], args.ns, False)
                if each["name"] in mgmtCustomApplicationSecrets:
                    mgmtCustomApplicationSecrets.remove(each["name"])
            
            if len(mgmtCustomApplicationSecrets) > 0:
                print ("Time when error occurred :", time.asctime())
                sys.exit("ERROR : Exiting the script as some secrets from management customApplicationCredentials are missing in the configuration. Missing secrets : {}".format(mgmtCustomApplicationSecrets))
        else:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Not able to verify the secrets for customApplicationCredentials from source configuration.  customApplicationCredentials not present in source configuration. Exiting...")
    else:
        print ("ACTION OUTPUT : Not checking for customApplicationCredentials as they are not present as source version is ", versionReconciled)

    if "encryptionSecret" in mgmtSubsystemDetails and "secretName" in mgmtSubsystemDetails["encryptionSecret"]:
        mgmtEncryptionSecret = mgmtSubsystemDetails["encryptionSecret"]["secretName"]
        runKubernetesCommand("get secret " + mgmtEncryptionSecret, args.ns, False)
    else:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Not able to verify the management encryption secret from source configuration. encryptionSecret not present in source configuration. Exiting...")

    if "databaseBackup" in mgmtSubsystemDetails and "credentials" in mgmtSubsystemDetails["databaseBackup"]:
        dbCredentialSecret = mgmtSubsystemDetails["databaseBackup"]["credentials"]
        runKubernetesCommand("get secret " + dbCredentialSecret, args.ns, False)
    else:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Not able to verify database backup credential secret from source configuration. databaseBackup not present in source configuration. Exiting...")
    
    selectedPortalSubsystem = None
    if args.no_portal == False and config_portal != None:
        portalSubsystemNames = config_portal["portal_subsystem"].keys()
        if len(portalSubsystemNames) > 1:
            print ()
            print ("List of portal subsystems from the saved configuration(source system) : ", list(portalSubsystemNames))
            print ("Portal encryption secret and backup secret wil be used from this subsystem while creating top level cr.")
            if args.silent:
                selectedPortalSubsystem = args.ptl_subsystem_name
            else:
                selectedPortalSubsystem = input("SELECT THE SUBSYSTEM FROM THE LIST which you want to use for top level cr : ")
            
            if selectedPortalSubsystem != None: selectedPortalSubsystem = selectedPortalSubsystem.strip()
            if selectedPortalSubsystem not in config_portal["portal_subsystem"]:
                if args.silent and selectedPortalSubsystem == None:
                    print("Multiple portal subsystems found in the saved configuration. You need to select one by using -ptl_subsys_name or --ptl_subsystem_name flag")
                print ("Time when error occurred :", time.asctime())
                sys.exit("ERROR : The selected subsystem({}) does not exist in the configuration. Exiting...".format(selectedPortalSubsystem))
                
        elif len(portalSubsystemNames) == 1:
            selectedPortalSubsystem = list(portalSubsystemNames)[0]
            
        if selectedPortalSubsystem != None and args.ns != None:
            portalSubsystemDetails = config_portal["portal_subsystem"][selectedPortalSubsystem]
            print ("selected portal subsystem from the source configuration : ", selectedPortalSubsystem)
        else:
            sys.exit ("ERROR : Invalid portal subsystem from source. Check values for source portal subsystem name : {} and target namespace : {}".format(selectedPortalSubsystem, args.ns))
        
        if "encryptionSecret" in portalSubsystemDetails and "secretName" in portalSubsystemDetails["encryptionSecret"]:
            ptlEncryptionSecret = portalSubsystemDetails["encryptionSecret"]["secretName"]
            runKubernetesCommand("get secret " + ptlEncryptionSecret, args.ns, False)
        else:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Not able to verify the portal encryption secret from source configuration. encryptionSecret not present in source configuration. Exiting...")

        if "portalBackup" in portalSubsystemDetails and "credentials" in portalSubsystemDetails["portalBackup"]:
            dbCredentialSecret = portalSubsystemDetails["portalBackup"]["credentials"]
            runKubernetesCommand("get secret " + dbCredentialSecret, args.ns, False)
        else:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Not able to verify portal backup credential secret from source configuration. portalBackup not present in source configuration. Exiting...")


def createTopLevelCR():
    print("Create top level CR::")

    topLevelCR["metadata"]["namespace"] = args.ns
    
    if args.name != None and args.name != "":
        topLevelCR["metadata"]["name"] = args.name

    if args.production:
        topLevelCR["spec"]["license"]["use"] = "production"
    
    if eusRelease == False:
        if args.license == None or args.license == "":
            print ("Time when error occurred :", time.asctime())
            sys.exit("Invalid license value({}) provided in top level CR. Refer https://www.ibm.com/docs/en/api-connect/10.0.x?topic=requirements-api-connect-licenses".format(args.license))
        topLevelCR["spec"]["license"]["license"] = args.license
    
    topLevelCR["spec"]["storageClassName"] = args.storageclass_apic
    
    topLevelCR["spec"]["version"] = apicVersion
    
    if args.profile != None and args.profile != "":
        if args.profile not in profiles:
            print ("Time when error occurred :", time.asctime())
            sys.exit("Invalid profile value({}) provided in top level CR, supported profile values :{}".format(args.profile, profiles))
        topLevelCR["spec"]["profile"] = args.profile
    else:
        topLevelCR["spec"]["profile"] = profiles[0]
    
    versionReconciled = mgmtSubsystemDetails["versionReconciled"]

    topLevelCR["spec"]["management"]["encryptionSecret"] = mgmtSubsystemDetails["encryptionSecret"]
    topLevelCR["spec"]["management"]["databaseBackup"] = mgmtSubsystemDetails["databaseBackup"]
    
    if versionReconciled != None and versionReconciled.startswith("10."):
        topLevelCR["spec"]["management"]["name"] = mgmtSubsystemDetails["name"]
        topLevelCR["spec"]["management"]["originalUID"] = mgmtSubsystemDetails["originalUID"]
        topLevelCR["spec"]["management"]["customApplicationCredentials"] = mgmtSubsystemDetails["customApplicationCredentials"]
        topLevelCR["spec"]["management"]["siteName"] = mgmtSubsystemDetails["siteName"]
    else:
        del topLevelCR["spec"]["management"]["name"]
        del topLevelCR["spec"]["management"]["originalUID"]
        del topLevelCR["spec"]["management"]["siteName"]
    
    if args.no_portal:
        del topLevelCR["spec"]["portal"]
        if "disabledServices" in topLevelCR["spec"]:
            topLevelCR["spec"]["disabledServices"].append("portal")
        else:
            topLevelCR["spec"]["disabledServices"] = ["portal"]
    else:
        if portalSubsystemDetails != None:
            #name from source not really needed for portal during dr
            if "portal" in topLevelCR["spec"] and "name" in topLevelCR["spec"]["portal"]:
                del topLevelCR["spec"]["portal"]["name"] # remove default value
            #topLevelCR["spec"]["portal"]["name"] = portalSubsystemDetails["name"]

            topLevelCR["spec"]["portal"]["encryptionSecret"] = portalSubsystemDetails["encryptionSecret"]
            topLevelCR["spec"]["portal"]["portalBackup"] = portalSubsystemDetails["portalBackup"]

            if versionReconciled != None and versionReconciled.startswith("10."):
                topLevelCR["spec"]["portal"]["originalUID"] = portalSubsystemDetails["originalUID"]
                topLevelCR["spec"]["portal"]["siteName"] = portalSubsystemDetails["siteName"]
            else:
                del topLevelCR["spec"]["portal"]["originalUID"]
                del topLevelCR["spec"]["portal"]["siteName"]
        else:
            del topLevelCR["spec"]["portal"]

    if args.no_analytics:
        del topLevelCR["spec"]["analytics"]
        if "disabledServices" in topLevelCR["spec"]:
            topLevelCR["spec"]["disabledServices"].append("analytics")
        else:
            topLevelCR["spec"]["disabledServices"] = ["analytics"]
    
    if args.no_gateway:
        if "disabledServices" in topLevelCR["spec"]:
            topLevelCR["spec"]["disabledServices"].append("gateway")
        else:
            topLevelCR["spec"]["disabledServices"] = ["gateway"]
    
    topLevelCRFileName = DATA_DIR + "/top_level_cr.yaml"
    with open(topLevelCRFileName, 'w') as topCRFile:
            yaml.dump(topLevelCR, topCRFile, default_flow_style=False)
    
    if args.no_install == False:
        print("Location of API Connect top level CR file : ", topLevelCRFileName)
        runKubernetesCommand("create -f " + topLevelCRFileName, args.ns, False, 20)
        time.sleep(30)

    else:
        print("no_install flag is set to true. Not installing API Connect.")
        print("Location of API Connect top level CR file : ", topLevelCRFileName)

    if args.no_install == False:
        flag = True
        loopCount = 0
        timeout = False
        apicInstalled = False
        while flag:
            loopCount = loopCount + 1
            if loopCount >= 50:
                flag = False
                print ("Timeout after waiting for APIC instance creation. Current time : ", time.asctime())
                timeout = True
                break # safe break after 2.5 hr
            if apicInstalled == False:
                res1 = runKubernetesCommand("get apiconnectcluster.apiconnect.ibm.com " + topLevelCR["metadata"]["name"] + " -o yaml", args.ns, True, 0, False)
                if res1 != None and res1 != "" and res1.lower().startswith("error") == False:
                    res1 = yaml.safe_load(res1)
                    if "status" in res1 and "conditions" in res1["status"]:
                        conditions = res1["status"]["conditions"]
                        for eachCondition in conditions:
                            if eachCondition["type"] == "Ready" and eachCondition["status"] == "True":
                                apicInstalled = True
            
            if apicInstalled:
                flag = False
            else:
                print ("Waiting for APIC instance to be ready. Current time : ", time.asctime())
                time.sleep(180)
        
        if timeout:
            print ("Time when error occurred :", time.asctime())
            sys.exit("ERROR : Timedout waiting for APIC instance in namespace, {}. Manually check the status of APIC instance.")
    
    #versionReconciled = mgmtSubsystemDetails["versionReconciled"]
    #if versionReconciled != None and versionReconciled.startswith("2018."):
    #    runKubernetesCommand("adm policy add-scc-to-user anyuid system:serviceaccount:" + args.ns + ":default", None)

    print()
    print("This script performed the following actions in the target cluster:")
    print("**********************************************************************")
    if args.cp4i and args.no_install == False:
        print("- Installed Platform Navigator and created an instance of it.")
    if args.no_install:
        print("- Generated the yamls for catalog sources, subscriptions and top level CR. Check the data directory and data/temp directory.")
    else:
        print("- Using the saved configuration from source system, installed API Connect on the target cluster.")
    print()
    print("Next steps:")
    print("1. Restore management backup by running the script, restore_management_db.py")
    print()
        

    

# start
def start():
    global ocpVersion
    
    print ("CHECKING IF KUBECTL/OC EXIST IN THE PATH AND HAVE ACCESS TO THE CLUSTER :")
    ocpVersion = runKubernetesCommand("version", "default", False)
    ocpVersion = ocpVersion.splitlines()
    for each in ocpVersion:
        if each.startswith("Server"):
            ocpVersion = each[each.index(":")+1:].strip()
            break

    if args.skip_namespace_validation == False:
        validateNamespaces([args.ns])
    
    if args.ns == None or args.ns == "" or "|" in args.ns:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Invalid namespace({}) provided to install target APIC system. Only one namespace need to be provided. Exiting...".format(args.ns))

    validateInputs()
    installCatalogSourcesAndSubscribe()
    time.sleep(30)
    createTopLevelCR()
    
	
parser = argparse.ArgumentParser(description="The script is used in form factor to form factor migration to install the target API Connect system on Openshift Cloud Platform.\n\
The latest version of the  Extended Update Support (EUS) or Continuous Delivery (CD) is installed.\n\
It does not support installation of API Connect on Kubernetes or VMWare appliance.\n \n\
Prerequisites ::\n\
1. Access to the OCP cluster using oc command,\n\
2. Python 3.x and PyYAML module need to be installed\n\
3. This script must be run on supported version of the OCP cluster.\n\
4. The entitlement key to pull the images from IBM Container Registry or other registry must be already added to the OCP cluster or the images must be already be available in the registry.\n\
5. The storageclasses needed for API Connect and platform navigator must already be created on the OCP cluster.\n\
6. The data directory where the configuration from the source system are saved. The data directory with source configuration must be present in the same directory as this script." , 
formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-n", "--namespace", dest = "ns", help="uses this namespace to install API Connect.")
parser.add_argument("-operator_in_specific_namespace", "--operator_in_specific_namespace", action='store_true', dest = "operator_in_specific_namespace", help="Operators will be installed in same namespace where API Connect will be installed. If not provided, default is all namespaces")

parser.add_argument("-production", "--production", action='store_true', dest = "production", help="License use is set to production. If not provided defaulted to nonproduction.")
parser.add_argument("-license", "--license", dest = "license", help="License value when using CD release. Refer https://www.ibm.com/docs/en/api-connect/10.0.x?topic=requirements-api-connect-licenses")
parser.add_argument("-name", "--name", dest = "name", help="Name of the top level CR. If not provided defaulted to minimum.")
parser.add_argument("-profile", "--profile", dest = "profile", help="profile value for the top level cr. If not provided defaulting to " + profiles[0])
parser.add_argument("-cp4i", "--cp4i",  action='store_true', dest = "cp4i", help="It is Cloud Pak for Integration. APIC and Platform navigator will be installed.")

parser.add_argument("-storageclass_apic", "--storageclass_apic", dest = "storageclass_apic", help="Storage class used by API Connect.")
parser.add_argument("-storageclass_pn", "--storageclass_pn", dest = "storageclass_pn", help="Storage class used by platform navigator in case of Cloud Pak for Integration.")
parser.add_argument("-license_pn", "--license_pn", dest = "license_pn", help="License for platform navigator instance.")

parser.add_argument('-skip_namespace_validation', "--skip_namespace_validation",  action='store_true', dest = "skip_namespace_validation", help='Skips validation of input namespaces.')

parser.add_argument("-no_portal", "--no_portal", action='store_true', dest = "no_portal", help="Portal subsystem will not be installed")
parser.add_argument("-no_gateway", "--no_gateway", action='store_true', dest = "no_gateway", help="Gateway subsystem will not be installed")
parser.add_argument("-no_analytics", "--no_analytics", action='store_true', dest = "no_analytics", help="Analytics subsystem will not be installed")

parser.add_argument('-mgmt_subsys_name', "--mgmt_subsystem_name", dest = "mgmt_subsystem_name", help='If multiple management subsytems present in the configuration, the script will use this.')
parser.add_argument('-ptl_subsys_name', "--ptl_subsystem_name", dest = "ptl_subsystem_name", help='If multiple portal subsytems present in the configuration, the script will use this.')
parser.add_argument('-silent', "--silent", action='store_true', dest = "silent", help='Does not prompt for additinal inputs and proceeds silently.')

parser.add_argument("-custom_build", "--custom_build",  action='store_true', dest = "custom_build", help="Indicates custom build during development or a fix.")
parser.add_argument("-apic_catsrc_image", "--apic_catsrc_image", dest = "apic_catsrc_image", help="Custom build image value for API Connect catalog source.")
parser.add_argument("-dp_catsrc_image", "--dp_catsrc_image", dest = "dp_catsrc_image", help="Custom build image value for Datapower catalog source.")

parser.add_argument("-no_install", "--no_install", action='store_true', dest = "no_install", help="Vaidates the configuration and creates the yaml for top level CR. Does not install operators or API Connect.")

args = parser.parse_args()

print ("Start time :", time.asctime())
print ()

print ("Input namespace where API Connect is installed (-n or --namespace flag) : ", args.ns)
print ("Operators will be installed in the namespace given as input (NOT in all namespaces which is default) : ", args.operator_in_specific_namespace)
print ()

print ("Production installation (-production or --production flag) : ", args.production)
print ("License value being used (-license or --license flag) : ", args.license)
print ("Name of the top level CR (-name or --name flag) : ", args.name)
print ("Profile being installed by the top level CR (-profile or --profile flag) : ", args.profile)
print ("is CP4I installation (-cp4i or --cp4i flag) : ", args.cp4i)
print ()

print ("Storage class used by API Connect (-storageclass_apic or --storageclass_apic flag) : ", args.storageclass_apic)
if args.cp4i:
    print ("Storage class used by platform navigator instance (-storageclass_pn or --storageclass_pn flag) : ", args.storageclass_pn)
    print ("License value for platform navigator instance (-license_pn or --license_pn flag) : ", args.license_pn)
print ()

print ("Do not install portal subsystem (-no_portal or --no_portal flag) : ", args.no_portal)
print ("Do not install gateway subsystem (-no_gateway or --no_gateway flag) : ", args.no_gateway)
print ("Do not install analytics subsystem (-no_analytics or --no_analytics flag) : ", args.no_analytics)
print ()

print ("Installation using custom build (-custom_build or --custom_build flag) : ", args.custom_build)
print ("Custom build apiconnect catalog source image value (-apic_catsrc_image or --apic_catsrc_image flag) : ", args.apic_catsrc_image)
print ("Custom build datapower catalog source image value (-dp_catsrc_image or --dp_catsrc_image flag) : ", args.dp_catsrc_image)
print ()
print ("Just generate the yaml files and do not install API Connect: ", args.no_install)
print ()

print ("Mangement subsystem name (-mgmt_subsys_name or --mgmt_subsystem_name flag) : ", args.mgmt_subsystem_name)
print ("Portal subsystem name (-ptl_subsys_name or --ptl_subsystem_name flag) : ", args.ptl_subsystem_name)
print ("silent (-silent or --silent flag) : ", args.silent)
print ()

pwd = os.getcwd()
DATA_DIR = pwd + "/data"
DATA_TEMP_DIR = pwd + "/data/temp"

if args.ns == None or args.ns == "":
    print ("Time when error occurred :", time.asctime())
    sys.exit ("ERROR : Namespace (-n or --namespace flag) where API Connect need to be installed is not provided. Exiting...")


# load config data if exists
if os.path.exists(DATA_DIR + "/" + CONFIG_FILE_NAME):
    print ("Source APIC system configuration file exists. Loading it")
    text_file = open(DATA_DIR + "/" + CONFIG_FILE_NAME, "r")
    config1 = text_file.read()
    print("Configuration file : ", config1)
    config = yaml.safe_load(config1)
    text_file.close()
else:
    print ("Time when error occurred :", time.asctime())
    sys.exit("ERROR : config.yaml file with details of the source APIC system in NOT present in the data directory. Exiting...")
    
# load portal config data if exists
if args.no_portal == False:
    if os.path.exists(DATA_DIR + "/" + CONFIG_PORTAL_FILE_NAME):
        print ("Source APIC system portal configuration file exists. Loading it")
        text_file = open(DATA_DIR + "/" + CONFIG_PORTAL_FILE_NAME, "r")
        config1 = text_file.read()
        print("portal configuration file : ", config1)
        config_portal = yaml.safe_load(config1)
        text_file.close()
    else:
        print("ACTION OUTPUT : No portal configuration found in the saved configuration of the source system")
        print()
        #print ("Time when error occurred :", time.asctime())
        #sys.exit("ERROR : portal_config.yaml file with details of the source APIC system portal configuration in NOT present in the data directory. Exiting...")

start()

print()
print ("End time :", time.asctime())
