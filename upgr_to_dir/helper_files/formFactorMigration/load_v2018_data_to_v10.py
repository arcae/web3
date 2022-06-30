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
import base64
import random

oc_client = "oc"
kubectl_client = "kubectl"
client = oc_client

pwd = None
DATA_DIR = None
DATA_TEMP_DIR = None

CONFIG_FILE_NAME = "config.yaml"
config =  None
selectedMgmtSubsystemName = None

isCP4I = False
cloudAdminServer = None

mgmt_restore = {
  "apiVersion": "management.apiconnect.ibm.com/v1beta1",
  "kind": "ManagementRestore",
  "metadata": {
    "name": "TBD"
  },
  "spec" : {
    "backupName": "test"
  }
}
targetSystemSpecVersion = None
targetSystemReconciledVersion = None

pvc_name = "pvc-v2018-load"
pvc_template = {
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "metadata": {
    "name": "SOME_NAME"
  },
  "spec": {
    "accessModes": [
      "ReadWriteOnce"
    ],
    "resources": {
      "requests": {
        "storage": "10Gi"
      }
    },
    "storageClassName": "STORAGE_CLASS"
  }
}

load_job_name = "v2018-mgmt-load"
load_job_yaml = {
  "apiVersion": "batch/v1",
  "kind": "Job",
  "metadata": {
    "name": load_job_name
  },
  "spec": {
    "backoffLimit": 6,
    "completions": 1,
    "parallelism": 1,
    "template": {
      "metadata": {
        "name": load_job_name
      },
      "spec": {
        "imagePullSecrets": [
            {
                "name": "REGISTRY_SECRET"
            }
        ],
        "containers": [
          {
            "name": load_job_name,
            "image": "apic-dev-docker-local.artifactory.swg-devops.com/ibm-apiconnect-management-v10-upgrade@sha256:4d96af476717dd0b1c6a5bc06c3587b59b658c78952fc611f1e4f6d75509ec2d",
            "imagePullPolicy": "IfNotPresent",
            "resources": {
              "limits": {
                "cpu": "8",
                "memory": "10G"
              },
              "requests": {
                "cpu": "1",
                "memory": "512Mi"
              }
            },
            "securityContext": {
              "allowPrivilegeEscalation": False,
              "runAsUser": 0
            },
            "env": [
              {
                "name": "DB_SERVICE_PORT",
                "value": "5432"
              },
              {
                "name": "DEBUG",
                "value": "v10-upgrade:*"
              },
              {
                "name": "LOG_DIRECTORY",
                "value": "/upgrade"
              },
              {
                "name": "NODE_OPTIONS",
                "value": "--max-old-space-size=4096"
              },
              {
                "name": "VELOX_APPLIANCE",
                "value": "true"
              },
              {
                "name": "VELOX_CERTS",
                "value": "/etc/velox/certs"
              },
              {
                "name": "VELOX_DB_MTLS",
                "value": "true"
              },
              {
                "name": "WORKING_DIRECTORY",
                "value": "/upgrade"
              }
            ],
            "volumeMounts": [
              {
                "mountPath": "/upgrade",
                "name": "v2018-load-volume"
              },
              {
                "mountPath": "/etc/db/postgres/creds",
                "name": "mgmt-postgres-postgres-secret",
                "readOnly": True
              },
              {
                "mountPath": "/etc/db/postgres/certs",
                "name": "mgmt-db-client-postgres",
                "readOnly": True
              },
              {
                "mountPath": "/etc/velox/certs",
                "name": "management-encryption-secret",
                "readOnly": True
              }
            ]
          }
        ],
        "restartPolicy": "OnFailure",
        "volumes": [
          {
            "name": "v2018-load-volume",
            "persistentVolumeClaim": {
              "claimName": pvc_name
            }
          },
          {
            "name": "mgmt-postgres-postgres-secret",
            "secret": {
              "defaultMode": 420,
              "secretName": "mgmt-postgres-postgres-secret"
            }
          },
          {
            "name": "mgmt-db-client-postgres",
            "secret": {
              "defaultMode": 420,
              "secretName": "mgmt-db-client-postgres"
            }
          },
          {
            "name": "management-encryption-secret",
            "secret": {
              "defaultMode": 420,
              "secretName": "mgmt-encryption-secret"
            }
          }
        ]
      }
    }
  }
}


deploy_name = "v2018-mgmt-upload-csv"
deploy_yaml = {
  "apiVersion": "apps/v1",
  "kind": "Deployment",
  "metadata": {
    "name": deploy_name
  },
  "spec": {
    "selector": {
      "matchLabels": {
        "app": "nginx"
      }
    },
    "replicas": 1,
    "template": {
      "metadata": {
        "labels": {
          "app": "nginx"
        }
      },
      "spec": {
        "imagePullSecrets": [
            {
                "name": "REGISTRY_SECRET"
            }
        ],
        "containers": [
          {
            "name": "nginx",
            "image": "nginx",
            "securityContext": {
              "allowPrivilegeEscalation": False,
              "runAsUser": 0
            },
            "ports": [
              {
                "containerPort": 80
              }
            ],
            "volumeMounts": [
              {
                "mountPath": "/upgrade",
                "name": "v2018-load-volume"
              }
            ]
          }
        ],
        "volumes": [
          {
            "name": "v2018-load-volume",
            "persistentVolumeClaim": {
              "claimName": pvc_name
            }
          }
        ]
      }
    }
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
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : Failed to run the command, [{}], return code {} and error is [{}].  Exiting...".format(obfuscatedCommand, returnObject.returncode, err)) 
                else:
                    out = err
                    flag = False  
    if not silent:
        print (out)
        print ()
    return out

#health check for portal and gateway of the target APIC system
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
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : Health check failed for {} subsystem with name {}. Phase : {} and state : {}".format(subsystem, subsystemName, crData["status"]["phase"], crData["status"]["state"]))
                print ("ACTION OUTPUT : {} with name {} is healthy".format(subsystem, subsystemName))
            print ()
    else:
        print ("ACTION OUTPUT : Skipping health check for {} subsytem as namespace is NOT provided in the input. Given namespace is {}".format(subsystem, ns))


def loadManagementData():
    global selectedMgmtSubsystemName
    print ("Load v2018 management data into v10 ::::")
    
    #get the saved configuration
    mgmtSubsystemNames = config["management_subsystem"].keys()
    managementSubsystemDetails = None
    selectedSubsystem = None
    if len(mgmtSubsystemNames) > 1:
        print ()
        print ("List of management subsystems from the saved configuration(source system) : ", list(mgmtSubsystemNames))
        
        if args.silent:
            selectedSubsystem = args.mgmt_subsystem_name
        else:
            selectedSubsystem = input("SELECT THE SUBSYSTEM FROM THE LIST : ")
        
        if selectedSubsystem != None: selectedSubsystem = selectedSubsystem.strip()
        if selectedSubsystem not in config["management_subsystem"]:
            if args.silent and selectedSubsystem == None:
                print("Multiple management subsystems found in the saved configuration. You need to select one by using -mgmt_subsys_name or --mgmt_subsystem_name flag")
            print ("Time when error occurred :", time.asctime())
            sys.exit("The selected subsystem({}) does not exist in the configuration. Exiting...".format(selectedSubsystem))
    
    elif len(mgmtSubsystemNames) == 1:
        selectedSubsystem = list(mgmtSubsystemNames)[0]
    
    if selectedSubsystem == None:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : No configuration found for the management subsystem from the source system.  Exiting...")
 
    print ("selected management subsystem from the source configuration : ", selectedSubsystem)
    selectedMgmtSubsystemName = selectedSubsystem
    
    print()
    managementSubsystemDetails = config["management_subsystem"][selectedSubsystem]
    sourceSystemReconciledVersion = managementSubsystemDetails["versionReconciled"]
    print ("Source system version : {}".format(sourceSystemReconciledVersion))
    print ("Target system version : {}".format(targetSystemReconciledVersion))
    print()

    if sourceSystemReconciledVersion.startswith("2018.") == False:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Source APIC system is not v2018 version. Version of source system is {}  Exiting...".format(sourceSystemReconciledVersion))


    #check if any existing management db restores are in running state, then wait
    flag = True
    loopCount = 0
    timeout = False
    while flag:
        loopCount = loopCount + 1
        if loopCount >= 60:
            flag = False
            print ("Timeout after Waiting for ALREADY running management db restores to be completed. current time : ", time.asctime())
            timeout = True
            break # safe break after 2 hr
        existingMgmtRestores = runKubernetesCommand("get managementrestore", args.mgmt_ns, True, 0, False)
        existingMgmtRestores = existingMgmtRestores.splitlines()
        currentRunningList = []
        for r1 in existingMgmtRestores:
            if "Running" in r1 or "Pending" in r1 or "RestoreInProgress" in r1 or "RestoreSuccessful" in r1 or "SFTPBackupDownloadSuccessful" in r1:
                currentRunningList.append(r1)

        if len(currentRunningList) == 0:
            flag = False
        else:
            print ("Waiting for ALREADY running management db restores to be completed. Current time : ", time.asctime())
            time.sleep(120)
    
    if timeout:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Timedout waiting for ALREADY running management db restores to be completed. Manually check the status of these restores , wait for them to complete and try again.")
        
    createPVCAndRunLoadJob()

    #scale apic operator to 1 replica
    scaleAPICOperator(1)

    print ("Finally scale up management micro services if they are down")
    scaleManagementServicesAccessingPostgres(False)
    time.sleep(60)

    print()
    print()
    print("Waiting for management subsystem to be healthy...    ")
    out = runKubernetesCommand("get mgmt", args.mgmt_ns, True)
    mgmtSubsystemNameInTarget = out.splitlines()[1]
    mgmtSubsystemNameInTarget = mgmtSubsystemNameInTarget[0:mgmtSubsystemNameInTarget.index(" ")]
    flag = True
    loopCount = 0
    timeout = False
    while flag:
        loopCount = loopCount + 1
        if loopCount >= 60:
            flag = False
            timeout = True
            print ("Timeout after Waiting 20 minutes for management subsytem to be healthy.")
            break # safe break after 30 minutes
        print ("Waiting for management subsystem to be healthy. Current time : ", time.asctime())
        time.sleep(30)
        crData = runKubernetesCommand("get mgmt " + mgmtSubsystemNameInTarget + " -o yaml", args.mgmt_ns, True)
        crData = yaml.safe_load(crData)
        state = crData["status"]["state"]
        if crData["status"]["phase"] == "Running" and state[0:state.index("/")] == state[state.index("/") + 1:]:
            print ("Management subsystem is healthy and restore is complete.")
            flag = False
            break
    print()

    if timeout == True:
        print("Timeout happened waiting for management subsystem to become healthy after db restore.")
        print("Check the health of management subsystem and operator logs.")
        print("Once management subsystem is healthy, run the next steps.")
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : EXITING")



def createPVCAndRunLoadJob():
    #check if load job exists and delete it
    loadJob = runKubernetesCommand("get job " + load_job_name + " --no-headers", args.mgmt_ns, False, 0, False)
    if loadJob != None and loadJob.lower().startswith(load_job_name) == True:
        runKubernetesCommand("delete job " + load_job_name, args.mgmt_ns, False)
        time.sleep(30)
    else:
        print ("ACTION OUTPUT : " + load_job_name + " job not found. Will create new load job")
    
    print ()
    #check if deployment for uploading csv into pvc exists and delete it
    downloadCSVDeploy = runKubernetesCommand("get deploy " + deploy_name + " --no-headers", args.mgmt_ns, False, 0, False)
    if downloadCSVDeploy != None and downloadCSVDeploy.lower().startswith(deploy_name):
        runKubernetesCommand("delete deploy " + deploy_name, args.mgmt_ns, False)
        time.sleep(30)
    else:
        print ("ACTION OUTPUT : " + deploy_name + " used to upload csv to pvc not found. Will create one and upload csv")

    print ()
    pvc = runKubernetesCommand("get pvc " + pvc_name + " --no-headers", args.mgmt_ns, False, 0, False)
    if pvc != None and pvc.lower().startswith(pvc_name):
        runKubernetesCommand("delete pvc " + pvc_name, args.mgmt_ns, False)
        time.sleep(30)
    else:
        print ("ACTION OUTPUT : " + pvc_name + " pvc not found. Will create new pvc")

    print ()
    #create pvc
    pvc_template["metadata"]["name"] = pvc_name
    pvc_template["spec"]["storageClassName"] = args.storage_class
    if args.load_storage_size != None: 
        pvc_template["spec"]["resources"]["requests"]["storage"] = args.load_storage_size + "Gi"
    #pvc_template["spec"]["volumeName"] = selectedAvaialblePV
    with open(DATA_TEMP_DIR + "/pvc_load.yaml", 'w') as pvcFile:
        yaml.dump(pvc_template, pvcFile, default_flow_style=False)
    runKubernetesCommand("apply -f " + DATA_TEMP_DIR + "/pvc_load.yaml", args.mgmt_ns)
    time.sleep(30)

    print ()
    #upload the extracted csv and copy to data folder
    if args.nginx_image != None:
        deploy_yaml["spec"]["template"]["spec"]["containers"][0]["image"] = args.nginx_image
        if args.registry_secret == None:
            del deploy_yaml["spec"]["template"]["spec"]["imagePullSecrets"]
        else:
            deploy_yaml["spec"]["template"]["spec"]["imagePullSecrets"][0]["name"] = args.registry_secret
    else:
        del deploy_yaml["spec"]["template"]["spec"]["imagePullSecrets"]

    loadCSVUploadDeploy = DATA_TEMP_DIR + "/load_csv_upload_deploy.yaml"
    with open(loadCSVUploadDeploy, 'w') as f3:
        yaml.dump(deploy_yaml, f3, default_flow_style=False)
    runKubernetesCommand("apply -f " + loadCSVUploadDeploy, args.mgmt_ns)
    time.sleep(40)

    pods = runKubernetesCommand("get pods --no-headers", args.mgmt_ns, True)
    neededPod = None
    if pods != None and pods.lower().startswith("error") == False:
        pods = pods.splitlines()
        for eachPod in pods:
            if deploy_name in eachPod:
                neededPod = eachPod[0:eachPod.index(" ")]
                break
    print ("Use this pod to upload csv into pvc : ", neededPod)

    if neededPod == None:
        sys.exit("Pod to upload csv to pvc is not ready/created. The pod name is not available. Check deployment yaml (oc get deploy " + deploy_name + " -o yaml)")
    
    if not os.path.exists(DATA_DIR + "/" + selectedMgmtSubsystemName + "/extracted_data/data"):
        sys.exit("Extracted csv data not found. Directoty, {} does not exist".format(DATA_DIR + "/" + selectedMgmtSubsystemName + "/extracted_data/data"))
    
    if not os.path.exists(DATA_DIR + "/" + selectedMgmtSubsystemName + "/extracted_data/logs"):
        sys.exit("Extracted csv data not found. Directoty, {} does not exist".format(DATA_DIR + "/" + selectedMgmtSubsystemName + "/extracted_data/logs"))

    runKubernetesCommand("cp " + DATA_DIR + "/" + selectedMgmtSubsystemName + "/extracted_data/data " + args.mgmt_ns + "/" + neededPod + ":/upgrade", None, False)
    runKubernetesCommand("cp " + DATA_DIR + "/" + selectedMgmtSubsystemName + "/extracted_data/logs " + args.mgmt_ns + "/" + neededPod + ":/upgrade", None, False)
    print ("ACTION OUTPUT : Uploaded csv data of v2018 management to PVC")
    time.sleep(120)
    runKubernetesCommand("delete -f " + loadCSVUploadDeploy, args.mgmt_ns)
    
    print ()
    print ("Initially scale up apic operator if it is down")
    scaleAPICOperator(1)
    
    print ()
    print ("Initially scale up management micro services if they are down")
    scaleManagementServicesAccessingPostgres(False)
    time.sleep(60)

    print ()
    #get inputs needed for load job
    apimDeploy = None
    apimDeploy = runKubernetesCommand("get deploy | grep apim", args.mgmt_ns, True)
    if apimDeploy != None and apimDeploy.lower().startswith("error") == False:
        apimDeploy = apimDeploy[0:apimDeploy.index(" ")]
        print (" apim deployment : ", apimDeploy)
    apimDeployment = runKubernetesCommand("get deploy " + apimDeploy + " -o yaml", args.mgmt_ns, True)
    apimDeployment = yaml.safe_load(apimDeployment)
    apimContainer = apimDeployment["spec"]["template"]["spec"]["containers"][0]
    dbServiceHost = None
    for each in apimContainer["env"]:
        if each["name"] == "DB_SERVICE_HOST":
            dbServiceHost = each["value"]
            break
    print ("DB_SERVICE_HOST : ", dbServiceHost)

    volumeMountNameEncSecret = None
    for each in apimContainer["volumeMounts"]:
        if each["mountPath"] == "/etc/velox/certs":
            volumeMountNameEncSecret = each["name"]
            break
    print ("volumeMount Name Encryption Secret : ", volumeMountNameEncSecret)

    encryptionSecretName = None
    dbClientPostgresSecretName = None
    postgresPostgresSecretName = None
    for each in apimDeployment["spec"]["template"]["spec"]["volumes"]:
        if volumeMountNameEncSecret in each["name"]:
            encryptionSecretName = each["secret"]["secretName"]
        elif each["name"].endswith("db-client-postgres"):
            dbClientPostgresSecretName = each["secret"]["secretName"]
        elif each["name"].endswith("postgres-postgres-secret"):
            postgresPostgresSecretName = each["secret"]["secretName"]
    
    print ("Encryption Secret name : ", encryptionSecretName)
    print ("db-client-postgres Secret name : ", dbClientPostgresSecretName)
    print ("postgres-postgres-secret name : ", postgresPostgresSecretName)
    print ()
    
    if args.registry_secret == None:
        del load_job_yaml["spec"]["template"]["spec"]["imagePullSecrets"]
    else:
        load_job_yaml["spec"]["template"]["spec"]["imagePullSecrets"][0]["name"] = args.registry_secret
    db_service_host_env = {
        "name": "DB_SERVICE_HOST",
        "value": dbServiceHost
    }
    load_job_yaml["spec"]["template"]["spec"]["containers"][0]["env"].append(db_service_host_env)
    if args.load_image != None:
        load_job_yaml["spec"]["template"]["spec"]["containers"][0]["image"] = args.load_image
    
    for each in load_job_yaml["spec"]["template"]["spec"]["volumes"]:
        if "management-encryption-secret" in each["name"]:
            each["secret"]["secretName"] = encryptionSecretName
        elif "db-client-postgres" in each["name"]:
            each["secret"]["secretName"] = dbClientPostgresSecretName
        elif "postgres-postgres-secret" in each["name"]:
            each["secret"]["secretName"] = postgresPostgresSecretName
    
    with open(DATA_TEMP_DIR + "/load_job.yaml", 'w') as f3:
        yaml.dump(load_job_yaml, f3, default_flow_style=False)

    print ()
    print ("Scale down management micro services before starting load job")
    scaleManagementServicesAccessingPostgres(True)
    print ()
    scaleAPICOperator(0)
    time.sleep(30)

    #start load job
    print ("Starting load job")
    runKubernetesCommand("apply -f " + DATA_TEMP_DIR + "/load_job.yaml", args.mgmt_ns)

    time.sleep(60)
    while isLoadJobCompleted() == False:
        print ("Waiting for load job({}) to be completed.".format(load_job_name))
        time.sleep(120)

    loadJob = runKubernetesCommand("get job " + load_job_name + " -o yaml", args.mgmt_ns, True, 15, False)
    loadJob = yaml.safe_load(loadJob)
    if "status" not in loadJob or "succeeded" not in loadJob["status"] or loadJob["status"]["succeeded"] != 1:
        sys.exit("ERROR : Load job failed. Could not load data into v10 management system.")
    print ("ACTION OUTPUT : Loaded v2018 management data into v10 management subsystem")


def isLoadJobCompleted():
    loadJob = runKubernetesCommand("get job " + load_job_name + " --no-headers", args.mgmt_ns, False, 15, False)
    if loadJob != None and loadJob.lower().startswith(load_job_name):
        loadJob = runKubernetesCommand("get job " + load_job_name + " -o yaml", args.mgmt_ns, True, 15, False)
        loadJob = yaml.safe_load(loadJob)
        if "conditions" in loadJob["status"]:
            for eachCondition in loadJob["status"]["conditions"]:
                if (eachCondition["type"] == "Complete" and eachCondition["status"] == "True"):
                    return True
    else:
        sys.exit("Load job not found. Exiting.")
    return False


mgmtServices = ["mgmt-apim", "apim-schema", "apim-data", "mgmt-lur", "lur-schema", "lur-data", "mgmt-taskmanager", "mgmt-portal-proxy", "mgmt-analytics-proxy", "mgmt-websocket-proxy", "mgmt-juhu", "mgmt-billing"]
mgmtServices2 = ["mgmt-apim", "mgmt-lur", "mgmt-taskmanager", "mgmt-portal-proxy", "mgmt-analytics-proxy", "mgmt-websocket-proxy", "mgmt-juhu"]
def scaleManagementServicesAccessingPostgres(scaleDown=True):
    if scaleDown == False:
        scalePostgresPGBouncer(scaleDown)
    
    print ("Scaling management services accessing postgres database. scale down : {}  and timestamp : {}".format(scaleDown, time.asctime()))
    apic = runKubernetesCommand("get apiconnectcluster --no-headers", args.mgmt_ns)
    topCRName = None
    if apic != None and apic.lower().startswith("error") == False:
        apic = apic.splitlines()[0]
        topCRName = apic[0:apic.index(" ")]
    apic = runKubernetesCommand("get apiconnectcluster " + topCRName + " -o yaml", args.mgmt_ns, True)
    apic = yaml.safe_load(apic)

    if scaleDown:
        if "template" not in apic["spec"]:
            runKubernetesCommand('patch apiconnectcluster ' + topCRName + ' --type="json" --patch="[{\\"op\\": \\"add\\", \\"path\\": \\"/spec/template\\", \\"value\\": [{\\"enabled\\": false, \\"name\\":\\"mgmt-apim\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-apim-schema\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-apim-data\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-lur\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-lur-schema\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-lur-data\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-taskmanager\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-analytics-proxy\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-portal-proxy\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-juhu\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-websocket-proxy\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-billing\\"}]}]"', args.mgmt_ns, False)
        else:
            runKubernetesCommand('patch apiconnectcluster ' + topCRName + ' --type="json" --patch="[{\\"op\\": \\"replace\\", \\"path\\": \\"/spec/template\\", \\"value\\": [{\\"enabled\\": false, \\"name\\":\\"mgmt-apim\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-apim-schema\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-apim-data\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-lur\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-lur-schema\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-lur-data\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-taskmanager\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-analytics-proxy\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-portal-proxy\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-juhu\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-websocket-proxy\\"}, {\\"enabled\\": false, \\"name\\":\\"mgmt-billing\\"}]}]"', args.mgmt_ns, False)
    else:
        if "template" in apic["spec"]:
            runKubernetesCommand('patch apiconnectcluster ' + topCRName + ' --type="json" --patch="[{\\"op\\": \\"remove\\", \\"path\\": \\"/spec/template\\" }]"', args.mgmt_ns, False)

    while True:
        flag = False
        podsOutput = runKubernetesCommand("get pods --no-headers | grep Running", args.mgmt_ns, False)
        if podsOutput != None and podsOutput.lower().startswith("error") == False:
            if scaleDown:
                for eachService in mgmtServices:
                    if eachService in podsOutput:
                        print ("{} present in pods output".format(eachService))
                        flag = True
                        break
            else:
                for eachService in mgmtServices2:
                    if eachService not in podsOutput:
                        print ("{} NOT present in pods output".format(eachService))
                        flag = True
                        break
            if flag:
                print ("Sleeping for 120 seconds for the management services accessing postgres to scale..", time.asctime())
                time.sleep(120)
            else:
                break
    print ("ACTION OUTPUT : Management services that access postgres database are scaled.", time.asctime())
    
    if scaleDown:
        scalePostgresPGBouncer(scaleDown)


def scalePostgresPGBouncer(scaleDown=True):
    print ("Scaling postgres pgbouncer")
    #postgres pgbouncer scale
    deployments = runKubernetesCommand("get deployment", args.mgmt_ns)
    deploymentList = deployments.splitlines()
    for eachDeploy in deploymentList:
        if "postgres-pgbouncer" in eachDeploy:
            pgBouncerDeploymentName = eachDeploy[0:eachDeploy.index(" ")]
            if scaleDown:
                runKubernetesCommand('patch deploy ' + pgBouncerDeploymentName + ' --type="json" --patch="[{\\"op\\": \\"replace\\", \\"path\\": \\"/spec/replicas\\", \\"value\\": 0}]"', args.mgmt_ns)
            else:
                runKubernetesCommand('patch deploy ' + pgBouncerDeploymentName + ' --type="json" --patch="[{\\"op\\": \\"replace\\", \\"path\\": \\"/spec/replicas\\", \\"value\\": 1}]"', args.mgmt_ns)
            break
    time.sleep(45)


def scaleAPICOperator(replicas=0):
    print ("Scaling({}) APIC operator. timestmap : {} ".format(replicas, time.asctime()))
    namespace = "openshift-operators"
    apicCSV = runKubernetesCommand("get csv | grep ibm-apiconnect", namespace)
    if apicCSV != None and apicCSV.lower().startswith("error") == True:
        namespace = args.mgmt_ns
        apicCSV = runKubernetesCommand("get csv | grep ibm-apiconnect", namespace)
    apicCSVName = apicCSV[0:apicCSV.index(" ")]
    print ("Scaling apic operator deployment in CSV {} in namespace {}".format(apicCSVName, namespace))

    if replicas == 0:
        runKubernetesCommand('patch csv ' + apicCSVName + ' --type="json" --patch="[{\\"op\\": \\"replace\\", \\"path\\": \\"/spec/install/spec/deployments/0/spec/replicas\\", \\"value\\": 0}]"', namespace)
        while True:
            podsOutput = runKubernetesCommand("get pods --no-headers | grep Running", namespace, False)
            if podsOutput != None and podsOutput.lower().startswith("error") == False:
                if "ibm-apiconnect-" in podsOutput:
                    print ("api connect operator present in pods output. Sleeping for 120 seconds..", time.asctime())
                    time.sleep(120)
                else:
                    break
    elif replicas == 1:
        runKubernetesCommand('patch csv ' + apicCSVName + ' --type="json" --patch="[{\\"op\\": \\"replace\\", \\"path\\": \\"/spec/install/spec/deployments/0/spec/replicas\\", \\"value\\": 1}]"', namespace)
        while True:
            podsOutput = runKubernetesCommand("get pods --no-headers | grep Running", namespace, False)
            if podsOutput != None and podsOutput.lower().startswith("error") == False:
                if "ibm-apiconnect-" not in podsOutput:
                    print ("api connect operator not present in pods output. Sleeping for 120 seconds..", time.asctime())
                    time.sleep(120)
                else:
                    break
    else:
        sys.exit("Invalid replicas ({}) value provided for scaloing api connec operator.".format(replicas))


    print ("ACTION OUTPUT : Scaled apic operator.", time.asctime())

def resetGateways():
    print("START resetGateways() : restart gateway pods")

    if args.gw_ns == None:
        args.gw_ns = args.mgmt_ns
    multipleNS = args.gw_ns.split("|")
    podInfo = {}
    for ns in multipleNS:
        output = runKubernetesCommand("get statefulsets -l app.kubernetes.io/component=datapower --no-headers", ns, True)
        if output != None and output != "" and output.lower().startswith("error") == False:
            output = output.splitlines()
            for eachLine in output:
                eachLine = eachLine.strip()
                stsName = eachLine[0:eachLine.index(" ")]
                pods = runKubernetesCommand("get pods | grep " + stsName, ns, True)
                if pods != None and pods != "" and pods.lower().startswith("error") == False:
                    pods = pods.splitlines()
                    for eachPod in pods:
                        eachPod = eachPod.strip()
                        podName = eachPod[0:eachPod.index(" ")]
                        runKubernetesCommand("delete pod " + podName, ns, False)
                        if ns in podInfo:
                            podInfo[ns].append(podName)
                        else:
                            podInfo[ns] = [podName]
    print("Waiting for 3 minutes for gateway pods to be ready. Current time : ", time.asctime())
    time.sleep(180)

    print(podInfo)
    flag = True
    loopCount = 0
    timeout = False
    while flag:
        loopCount = loopCount + 1
        if loopCount >= 30:
            flag = False
            print ("Timeout after Waiting for gateways to be healthy")
            timeout = True
            break # safe break after 30 min
        ready = True
        for eachNS in podInfo:
            gwPodNames = podInfo[eachNS]
            for eachGWPodName in gwPodNames:
                crData = runKubernetesCommand("get gw " + eachGWPodName + " -o yaml", eachNS, True, 0, False)
                if crData != None and crData != "" and crData.lower().startswith("error") == False:
                    crData = yaml.safe_load(crData)
                    if crData["status"]["phase"] != "Running":
                        ready = False
                        break
            if ready == False: break

        if ready:
            print("Gateway(s) are healthy.")
            flag = False
            break
        else:
            print ("Waiting for gateway pods to be ready. Current time : ", time.asctime())
            time.sleep(60)


def resetPortals():
    mgmtSubsystemNames = config["management_subsystem"].keys()
    if len(mgmtSubsystemNames) > 1:
        print ()
        print ("List of management subsystems from the saved configuration(source system) : ", list(mgmtSubsystemNames))

        if args.silent:
            selectedSubsystem = args.mgmt_subsystem_name
        else:
            selectedSubsystem = input("SELECT THE SUBSYSTEM FROM THE LIST : ")

        if selectedSubsystem != None: selectedSubsystem = selectedSubsystem.strip()
        if selectedSubsystem not in config["management_subsystem"]:
            if args.silent and selectedSubsystem == None:
                print("Multiple management subsystems found in the saved configuration. You need to select one by using -mgmt_subsys_name or --mgmt_subsystem_name flag")
            print ("Time when error occurred :", time.asctime())
            sys.exit("The selected subsystem({}) does not exist in the configuration. Exiting...".format(selectedSubsystem))
    elif len(mgmtSubsystemNames) == 1:
        selectedSubsystem = list(mgmtSubsystemNames)[0]

    managementSubsystemDetails = config["management_subsystem"][selectedSubsystem]

    portalServices = getGatewayOrPortalServices("portal")
    print()
    print()
    portalReset = False
    for eachEndpoint in portalServices:
        if "registered_portals" in managementSubsystemDetails:
            portalsFromSouceSystem = managementSubsystemDetails["registered_portals"]
            if eachEndpoint in portalsFromSouceSystem: #old portal entry
                continue

        print("Resetting registered portal service with name : ", portalServices[eachEndpoint])
        out = runCommand("apic factory-reset:delete --mode portaladmin --execute_reset true --server " + cloudAdminServer + " --portal_service_endpoint " + eachEndpoint, False, 0, False)
        print ("Portal factory resest output : [[" + out + "]]")
        print()
        if out != None and out.lower().startswith("error") == False:
            portalReset = True
            time.sleep(30)
        else:
            sys.exit("Portal reset for portal service with name {}, endpoint {} failed with error, {}. Exiting...".format(portalServices[eachEndpoint], eachEndpoint, out))

        if portalReset:
            print("Waiting for 3 minutes. Current time : ", time.asctime())
            print("ACTION OUTPUT : login to portal admin pod and confirm that all portal sites are deleted(command : list_sites) before proceeding further.")
            time.sleep(180)
        else:
            print("ACTION OUTPUT : No new registered portals in management subsystem or no data to reset on the portal subsystem for this portal.")
    print("\n")


def loginAndResetPortal():
    global cloudAdminServer
    adminPassword = None
    
    if isCP4I:
        out1 = runKubernetesCommand("get apiconnectcluster.apiconnect.ibm.com --no-headers", args.mgmt_ns, True)
        if out1 != None and out1 != "":
            out1 = out1.strip()
            topCRName = out1[0:out1.index(" ")]
            print("top cr name : ", topCRName)

            if args.password == None or args.password  == "":
                adminSecret = runKubernetesCommand("get secret " + topCRName + "-mgmt-admin-pass -o yaml", args.mgmt_ns, False)
                adminSecret = yaml.safe_load(adminSecret)

                #saving to track the original value
                adminPassSecretFilename = DATA_TEMP_DIR + "/" + topCRName + "-mgmt-admin-pass_step4.yaml"
                if os.path.exists(adminPassSecretFilename) == False:
                    with open(adminPassSecretFilename, 'w') as f1:
                        yaml.dump(adminSecret, f1, default_flow_style=False)
                adminPassword = adminSecret["data"]["password"]
                adminPassword = base64.b64decode(adminPassword.encode('ascii'))
                adminPassword = adminPassword.decode('ascii').strip()
            else:
                print("Using password from flag -password.")
                adminPassword = args.password
                #update topCRName-mgmt-admin-pass secret with the actual cloud manager admin password of cloud manager LUR
                encodedPassword = base64.b64encode(adminPassword.encode('ascii'))
                encodedPassword = encodedPassword.decode("ascii")
                runKubernetesCommand('patch secret ' + topCRName + '-mgmt-admin-pass --patch="{\\"data\\":{\\"password\\":\\"'+encodedPassword+'\\"}}"', args.mgmt_ns, False)
                print("ACTION OUTPUT : Updated secret(" + topCRName + "-mgmt-admin-pass) with cloud manager password after restoring database.")
    else:
        adminPassword = args.password


    if args.server == None:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Exiting. This is either CP4I instance or -reset_gateway_portal flag ise set. Hostname to connect to cloud manager is NOT provided. Need this to factory reset portal subsystem. Use flag --server or -s to provide the hostname and try again.")
    
    if adminPassword == None:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Exiting. This is either CP4I instance or -reset_gateway_portal flag ise set. admin password is needed to connect to cloud manager. Need this to factory reset portal subsystem. Use flag --password or -p to provide the password and try again.")

    runCommand("apic login --realm admin/default-idp-1 --username admin --server " + args.server + " --password '" + adminPassword + "'", False, 1)
    cloudAdminServer = args.server

    print("Calling resetPortals()")
    resetPortals()


def getGatewayOrPortalServices(serviceName):
    if serviceName != "gateway" and serviceName != "portal":
        print ("Time when error occurred :", time.asctime())
        sys.exit("Invalid service name provided. Valid values are gateway or portal.")
    output = {}
    orgs = runCommand("apic orgs:list --org_type=admin --fields id,name --server " + cloudAdminServer, True)
    orgs = yaml.safe_load(orgs)
    for org in orgs["results"]:
        azones = runCommand("apic availability-zones:list --fields id,name --server " + cloudAdminServer + " --org " + org["name"], True)
        azones = yaml.safe_load(azones)
        for azone in azones["results"]:
            services = runCommand("apic " + serviceName + "-services:list --fields name,endpoint --server " + cloudAdminServer + " --org " + org["name"] + " --availability-zone " + azone["name"], True)
            services = yaml.safe_load(services)
            for service in services["results"]:
                output[service["endpoint"]] = service["name"]
    return output


def checkAndApplyCP4ICredsSecret():
    if "cp4i_registration_secret" in config["management_subsystem"][selectedMgmtSubsystemName]:
        print("Applying the same source system cp4i registration secret (topcr-cp4i-secret) on the target cp4i system.")
        cp4iCredsSecretName = runKubernetesCommand("get secret | grep cp4i-creds", args.mgmt_ns)
        if cp4iCredsSecretName != None and cp4iCredsSecretName != "":
            cp4iCredsSecretName = cp4iCredsSecretName.strip()
            cp4iCredsSecretName = cp4iCredsSecretName[0:cp4iCredsSecretName.index(" ")]
            srcFile = DATA_DIR + "/" + selectedMgmtSubsystemName + "/" + config["management_subsystem"][selectedMgmtSubsystemName]["cp4i_registration_secret"]
            targetFile = DATA_TEMP_DIR + "/" + cp4iCredsSecretName+".yaml"
            shutil.copyfile(srcFile, targetFile)

            # change secret name to what is used in the target
            cp4i_creds_secret = None
            if os.path.exists(targetFile):
                text_file3 = open(targetFile, "r")
                c3 = text_file3.read()
                cp4i_creds_secret = yaml.safe_load(c3)
                cp4i_creds_secret["metadata"]["name"] = cp4iCredsSecretName
                text_file3.close()
            with open(DATA_TEMP_DIR + "/" + cp4iCredsSecretName+".yaml", 'w') as updatedFile:
                yaml.dump(cp4i_creds_secret, updatedFile, default_flow_style=False)
            runKubernetesCommand("apply -f " + targetFile, args.mgmt_ns)


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


# start
def start():
    global isCP4I
    print ("CHECKING IF KUBECTL/OC EXIST IN THE PATH AND HAVE ACCESS TO THE CLUSTER :")
    runKubernetesCommand("version", "default")
    
    if args.skip_namespace_validation == False:
        validateNamespaces([args.mgmt_ns])

    if args.cp4i:
        isCP4I = True
        print("CP4I flag provided in the script.")
    else:
        #is this correct way?
        out = runKubernetesCommand("get crd | grep cp4i.ibm.com", "default", True, 1, False)
        print("check for cp4i.ibm.com api group")
        if out != None and out != "" and "cp4i.ibm.com" in out:
            isCP4I = True
    print("ACTION OUTPUT : is CP4I :", isCP4I)

    print()
    if isCP4I or args.reset_gateway_portal:
        loginAndResetPortal()
    
    if args.mgmt_ns == None or args.mgmt_ns == "" or  "|" in args.mgmt_ns:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Invalid namespace({}) provided for management subsystem. Only one namespace need to be provided. Exiting...".format(args.mgmt_ns))
    print("Checking health of management subsystem")
    healthCheck("mgmt", args.mgmt_ns)

    print("Loading management data of source system")
    loadManagementData()
    
    if isCP4I: 
        checkAndApplyCP4ICredsSecret()

    if isCP4I or args.reset_gateway_portal:
        #restart gw pods after management db restore
        resetGateways()
    
    print()
    print()
    print("This script performed the following actions in the target APIC system:")
    print("**********************************************************************")
    print("1. Checked the health of the manageemnt subsystem in the target APIC subsystem.")
    print("2. Restored the management database backup that was taken from the source APIC system.")
    print()
    print("Next steps:")
    print("1. Run the register_gateway_portals_in_target.py script to create the new gateways and portals using the mapping between old and new endpoints.")
    print("    -  Two ways to run the register_gateway_portals_in_target.py script")
    print("    -  Interactive mode : Prompts the user to enter the new endpoints corresponding to the old endpoints from gateway and portal.")
    print("    -  Silent mode : Using the -silent flag and the gateway_portal_mapping.yaml containing mapping between old and new endpoints. Correct values must be present in the yaml file.")
    print()
                	
    
    
    
	
parser = argparse.ArgumentParser(description="The script is used in form factor to form factor migration to restore a backup from source system management database\n\
into the target system management database. Users can restore using this script or using the management restore CR in api connect.\n \n\
Prerequisites ::\n\
1. Access to the cluster(target system) using kubectl or oc,\n\
2. Python 3.x and PyYAML module need to be installed\n\
3. This script must be run on the target APIC system after the management subsystem is up and running.\n\
4. The data directory where the configuration from the source system are saved. The data directory with source configuration must be present in the same directory as this script." , 
formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-n", "--namespace", dest = "ns", help="uses this namespace value for all subsystems if individual subsystem namespace is not provided.")
parser.add_argument("-mgmt_ns", "--management_namespace", dest = "mgmt_ns", help="namespace of the management subsystem. This has more precedence than the common flag, -n or --namespace.")

parser.add_argument("-gw_ns", "--gateway_namespace", dest = "gw_ns", help="namespace of the gateway subsystems. Used to reset gateway susbsystems when they are in multiple namespacces. If not privded, it is assumed the gateways are present in same namespace as management subsystem.")
parser.add_argument("-s", "--server", dest = "server", help="hostname to connect to cloud manager. Use platform api hostname. This is needed to need to factory reset portal subsystems.")
parser.add_argument("-p", "--password", dest = "password", help="password to connect to cloud manager using admin user. This is needed to need to factory reset portal subsystems when Kubernetes is the target cluster.")
parser.add_argument('-reset_gateway_portal', "--reset_gateway_portal", action='store_true', dest = "reset_gateway_portal", help='Restart gateway pods and factory reset portal subsystems.')

parser.add_argument('-ignore_health_check', "--ignore_health_check", action='store_true', dest = "ignore_health_check", help='ignores health check status for each subsystem and proceeds.')

parser.add_argument('-skip_namespace_validation', "--skip_namespace_validation",  action='store_true', dest = "skip_namespace_validation", help='Skips validation of input namespaces.')

parser.add_argument('-silent', "--silent", action='store_true', dest = "silent", help='Does not prompt for additinal inputs and proceeds silently.')
parser.add_argument('-mgmt_subsys_name', "--mgmt_subsystem_name", dest = "mgmt_subsystem_name", help='If multiple management subsytems present in the configuration, the script will use this.')
parser.add_argument("-cp4i", "--cp4i",  action='store_true', dest = "cp4i", help="It is Cloud Pak for Integration cluster.")

parser.add_argument("-storage_class", "--storage_class", dest = "storage_class", help="Storage class used by the upgrade PVC.")
parser.add_argument("-registry_secret", "--registry_secret", dest = "registry_secret", help="Registry secret of the registry where the v2018 extract docker image is present. This is optional and need to be given if required for the download of the image.")
parser.add_argument("-load_image", "--load_image", dest = "load_image", help="The image value used to run load pod which loads v2018 management data into v10 postgres. This is optional and used to override default value.")
parser.add_argument("-nginx_image", "--nginx_image", dest = "nginx_image", help="temporarily use this to download the csv files.")
parser.add_argument("-load_storage_size", "--load_storage_size", dest = "load_storage_size", help="The storage request size used by the pvc in load pod. Default is 10 GB. You need to give the value as a number 10 or 20 etc.")

args = parser.parse_args()

print ("Start time :", time.asctime())
print ()

print ("Input namespace provided for all subsystems (-n or --namespace flag) : ", args.ns)
print ("Input namespace provided for management subsystem (-mgmt_ns or --management_namespace flag) : ", args.mgmt_ns)
print ("Input namespace where additional gateway subsystem are installed(-gw_ns or --gw_ns flag) : ", args.gw_ns)
print ()

print ("hostname to connect to cloud manager(-s or --server flag) : ", args.server)
print ()

print ("Reset gateway portal flag : (-reset_gateway_portal or --reset_gateway_portal flag) : ", args.reset_gateway_portal)
print ("Ignore health check status for each subsystem (-ignore_health_check or --ignore_health_check flag) : ", args.ignore_health_check)
print ()

print ("Storage class used to create the pvc used by extract job (-storage_class or --storage_class flag) : ", args.storage_class)
print ("Load image value. The load image will be downloaded from this location (-load_image or --load_image flag) : ", args.load_image)
print ("Registry secret used to download extract image from the registry. This is optional. (-registry_secret or --registry_secret flag) : ", args.registry_secret)
print ("Load PVC storage size (-load_storage_size or --load_storage_size flag) : ", args.load_storage_size)
print ("image used to upload csv to pvc needed for load job (-nginx_image or --nginx_image flag) : ", args.nginx_image)
print ()

print ("silent (-silent or --silent flag) : ", args.silent)
print ("Mangement subsystem name (-mgmt_subsys_name or --mgmt_subsystem_name flag) : ", args.mgmt_subsystem_name)
print ("is CP4I installation (-cp4i or --cp4i flag) : ", args.cp4i)
print ()

pwd = os.getcwd()
DATA_DIR = pwd + "/data"
DATA_TEMP_DIR = pwd + "/data/temp"

if args.mgmt_ns == None:
    print ("Management namespace (-mgmt_ns or --management_namespace flag) not provided. Defaulting to flag -n or --namespace if provided which is applicable for all subsystems.")
    args.mgmt_ns = args.ns

if args.mgmt_ns == None:
    print ("Time when error occurred :", time.asctime())
    sys.exit("ERROR : Namespace for the management subsystem not provided . Exiting...")

if args.storage_class == None:
    print ("Time when error occurred :", time.asctime())
    sys.exit("ERROR : Storage class used by the upgrade pvc cannot be null. Use flag -sc or --storage_class to provide the storage class. Exiting...")

if args.load_image == None:
    print ("Time when error occurred :", time.asctime())
    sys.exit("ERROR : Need to provide load image used to load the extracted csv into v10. Use flag -load_image or --load_image. Exiting...")


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

start();

print()
print ("End time :", time.asctime())