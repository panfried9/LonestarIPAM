from pydantic import BaseModel
from typing import Union, Literal

####################################################################################
# Workspace and User Models                                                        #
####################################################################################

class workspaceBase(BaseModel):
   workspacename: str

class userBase(BaseModel):
   username: str

class userFull(userBase):
   password: str


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