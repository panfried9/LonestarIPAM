from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import postgresdatabase as database 
import ipaddress
from typing_extensions import Annotated
from pydantic import BaseModel

app = FastAPI()
security = HTTPBasic()

####################################################################################
# Helper functions                                                                 #
####################################################################################
def authenticate(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
      if database.authenticate(credentials.username, credentials.password):
         return credentials.username
      else:
        # If the user does not exist or the password is incorrect, return false
         print("credentials ", credentials.username, credentials.password) 
         raise HTTPException(status_code=401, detail="Invalid username or password")

def authorized_for_net(username, network, vrf, workspace):
    a = database.get_network(network, vrf, workspace)
    if a["status"] == 0:
      return 0
    if database.authorized(username, a["workspace"] ):
      return 1
    else:
      print("that net does not belongs to ", workspace)
      return 0 


####################################################################################
# Workspaces manipulation functions                                                #
####################################################################################
class ws (BaseModel):
   wsname: str
@app.post("/workspaces")
async def add_workspace(request: Request, options: ws, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   if not database.authorized( username, "admin"):
      raise HTTPException(status_code=401, detail="Only users in the admin group can add workspaces")
   a = database.add_workspace(requested["wsname"], username)
   if a[0] == 0:
      raise HTTPException(status_code=500, detail="Unable add workspace, " + a[1] )
   return status.HTTP_201_CREATED

@app.get("/workspaces")
async def get_workspaces( username: Annotated[str, Depends(authenticate)] ):
   a = database.get_workspaces( username)
   if a[0] == 1:
     return { "workspaces" :  a[1] }
   else:
     raise HTTPException(status_code=500, detail="Unable add workspace, " + a[1] )
 
####################################################################################
# Mappings between users and workspaces                                            #
####################################################################################
class uw (BaseModel):
   usertoadd: str
   workspace: str
@app.post("/usersworkspaces")
async def add_user_to_workspace( request: Request, options: uw, username: Annotated[str, Depends(authenticate)]):
  requested = await request.json()
  if not database.authorized( username, requested["workspace"]):
     raise HTTPException(status_code=401, detail="Requestor not authorized for the workspace")
  b = database.add_workspace(requested["workspace"], requested["usertoadd"])
  if b[0] == 0:
     raise HTTPException(status_code=500, detail="Unable to add user to workspace, " + b[1])
  return status.HTTP_201_CREATED

class workspace(BaseModel):
   workspace: str
@app.delete("/usersworkspaces")
async def delete_user_from_workspace( request: Request, options: workspace, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   s,b = database.delete_user_from_workspace(username, requested["workspace"] )   
   if s == 0:
      raise HTTPException (status_code=500, detail=b)
   return status.HTTP_200_OK 


####################################################################################
# User manipulation functions                                                      #
# these functions does not need any authorization
####################################################################################
class nu (BaseModel):
   newuser: str
   newpass: str
@app.post("/users")
async def newuser(request: Request, options: nu, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   a = database.add_user(requested["newuser"], requested["newpass"] )
   if a[0] == 1:
      return status.HTTP_201_CREATED
   else:
      raise HTTPException(status_code=500, detail="Unable to insert, " + a[1] )

# Delete requestor from database.
@app.delete("/users")
async def delete_user(username: Annotated[str, Depends(authenticate)]):
   a = database.get_workspaces( username )
   if a[0] == 0:
      raise HTTPException(status_code  = 500, detail= a[1] )
   if len( a[1] ) != 0:
      raise HTTPException(status_code = 500, detail="Can't delete, user still member of at least one workspace.")
   b = database.delete_user( username)
   if b == 1:
      return status.HTTP_200_OK 
   else:
      raise HTTPException(status_code=500, detail="Unable to delete, user doesn't exists")

@app.get("/users/{workspace}")
async def get_user( workspace: str, username: Annotated[str, Depends(authenticate)]):
   if not database.authorized( username, workspace):
     raise HTTPException(status_code=500, detail="User not authorized for this workspace")
   a = database.get_user(workspace)
   if a[0] == 1:
     return a[1] 
   raise HTTPException(status_code=500, detail=a[1])

####################################################################################
# Network manipulation functions                                                   #
####################################################################################
class net (BaseModel):
   ipnet: str # with mask that can be 24 or 255.255.255.0 notation 
   vrf: str 
   workspace: str
   comment: str
@app.post("/networks") 
async def add_net(request: Request, options: net, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   try:
      network = ipaddress.ip_network( requested["ipnet"] , strict=True )
   except Exception as e:
      raise HTTPException(status_code=500,detail="not valid IPv4 or IPv6 network " + str(e)  )
   a = database.add_network( network, requested["vrf"], requested["workspace"], requested["comment"]) 
   if a["status"] == 1:
       return status.HTTP_201_CREATED
   raise HTTPException(status_code=500,detail= a["error"])     

@app.get("/networks/{workspace}/{vrf}/{ipnet}/{mask}")
async def get_net(workspace: str, vrf: str, ipnet: str, mask: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) ) 
   if not authorized_for_net(username, network, vrf, workspace):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network)  )  
   ipdata = database.get_network( network, vrf, workspace)
   if ipdata["status"] == 0:
      raise HTTPException(status_code=500, detail = ipdata["error"])
   return ipdata 

class netnc (BaseModel):
   ipnet: str # including mask
   vrf: str
   workspace: str
@app.delete("/networks")
async def delete_net(request: Request, options: netnc, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()   
   try:
      network = ipaddress.ip_network( requested["ipnet"] , strict=False)
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  ) 
   a = database.get_network(network, requested["vrf"], requested["workspace"])
   if a["status"] == 0: 
      raise HTTPException(status_code=500, detail = a["error"])
   database.delete( network, requested["vrf"], requested["workspace"])
   return status.HTTP_200_OK 

# Get the parent (overlapping) network
@app.get("/networks/overlaps/{workspace}/{vrf}/{ipnet}/{mask}")
async def get_overlaps(workspace: str, vrf: str, ipnet: str, mask: str, username: Annotated[str, Depends(authenticate)]):   
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) )     
   a = database.get_overlaps( network, vrf, workspace)
   if a[0] == 0:
      raise HTTPException(status_code=500, detail= a[1] )
   return { "overlaps" : a[1] }  

# Edit VRF or Comment on a network
class nettra (BaseModel):
   ipnet: str #including mask
   workspace: str
   oldvrf: str
   newvrf: str
   comment: str
   current_status: str
@app.post("/networks/edit")
async def transfer_net(request: Request, options: nettra, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   try:
      network = ipaddress.ip_network( requested["ipnet"] , strict=True)
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  )
   if not authorized_for_net(username, network, requested["oldvrf"], requested["workspace"]):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists "  )  
   a = database.edit_network(network, requested["oldvrf"], requested["newvrf"], requested["comment"], requested["current_status"], requested["workspace"] )
   if a[0] == 0:
      raise HTTPException(status_code=500,detail= a[1] ) 
   return status.HTTP_201_CREATED


# Split a network
class netspl (BaseModel):
   ipnet: str # including mask
   vrf: str
   workspace: str
   excludeip: str # including mask 
#split network
@app.post("/networks/split")
async def exclude_net(request: Request, options: netspl, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json() 
   networks = []  
   try:
      network = ipaddress.ip_network( requested["ipnet"] , strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="Network to split from is not valid IPv4 or IPv6 network " + str(e) ) 
   if not authorized_for_net(username, network, requested["vrf"], requested["workspace"]):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network)  )  
   try:
      exclude_network = ipaddress.ip_network( requested["excludeip"] , strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="Network to split out is not valid IPv4 or IPv6 network " + str(e) ) 
   a = database.get_network(network, requested["vrf"], requested["workspace"])
   if a["status"] == 0:
      print("STATUS NOT 0") 
      raise HTTPException(status_code=500, detail=a["error"])

   try:
      newnets = list(network.address_exclude(exclude_network))
   except Exception as e:
       raise HTTPException(status_code=500, detail="Unable to split out networks " +str(e))     
   newnets.append( exclude_network) # append the network that was requested to be split out so that this also is added back
   print("TYPE ,", type(network)) 
   networks.append(network)
   c = database.del_then_add_network(networks, requested["vrf"], requested["workspace"], newnets, a["comment"], a["current_status"]) 
   if c[0] == 0:
      raise HTTPException(status_code=500, detail="Unable to split, " + c[1])  
   return { "networks" : newnets }

# summarize networks
class netsum (BaseModel):
   ipnets: list
   vrf: str
   workspace: str
#split network
@app.post("/networks/summarize")
async def summarize_net(request: Request, options: netsum, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   confirmed_nets = []
   return_nets = []  
   fourfound = sixfound = 0 
   # check that the network is valid and correct and exists
   for net in requested["ipnets"]:
      try:
         newnet = ipaddress.ip_network(net, strict=True)
      except:
         raise HTTPException(status_code=500, detail="Submitted string is not a network " + net)
      if newnet.version == 4:
         fourfound = 1
         if sixfound:
            raise HTTPException( status_code=500, detail="mixed v4 and v6 nets can't be summarized")   
      else:
         sixfound = 1
         if fourfound:
            raise HTTPException( status_code=500, detail="mixed v4 and v6 nets can't be summarized") 
      try:
         a = database.get_network( newnet, requested["vrf"], requested["workspace"] )
      except:
         raise HTTPException( status_code=500, detail="Unable to find network " + str(newnet) + " in vrf " + requested["vrf"]) 
      if a["status"] == 0: 
         raise HTTPException( status_code=500, detail= a["error"] ) 
      # also the requested network should be added back to the database, append it
      confirmed_nets.append(newnet ) 
   # if 0 or 1 network just return that, no database change needed
   if len(confirmed_nets) <2 :
      return { "networks" : confirmed_nets }

   # make sure nets are contigious 
   sort_nets = sorted( confirmed_nets,  key=lambda i: i.network_address )
   last_last = sort_nets[0].broadcast_address 
   for i in range(1, len(sort_nets)):
      if last_last + 1 != sort_nets[i].network_address:
         raise HTTPException( status_code=500, detail="network not contigiuos gap/overlap between " + str(sort_nets[i-1]) +" and " + str(sort_nets[i])) 
      last_last = sort_nets[i].broadcast_address

   # if we are here, networks are not overlapping or gapping
   # try to fuse them together
   try:
      print("F L ," , sort_nets[0].network_address, sort_nets[-1].broadcast_address) 
      summarized = ipaddress.summarize_address_range(sort_nets[0].network_address, sort_nets[-1].broadcast_address)
   except Exception as e:
      raise HTTPException( status_code=500, detail="unable to summarize " + str(e)) 
   for a in summarized:
      return_nets.append(a)
   c = database.del_then_add_network(confirmed_nets, requested["vrf"], requested["workspace"], return_nets, "created via split", "available")
   return { "networks" : return_nets }
