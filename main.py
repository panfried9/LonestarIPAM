from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import postgresdatabase as database 
import ipaddress
from typing import Union, Literal, List
from typing_extensions import Annotated
from pydantic import BaseModel
from fastapi_pagination import Page, add_pagination, paginate

app = FastAPI()
security = HTTPBasic()
add_pagination(app)


def authenticate(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
      if database.authenticate(credentials.username, credentials.password):
         return credentials.username
      else:
        # If the user does not exist or the password is incorrect, return false
         raise HTTPException(status_code=401, detail="Invalid username or password")

def authorized_for_net(username, net):
    a = database.get_network(net)
    if a.get("error"):
      return 0
    if database.authorized(username, a["workspace"] ):
      return 1
    else:
      return 0 

class workspaceBase(BaseModel):
   workspacename: str

class userBase(BaseModel):
   username: str

class userFull(userBase):
   password: str

####################################################################################
# Workspaces manipulation functions                                                #
####################################################################################
@app.post("/workspaces")
async def add_workspace(workspace: workspaceBase, username: Annotated[str, Depends(authenticate)]):
   if not database.authorized( username, "admin"):
      raise HTTPException(status_code=401, detail="Only users in the admin group can add workspaces")
   a = database.add_workspace(workspace, username)
   if a[0] == 0:
      raise HTTPException(status_code=500, detail="Unable add workspace, " + a[1] )
   return status.HTTP_201_CREATED

@app.get("/workspaces", response_model=List[workspaceBase])
async def get_workspaces( username: Annotated[str, Depends(authenticate)] ):
   a = database.get_workspaces( username)
   if a[0] == 0:
      raise HTTPException(status_code=500, detail="Unable get workspace, " + a[1] )   
   return a[1] 
     
####################################################################################
# Mappings between users and workspaces                                            #
####################################################################################
@app.post("/usersworkspaces")
async def add_user_to_workspace( usertoadd: userBase, workspace: workspaceBase, username: Annotated[str, Depends(authenticate)]):
  if not database.authorized( username, workspace.workspacename):
     raise HTTPException(status_code=401, detail="Requestor " + str(username) + " not authorized for the workspace " + str(workspace.workspacename))
  b = database.add_workspace(workspace, usertoadd.username)
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
@app.post("/users")
async def newuser(user: userFull, username: Annotated[str, Depends(authenticate)]):
   a = database.add_user(user)
   if a[0] == 1:
      return status.HTTP_201_CREATED
   else:
      raise HTTPException(status_code=500, detail="Unable to insert a new user, " + a[1] )

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

# get all users from a particular workspace
@app.get("/users/{workspace}", response_model=userBase, response_model_exclude={"password"})
async def get_user( workspace: str, username: Annotated[str, Depends(authenticate)]):
   if not database.authorized( username, workspace):
     raise HTTPException(status_code=401, detail="User not authorized for this workspace")
   a = database.get_user(workspace)
   if a[0] == 1:
     return a[1] 
   raise HTTPException(status_code=500, detail=a[1])

####################################################################################
# Network Models                                                                   #
####################################################################################
class netBase(BaseModel):
   ipnet: str # with mask that can be 24 or 255.255.255.0 notation 
   vrf: str 
   workspace: str

class netFull(netBase):
   comment: Union[str,None] = None
   current_status: Literal['unassigned','available', 'in-use-set', 'in-use-found', 'reserved', 'capped'] = 'available'

class netEdit(netFull):
   newvrf: str # need both the old vrf to find the network and a new if the user is changing the vrf

# next available of a certain size
class netNext(BaseModel):
   requestedmask: int
   iptype: int 
   vrf: str 
   workspace: str

# Split a network
class netSplit(netBase):
   excludeip: str # network to split out, including mask 


####################################################################################
# Network manipulation functions                                                   #
####################################################################################
@app.post("/networks", response_model=netFull) 
async def add_net(net: netFull, username: Annotated[str, Depends(authenticate)]):
   a = database.add_network( net) 
   if a.get('error'):
      raise HTTPException(status_code=500,detail= a["error"])     
   return a

@app.get("/networks/{workspace}/{vrf}/{ipnet}/{mask}", response_model=netBase)
async def get_net(workspace: str, vrf: str, ipnet: str, mask: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) ) 
   NetIn = netBase( ipnet= str(network), workspace=workspace, vrf=vrf )
   if not authorized_for_net(username, NetIn):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network)  )  
   ipdata = database.get_network(NetIn) 
   if ipdata.get("error"):
      raise HTTPException(status_code=500, detail = ipdata["error"])
   return ipdata 

@app.delete("/networks")
async def delete_net(net: netBase, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( net.ipnet , strict=True)
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  ) 
   if not authorized_for_net(username, net):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network) )  
   a = database.get_network(net)
   if a.get("error"): 
      raise HTTPException(status_code=500, detail = a["error"])
   b = database.delete( network, net.vrf, net.workspace)
   if b[0] == 0:
      raise HTTPException(status_code=500, detail = b[1])
   return status.HTTP_200_OK 

# Get the parent (overlapping) network
@app.get("/networks/overlaps/{workspace}/{vrf}/{ipnet}/{mask}",response_model=Page[netFull])
async def get_overlaps(workspace: str, vrf: str, ipnet: str, mask: str, username: Annotated[str, Depends(authenticate)]  ):  #limit: Union[int,None] = None , skip: Union[int,None] = None  
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) )     
   a = database.get_overlaps( network, vrf, workspace)
   if a[0] == 0:
      raise HTTPException(status_code=500, detail=a[1] )
   return paginate(a[1])   

# Edit VRF or Comment on a network

@app.post("/networks/edit", response_model=netFull)
async def transfer_net(net: netEdit, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( net.ipnet, strict=True)
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  )
   if not authorized_for_net(username, net):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists "  )  
   a = database.edit_network(network, net.vrf, net.newvrf, net.comment, net.current_status, net.workspace )
   if a[0] == 0:
      raise HTTPException(status_code=500,detail=a[1] )
   return net


@app.post("/networks/next", response_model=netFull)
async def next_network( net: netNext, username: Annotated[str, Depends(authenticate)]):
   mask = net.requestedmask 
   if net.iptype != 4 and net.iptype != 6:
      raise HTTPException(status_code=500, detail = "IP type is not 4 or 6")   
   if mask < 0 or ( net.iptype == 4 and mask > 32) or (net.iptype == 6 and mask > 128): 
      raise HTTPException(status_code=500, detail = "mask " +str(mask) + " is not within range for iptype " + str(net.iptype)) 
   if net.iptype == 4:
       entire_space = ipaddress.ip_network("0.0.0.0/0")
   else:
       entire_space = ipaddress.ip_network("::/0") 
   a = database.get_overlaps(entire_space, net.vrf, net.workspace )  
   if a[0] == 0:
       raise HTTPException(status_code=500, detail = "failed to get overlapping networks, " + a[1] )
   smallest_delta = 1000 
   smallest_net   = None
   for available_net in a[1]:
       if available_net["current_status"] != 'available':
          continue
       netlen = ipaddress.ip_network(available_net["ipnet"]).prefixlen
       lendelta = mask - netlen 
       if lendelta == 0 :
          return available_net 
       # plan-b   
       if lendelta > 0: # only save candidates that are larger than the requested network
          if lendelta < smallest_delta: # only save if we don't have another candidate that is better 
             smallest_delta = lendelta
             smallest_net   = available_net  
   if smallest_net:
       return smallest_net 
   raise HTTPException(status_code=404, detail = "No network of that size or larger is available" )


#split network
# takes a netBase and an excludenet to split out and return a list of networks
@app.post("/networks/split", response_model=List[netFull])
async def exclude_net(net: netSplit , username: Annotated[str, Depends(authenticate)]):
   add_nets = []  
   newnets = [] 
   try:
      network = ipaddress.ip_network( net.ipnet, strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="Network to split from is not valid IPv4 or IPv6 network " + str(e) ) 
   if not authorized_for_net(username, net):
      raise HTTPException(status_code=500,detail="user not authorized for this network or network doesn't exists " + str(network)  )  
   try:
      exclude_network = ipaddress.ip_network( net.excludeip , strict=True) 
   except Exception as e:
      raise HTTPException(status_code=500, detail="Network to split out is not valid IPv4 or IPv6 network " + str(e) ) 
   a = database.get_network(net)
   if a.get("error"):
      raise HTTPException(status_code=500, detail=a["error"])
   try:
      newnets = list(network.address_exclude(exclude_network))
      # append the network that was requested to be split out so that this also is added back
      newnets.append(exclude_network)
   except Exception as e:
       raise HTTPException(status_code=500, detail="Unable to split out networks " +str(e))
   # create a list of all the networks. Use the comment and status from variable a which is the incoming network. 
   for n in newnets:
       add_nets.append( netFull(ipnet = str(n), vrf = net.vrf, workspace = net.workspace, comment = a['comment'].strip(), current_status =a['current_status']) )        
   c = database.del_then_add_network([net], add_nets) 
   if c[0] == 0:
      raise HTTPException(status_code=500, detail="Unable to split, " + c[1])
   return add_nets



#split network
#######################################################################
# takes two networks
# summarizes if possible
# returns a baseNet that is the summary of the input.
# FIXME, should use collapse network from ipnetwork module instead
#######################################################################
@app.post("/networks/summarize", response_model = List[netFull] )
async def summarize_net(firstnet: netBase, secondnet: netBase, username: Annotated[str, Depends(authenticate)]):
   ss = [] 
   # make sure input is sane
   if firstnet.vrf != secondnet.vrf:
         raise HTTPException(status_code=500, detail="networks to be summarized must belong to the same vrf" )        
   if firstnet.workspace != secondnet.workspace:
         raise HTTPException(status_code=500, detail="networks to be summarized must belong to the same workspace" )
   try:
      firstnet_true   = ipaddress.ip_network(firstnet.ipnet, strict=True)
      secondnet_true = ipaddress.ip_network(secondnet.ipnet, strict=True)
   except:
      raise HTTPException(status_code=500, detail="One of the submitted string is not a network " )
   if firstnet_true.version != secondnet_true.version:
      raise HTTPException( status_code=500, detail="mixed v4 and v6 nets can't be summarized")   
  
  # make sure networks actually exists 
   firstnet_db = database.get_network( firstnet ) 
   secondnet_db= database.get_network( secondnet )
   if firstnet_db.get("error"): 
      raise HTTPException( status_code=500, detail= firstnet_db["error"] ) 
   if secondnet_db.get("error"):
      raise HTTPException( status_code=500, detail= secondnet_db["error"] ) 
   
   # make sure networks are contigious
   if ipaddress.ip_network(firstnet.ipnet).broadcast_address + 1 != ipaddress.ip_network(secondnet.ipnet).network_address:
      raise HTTPException( status_code=500, detail="network not contigiuos" )  

   # if we are here, we know the networks are clean and contingious
   # try to fuse them together
   try:
      summarized_iterator = ipaddress.summarize_address_range(ipaddress.ip_network(firstnet.ipnet).network_address, ipaddress.ip_network(secondnet.ipnet).broadcast_address)
   except Exception as e:
      raise HTTPException( status_code=500, detail="unable to summarize, " + str(e)) 
   for s in summarized_iterator:
      ss.append( netFull(ipnet = str(s), vrf = firstnet.vrf, workspace = firstnet.workspace, comment= firstnet_db["comment"].strip(), current_status = firstnet_db["current_status"] ) )
   c = database.del_then_add_network([firstnet, secondnet], ss)
   return ss

