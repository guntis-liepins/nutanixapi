#!/usr/bin/env python
import sys 
import os
import json
from requests import Response
from nutanixapi.nutanixapi import NutanixAPI
import logging  
from getpass import getpass


URL="" #Prism API URL
cluster_uuid="" #Cluster UUID
#-----------------------------------------------------------------------------

username=input("Nutanix username:")
password=getpass("Nutanix password:")
max_results=99999       #limits maximum results. Not needed for small installs.
api=NutanixAPI(URL,username,password,"/tmp/nutanix_api.log",logging.DEBUG,False)
#and here we are practicing


print("### SUBNETS ###")
api.list_subnets() #list subnets
print("### IMAGES ###")
api.list_images() #list images
print("### PROJECTS ###")
api.list_projects() #list-projects
print("### VMS ###")
api.list_vms()
