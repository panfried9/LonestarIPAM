import psycopg2
from fastapi import HTTPException
import ipaddress
import json
import hashlib

f = open('config.json') 
config = json.load(f) 

# FIXME, removed once moved over to class
#conn = psycopg2.connect( host=config["host"], database=config["database"], user=config["user"], password=config["password"] )


def first_last_to_net(first, last):
   f = ipaddress.ip_address(first)
   l = ipaddress.ip_address(last)
   if f.version == 4:
      # converts a number of hosts (including broadcast and network) into a subnet size
      diff = int(l) - int(f) + 1
      m = 35-len(str(bin(diff)))
      return str(f) + "/" + str(m)
   else:
      diff = int(l) - int(f) + 1 
      m =  131-len(str(bin(diff)))
      return str(f) + "/" +str(m) 



class IpamDB():
    def __init__(self):
        self.conn = psycopg2.connect(host=config["host"], database=config["database"], user=config["user"], password=config["password"])
        self.cur = self.conn.cursor()

    def ss(self, query, t):   # Single Statement
         self.cur.execute(query, t)

    def sfa(self, query, t):   # statement and fetch all
         self.cur.execute(query, t)
         return self.cur.fetchall()

    def sfo(self, query, t):   # statement and fetch one
         self.cur.execute(query, t)
         return self.cur.fetchone()

    def srow(self, query, t):
         self.cur.execute(query, t)
         return self.cur.rowcount 

    def commit(self):
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def rollback(self):
        self.cur.close()
        self.conn.rollback()
        self.conn.close()


def add_user(user):
   pwdsalt  = user.password + config["salt"]
   hashtodb = hashlib.sha512(pwdsalt.encode())
   data_tuple = (user.username, hashtodb.hexdigest(), user.username)
   sql_statement = "INSERT INTO users (username, password) SELECT %s, %s WHERE NOT EXISTS (SELECT username FROM users WHERE username = %s);"
   try:
      db = IpamDB()
      db.ss(sql_statement, data_tuple)
      db.commit()
   except Exception as e:
      db.rollback()
      return(0, "Error when trying to add user " + str(e))  
   return (1,"") 

def delete_user(currentuser):
   data_tuple = (currentuser,)
   sql_statement = "DELETE FROM users WHERE username = %s;"
   try:
      db = IpamDB()
      db.ss( sql_statement, data_tuple)
      db.commit()
   except Exception as e:
      db.rollback()
      return(0, "Unable to delete user " + str(e) ) 
   return(1,"")

# returns all users from a workspace 
def get_user(workspace):
   data_tuple = (workspace,)
   sql_statement = "SELECT * FROM users WHERE workspace = %s;"
   try:
      db = IpamDB()
      userdata = db.sfo( sql_statement, data_tuple)
   except Exception as e:
      db.rollback()
      return (0, "unable to connect to database to get user details" + str(e) )
   db.commit()   
   if userdata is None:
      return (1, [])
   cleandata = [] 
   for user in userdata:
         cleandata.append( user[0].strip())
   return (1,cleandata)

########################################
# workspace functions
########################################
def add_workspace(workspace, user):
   # make sure the new user exists
   # this function is used both for adding a brand new workspace 
   # as well as adding a user to the workspace
   # for adding a new workspace, it is a given that the user exists since
   # we are using the callers username
   # but for adding a new users, it is not and must explicitly be checked  
   data_tuple = (user,)
   print("trying to add ", user, "to workspace", workspace)
   sql_statement = "SELECT username FROM users WHERE username = %s;"
   try:
      db = IpamDB()
      userdata = db.sfo(sql_statement, data_tuple)[0].strip()
   except Exception as e:
      db.rollback()
      return (0, "unable to connect to database to get user details " + str(e) )
   if userdata != user:
      return (0, "unable to verify new users exists" )

   # make sure there is no such mapping already
   data_tuple_a = (workspace.workspacename, user)  
   sql_statement_a = "SELECT COUNT(*) FROM workspaces WHERE name = %s AND username = %s;"  
   try:
      count = db.sfo( sql_statement_a, data_tuple_a)[0]  
      print( "COUNT", count, "datatuple", data_tuple_a)
   except Exception as e:
     db.rollback()
     return (0, "unable to connect to database to get user workspace details , " +str(e)  )
   #db.commit()
   if count != 0:
     return (0, "This user/workspace mapping already exists in database " + str(count) )

   # insert
   data_tuple_b = (workspace.workspacename, user)
   sql_statement_b = "INSERT INTO workspaces (name, username) VALUES (%s, %s) ;"
   try:
      db.ss( sql_statement_b, data_tuple_b)
   except Exception as e:
      db.rollback()
      return(0,"unable to add workspace " + str(e)) 
   db.commit()
   return(1,"")

def get_workspaces(username):
   data_tuple = (username,)
   sql_statement = "SELECT name FROM workspaces WHERE username = %s;"
   try:
      db = IpamDB()
      wsdata = db.sfa( sql_statement, data_tuple )
   except Exception as e:
      db.rollback()
      return (0, "get workspaces error " + str(e))
   db.commit()
   if wsdata == []:
      return(0, "no workspace for this user")

   cleandata = []
   for data in wsdata:
      cleandata.append({ "workspacename" : data[0].strip() })

   return (1, cleandata)

def delete_user_from_workspace(username, workspace):
   # does the user belong to this workspace? 
   if not authorized( username, workspace.workspacename):
      return (0, "user not authorized for this workspace")
   # is this the last user in the workspace?
   data_tuple = (workspace.workspacename,)
   sql_statement  = "SELECT * FROM workspaces WHERE name = %s"
   try:
      db = IpamDB()
      rowcount = db.srow( sql_statement, data_tuple)
   except Exception as e:
      db.rollback()
      return(0,"unable to determine if this is the last user " + str(e) ) 
   if rowcount < 2:
      db.commit()
      return (0, "Can't delete the last user in a workspace")
   data_tuple_b  = (workspace.workspacename, username)
   sql_statement_b = "DELETE FROM workspaces WHERE name = %s AND username = %s;"   
   try:
      db.ss( sql_statement_b, data_tuple_b)
   except Exception as e:
      db.rollback()
      return(0,"unable to delete from workspace " + str(e))
   db.commit()
   return(1,"")

def delete_workspace(username, workspacename):
   # does the user belong to this workspace? 
   if not authorized(username, workspacename):
       return (0, "user not authorized for this workspace")
   # does this workspace own objects, if so they need to be deleted first
   data_tuple = ( workspace, )
   sql_query = "SELECT COUNT(*) FROM networks WHERE workspace = %s"
   try:
      db = IpamDB()
      count = db.sfo(sql_query, data_tuple)[0]
   except Exception as e:
      db.rollback()
      return (0, "unable to determine if objects are present for this workspace, " + str(e))
   if count != 0 :
       db.commit()
       return (0, "Objects are still owned by this workspace, cant delete. Number of objects: "+ count) 
   # is this the last user in the workspace, it must be for it to be deleted
   data_tuple_b = (workspacename,)
   sql_statement_b  = "SELECT * FROM workspaces WHERE name = %s"
   try:
      rowcount = db.srow( sql_statement_b, data_tuple_b)
   except Exception as e:
      db.rollback()
      return(0,"unable to make sure this is the last user " + str(e))
   if rowcount != 1:
      db.rollback()
      return (0, "Can't delete workspace unless only the final user remains, please remove any other users first")
   data_tuple_c  = (workspacename, username)
   sql_statement_c = "DELETE FROM workspaces WHERE name = %s AND username = %s"   
   try:
      db.ss( sql_statement_c, data_tuple_c)
   except Exception as e:
      db.rollback() # there is really nothing to roll back but still to be safe
      return(0, "Unable to insert into database " + str(e) ) 
   db.commit()
   return (1, "")

#############################################
# network functions
#############################################

# TRANSACTION SAFE
def add_network(net):
   try:
      network = ipaddress.ip_network( net.ipnet , strict=True )
   except Exception as e:
      return  {"error" : "unable to process network, address is incorrect , " + str(e) }   
   first = str(network.network_address)
   last  = str(network.broadcast_address)    
   data_tuple = (first, last, net.vrf, net.workspace, net.comment, net.current_status )
   sql_statement = "INSERT INTO networks (first, last, vrf, workspace, comment, current_status) VALUES (%s,%s,%s,%s,%s,%s );"
   try:
      db = IpamDB()
      db.ss( sql_statement, data_tuple)
   except Exception as e:
      db.rollback()
      return {"error" : "unable to connect to database to add network , " +str(e) }
   db.commit()
   return {"ipnet" : str(network), "vrf": net.vrf, "workspace": net.workspace, "comment": net.comment, "current_status" : net.current_status} 

########################################################################
# takes a list of type netSplit of old network                         # 
# and a list of new networks of type fullNet                           #
# delete the old network                                               #
# add the new network                                                  #
########################################################################
def del_then_add_network(oldnets, newnets):
   for oldnet in oldnets:
      first_o = str( ipaddress.ip_network(oldnet.ipnet).network_address)
      last_o  = str( ipaddress.ip_network(oldnet.ipnet).broadcast_address)
      data_tuple = (first_o, last_o, oldnet.vrf, oldnet.workspace)
      sql_statement_a = "DELETE FROM networks WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace=%s;"
      try:
         db = IpamDB()
         db.ss(sql_statement_a, data_tuple)
      except Exception as e:
         db.rollback() 
         return (0,"unable to delete network ," + str(e))  
   for newnet in newnets: 
      first_n = str( ipaddress.ip_network(newnet.ipnet).network_address)
      last_n  = str( ipaddress.ip_network(newnet.ipnet).broadcast_address)
      # grab comment and status from the first element of old network
      data_tuple = (first_n, last_n, newnet.vrf, newnet.workspace, newnet.comment, newnet.current_status )
      sql_statement_b = "INSERT INTO networks (first, last, vrf, workspace, comment, current_status ) VALUES (%s,%s,%s,%s,%s,%s);"
      try:
         db.ss( sql_statement_b, data_tuple)
      except Exception as e:
         db.rollback()
         return (0, "unable to connect to database to add network , " + str(e)) 
   db.commit() 
   return (1,"")  
   
# TRANSACTION SAFE
def get_network(net):
   try:
      network = ipaddress.ip_network( net.ipnet , strict=True )
   except Exception as e:
      return  {"error" : "unable to process network, address is incorrect , " + str(e) }   
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, net.vrf, net.workspace)
   sql_statement = "SELECT * FROM networks WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      db = IpamDB()
      ipdata = db.sfo( sql_statement, data_tuple)
   except Exception as e:
      db.rollback()
      return {"error" : "unable to connect to database to get network details, " + str(e) } 
   if ipdata is None:
      db.rollback() 
      return {"error" : "no such network, " + str(network) } 
   db.commit()
   try:
      newnet = first_last_to_net(ipdata[0], ipdata[1])
   except Exception as e: 
      return { "error" : "Unable to convert database info to network, " + str(e)}  
   return { "ipnet" : newnet, "vrf" : ipdata[2], "workspace" : ipdata[3], "comment" : ipdata[4], "current_status" : ipdata[5] }

# TRANSACTION SAFE
def get_overlaps(network , vrf, workspace):
    overlapping = [] 
    cleaned_overlapping = [] 
    first = str(network.network_address)
    last  = str(network.broadcast_address)
    data_tuple = ( last, first, vrf, workspace) 
    sql_query = "SELECT * FROM networks WHERE first <= (inet %s) AND last >= (inet %s) AND vrf = %s AND workspace = %s"
    try: 
       db = IpamDB()
       overlapping = db.sfa(sql_query, data_tuple)
    except Exception as e:
       db.rollback() 
       return (0, "Unable to get overlaps from database, " + str(e)  )
    db.commit()
    for net in overlapping:
      try:
         newnet = first_last_to_net(net[0], net[1]) 
      except:
         return (0,"Unable to create network/mask from one of the found network, database unclean")   
      cleaned_overlapping.append( {"ipnet" : newnet, "vrf" : net[2].strip(), "workspace" : net[3].strip(), "comment" : net[4].strip(), "current_status" : net[5] } )
    return (1, cleaned_overlapping)   

# TRANSACTION SAFE
def delete_net(network, vrf, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, vrf, workspace)
   sql_query = "DELETE FROM networks WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace=%s;"
   try:
      db = IpamDB()
      db.ss(sql_query, data_tuple)
   except Exception as e:
      db.rollback()
      return (0, "Unable to delete from database, " + str(e))
   db.commit() 
   return(1,"")

# updates vrf, comment and status for a network in oldvrf in workspace 
def edit_network(network, oldvrf, newvrf, comment, current_status, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (newvrf, comment, current_status, first, last, oldvrf, workspace)
   sql_query = "UPDATE networks SET vrf = %s, comment = %s, current_status=%s WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      db = IpamDB()
      rowcount = db.srow( sql_query, data_tuple)
   except Exception as e:
      db.rollback()
      return (0, "Unable to edit network ," + str(e))
   db.commit() 
   if rowcount == 0:
      return (0, "Unable to edit, network not found")
   return (1,"")

# TRANSACTION SAFE   
def authenticate( username, password):
   #try:
   db = IpamDB()
   hashfromdb = db.sfo("SELECT PASSWORD FROM users WHERE username = %s", (username,))[0]
   if hashfromdb == None:
      print("username ", username, " doesn't have a password in the db")
      return False
   #print("result", result)
   #except:
   #   db.rollback()
   #   return False
   db.commit()
   pwdsalt  = password + config["salt"]
   hashfromuser = (hashlib.sha512(pwdsalt.encode())).hexdigest()
   if( hashfromdb.strip() == hashfromuser ): 
      return True 
   else:
      print("from db--->" + str(hashfromdb) + "<-- from user -->" + str(hashfromuser) + "<-- end" ) 
      return False 

# TRANSACTION SAFE
def authorized( username, workspace):
   try:
      db = IpamDB()
      result = db.sfo("SELECT NAME FROM workspaces WHERE username =%s AND name =%s", (username, workspace))[0].strip()
   except Exception as e:
       print( "Failed", str(e))
       db.rollback()
       return False
   db.commit() 
   if result: 
      return True 
   else:
      return False



########################################################################################
# Host functions
########################################################################################
def add_host(host):
   try:
      ip = ipaddress.ip_address( host.ip )
   except Exception as e:
      return  {"error" : "unable to process ip address, address is incorrect , " + str(e) }     
   #Make sure there is a network that is available or in-use before adding
   if ip.version == 4:
      mask = "32"
   else:
      mask = "128"
   net_enclosing = ipaddress.ip_network(str(ip) + "/" + mask )
   a = get_overlaps( net_enclosing, host.vrf, host.workspace) 
   if a[0] == 0:
      return {"error" : "unable to get overlaps for this host , " + str(a[1]) }  
   overlap_status = a[1][0]["current_status"] # we know there is only one overlap on /32 or /128 so we can check item 0 on the returned list. The list is given in pos 1 of the return tuple
   overlap_first  = str(ipaddress.ip_network(a[1][0]["ipnet"]).network_address)

   if( overlap_status != 'available' and overlap_status != 'used'):
      return  {"error" : "Cannot add IP. The network requested " + str(net_enclosing) + " is not in status available or used" }   
   data_tuple_b = (host.ip, overlap_first, host.vrf, host.workspace, host.hostname, host.comment )
   sql_statement_b = "INSERT INTO hosts (ip, first, vrf, workspace, hostname, comment) VALUES (%s,%s,%s,%s,%s,%s );"
   try:
      db = IpamDB()
      db.ss( sql_statement_b, data_tuple_b)
   except Exception as e:
      db.rollback()
      return {"error" : "unable to connect to database to add network , " +str(e) }
   db.commit()
   return host.dict() 

def get_host(host):
   try:
      host_validated = str(ipaddress.ip_address( host.ip ))
   except Exception as e:
      return  {"error" : "unable to process address, address is incorrect , " + str(e) }   
   data_tuple = (host_validated, host.vrf, host.workspace)
   sql_statement = "SELECT * FROM hosts WHERE ip = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      db = IpamDB()
      hostdata = db.sfo( sql_statement, data_tuple)
   except Exception as e:
      db.rollback()
      return {"error" : "unable to connect to database to get host details, " + str(e) } 
   if hostdata is None:
      db.commit()
      return {"error" : "no such address, " + str(host.ip) } 
   db.commit()
   return { "ip" : hostdata[0], "first" : hostdata[1], "vrf" : hostdata[2].strip(), "workspace" : hostdata[3].strip(), "hostname" : hostdata[4].strip(), "comment" : hostdata[5].strip() }

def delete_host(host):
   data_tuple = (host.ip, host.vrf, host.workspace)
   sql_query = "DELETE FROM hosts WHERE ip = (inet %s) AND vrf = %s AND workspace=%s;"
   try:
      db = IpamDB()
      db.ss(sql_query, data_tuple)
   except Exception as e:
      db.rollback()
      return (0, "Unable to delete from database, " + str(e))
   db.commit()
   return(1,"")

def edit_host(hostIn):
   # fixme, if none is given as comment or vrf it shouldn't overwrite with none
   data_tuple = (hostIn.newvrf, hostIn.hostname, hostIn.comment, hostIn.ip, hostIn.vrf, hostIn.workspace)
   sql_query = "UPDATE hosts SET vrf = %s, hostname = %s, comment=%s WHERE ip = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      db = IpamDB()
      rowcount = db.srow( sql_query, data_tuple)
   except Exception as e:
      db.rollback() 
      return (0, "Unable to edit host ," + str(e))
   db.commit() 
   if rowcount == 0:
      return (0, "Unable to edit, host not found")
   return (1,"")
