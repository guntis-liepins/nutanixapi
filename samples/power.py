#!/usr/bin/env python/usr/bin/
import sys
import os
import json
import time
from requests import Response
from nutanixapi.nutanixapi import NutanixAPI
import logging
from getpass import getpass
from pathlib import Path

DBG=True
#LOG_FILE="c:\\temp\\nutanix_api.log" #windows
LOG_FILE="/tmp/nutanix_api.log" #linux

def main():
    current_path = Path(__file__).parent.resolve()
    template_dir=os.path.join(current_path,"templates")
    URL="" #Prism Central URL
    
    username=input("Nutanix username:")
    password=getpass("Nutanix password:")
    
    api=NutanixAPI(URL,username,password,LOG_FILE,logging.DEBUG,False)
    
    #poweron test
    vm_uuid=""
    poweron_response=api.vm_poweron(vm_uuid)
    (poweron_status_code,poweron_result_json)=process_response(poweron_response)
    continue_if_ok(poweron_status_code,"ERROR: VM power ON call failed")
    poweron_task_uuid=get_task_uuid(poweron_result_json)
    poweron_task_status=wait_for_task(api,poweron_task_uuid)
    continue_if_task_ok(poweron_task_status,"poweron task failed")

    #poweroff test
    poweron_response=api.vm_poweroff(vm_uuid)
    (poweron_status_code,poweron_result_json)=process_response(poweron_response)
    continue_if_ok(poweron_status_code,"ERROR: VM power ON call failed")
    poweron_task_uuid=get_task_uuid(poweron_result_json)
    poweron_task_status=wait_for_task(api,poweron_task_uuid)
    continue_if_task_ok(poweron_task_status,"poweron task failed")

    sys.exit(0) #great success

def get_task_uuid(result):
    try:
        task_uuid=result['status']['execution_context']['task_uuid']
    except IndexError:
        return None
    return task_uuid

def process_response(response):
    status_code=response.status_code
    if DBG: print(f"Status code:{status_code}")
    if status_code == 200 or status_code == 202:
        result=json.loads(response.content)
        if DBG: print(f"Result:{result}")
    else:
        result =None
    return(status_code,result)
    
def continue_if_ok(status_code,msg):
    """
    check API call status and if error exit further execution
    Args:
     status_code ([string]): status code from response
     msg ([string]): prints message in case of error
    """
    if not ( status_code == 200 or status_code == 202):
        print(msg)
        os.exit(-1)
    return True

def continue_if_task_ok(task_status,msg):
    """
    check task status and if error exit further execution
    Args:
     task_status ([string]): Nutanix API object instance    
     msg ([string]): prints message in case of error
    """
    if task_status != "SUCCEEDED":
        print(msg)
        os.exit(-1)
    return True

def wait_for_task(api,task_uuid):
    """
    waits for Nutanix task to finish
    Args:
     vm_name ([NutanixAPI Object]): Nutanix API object instance    
     task_uuid ([string]): Nutanix tasks UUID
    Returns: 
        task status  (SUCCEEDED or FAILED or smth else)
    """
    task_status="PENDING"
    while True:
        response_task=api.get_task_status(task_uuid)
        status_code_task=response_task.status_code
        result_json_task = json.loads(response_task.content)
        task_status=result_json_task['status']
        if DBG: print(f"Task {task_uuid} status {task_status}")
        #print(f'task_status:{task_status}')
        if not ( task_status == 'PENDING' or task_status =='RUNNING'):
            return task_status
            break
        time.sleep(1)


if __name__ == "__main__":
    main()