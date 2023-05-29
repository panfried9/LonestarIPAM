from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import postgresdatabase as database 
import ipaddress
from typing_extensions import Annotated

app = FastAPI()
security = HTTPBasic()

def authenticate(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
      print("WIll check for ", credentials.username)
      if database.authenticate(credentials.username, credentials.password):
         return credentials.username
      else:
        # If the user does not exist or the password is incorrect, return false
         raise HTTPException(status_code=401, detail="Invalid username or password")



####################################################################################
# User manipulation functions                                                      #
####################################################################################
@app.post("/user/{newuser}/{newpass}")
async def add_user(newuser: str, newpass: str, username: Annotated[str, Depends(authenticate)]):
   if len(newuser) > 50 or len(newpass) > 50:
      raise HTTPException(status_code=500, detail="Username and/or password too long, max 50")
   a = database.add_user(newuser, newpass, username)
   if a == 1:
      return status.HTTP_201_CREATED
   else:
      raise HTTPException(status_code=500, detail="Unable to insert, user already exists")

@app.delete("/user")
async def delete_user(username: Annotated[str, Depends(authenticate)]):
   a = database.delete_user( username)
   if a == 1:
      return status.HTTP_200_OK 
   else:
      raise HTTPException(status_code=500, detail="Unable to delete, user doesn't exists")

@app.get("/user")
async def get_user( username: Annotated[str, Depends(authenticate)]):
   userdata = database.get_user()
   return userdata 


####################################################################################
# Network manipulation functions                                                   #
####################################################################################
@app.post("/net/{ipnet}/{mask}/{vrf}") 
async def add_net(ipnet: str, mask: str, vrf: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask , strict=True )
   except Exception as e:
      raise HTTPException(status_code=500,detail="not valid IPv4 or IPv6 network " + str(e)  )
   database.add( network, vrf) 
   return status.HTTP_201_CREATED

@app.post("/net/{ipnet}/{mask}/{oldvrf}/{newvrf}")
async def transfer_net(ipnet: str, mask: str, oldvrf: str, newvrf: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask , strict=True)
   except:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  )
   print("WILL try to transfer", str(network), "to", str(newvrf))
   database.transfer(network, oldvrf, newvrf)
   return status.HTTP_201_CREATED

@app.get("/net/{ipnet}/{mask}/{vrf}")
async def get_net(ipnet: str, mask: str, vrf: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) ) 
   print( "Lets query for", str(network), str(vrf) ) 
   ipdata = database.get( network, vrf)
   return ipdata 

# Get the parent (overlapping) network
@app.get("/net_overlaps/{ipnet}/{mask}/{vrf}")
async def get_overlaps(ipnet: str, mask: str, vrf: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e) ) 
   print( "Lets query for", str(network), str(vrf) ) 
   ipdata = database.get_overlaps( network, vrf)
   return ipdata 

#split network
@app.post("/split/{ipnet}/{mask}/{vrf}/{excludeip}/{excludemask}")
async def exclude_net(ipnet: str, mask: str, vrf: str, excludeip: str, excludemask: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask, strict=True) 
   except:
      raise HTTPException(status_code=500, detail="Network to split from is not valid IPv4 or IPv6 network " + str(e) ) 
   try:
      exclude_network = ipaddress.ip_network( excludeip + "/" + excludemask, strict=True) 
   except:
      raise HTTPException(status_code=500, detail="Network to split out is not valid IPv4 or IPv6 network " + str(e) ) 
   a = database.get(network, vrf)
   if not a:
      raise HTTPException(status_code=500, detail="Network to split from is not found")
   newnets = list(network.address_exclude(exclude_network))
   newnets.append( exclude_network)
   database.delete(network, vrf)
   for newnet in newnets:
      database.add(newnet, vrf)
   return newnets

####################################################################################
# Address manipulation functions                                                   #
####################################################################################
#@app.post("/address/{start}/{end}/{vrf}") 
#async def add_address(start: str, end: str, vrf: str, username: Annotated[str, Depends(authenticate)]):
#   try:
#      network = ipaddress.ip_network( ipnet + "/" + mask , strict=False )
#   except Exception as e:
#      raise HTTPException(status_code=500,detail="not valid IPv4 or IPv6 network " + str(e)  )
#   database.add( network, vrf) 
#   return status.HTTP_201_CREATED















@app.delete("/net/{ipnet}/{mask}/{vrf}")
async def delete_net(ipnet: str, mask: str, vrf: str, username: Annotated[str, Depends(authenticate)]):
   try:
      network = ipaddress.ip_network( ipnet + "/" + mask , strict=False)
   except Exception as e:
      raise HTTPException(status_code=500, detail="not valid IPv4 or IPv6 network " + str(e)  ) 
   print("NOW query database")
   database.delete( network, vrf)
   return status.HTTP_200_OK 


