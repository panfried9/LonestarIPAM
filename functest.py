import requests
import ipaddress
import time
from requests.auth import HTTPBasicAuth
import sys
import json as jsonstuff

#baseurl = "http://192.168.0.122:8000"
baseurl  = "http://127.0.0.1:8000"
start_time = time.time()
auth = HTTPBasicAuth('stephan', 'mufflers' ) 

# add user
json = { "newuser" : "tuffin", "newpass" : "blank123" }
#json = { "newuser" : "tuffinuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu", "newpass" : "blank123" }

r = requests.post( baseurl + "/users", json = json, auth=auth )
if r.status_code != 200 :
   print("fail add user ", r.content, json)
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
json3 = { "ipnet" : str(ipaddress.IPv4Address("60.50.40.0")) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json4 = { "ipnet" : str(ipaddress.IPv4Address("60.50.41.0")) , "mask" : "24", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }


r = requests.post( baseurl + "/networks/", json = json, auth=auth )
r2= requests.post( baseurl + "/networks/", json = json2, auth=auth )
r3= requests.post( baseurl + "/networks/", json = json3, auth=auth )
r4= requests.post( baseurl + "/networks/", json = json4, auth=auth )
if r.status_code != 200 or r2.status_code != 200 or r3.status_code != 200 or r4.status_code != 200:
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
r = requests.get( baseurl + "/networks/admin/nmnet/20.20.20.0/24" , auth=auth)
if r.status_code !=200:
   print("fail get v4", r) 
   sys.exit()


# get a v6 network
r = requests.get( baseurl + "/networks/admin/nmnet/2001:db8::/64" , auth=auth)
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

# split v4 network
# first add a network that we can later split
ip = "40.40.0.0"
json = { "ipnet" : str(ipaddress.IPv4Address(ip)) , "mask" : "16", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks", json = json, auth=auth )
if r.status_code != 200:
   print("failed to add", r, json)  
   sys.exit()
# now split that network 
json2 = { "ipnet" : str(ipaddress.IPv4Address("40.40.0.0")) , 
         "mask" : "16", 
         "vrf": "nmnet",
         "workspace" : "admin",  
         "excludeip" : str(ipaddress.IPv4Address("40.40.40.0")),
         "excludemask" : "24" }
r = requests.post( baseurl + "/networks/split", json = json2, auth=auth )
if r.status_code != 200:
   print("failed to split ", r.content, json)  
   sys.exit()
#print( r.content )
expected_results = ["40.40.128.0/17","40.40.64.0/18","40.40.0.0/19","40.40.48.0/20","40.40.32.0/21","40.40.44.0/22","40.40.42.0/23","40.40.41.0/24","40.40.40.0/24"] 
newnets = jsonstuff.loads(r.content)
if newnets["networks"] != expected_results :
    print("Return list doesn't match expectattion")
    sys.exit()

# summarize v4 network
json= { "ipnets" : [ "60.50.40.0/24", "60.50.41.0/24" ], "vrf" : "nmnet" , "workspace" : "admin" }
r = requests.post( baseurl + "/networks/summarize", json = json, auth=auth )
if r.status_code != 200:
   print("error summarizing", r.content, json) 
   sys.exit()
sumnet = jsonstuff.loads(r.content) 
expected_results = ["60.50.40.0/23"]   
if sumnet["networks" ] != expected_results:
   print("Unexpected result from summarizing", r.content, json) 
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
  print("failed overlaps v4 test, didn't return correct overlaps ", overlaps["overlaps"], r.content) 
  sys.exit()

# write 5 x 256 v6 networks
for b in range(0,5):
  for c in range(0,255):
    ip = "3001:"+str(b)+":"+str(c)+"::0"
    json = { "ipnet" : str(ipaddress.IPv6Address(ip)) , "mask" : "64", "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
    r = requests.post( baseurl + "/networks", json = json, auth=auth )
    if r.status_code != 200:
       print("failed to add", r, json)  
       sys.exit()

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
