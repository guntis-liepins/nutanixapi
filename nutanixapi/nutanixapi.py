import json
import os
import urllib3
urllib3.disable_warnings()  #for now
import requests     #https://requests.readthedocs.io/en/master/
from base64 import b64encode
import logging
from jinja2 import Template 
import humanfriendly

from urllib.parse import urlparse
from urllib.parse import urlencode

class NutanixAPI:
    def __init__(self,url,username,password,log_file,log_level,ssl_verify=True,max_results=99999):
        """
        Creates Nutanix API object
        Args:
            url ([string]): URL of API en dpoint
            username (string): username
            password ([string]): password
            log_file ([string]): logfile , where operations is logged
            log_level ([type]): logging.DEBUG/logging.WARNING/logging.INFO, 
            ssl_verify (bool, optional): SSL verification. Defaults to True.   #not implemented properly
            max_results (int, optional): maximum number of returned results. Defaults to 99999.
        """
        # Initialise the options.
        self.url = url
        self.username = username.replace('\n', '')
        self.password = password.replace('\n', '')
        self.ssl_verify=ssl_verify
        self.max_results=99999
        logging.basicConfig(filename=log_file,level=log_level,format='%(asctime)s %(message)s')
        if(self.ssl_verify==True):
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)      
        
    # Create a REST client session.
    def rest_call(self,method,sub_url,data=None):
        req_url = f'{self.url}/api/nutanix/v3/{sub_url}'            
        #request_url = 'https://10.99.134.250:9440/api/nutanix/v3/vms/list'
        try:
            encoded_credentials = b64encode(bytes(f'{self.username}:{self.password}',encoding='ascii')).decode('ascii')
            headers={}
            headers["Authorization"]=f'Basic {encoded_credentials}'
            headers["Content-Type"]="application/json"
            headers["Accept"]="application/json"
            headers["cache-control"]="no-cache"
            if method.upper() in {"POST"}: #need data
                encoded_data=json.dumps(data).encode('utf-8')
                logging.debug("rest_call url:")
                logging.debug(req_url)
                logging.debug("rest_call headers:")
                logging.debug(headers)
                logging.debug("rest_call data:")
                logging.debug(encoded_data)
                response = requests.request(method.upper(), req_url, data=encoded_data, headers=headers,verify=self.ssl_verify)
                logging.debug(f"rest_call response status code {response.status_code}")
                logging.debug("rest_call response:")
                logging.debug(response.json())
            elif method.upper() in {"GET"}: #does not need data
                logging.debug("rest_call GET url:")
                logging.debug(req_url)
                logging.debug("rest_call headers:")
                logging.debug(headers)
                response = requests.request(method.upper(),req_url,headers=headers,verify=self.ssl_verify)
                logging.debug(f"rest_call response status code {response.status_code}")
                logging.debug("rest_call response:")
                logging.debug(response.json())
            elif method.upper() in {"PUT"}: #does not need data
                encoded_data=json.dumps(data).encode('utf-8')
                logging.debug("rest_call PUT url:")
                logging.debug(req_url)
                logging.debug("rest_call headers:")
                logging.debug(headers)
                logging.debug("rest_call data:")
                logging.debug(encoded_data)
                response = requests.request(method.upper(), req_url, data=encoded_data, headers=headers,verify=self.ssl_verify)
                logging.debug(f"rest_call response status code {response.status_code}")
                logging.debug("rest_call response:")
                logging.debug(response.json())
            else:
                raise ValueError("Unsupported method") #will implement later
        except BaseException as ex:
             print(repr(ex))
        return response

    def _get_templ_path(self,template_dir,template_name):
        #template_dir=base=os.path.join(os.path.dirname(__file__),"templates")
        full_path=os.path.join(template_dir,template_name)
        return full_path

    def _read_file(self,path):
        """
        Read a cloud-init template from file.

        Args:
            path (String): path to the file
        """
        with open(path, 'r') as content_file:
            content = content_file.read()
        return content

    def _write_file(self,path,data):
        """
        Write data to a file
        use in debugging

        Args:
            path (String): path to the file
            data (String): data to save in file
        """
        with open(path, 'w') as f:
            f.write(data)
        
    def _prepare_user_data_managed(self,template_dir): 
        """
        Gets network configuration as  and creates cloud-init file
        which genereates proper configuration and encodes it for use in vm
        creation in Nutanix managed networks

        Args:
        """
        cloud_init_file=self._read_file(self._get_templ_path(template_dir,"cloud-init.yaml.j2"))
        return ""

    def _prepare_user_data_unmanaged(self,template_dir,net_cfg): 
        """
        Gets network configuration as dictionary and creates cloud-init file
        which genereates proper configuration and encodes it for use in vm
        creation in unmaged networks

        Args:
            network_cfg (Dict): Network configuration
                {
                ip_address
                prefix
                default_gw
                dns_server1
                dns_server2            
                dns_search
                }
        """
        cloud_init_file=self._read_file(self._get_templ_path(template_dir,"cloud-init-net.yaml.j2"))
        net_tmpl_file=self._read_file(self._get_templ_path(template_dir,"static.yaml.j2"))
        t_net=Template(net_tmpl_file)        #create jinja templates
        rendered_net_template=t_net.render(
                        ip_address=net_cfg['ip_address'],
                        prefix=net_cfg['prefix'],
                        default_gw=net_cfg['default_gw'],
                        dns_server1=net_cfg['dns_server1'],
                        dns_server2=net_cfg['dns_server2'],
                        dns_search=net_cfg['dns_search']
                        )
        #self._write_file("c:\\temp\\network_cfg.yaml",rendered_net_template)
        rendered_net_template_b64=b64encode(rendered_net_template.encode())
        t_ci=Template(cloud_init_file)
        b64_str=rendered_net_template_b64.decode('ascii')
        rendered_ci_template=t_ci.render(netplan_content=b64_str)
        #rendered_ci_template=t_ci.render(netplan_content=rendered_net_template)
        #self._write_file("c:\\temp\\user_data.yaml",rendered_ci_template)
        user_data=b64encode(rendered_ci_template.encode()).decode('ascii')
        return user_data

    def list_clusters_screen(self):
         data={
             "kind":"cluster",
             "length":self.max_results
             }   
         response=self.rest_call('POST','clusters/list',data)
         if response.status_code == 200:
             self._print_entities(response)

    def list_clusters(self):
         data={
             "kind":"cluster",
             "length":self.max_results
             }   
         response=self.rest_call('POST','clusters/list',data)
         if response.status_code == 200:
             return(response)

    def list_images_screen(self):
         data={
             "kind":"image",
             "length":self.max_results
             }   
         response=self.rest_call('POST','images/list',data)
         if response.status_code == 200:
             self._print_entities(response)

    def list_images(self):
         data={
             "kind":"image",
             "length":self.max_results
             }   
         response=self.rest_call('POST','images/list',data)
         if response.status_code == 200:
             return(response)
    

    def get_image_uuid(self,image_name):
        data={
             "kind":"image",
             "length":self.max_results
             }   
        response=self.rest_call('POST','images/list',data)    
        return self._get_uuid_by_name(response,image_name) if response.status_code == 200 else False
    
    def list_subnets(self):
         data={
             "kind":"subnet",
             "length":self.max_results
             }   
         response=self.rest_call('POST','subnets/list',data)
         if response.status_code == 200:
            return(response)

    def list_subnets_screen(self):
         data={
             "kind":"subnet",
             "length":self.max_results
             }   
         response=self.rest_call('POST','subnets/list',data)
         if response.status_code == 200:
            self._print_entities(response)

    def get_subnet_uuid(self,subnet_name):
        data={
             "kind":"subnet",
             "length":self.max_results
             }   
        response=self.rest_call('POST','subnets/list',data)
        return self._get_uuid_by_name(response,subnet_name) if response.status_code == 200 else False
    
    def list_clusters(self):
         data={
             "kind":"cluster",
             "length":self.max_results
             }   
         response=self.rest_call('POST','clusters/list',data)
         if response.status_code == 200:
             self._print_entities(response) 
    
    def list_vms_screen(self):
         data={
             "kind":"vm",
             "length":self.max_results
             }   
         response=self.rest_call('POST','vms/list',data)
         if response.status_code == 200:
             self._print_entities(response) 

    def list_vms(self):
         data={
             "kind":"vm",
             "length":self.max_results
             }   
         response=self.rest_call('POST','vms/list',data)
         if response.status_code == 200:
             result_json = json.loads(response.content)
             return(result_json) 

    def list_projects(self):
         data={
             "kind":"project",
             "length":self.max_results
             }   
         response=self.rest_call('POST','projects/list',data)
         if response.status_code == 200:
             return(response) 

    def list_projects_screen(self):
         data={
             "kind":"project",
             "length":self.max_results
             }   
         response=self.rest_call('POST','projects/list',data)
         if response.status_code == 200:
             self._print_entities(response) 
    
    def get_current_user_uuid(self):
        """
        return uuid of current user in nutanix API
        """
        response=self.rest_call('GET','users/me')
        result_json = json.loads(response.content)  
        if response.status_code == 200:
           return result_json['metadata']['uuid']
        return False
    
    def create_vm_simple(self,
                  vm_name,
                  vm_description,
                  cluster_uuid,
                  project_uuid,
                  owner_uuid,
                  source_image_uuid,
                  subnet_uuid,
                  num_threads_per_core=1,
                  num_vcpus_per_socket=1,
                  num_sockets=1,
                  memory_size_mib=1024,
                  template_dir="./templates",
                  network_cfg=None
                  ):
        """
        Creates basic VM in nutanix
        VM is created from Nutanix image
        Args:
            vm_name ([string]): desired name of VM (hostname)
            vm_description ([string]): description of VM
            cluster_uuid ([string]): uuid of cluster where to deploy VM
            project_uuid ([string]): uuid of project which wjill own VM
            owner_uuid ([string]): uuid of VM owner(of creating user)
            source_image_uuid ([string]): OS image uuid 
            subnet_uuid ([uuid]): uuid of vm subnet 
            num_threads_per_core (int, optional): Number of threads per CPU. Defaults to 1.
            num_vcpus_per_socket (int, optional): Numbers of vcpu per socker. Defaults to 1.
            num_sockets (int, optional): Number of CPU sockets. Defaults to 1.
            memory_size_mib (int, optional): How much memory VM will get. Defaults to 1024.
            network_cfg(Dictionary,optional)=None: network configuraton

            Thre are three cases in Nutanix:
                network_cfg = None
                              Assign ip address automatically DHCP. 
                              Must be used by only on networks managed by nutanix.
                network_cfg (String) = ip_address
                              Assign specified ip_address. 
                              Sets specified IP address using Nutanix. Netmask and gatway is 
                              inherited from network definition 
                              Must be used by networks managed by nutanix,otherwise it will fail.
                              (with error Cannot assign IP address in unmanaged network)
                network_cfg (Dictionary) = 
                                { ip_address  (String)
                                  prefix (String)
                                  default_gw (String)
                                  dns_server1 (String)
                                  dns_server2 (String)   
                                  dns_search  (String)
                                }
                               Sets network according to dictionary.
                               Must be used for networks not managed by Nutanix 
                              
        Returns:
            None: Response object
        """
        if network_cfg is None:  #if no IP address is not specified , using DHCP
            user_data=self._prepare_user_data_managed()
            ip_endpoint_list=[{ "ip_type":"DHCP" }]
        elif isinstance(network_cfg,str):    #if parameter is simple string
            user_data=self._prepare_user_data_managed(network_cfg)
            ip_endpoint_list=[{
	            "ip": network_cfg, #!!! need validation or exception?
                "type": "ASSIGNED"
            }]
        elif isinstance(network_cfg,dict):
            user_data=self._prepare_user_data_unmanaged(network_cfg)
            ip_endpoint_list=[{ "type": "ASSIGNED"}]
        else:   #error
            return False

        data = {
                "spec": {
                    #"api_version": "3.1.0",
                    "name": vm_name,
                    "description": vm_description,
                    "resources": {
                        "num_threads_per_core": num_threads_per_core,
                        "memory_size_mib": memory_size_mib,
                        "disk_list":[{
                            "device_properties":{
                                "device_type":"DISK",
                                "disk_address": 
                                    {
                                    "device_index": 0,
                                    "adapter_type": "SCSI"
                                    }
                                },
                            "data_source_reference": {
                                    "kind": "image",
                                    "uuid": source_image_uuid
                                    }
                                 },
                                    {
                                    "device_properties":{
                                        "disk_address": {
                                            "adapter_type": "IDE",
                                            "device_index": 1
                                        },
                                        "device_type":"CDROM"
                                    }}
                        ], #end disk list
                    
                    "num_vcpus_per_socket": num_vcpus_per_socket,
                    "num_sockets": num_sockets,
                    "nic_list":[{
                            "nic_type":"NORMAL_NIC",
                            "is_connected": True,
                            "ip_endpoint_list":ip_endpoint_list,
                            "subnet_reference":{
                                "kind":"subnet",
                                "uuid": subnet_uuid
                            }
                        }],
                    "guest_tools":{
				                    "nutanix_guest_tools":{
					                    "state":"ENABLED",
					                    "iso_mount_state":"MOUNTED"
                                        }
				    },
                    "guest_customization": {
				        "cloud_init": {
                            "user_data": user_data
				        },
				    "is_overridable": False
			        },
                    }, #end respources
                    "cluster_reference": {
                        "kind": "cluster",
                        "uuid": cluster_uuid
                    }
                    }, #end spec
                "metadata": {
                    "kind": "vm",
                    "project_reference": {
                        "kind": "project",
                        "uuid": project_uuid
                        },
                    "owner_reference": {
                        "kind": "user",
                        "uuid": owner_uuid
                        },
                    #"categories": {},
                    "name": vm_name
                }
        
                }
        logging.debug("create_vm_simple data:")
        logging.debug(data)
        response=self.rest_call('POST','vms',data)
        if response.status_code == 200 or response.status_code == 202:
            logging.debug("create_vm_simple call success")
            return response
        logging.debug("create_vm_simple call failed")
        logging.debug(repr(response))
        return False 

    def _get_uuid_by_name(self,response,search_name):
        """
        Goes through entities returned in response
        If finds entity which name mathes search_name return uuid of this entity
        If many entities match search_criteria - it is error and false is returned
        Args:
            response:
            search_name: string 
        Returns:
            string: with uuid of named entity
        """
        uuid=False
        try:
            result_json = json.loads(response.content)  
            search_result=list(filter(lambda x: x['spec']['name'] == search_name,result_json['entities']))
            if len(list(search_result))==1:
                uuid=search_result[0]['metadata']['uuid']
            else:   
                uuid=False    #not found or duplicates
        except json.JSONDecodeError as ex:
            print("Invalid json")
            print(f"Content: {response.content}")
            uuid=False
        except BaseException as ex:   #in case of ANY error , image is not found return False
            print("Unknown exception")
            print(f"{repr(ex)}")
            uuid=False
        return uuid

    def _print_entities(self,response):
        """
        prints basic attributes for entities from respones
        using for exploration and testing
        Args:
            response requests.Response: response received from web server
        """
        result_json = json.loads(response.content)
        for entity in result_json['entities']:
            print(f"spec_name: {entity['spec']['name']} ent_name: {entity['status']['name']} uuid: {entity['metadata']['uuid']}")
            

    def get_vm(self,vm_uuid):
        #"bebb4394-0073-4864-9c67-29db86e1c77d"
        
        data={
             "kind":"vm",
             "length":self.max_results,
             }   
        logging.debug("get_vm data:{repr(data)}")
        request_url='vms/%s' % vm_uuid 
        logging.debug(f"request_url: {request_url}")
        response=self.rest_call('GET',request_url,data)
        result_json=None
        if response.status_code == 200:
            result_json = json.loads(response.content ,encoding='utf-8')
        return result_json

    

    def get_disk0(self,vm_uuid):
        """
        from device list filter out device of type SCSI and device index 0
        which must be system disk
        Args:
            vm_uuid String: UUID of VM

        returns: 
            dictinary of disk object
            as Example:
            {
            'uuid':  'e194e540-d3b6-4668-a19f-bf98cb0ba140',
            'disk_size_bytes':  2361393152,
            'storage_config':  { 'storage_container_reference':  {'kind':  'storage_container','uuid':  '527ce9b6-a154-4f31-85b3-6fc7cfd2db44','name':  'SelfServiceContainer'}},
            'device_properties':  {'disk_address':  {'device_index':  0,'adapter_type':  'SCSI'},'device_type':  'DISK'},
            'data_source_reference':  {'kind':  'image','uuid':  'd7024166-9d1e-4e49-a424-864b04f1f836'},
            'disk_size_mib':  2252
            }
        """
        def disk0_filter(x):
            if (x['device_properties']['disk_address']['device_index'] == 0 and 
                x['device_properties']['disk_address']['adapter_type'] == 'SCSI' and
                x['device_properties']['device_type'] == 'DISK' ):
                return x
                
        logging.debug(f"get_disk0: vm_uuid:{vm_uuid}")
        result=self.get_vm(vm_uuid)
        if result == False:
            return None
        disk_list=result['status']['resources']['disk_list']
        disk0=list(filter(disk0_filter,disk_list)).pop()
        logging.debug(f"disk0: {disk0['uuid']}")
        return disk0['uuid']

    def get_disk_address(self,vm_uuid,disk_uuid):
        def disk_filter(x): #filter func
            if x['uuid']==disk_uuid:
                return x
                
        
        result=self.get_vm(vm_uuid)
        if result == False:
            return None
        disk_list=result['status']['resources']['disk_list']
        disk=list(filter(disk_filter,disk_list)).pop()
        logging.debug(f"disk: {disk}")
        disk_address=disk['device_properties']['disk_address']
        logging.debug(f"disk address: {disk_address}")
        return disk_address

    # def set_disk_size(self,vm_uuid,disk_uuid,disk_address,new_size_bytes):
    #     data={ "updateSpec":
    #             {"vmDiskClone":
    #                 {
    #                 "minimumSize":new_size_bytes,
    #                 "vmDiskUuid":disk_uuid
    #                 }
    #             }
    #     }
    #     json_data=json.dumps(data)
    #     urlencoded_diskaddress=urlencode(disk_address)
    #     url=f"vms/{vm_uuid}/disks/{urlencoded_diskaddress}"
    #     response=self.rest_call('PUT',url,data)
    #     return response
    def resize_vm_disk(self,vm_uuid,disk_uuid,new_size):
        # https://www.nutanix.dev/2019/12/06/put-that-down-updating-a-vm-with-prism-central-v3-api/
        logging.debug(f"resize_vm_disk vm_uuid:{vm_uuid} disk_uuid:{disk_uuid} new_size:{new_size}")
        new_size_in_bytes=humanfriendly.parse_size(new_size)
        vm_data_json=self.get_vm(vm_uuid)
        logging.debug(f"vm_data_json:{json.dumps(vm_data_json)}")
        spec=vm_data_json['spec']
        disk_list=spec['resources']['disk_list']
        logging.debug(f"spec before update:{json.dumps(spec)}")
        #find index of disk in spec by uuid
        idx=-1
        for temp_idx in range(0,len(disk_list)):
            if disk_list[temp_idx]['uuid'] == disk_uuid:
                idx=temp_idx
        disk_list[idx]['disk_size_bytes']=new_size_in_bytes
        spec_after=json.dumps(spec)
        logging.debug(f"spec after update:{json.dumps(spec)}")
        data={
             "api_version": "3.1",
             "spec": spec,
             "metadata": vm_data_json['metadata']
             }
        logging.debug(f"request data:{json.dumps(data)}")
        response=self.rest_call('PUT',f"vms/{vm_uuid}",data)
        return response
        
         
        
    def get_task_status(self,task_uuid):
        response=self.rest_call('GET',f"tasks/{task_uuid}")
        result_json = json.loads(response.content)
        return response

    def _vm_set_power_state(self,vm_uuid,power_state):
        #from https://www.nutanix.dev/2019/12/06/put-that-down-updating-a-vm-with-prism-central-v3-api/
        logging.debug(f"_vm_set_power_state vm_uuid:{vm_uuid} power_state:{power_state}")
        vm_data_json=self.get_vm(vm_uuid)
        logging.debug(f"vm_data_json:{json.dumps(vm_data_json)}")
        spec=vm_data_json['spec']
        spec["resources"]["power_state"]=power_state
        data={
                "api_version": "3.1",
                "spec": spec,
                "metadata": vm_data_json['metadata']
                }
        logging.debug(f"request data:{json.dumps(data)}")
        response=self.rest_call('PUT',f"vms/{vm_uuid}",data)
        return response

    def vm_poweron(self,vm_uuid):
        logging.debug(f"vm_poweron vm_uuid:{vm_uuid}")
        return self._vm_set_power_state(vm_uuid,'ON')

    def vm_poweroff(self,vm_uuid):
        logging.debug(f"vm_poweroff vm_uuid:{vm_uuid}")
        return self._vm_set_power_state(vm_uuid,'OFF')

#utilities
    @staticmethod
    def get_task_uuid(result):
        try:
            task_uuid=result['status']['execution_context']['task_uuid']
        except IndexError:
            return None
        return task_uuid

    @staticmethod
    def process_response(response):
        logging.debug(f"process_response response:{response}")
        status_code=response.status_code
        logging.debug(f"Status code:{status_code}")    
        if status_code == 200 or status_code == 202:
            result=json.loads(response.content)
            logging.debug(f"result:{result}")    
        else:
            result =None
        return(status_code,result)

    @staticmethod
    def continue_if_ok(status_code,msg):
        """
        check API call status and if error exit further execution
        Args:
        status_code ([string]): status code from response
        msg ([string]): prints message in case of error
        """
        if not ( status_code == 200 or status_code == 202):
            print(msg)
            os._exit(-1) #!!! have to think about cleanup
        return True

    @staticmethod
    def continue_if_task_ok(task_status,msg):
        """
        check task status and if error exit further execution
        Args:
        task_status ([string]): Nutanix API object instance
        msg ([string]): prints message in case of error
        """
        if task_status != "SUCCEEDED":
            print(msg)
            os._exit(-1) #!!! have to think about cleanup
        return True

    def wait_for_task(self,task_uuid):
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
            response_task=self.get_task_status(task_uuid)
            status_code_task=response_task.status_code
            if status_code_task==200 or status_code_task==202:
                result_json_task = json.loads(response_task.content)
                task_status=result_json_task['status']
                logging.debug(f"Task {task_uuid} status {task_status}")
            else:
                return('ERROR')
            if not ( task_status == 'PENDING' or task_status =='RUNNING'):
                return task_status
            time.sleep(1)   