import requests
import ipaddress
import time
from requests.auth import HTTPBasicAuth
import sys
import json as jsonstuff

#baseurl = "http://10.31.0.54:8000"
#baseurl  = "http://127.0.0.1:8000"
baseurl   = "http://192.168.0.122:8000"
start_time = time.time()
auth = HTTPBasicAuth('stephan', 'mufflers' ) 

json = { "ipnet" : str(ipaddress.ip_network("70.50.41.0/24")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
if r.status_code != 200 :
   print("fail to add v4 in host test", r.status_code, r.content, json )   
   sys.exit()


json = { "ipnet" : str(ipaddress.ip_network("80.50.41.0/24")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : 'capped' }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
if r.status_code != 200 :
   print("fail to add v4 in host test", r.status_code, r.content, json, json2, json3, json4,json5 )   
   sys.exit()

print("ADD V4 host::::::")
# add v4 host
json = { "ip" : str(ipaddress.ip_address("70.50.41.1")) , "vrf": "nmnet", "hostname" : "something.somedomain.com" , "workspace" : "admin", "comment" : "This host should be decommed soon" }
r = requests.post( baseurl + "/hosts/", json = json, auth=auth )
if r.status_code != 200:
   print("Unable to add v4 host", r.status_code, r.content, json) 

print("ADD V4 negative test host::::::")
# negative test add v4 host on capped network
json = { "ip" : str(ipaddress.ip_address("80.50.41.1")) , "vrf": "nmnet", "hostname" : "something.somedomain.com" , "workspace" : "admin", "comment" : "This host should be decommed soon" }
r = requests.post( baseurl + "/hosts/", json = json, auth=auth )
if r.status_code == 200:
   print("Successful in adding host to capped network ", r.status_code, r.content, json) 

# get v4 host
ip = str(ipaddress.ip_address("70.50.41.1")) 
json_out = { "ip" : str(ipaddress.ip_address("70.50.41.1")) , "vrf": "nmnet", "workspace" : "admin", "hostname" : "something.somedomain.com", "comment" : "This host should be decommed soon" }
r = requests.get( baseurl + "/hosts/admin/nmnet/" + ip, json = json, auth=auth )
if r.status_code != 200:
   print("Unable to get v4 host", r.status_code, r.content, json) 
   sys.exit()
if jsonstuff.loads(r.content) != json_out:
   print("Unable to get v4 host\n",  r.content, " doesn't match\n", jsonstuff.loads(r.content)) 
   sys.exit()

# edit v4 host
json = { "ip" : str(ipaddress.ip_address("70.50.41.1")) , "vrf": "nmnet", "newvrf": "nmnet", "hostname" : "something.somedomain.com" , "workspace" : "admin", "comment" : "New Comment" }
r = requests.post( baseurl + "/hosts/edit", json = json, auth=auth )
if r.status_code != 200:
   print("Unable to edit v4 host", r.status_code, r.content, json) 



print("DELETE V4 host::::::")
# delte v4 host
json = { "ip" : str(ipaddress.ip_address("70.50.41.1")) , "vrf": "nmnet", "hostname" : "something.somedomain.com" , "workspace" : "admin", "comment" : "This host should be decommed soon" }
r = requests.delete( baseurl + "/hosts/", json = json, auth=auth )
if r.status_code != 200:
   print("Unable to delete v4 host", r.status_code, r.content, json)