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

# add user
json = { "username" : "tuffin", "password" : "blank123" }
json2 = { "username" : "tuffinuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu", "password" : "blank123" }

r = requests.post( baseurl + "/users", json = json, auth=auth )
if r.status_code != 200 :
   print("fail add user ", r.content, json)
   sys.exit()
 
r = requests.post( baseurl + "/users", json = json2, auth=auth )
if r.status_code == 200 :
   print("add user with too long username was added", r.content, json)
   sys.exit()

# add new workspace
json = { "workspacename" : "eken_AB" }
r = requests.post( baseurl + "/workspaces", json=json, auth=auth) 
if r.status_code !=200 :
   print( "Failed to add new workspace ", r.status_code, r.content, json) 
   sys.exit()

# add new user to workspace
json = { "usertoadd" : { "username": "tuffin" }, 
         "workspace" : { "workspacename" : "eken_AB" } }
r = requests.post( baseurl + "/usersworkspaces", json=json, auth=auth) 
if r.status_code !=200 :
   print( "Failed to add user to workspace ", r.content, json) 
   sys.exit()

# add new user to workspace, negative test user already exists
json = { "usertoadd" : { "username": "tuffin" }, 
         "workspace" : { "workspacename" : "eken_AB" } }
r = requests.post( baseurl + "/usersworkspaces", json=json, auth=auth)
if r.status_code ==200 :
   print( "Failed to not add user to workspace when already existing", r.content, json)
   sys.exit()

# add new user to workspace, negative test user doesn't exist
json = { "usertoadd" : { "username": "asd345" }, 
         "workspace" : { "workspacename" : "eken_AB" } }
r = requests.post( baseurl + "/usersworkspaces", json=json, auth=auth)
if r.status_code ==200 :
   print( "Failed to not add non existing user to workspace ", r.content, json)
   sys.exit()

# add new user to workspace, negative test workspace doesn't exists
json = { "usertoadd" : { "username": "tuffin" }, 
         "workspace" : { "workspacename" : "blomman" } }
r = requests.post( baseurl + "/usersworkspaces", json=json, auth=auth)
if r.status_code ==200 :
   print( "Failed to not add user to non existing workspace ", r.content, json)
   sys.exit()

# delete user, negative test user still in workspace
r = requests.delete( baseurl + "/users", auth=HTTPBasicAuth('tuffin','blank123' ) ) 
if r.status_code == 200:
   print("fail delete user possible even when still member of workspace ", r.status_code, r.content )  
   sys.exit()

# delete user negative test, user doesn't exist
r = requests.delete( baseurl + "/users", auth=HTTPBasicAuth('xxx','blank123' ) )
if r.status_code == 200:
   print("Delete with unauthenticated user ", r.status_code, r.content )
   sys.exit()

# delete user from workspace, negative test workspace doesn't exists 
json = { "workspace" : "e" }
r = requests.delete( baseurl + "/usersworkspaces/", json=json, auth=HTTPBasicAuth('tuffin','blank123' ))
if r.status_code == 200:
   print("manage to delete user from nonexisting workspace ", json, r.status_code, r.content)
   sys.exit()

# delete user from workspace
json = { "workspace" : "eken_AB" }  
r = requests.delete( baseurl + "/usersworkspaces/", json=json, auth=HTTPBasicAuth('tuffin','blank123' ))
if r.status_code != 200:
   print("fail to delete user from workspace", json, r.status_code, r.content)
   sys.exit()


# add  v4 network
json = { "ipnet" : str(ipaddress.ip_network("20.20.20.0/24")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json2 = { "ipnet" : str(ipaddress.ip_network("30.30.30.0/29")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json3 = { "ipnet" : str(ipaddress.ip_network("60.50.40.0/24")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json4 = { "ipnet" : str(ipaddress.ip_network("60.50.41.0/24")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json5 = { "ipnet" : str(ipaddress.ip_network("70.50.41.0/29")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
r2= requests.post( baseurl + "/networks/", json = json2, auth=auth )
r3= requests.post( baseurl + "/networks/", json = json3, auth=auth )
r4= requests.post( baseurl + "/networks/", json = json4, auth=auth )
r5= requests.post( baseurl + "/networks/", json = json5, auth=auth )
if r.status_code != 200 or r2.status_code != 200 or r3.status_code != 200 or r4.status_code != 200 or r5.status_code !=200:
   print("fail to add v4", r.status_code, r.content, json, json2, json3, json4,json5 )   
   sys.exit()

# illegal mask negative test
json = { "ipnet" : "150.1.1.0/23" , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
if r.status_code == 200:
   print("Managed to add v4 with illegal mask", r, json) 



# add a v6 network
json = { "ipnet" : str(ipaddress.ip_network("2001:db8::/64")) ,  "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
json2 = { "ipnet" : str(ipaddress.ip_network("2001:db9::/64")) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks/", json = json, auth=auth )
r2 = requests.post( baseurl + "/networks/", json = json2, auth=auth )
if r.status_code != 200 or r2.status_code != 200:
   print("fail add v6",  r, json) 
   sys.exit()

# get a v4 network
r = requests.get( baseurl + "/networks/admin/nmnet/20.20.20.0/24" , auth=auth)
if r.status_code !=200:
   print("fail get v4", r.status_code, r.content) 
   sys.exit()

# get a v6 network
r = requests.get( baseurl + "/networks/admin/nmnet/2001:db8::/64" , auth=auth)
if r.status_code !=200:
   print("fail get v6",  r)    
   sys.exit()

# get a v6 network, negative test doesn't exist
r = requests.get( baseurl + "/networks/admin/nmnet/9010:db8::/60" , auth=auth)
if r.status_code ==200:
   print("managed to get v6 even if not existing",  r)   
   sys.exit()


# delete v4 network
json = { "ipnet" : str(ipaddress.ip_network("30.30.30.0/29")) ,  "vrf": "nmnet", "workspace" : "admin" }
r = requests.delete( baseurl + "/networks", json=json, auth=auth)  
if r.status_code !=200:
  print("fail to delete v4 ",  r)
  sys.exit() 


# delete v6 network
json = { "ipnet" : str(ipaddress.ip_network("2001:db9::/64")) ,  "vrf": "nmnet", "workspace" : "admin" }
r = requests.delete( baseurl + "/networks", json=json, auth=auth)
if r.status_code !=200:
  print("fail delete v6 ",  r)
  sys.exit()

# split v4 network
# first add a network that we can later split
ip = "40.40.0.0/16"
json = { "ipnet" : str(ipaddress.ip_network(ip)) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks", json = json, auth=auth )
if r.status_code != 200:
   print("failed to add", r, json)  
   sys.exit()
# now split that network 
json2 = { "ipnet" : str(ipaddress.ip_network("40.40.0.0/16")) , 
         "vrf": "nmnet",
         "workspace" : "admin",  
         "excludeip" : str(ipaddress.ip_network("40.40.40.0/24"))
          }
r = requests.post( baseurl + "/networks/split", json = json2, auth=auth )
if r.status_code != 200:
   print("failed to add for split A--->", r.content, json)  
   sys.exit()
expected_results = [{"ipnet" : "40.40.128.0/17", "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" }, 
                    { "ipnet" : "40.40.64.0/18", "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" }, 
                    {"ipnet" : "40.40.0.0/19"  , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                    { "ipnet" : "40.40.48.0/20", "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                    {"ipnet" : "40.40.32.0/21" , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                    {"ipnet" :  "40.40.44.0/22", "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                    { "ipnet" : "40.40.42.0/23", "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" }, 
                    {"ipnet" : "40.40.41.0/24" , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                    { "ipnet" : "40.40.40.0/24", "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" } ]  
newnets = jsonstuff.loads(r.content)
if newnets != expected_results :
    print("Return list doesn't match expectation ", newnets)
    sys.exit()

# summarize v4 network
json= { "firstnet" : {"ipnet" : "60.50.40.0/24", "vrf" : "nmnet", "workspace" : "admin" }, 
        "secondnet": {"ipnet" : "60.50.41.0/24", "vrf" : "nmnet", "workspace" : "admin" }  } 
r = requests.post( baseurl + "/networks/summarize", json = json, auth=auth )
if r.status_code != 200:
   print("error summarizing", r.content, json) 
   sys.exit()
sumnet = jsonstuff.loads(r.content) 
expected_results = "60.50.40.0/23"   
if sumnet[0]["ipnet"] != expected_results:
   print("Unexpected result from summarizing A ", r.content, r.status_code, json) 
   sys.exit()

# split v6 network
# first add a network that we can later split
ip = "8765::/60"
json = { "ipnet" : str(ipaddress.ip_network(ip)) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
r = requests.post( baseurl + "/networks", json = json, auth=auth )
if r.status_code != 200:
   print("failed to add", r, json)
   sys.exit()
# now split that network
json2 = { "ipnet" : str(ipaddress.ip_network("8765::/60")) ,
         "vrf": "nmnet",
         "workspace" : "admin",
         "excludeip" : str(ipaddress.ip_network("8765:0:0:1::/64"))
          }
r = requests.post( baseurl + "/networks/split", json = json2, auth=auth )
if r.status_code != 200:
   print("failed to split v6", r.content, json)
   sys.exit()
#print( r.content )
expected_results =[{"ipnet" : "8765:0:0:8::/61" , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" }, 
                   {"ipnet" : "8765:0:0:4::/62" , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" }, 
                   {"ipnet" : "8765:0:0:2::/63" , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                   {"ipnet" : "8765::/64"       , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" },
                   {"ipnet" : "8765:0:0:1::/64" , "vrf" : "nmnet", "workspace" : "admin", "comment" : "blank", "current_status" : "available" } ] 
newnets = jsonstuff.loads(r.content)
if newnets != expected_results :
    print("Return list from v6 doesn't match expectation")
    sys.exit()

# edit network
json = { "ipnet" : "8765:0:0:8::/61", "workspace" : "admin" , "vrf" : "nmnet" , "newvrf" : "boostnet" , "comment" : "this is a comment", "current_status" : "available" } 
r = requests.post( baseurl + "/networks/edit", json = json, auth=auth )
if r.status_code != 200:
   print("failed to edit", r.content, json)
   sys.exit()
 





# write 2 x 256 networks
for b in range(0,2):
  for c in range(0,255):
    ip = "30."+str(b)+"."+str(c)+".0/24"
    json = { "ipnet" : str(ipaddress.ip_network(ip)) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
    r = requests.post( baseurl + "/networks", json = json, auth=auth )
    if r.status_code != 200:
       print( r, json)  

# find overlaps on above
params = { 'size' : 20 , 'page' : 1 }
print("Param test")  
r = requests.get( baseurl + "/networks/overlaps/admin/nmnet/30.0.0.0/8", params = params, auth=auth)
if r.status_code !=200:
  print("failed to find overlaps v4 ",  r)
  sys.exit()
overlaps = jsonstuff.loads(r.content)["items"]
#print("OVERLAPS---> ", overlaps) 
#summar = len(overlaps) - ((b+1) * (c+1))
summar  = len(overlaps) - 20
if summar != 0:
  print("failed overlaps v4 test, didn't return correct overlaps. Expected ", params["size"], "but got", len(overlaps)) 
  sys.exit()
print("Param test done") 

# write 2 x 256 v6 networks
for b in range(0,2):
  for c in range(0,255):
    ip = "3001:"+str(b)+":"+str(c)+"::0/64"
    json = { "ipnet" : str(ipaddress.ip_network(ip)) , "vrf": "nmnet", "workspace" : "admin", "comment" : "blank" }
    r = requests.post( baseurl + "/networks", json = json, auth=auth )
    if r.status_code != 200:
       print("failed to add", r, json)  
       sys.exit()

# find overlaps on above , don't send params use default size 50 and Page 1. 
r = requests.get( baseurl + "/networks/overlaps/admin/nmnet/3001:0:0::/16", auth=auth)
if r.status_code !=200:
  print("failed to find overlaps v6 ",  r)
  sys.exit()
overlaps = jsonstuff.loads(r.content)["items"]
#fixme, also check how many pages and total items
summar = len(overlaps) - 50
if summar != 0:
  print("failed overlaps test, didn't return correct overlaps on v6", summar) 
  sys.exit()

# find next available with an exact match
json = { "requestedmask" : 24 , "iptype" : 4, "vrf" : "nmnet" , "workspace" : "admin"  } 
r =  requests.post( baseurl + "/networks/next", json=json, auth=auth)
if r.status_code !=200:
   print("Failed to find next network 1", r.content )
   sys.exit()

# find next available with smaller match
json = { "requestedmask" : 30 , "iptype" : 4, "vrf" : "nmnet" , "workspace" : "admin"  }
r =  requests.post( baseurl + "/networks/next", json=json, auth=auth)
if r.status_code !=200:
   print("Failed to find next network 2", r.content )
   sys.exit()

# find next available fail no of that size available 
json = { "requestedmask" : 8 , "iptype" : 4, "vrf" : "nmnet" , "workspace" : "admin"  }
r =  requests.post( baseurl + "/networks/next", json=json, auth=auth)
if r.status_code !=404:
   print("Managed to find next network of size /8", r.content )
   sys.exit()



print("Total Exec time:", time.time() - start_time ) 
