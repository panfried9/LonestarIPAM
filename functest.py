import requests
import ipaddress
import time
from requests.auth import HTTPBasicAuth
import sys
import json as jsonstuff

baseurl = "http://192.168.0.122:8000"
start_time = time.time()
auth = HTTPBasicAuth('stephan', 'mufflers' ) 

# add user
json = { "newuser" : "tuffin", "newpass" : "blank123" }
r = requests.post( baseurl + "/users", json = json, auth=auth )
if r.status_code != 200 :
   print("fail add user ", r, json)
   sys.exit()

# add new workspace
json = { "wsname" : "eken_AB" }
r = requests.post( baseurl + "/workspaces", json=json, auth=auth) 
if r.status_code !=200 :
   print( "Failed to add new workspace ", r.content, json) 
   sys.exit()

# add new user to workspace
json = { "usertoadd" : "tuffin", "workspace" : "eken_AB" }
r = requests.post( baseurl + "/usersworkspaces", json=json, auth=auth) 
if r.status_code !=200 :
   print( "Failed to add user to workspace ", r.content, json) 
   sys.exit()

# delete user
r = requests.delete( baseurl + "/users", auth=HTTPBasicAuth('tuffin','blank123' ) ) 
if r.status_code == 200:
   print("fail delete user possible even when still member of workspace ", r.status_code, r.content )  
   sys.exit()

# delete user from workspace
json = { "workspace" : "eken_AB" }  
r = requests.delete( baseurl + "/usersworkspaces/", json=json, auth=HTTPBasicAuth('tuffin','blank123' ))
if r.status_code != 200:
   print("fail to delete user from workspace", json, r.status_code, r.content)
   sys.exit()


# add  v4 network
json = { "ipnet" : str(ipaddress.IPv4Address("20.20.20.0")) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json2 = { "ipnet" : str(ipaddress.IPv4Address("30.30.30.0")) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
r2= requests.post( baseurl + "/networks/", json = json2, auth=auth )
if r.status_code != 200 or r2.status_code != 200 :
   print("fail add v4", r, json, json2 )   
   sys.exit()


# add a v6 network
json = { "ipnet" : str(ipaddress.IPv6Address("2001:db8::")) , "mask" : "64", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json2 = { "ipnet" : str(ipaddress.IPv6Address("2001:db9::")) , "mask" : "64", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
r2 = requests.post( baseurl + "/networks/", json = json2, auth=auth )
if r.status_code != 200:
   print("fail add v6",  r, json) 
   sys.exit()

# get a v4 network
r = requests.get( baseurl + "/networks/nmnet/20.20.20.0/24" , auth=auth)
if r.status_code !=200:
   print("fail get v4", r) 
   sys.exit()


# get a v6 network
r = requests.get( baseurl + "/networks/nmnet/2001:db8::/64" , auth=auth)
if r.status_code !=200:
   print("fail get v6",  r)    
   sys.exit()

# delete v4 network
json = { "ipnet" : str(ipaddress.IPv4Address("30.30.30.0")) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin" }
r = requests.delete( baseurl + "/networks", json=json, auth=auth)  
if r.status_code !=200:
  print("fail delete v4 ",  r)
  sys.exit() 


# delete v6 network
json = { "ipnet" : str(ipaddress.IPv6Address("2001:db9::")) , "mask" : "64", "vrf": "nmnet", "workspace" : "admin" }
r = requests.delete( baseurl + "/networks", json=json, auth=auth)
if r.status_code !=200:
  print("fail delete v4 ",  r)
  sys.exit()

# write 5 x 256 networks
for b in range(0,5):
  for c in range(0,255):
    ip = "30."+str(b)+"."+str(c)+".0"
    json = { "ipnet" : str(ipaddress.IPv4Address(ip)) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
    r = requests.post( baseurl + "/networks", json = json, auth=auth )
    if r.status_code != 200:
       print( r, json)  

# find overlaps on above 
r = requests.get( baseurl + "/networks/overlaps/admin/nmnet/30.0.0.0/8", auth=auth)
if r.status_code !=200:
  print("failed to find overlaps v4 ",  r)
  sys.exit()
overlaps = jsonstuff.loads(r.content)
summar = len(overlaps["overlaps"]) - ((b+1) * (c+1))
if summar != 0:
  print("failed overlaps test, didn't return correct overlaps") 
  sys.exit()

# write 5 x 256 v6 networks
for b in range(0,5):
  for c in range(0,255):
    ip = "3001:"+str(b)+":"+str(c)+"::0"
    json = { "ipnet" : str(ipaddress.IPv6Address(ip)) , "mask" : "64", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
    r = requests.post( baseurl + "/networks", json = json, auth=auth )
    if r.status_code != 200:
       print( r, json)  

# find overlaps on above 
r = requests.get( baseurl + "/networks/overlaps/admin/nmnet/3001:0:0::/16", auth=auth)
if r.status_code !=200:
  print("failed to find overlaps v6 ",  r)
  sys.exit()
overlaps = jsonstuff.loads(r.content)
summar = len(overlaps["overlaps"]) - ((b+1) * (c+1))
if summar != 0:
  print("failed overlaps test, didn't return correct overlaps on v6", summar) 
  sys.exit()


print("Total Exec time:", time.time() - start_time ) 
