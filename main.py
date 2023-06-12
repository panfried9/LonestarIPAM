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
      #print("Will check for ", credentials.username)
      if database.authenticate(credentials.username, credentials.password):
         return credentials.username
      else:
        # If the user does not exist or the password is incorrect, return false
         raise HTTPException(status_code=401, detail="Invalid username or password")

def authorized(username, workspace):
    if database.authorized(username, workspace):
      return 1
    return 0 
 
def authorized_for_net(username, network, vrf):
    # then find out what workspace this network belongs to
    #try:
    print( "Check that ", username, " is authorized for ", str(network) )
    a = database.get(network, vrf)
    #except:
    #  print("Couldn't even get that net ", str(network))
    #  return 0
    # tcheck to see if user is authorized for this workspace
    if authorized(username, a["workspace"] ):
      return 1
    else:
      print("that net belongs to ", a["workspace"])
      return 0 


####################################################################################
# Workspaces manipulation functions                                                #
####################################################################################
class ws (BaseModel):
   wsname: str
@app.post("/workspaces")
async def add_workspace(request: Request, options: ws, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   if not authorized( username, "admin"):
      raise HTTPException(status_code=401, detail="Only users in the admin group can add workspaces")
   if len(requested["wsname"]) > 50:
      raise HTTPException(status_code=500, detail="Workspace name too long, max 50")
   a = database.add_workspace(requested["wsname"], username)
   if a == 1:
      return status.HTTP_201_CREATED
   else:
      raise HTTPException(status_code=500, detail="Unable to insert, workspace already exists")

@app.get("/workspaces")
async def get_workspaces( username: Annotated[str, Depends(authenticate)] ):
   # no explicity authorization required 
   a = database.get_workspaces( username)
   print("A type:", type(a)) 
   return a


####################################################################################
# Mappings between users and workspaces                                            #
####################################################################################

class uw (BaseModel):
   usertoadd: str
   workspace: str
@app.post("/usersworkspaces")
async def add_user_to_workspace( request: Request, options: uw, username: Annotated[str, Depends(authenticate)]):
  requested = await request.json()
  if not authorized( username, requested["workspace"]):
     raise HTTPException(status_code=401, detail="Requestor not authorized for the workspace")
  #check if user exists
  statusin, userstatus = database.user_exists(requested["usertoadd"])
  if statusin == 0: 
     raise HTTPException(status_code=500, detail=userstatus)
  a = database.add_workspace(requested["workspace"], requested["usertoadd"])
  if a == 1:
     return status.HTTP_201_CREATED
  else:
     raise HTTPException(status_code=500, detail="Unable to insert, add_workspace error")

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
   if len(requested["newuser"]) > 50 or len(requested["newpass"]) > 50:
      raise HTTPException(status_code=500, detail="Username and/or password too long, max 50")
   a = database.add_user(requested["newuser"], requested["newpass"], username)
   if a == 1:
      return status.HTTP_201_CREATED
   else:
      raise HTTPException(status_code=500, detail="Unable to insert, user already exists")

# Delete requestor from database.
@app.delete("/users")
async def delete_user(username: Annotated[str, Depends(authenticate)]):
   status, ws = database.get_workspaces( username )
   if status == 0:
      raise HTTPException(status_code  = 500, detail= ws )
   if len( ws ) != 0:
      raise HTTPException(status_code = 500, detail="Can't delete, user still member of at least one workspace.")
   a = database.delete_user( username)
   if a == 1:
      return status.HTTP_200_OK 
   else:
      raise HTTPException(status_code=500, detail="Unable to delete, user doesn't exists")

# FIXME, should this function be limited to the workspace you are in? Seems dangerous to get all users
@app.get("/users")
async def get_user( username: Annotated[str, Depends(authenticate)]):
   status, userdata = database.get_user()
   if status == 1:
     return userdata 
   else:
     raise HTTPException(status_code=500, detail=userdata)

####################################################################################
# Network manipulation functions                                                   #
####################################################################################
class net (BaseModel):
   ipnet: str
   mask: str # can be 24 or 255.255.255.0  
   vrf: str 
   workspace: str
   comment: str
@app.post("/networks") 
async def add_net(request: Request, options: net, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   if not authorized(username, requested["workspace"]):
      raise HTTPException(status_code=500,detail="user not authorized for this workspace or workspace doesn't exists " )      
   try:
      network = ipaddress.ip_network( requested["ipnet"] + "/" + requested["mask"] , strict=True )
   except Exception as e:
      raise HTTPException(status_code=500,detail="not valid IPv4 or IPv6 network " + str(e)  )
   st, details = database.add_network( network, requested["vrf"], requested["workspace"], requested["comment"]) 
   if st == 1:
       return status.HTTP_201_CREATED
   else:
       raise HTTPException(status_code=500,detail= details)     

@app.get("/networks/{vrf}/{ipnet}/{mask}")
async def get_net(vrf: str, ipnet: str, mask: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) ) 
   #print( "Lets query for", str(network), str(vrf) ) 
   if not authorized_for_net(username, network, str(vrf)):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network)  )  
   ipdata = database.get( network, vrf)
   return ipdata 

class netnc (BaseModel):
   ipnet: str
   mask: str # can be 24 or 255.255.255.0
   vrf: str
   workspace: str
@app.delete("/networks")
async def delete_net(request: Request, options: netnc, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()   
   # FIXME, this function should not have to take a workspace, instead the workspace should be found and authorized before deleting 
   #if not authorized(username, requested["workspace"]):
   #   raise HTTPException(status_code=500,detail="user not authorized for this workspace or workspace doesn't exists" )      
   try:
      network = ipaddress.ip_network( requested["ipnet"] + "/" + requested["mask"] , strict=False)
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  ) 
   a = database.get(network, requested["vrf"])
   print("FOUND THIS NETWORK AS" , a)


   database.delete( network, requested["vrf"])
   return status.HTTP_200_OK 

# Get the parent (overlapping) network
@app.get("/networks/overlaps/{workspace}/{vrf}/{ipnet}/{mask}")
async def get_overlaps(workspace: str, vrf: str, ipnet: str, mask: str, username: Annotated[str, Depends(authenticate)]):   
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) )     
   print( "Lets query for", str(network), str(vrf) ) 
   try:
      st, ipdata = database.get_overlaps( network, vrf, workspace)
   except:
      # maybe this network doesn't exist, in that case we can't check if the user is authorized or not
      return { "overlaps": [] }
   if st == 0:
      raise HTTPException(status_code=500, detail=ipdata )
   # just check the first network, we know the user is authorized for all of them if authorized for one, since the SELECT in get_overlaps is filtering out just this workspace
   check_net = ipaddress.ip_network( ipdata[0] )
   if not authorized_for_net(username, check_net, str(vrf) ): 
      raise HTTPException(status_code=401,detail="user not authorized for this workspace or workspace doesn't exists" + str( ipdata[3]) )  
   return { "overlaps" : ipdata }  

# Edit VRF or Comment on a network
class nettra (BaseModel):
   ipnet: str
   mask: str # can be 24 or 255.255.255.0  
   oldvrf: str
   newvrf: str
   comment: str
@app.post("/networks/edit")
async def transfer_net(request: Request, options: nettra, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()
   try:
      network = ipaddress.ip_network( requested["ipnet"] + "/" + requested["mask"] , strict=True)
   except:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  )
   if not authorized_for_net(username, network, requested["oldvrf"]):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(e)  )  
   # ipdata = database.get( network, vrf) ### commented this out not sure why we would need to get the address prior to editing. 
   print("WILL try to edit", str(network) )
   database.edit(network, requested["oldvrf"], requested["newvrf"], requested["comment"] )
   return status.HTTP_201_CREATED

class netspl (BaseModel):
   ipnet: str
   mask: str # can be 24 or 255.255.255.0  
   vrf: str
   excludeip: str 
   excludemask: str 
#split network
@app.post("/networks/split")
async def exclude_net(request: Request, options: netspl, username: Annotated[str, Depends(authenticate)]):
   requested = await request.json()  
   try:
      network = ipaddress.ip_network( requested["ipnet"] + "/" + requested["mask"], strict=True) 
   except:
      raise HTTPException(status_code=500, detail="Network to split from is not valid IPv4 or IPv6 network " + str(e) ) 
   if not authorized_for_net(username, network, requested["vrf"]):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network)  )  
   #ipdata = database.get( network, requested["vrf"]) ### commenting this out not sure why we would need it not used below

   try:
      print("exclude IP ", requested["excludeip"], "Exclude mask", requested["excludemask"])
      exclude_network = ipaddress.ip_network( requested["excludeip"] + "/" + requested["excludemask"], strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="Network to split out is not valid IPv4 or IPv6 network " + str(e) ) 
   a = database.get(network, requested["vrf"])
   if not a:
      raise HTTPException(status_code=500, detail="Network to split from is not found")
   try:
      newnets = list(network.address_exclude(exclude_network))
   except Exception as e:
       raise HTTPException(status_code=500, detail="Unable to split out networks " +str(e))     
   newnets.append( exclude_network) # append the network that was requested to be split out so that this also is added back
   #FIXME entire below need to be in one transaction 
   database.delete(network, requested["vrf"])    # delete the old network
   for newnet in newnets:           # add all the new networks
      database.add_network(newnet, requested["vrf"],a["workspace"], a["comment"]) # retain the workspace and comment for the new networks
      #FIXME check return codes
   return newnets

