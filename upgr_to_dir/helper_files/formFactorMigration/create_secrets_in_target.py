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

subsystems = ("mgmt", "ptl", "gw", "a7s")



oc_client = "oc"
kubectl_client = "kubectl"
client = oc_client

pwd = None
DATA_DIR = None
DATA_TEMP_DIR = None
CONFIG_FILE_NAME = "config.yaml"
CONFIG_PORTAL_FILE_NAME = "config_portal.yaml"
config = None
config_portal = None

managementSecretsValidate = {
    "atm-cred": False, 
    "ccli-cred": False, 
    "cui-cred": False, 
    "dsgr-cred": False, 
    "juhu-cred": False, 
    "cli-cred": False, 
    "ui-cred": False
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
                    print ("Time when error occurred :", time.asctime())
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

    print ("CHECKING IF KUBECTL/OC EXIST IN THE PATH AND HAVE ACCESS TO THE CLUSTER :")
    runKubernetesCommand("version", "default")
    #print (config)
    #print (config_portal)
    
    print ("namespace used for management subsystem where the secrets are to be created: ", args.mgmt_ns)
    print ("namespace used for portal subsystem where the secrets are to be created: ", args.ptl_ns)
    print ("")
    
    if args.skip_namespace_validation == False:
        validateNamespaces([args.mgmt_ns, args.ptl_ns])

    if args.mgmt_ns != None and "|" in args.mgmt_ns:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Invalid namespace({}) provided for management subsystem. Only one namespace need to be provided. Exiting...".format(args.mgmt_ns))
    
    if args.ptl_ns != None and "|" in args.ptl_ns:
        print ("Time when error occurred :", time.asctime())
        sys.exit("ERROR : Invalid namespace({}) provided for portal subsystem. Only one namespace need to be provided. Exiting...".format(args.ptl_ns))
    
    if args.skip_mgmt == False:
        # management subsystem secrets	
        mgmtSubsystemNames = config["management_subsystem"].keys()
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
                sys.exit("ERROR : The selected subsystem({}) does not exist in the configuration. Exiting...".format(selectedSubsystem))
            
        elif len(mgmtSubsystemNames) == 1:
            selectedSubsystem = list(mgmtSubsystemNames)[0]
        
        if selectedSubsystem != None and args.mgmt_ns != None:
            mgmtSubsystemDetails = config["management_subsystem"][selectedSubsystem]
            print ("selected management subsystem from the source configuration : ", selectedSubsystem)
                        
            print()
            print ("management subsystem namespace for creating secrets : ", args.mgmt_ns)
            print()


            # check if management encryption secret exist
            if "encryptionSecret" not in mgmtSubsystemDetails:
                print ("Time when error occurred :", time.asctime())
                sys.exit("ERROR : {} does not exist in the configuration for the management subsystem with name {}. Exiting...".format("encryptionSecret", selectedSubsystem))
            secretFile = DATA_DIR + "/" + selectedSubsystem + "/" + mgmtSubsystemDetails["encryptionSecret"]["secretName"] + ".yaml"
            if os.path.exists(secretFile) == False:
                print ("Time when error occurred :", time.asctime())
                sys.exit("ERROR :  Secret file({}) does not exist for the secret({}) in the data directory. Selected management subsystem is {}. Exiting...".format(secretFile, mgmtSubsystemDetails["encryptionSecret"]["secretName"], selectedSubsystem))

            #management encryption  secret
            runKubernetesCommand("apply -f " + secretFile, args.mgmt_ns)

            versionReconciled = None
            if "versionReconciled" in mgmtSubsystemDetails:
                versionReconciled = mgmtSubsystemDetails["versionReconciled"]
            print ("version reconciled : ", versionReconciled)
            
            if versionReconciled != None and versionReconciled.startswith("10."):
                # check if application credentials exist
                if "customApplicationCredentials" not in mgmtSubsystemDetails:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("{} does not exist in the configuration for the management subsystem with name {}. Exiting...".format("customApplicationCredentials", selectedSubsystem))
                else:
                    for each in mgmtSubsystemDetails["customApplicationCredentials"]:
                        if "name" in each and "secretName" in each:
                            secretFile = DATA_DIR + "/" + selectedSubsystem + "/" + each["secretName"] + ".yaml"
                            if os.path.exists(secretFile) == False:
                                print ("Time when error occurred :", time.asctime())
                                sys.exit("ERROR : Secret file({}) does not exist for the secret({}) in the data directory. Selected management subsystem is {}. Exiting...".format(secretFile, each["name"], selectedSubsystem))
                            else:
                                if each["name"] in managementSecretsValidate:
                                    managementSecretsValidate[each["name"]] = True
                
                for each in managementSecretsValidate:
                    if managementSecretsValidate[each] == False:
                        print ("Time when error occurred :", time.asctime())
                        sys.exit("ERROR : {} does not exist in the configuration for the management subsystem with name {}. Exiting...".format(each, selectedSubsystem))

                #create application credentials secrets
                for each in mgmtSubsystemDetails["customApplicationCredentials"]:
                    secretFile = DATA_DIR + "/" + selectedSubsystem + "/" + each["secretName"] + ".yaml"
                    runKubernetesCommand("apply -f " + secretFile, args.mgmt_ns)
            else:
                print ("ACTION OUTPUT : customApplicationCredentials not found. Looks like source environment is v2018. Source version : ", versionReconciled)
                print()

            # condition for RI stack(management backup not present in RI stack)
            if "databaseBackup" in mgmtSubsystemDetails and "credentials" in mgmtSubsystemDetails["databaseBackup"]:
                dbBackupSecretFile = DATA_DIR + "/" + selectedSubsystem + "/" + mgmtSubsystemDetails["databaseBackup"]["credentials"] + ".yaml"
                if os.path.exists(secretFile) == False:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : Secret file({}) does not exist for the secret({}) in the data directory. Selected management subsystem is {}. Exiting...".format(dbBackupSecretFile, mgmtSubsystemDetails["databaseBackup"]["credentials"], selectedSubsystem))

                #management db backup credentials secret
                runKubernetesCommand("apply -f " + dbBackupSecretFile, args.mgmt_ns)

        else:
            print ("ACTION OUTPUT : Not applying secrets in target namespace for management subsystem. check values for source management subsystem name : {} and target management subsytem namespace : {}".format(selectedSubsystem, args.mgmt_ns))
    else:
        print("ACTION OUTPUT : Skipped creating secrets for management subsystem as skip_mgmt/skip_mamangement flag is set.")
        
        
    if args.skip_ptl == False:
        if config_portal != None:
            # portal subsystem secrets	
            portalSubsystemNames = config_portal["portal_subsystem"].keys()
            selectedSubsystem = None
            if len(portalSubsystemNames) > 1:
                print ()
                print ("List of portal subsystems from the saved configuration(source system) : ", list(portalSubsystemNames))
                if args.silent:
                    selectedSubsystem = args.ptl_subsystem_name
                else:
                    selectedSubsystem = input("SELECT THE SUBSYSTEM FROM THE LIST : ")
                
                if selectedSubsystem != None: selectedSubsystem = selectedSubsystem.strip()
                if selectedSubsystem not in config_portal["portal_subsystem"]:
                    if args.silent and selectedSubsystem == None:
                        print("Multiple portal subsystems found in the saved configuration. You need to select one by using -ptl_subsys_name or --ptl_subsystem_name flag")
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : The selected subsystem({}) does not exist in the configuration. Exiting...".format(selectedSubsystem))
                    
            elif len(portalSubsystemNames) == 1:
                selectedSubsystem = list(portalSubsystemNames)[0]
        
            if selectedSubsystem != None and args.ptl_ns != None:
                portalSubsystemDetails = config_portal["portal_subsystem"][selectedSubsystem]
                print ("selected portal subsystem from the source configuration : ", selectedSubsystem)
                    
                print()
                print ("portal subsystem namespace for creating secrets : ", args.ptl_ns)
                print()
            
                # check if portal encryption secret exist
                if "encryptionSecret" not in portalSubsystemDetails:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("{} does not exist in the configuration for the portal subsystem with name {}. Exiting...".format("encryptionSecret", selectedSubsystem))
                secretFile = DATA_DIR + "/" + selectedSubsystem + "/" + portalSubsystemDetails["encryptionSecret"]["secretName"] + ".yaml"
                if os.path.exists(secretFile) == False:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : Secret file({}) does not exist for the secret({}) in the data directory. Selected portal subsystem is {}. Exiting...".format(secretFile, portalSubsystemDetails["encryptionSecret"]["secretName"], selectedSubsystem))
    	
                #portal encryption secret
                runKubernetesCommand("apply -f " + secretFile, args.ptl_ns)
                	
                if ("portalBackup" not in portalSubsystemDetails) or ("credentials" not in portalSubsystemDetails["portalBackup"]) :
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("{} does not exist in the configuration for the portal subsystem with name {}. Exiting...".format("portalBackup/credentials", selectedSubsystem))
                secretFile = DATA_DIR + "/" + selectedSubsystem + "/" + portalSubsystemDetails["portalBackup"]["credentials"] + ".yaml"
                if os.path.exists(secretFile) == False:
                    print ("Time when error occurred :", time.asctime())
                    sys.exit("ERROR : Secret file({}) does not exist for the secret({}) in the data directory. Selected portal subsystem is {}. Exiting...".format(secretFile, portalSubsystemDetails["portalBackup"]["credentials"], selectedSubsystem))    

            
                #portal db backup credentials secret
                runKubernetesCommand("apply -f " + secretFile, args.ptl_ns)
    	
            else:
                print ("ACTION OUTPUT : Not applying secrets in target namespace for portal subsystem. Check values for source portal subsystem name : {} and target portal subsystem namespace : {}".format(selectedSubsystem, args.ptl_ns))
        else:
            print ("ACTION OUTPUT : Sources system portal configuration not found. Not creating secrets for portal subsystem")
    else:
        print("ACTION OUTPUT : Skipped creating secrets for portal subsystem as skip_ptl/skip_portal flag is set.")
    
    print()
    print()
    print("This script performed the following actions in the target cluster:")
    print("******************************************************************")
    print("1. Created the database backup credentials secret.")
    print("2. Created the custom application credentials and other secrets.")
    print()
    print("Next steps:")
    print("1. Install the target APIC cluster.")
    print("    -  If target cluster is OCP/CP4I, you can use the install_apic_on_ocp.py script to install or install manually (for advanced configurations) from OCP or CP4I UI.")
    print("    -  Its recommended to install the target system manually for customizing the configuration.")
    print("    -  For other form factors, install APIC manually in the target cluster.")
    print()
    print("Note : If installing manually, make sure the configuration from source system saved in data/config.yaml and data/config.portal_yaml is used while installing the target APIC cluster.")
    print("    -  For management subsystem : customApplicationCredentials, databaseBackup, encryptionSecret, name, originalUID and siteName.")
    print("    -  For portal subsystem : portalBackup, encryptionSecret, name, originalUID and siteName.")
    print()
	
parser = argparse.ArgumentParser(description="The script is used in form factor to form factor migration. The secrets obtained from the source system for management and portal subsystems \n\
are created in the target system in the specified namespace. The script has to be run once the namespace is created and before API Connect is installed.\n\n\
Prerequisites ::\n\
1. Access to the cluster(target system) using kubectl or oc,\n\
2. Python 3.x and PyYAML module need to be installed\n\
3. The data directory where the secrets from the source system are saved. The data directory with source configuration must be present in the same directory as this script.", 
formatter_class=argparse.RawDescriptionHelpFormatter)


parser.add_argument("-n", "--namespace", dest = "ns", help="uses this namespace value for all subsystems if individual subsystem namespace is not provided.")
parser.add_argument("-mgmt_ns", "--management_namespace", dest = "mgmt_ns", help="namespace of the management subsystem. This has more precedence than the common flag, -n or --namespace.")
parser.add_argument("-ptl_ns", "-portal_namespace", dest = "ptl_ns", help="namespace of the portal subsystem. This has more precedence than the common flag, -n or --namespace.")
parser.add_argument('-skip_mgmt', "--skip_management", action='store_true', dest = "skip_mgmt", help='Skips applying secrets for management subsystem.')
parser.add_argument('-skip_ptl', "--skip_portal",  action='store_true', dest = "skip_ptl", help='Skips applying secrets for portal subsystem.')

parser.add_argument('-skip_namespace_validation', "--skip_namespace_validation",  action='store_true', dest = "skip_namespace_validation", help='Skips validation of input namespaces.')

parser.add_argument('-silent', "--silent", action='store_true', dest = "silent", help='Does not prompt for additinal inputs and proceeds silently.')
parser.add_argument('-mgmt_subsys_name', "--mgmt_subsystem_name", dest = "mgmt_subsystem_name", help='If multiple management subsytems present in the configuration, the script will use this.')
parser.add_argument('-ptl_subsys_name', "--ptl_subsystem_name", dest = "ptl_subsystem_name", help='If multiple portal subsytems present in the configuration, the script will use this.')

args = parser.parse_args()

print ("Start time :", time.asctime())
print ()

print ("Input namespace provided for all subsystems (-n or --namespace flag) : ", args.ns)
print ("Input namespace provided for management subsystem (-mgmt_ns or --management_namespace flag) : ", args.mgmt_ns)
print ("Input namespace provided for portal subsystem (-ptl_ns or --portal_namespace flag) : ", args.ptl_ns)
print ()

print ("skip creating secrets for management subsystem (-skip_mgmt or --skip_management flag) : ", args.skip_mgmt)
print ("skip creating secrets for portal subsystem  (-skip_ptl or --skip_portal flag) : ", args.skip_ptl)
print ()

print ("silent (-silent or --silent flag) : ", args.silent)
print ("Mangement subsystem name (-mgmt_subsys_name or --mgmt_subsystem_name flag) : ", args.mgmt_subsystem_name)
print ("Portal subsystem name (-ptl_subsys_name or --ptl_subsystem_name flag) : ", args.ptl_subsystem_name)
print ()


if args.mgmt_ns == None:
    print ("management namespace not provided. Defaulting to flag -n or --namespace if provided which is applicable for all subsystems.")
    args.mgmt_ns = args.ns

if args.ptl_ns == None:
    print ("portal namespace not provided. Defaulting to flag -n or --namespace if provided which is applicable for all subsystems.")
    args.ptl_ns = args.ns

print ()
print ("namespace used for management subsystem : ", args.mgmt_ns)
print ("namespace used for portal subsystem : ", args.ptl_ns)
print ()

pwd = os.getcwd()
DATA_DIR = pwd + "/data"
DATA_TEMP_DIR = pwd + "/data/temp"

# load config data if exists
if os.path.exists(DATA_DIR + "/" + CONFIG_FILE_NAME):
    print ("Source APIC system configuration file exists. Loading it")
    text_file = open(DATA_DIR + "/" + CONFIG_FILE_NAME, "r")
    config1 = text_file.read()
    print("management configuration file : ", config1)
    config = yaml.safe_load(config1)
    text_file.close()
else:
    print ("Time when error occurred :", time.asctime())
    sys.exit("ERROR : config.yaml file with details of the source APIC system in NOT present in the data directory. Exiting...")

print()
if os.path.exists(DATA_DIR + "/" + CONFIG_PORTAL_FILE_NAME):
    print ("Source APIC system portal configuration file exists. Loading it")
    text_file2 = open(DATA_DIR + "/" + CONFIG_PORTAL_FILE_NAME, "r")
    config2 = text_file2.read()
    print("portal configuration : ", config2)
    config_portal = yaml.safe_load(config2)
    text_file2.close()
else:
    print ("portal configuration from source system not existing.")
print()
    
start();

print()
print ("End time :", time.asctime())