import requests
import ipaddress
import time
from requests.auth import HTTPBasicAuth

baseurl = "http://192.168.0.122:8000"
addurl = "/net/"

start_time = time.time()
auth = HTTPBasicAuth('stephan', 'mufflers' ) 


# write 5 x 256 networks
for b in range(0,5):
  for c in range(0,255):
    ip = "10."+str(b)+"."+str(c)+".0"
    json = { "ipnet" : str(ipaddress.IPv4Address(ip)) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
    r = requests.post( baseurl + addurl, json = json, auth=auth )
    if r.status_code != 200:
       print( r, json)   

# get 5 x 256 networks 
for b in range(0,5):
  for c in range(0,255):
    ip = "10."+str(b)+"."+str(c)+".0"
    extraurl = "nmnet/" + ip + "/24"
    r = requests.get( baseurl + addurl + extraurl, auth=auth)
    if r.status_code !=200:
       print( r) 

 

print("Total Exec time:", time.time() - start_time ) 
