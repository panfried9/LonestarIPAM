import psycopg2
from fastapi import HTTPException
import ipaddress

conn = psycopg2.connect( host="localhost", database="ipam", user="postgres", password="xxx777&")

def addresses_to_mask(first, last):
   # FIXME, if first and last is not a network, raise exception and catch on the caller side so that we can save ranges as well
   print("in the addresses to mask function", last, first)
   f = ipaddress.ip_address(first)
   l = ipaddress.ip_address(last)
   if f.version == 4:
      # converts a number of hosts (including broadcast and network) into a subnet size
      diff = int(l) - int(f) + 1
      m = 35-len(str(bin(diff)))
      return m
   else:
      diff = int(l) - int(f) + 1 
      m =  131-len(str(bin(diff)))
      return m

def add_user(newuser, newpass, currentuser):
   data_tuple = (newuser, newpass, newuser)
   sql_statement = "INSERT INTO users (username, password) SELECT %s, %s WHERE NOT EXISTS (SELECT username FROM users WHERE username = %s);"
   return dbexecute(sql_statement, data_tuple)

def delete_user(currentuser):
   data_tuple = (currentuser,)
   sql_statement = "DELETE FROM users WHERE username = %s;"
   return dbexecute(sql_statement, data_tuple)

# returns all users in the system 
def get_user():
   sql_statement = "SELECT username FROM users;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement)
      conn.commit()
      userdata = cur.fetchall()
      print("userdata", userdata)
      cur.close() 
   except:
      return (0, "unable to connect to database to get user details" )
      #raise HTTPException(status_code=500, detail="unable to connect to database to get user details")
   if userdata is None:
      return (0, "No users found")
      #raise HTTPException(status_code=500, detail="No users found" )
   cleandata = [] 
   for user in userdata:
         cleandata.append( user[0].strip())
   return (1,cleandata)

def user_exists(username): 
   data_tuple = (username,) 
   sql_statement = "SELECT username FROM users WHERE username = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      userdata = cur.fetchone()[0].strip() 
      cur.close()
   except:
      return (0, "unable to connect to database to get user details" )
      #raise HTTPException(status_code=500, detail="unable to connect to database to get user details")
   if userdata == username:
      return (1, username) 
   else:
      return (0, "Could not find this user in the database") 

########################################
# workspace functions
########################################
def add_workspace(name, currentuser):
   data_tuple = (name, currentuser, name, currentuser)
   sql_statement = "INSERT INTO workspaces (name, username) SELECT %s, %s WHERE NOT EXISTS (SELECT name, username FROM workspaces WHERE name = %s AND username = %s);"
   a = dbexecute(sql_statement, data_tuple)
   return a

def get_workspaces(username):
   data_tuple = (username,)
   sql_statement = "SELECT name FROM workspaces WHERE username = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple )
      conn.commit()
      wsdata = cur.fetchall()
      cur.close() 
   except Exception as e:
      return (0, "get workspaces error " + str(e))
      #raise HTTPException(status_code=500, detail="get workspaces error " + str(e) )
   cleandata = []
   for data in wsdata:
      cleandata.append(data[0].strip())
   return (1, cleandata)

def delete_user_from_workspace(username, workspacename):
   # does the user belong to this workspace? 
   status, wslist = get_workspaces(username)
   if status == 0:
      return (0, wslist)
   if workspacename not in wslist:
      return (0, "User is not in this workspace" + str(wslist) + " " + workspacename)
      #raise HTTPException(status_code=500, detail = "User not in this workspace")    

   # is this the last user in the workspace?
   data_tuple = (workspacename,)
   sql_statement  = "SELECT * FROM workspaces WHERE name = %s"
   if dbexecute(sql_statement , data_tuple ) < 2:
      return (0, "Can't delete the last user in a workspace")
      #raise HTTPException(status_code=500, detail = "Can't delete the last user in a workspace.")
   data_tuple_b  = (workspacename, username)
   print("USERNAME...", username)
   sql_statement_b = "DELETE FROM workspaces WHERE name = %s AND username = %s;"   
   return (1, dbexecute(sql_statement_b, data_tuple_b))


def delete_workspace(username, workspacename):
   # does the user belong to this workspace? 
   status, wslist = get_workspaces(username)
   if status == 0:
      return (0, wslist)
   if workspacename not in wslist:
      return (0, "User is not in this workspace")

   # does this workspace own objects, if so they need to be deleted first
   a = get_workspace_object_count( workspacename )
   if a != 0 :
       return(0, "Objects are still owned by this workspace, can't delete. Number of objects:" + str(a))  

   # is this the last user in the workspace, it must be for it to be deleted
   data_tuple = (workspacename,)
   sql_statement  = "SELECT * FROM workspaces WHERE name = %s"
   if dbexecute(sql_statement , data_tuple ) != 1:
      return (0, "Can't workspace unless only the final user remains, please remove any other users first")
   data_tuple_b  = (workspacename, username)
   sql_statement_b = "DELETE FROM workspaces WHERE name = %s AND username = %s"   
   return (1, dbexecute(sql_statement_b, data_tuple_b))

#############################################
# network functions
#############################################

# add network, returns 1 if successful
def add_network(network, vrf, workspace, comment):
   first = str(network.network_address)
   last  = str(network.broadcast_address)    
   data_tuple = (first, last, vrf, workspace, comment)
   sql_statement = "INSERT INTO IPAM (FIRST, LAST, VRF, WORKSPACE, COMMENT) VALUES (%s,%s,%s,%s,%s);"
   st, list_of_overlaps = get_overlaps( network, vrf, workspace)
   if st == 0:
      return (0, list_of_overlaps)
   if( len(list_of_overlaps) > 0 ):
      return (0, "overlaps with existing network")
   return (1, dbexecute(sql_statement, data_tuple))


def get(network, vrf):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   print("trying to get", first, last, vrf)
   data_tuple = (first, last, vrf)
   sql_statement = "SELECT * FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      ipdata = cur.fetchone()
      cur.close() 
   except:
      print("SQL error")
      return {"status" : 0, "error" : "unable to connect to database to get network details" } 
      #raise HTTPException(status_code=500, detail="unable to connect to database to get network details")
   if ipdata is None:
      print("ip data is none -->", str(sql_statement), str(data_tuple))
      return {"status" : 0, "error" : "no such network" } 
      #raise HTTPException(status_code=500, detail="No such network" )
   # FIXME, implement a filter function to remove certain data
   print("About to return this:", ipdata)
   mask = addresses_to_mask(ipdata[0], ipdata[1])
   return { "status": 1 , "error" : "", "network" : ipdata[0] +"/"+ str(mask), "vrf" : ipdata[2], "workspace" : ipdata[3], "comment" : ipdata[4] }

def get_workspace_object_count( workspace):
    data_tuple = ( workspace, )
    sql_query = "SELECT COUNT(*) FROM IPAM WHERE workspace = %s"
    #try:
    cur = conn.cursor()
    cur.execute(sql_query, data_tuple)
    count = cur.fetchone()[0]
    print("count is ", count )
    cur.close()
    #except Exception as e:
    #   print("Warning: ", str(e))
    #   raise KeyError("overlap or database error")
    return count 



def get_overlaps(network , vrf, workspace):
    overlapping = [] 
    cleaned_overlapping = [] 
    first = str(network.network_address)
    last  = str(network.broadcast_address)
    data_tuple = ( last, first, vrf, workspace) 
    sql_query = "SELECT * FROM IPAM WHERE first <= (inet %s) AND last >= (inet %s) AND vrf = %s AND workspace = %s"
    try: 
       cur = conn.cursor() 
       cur.execute(sql_query, data_tuple)
       overlapping = cur.fetchall()
       cur.close()
    except Exception as e:
       return (0, "database error" )
       #raise KeyError("No overlap or database error")
    for net in overlapping:
      mask = addresses_to_mask(net[0], net[1]) 
      cleaned_overlapping.append( str(net[0]) + "/" + str(mask) )
    return (1, cleaned_overlapping)   

#FIXME, need to convert into using len( get_overlaps)
#def count_overlaps(first, last , vrf):
#    print("IN THE COUNT OVERLAPS FUNCTION")
#    data_tuple = ( last, first, vrf) 
#    sql_query = "SELECT COUNT(*) FROM IPAM WHERE first <= (inet %s) AND last >= (inet %s) AND vrf = %s"
#    try: 
#       cur = conn.cursor() 
#       cur.execute(sql_query, data_tuple)
#       numi = cur.fetchone()[0]
#       cur.close()
#    except Exception as e:
#       print("E:", str(e)) 
#       raise HTTPException(status_code=500, detail="Unable to verify overlaps, database issue") 
#    return numi


def delete(network, vrf):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, vrf)
   sql_query_a = "SELECT COUNT(*) FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s;"
   sql_query = "DELETE FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_query_a, data_tuple)
      numi = cur.fetchone()[0]
   except Exception as e:
      raise HTTPException(status_code=500,detail="Unable to verify that the network is in the database "+ str(e) )
   if numi != 1:
      raise HTTPException(status_code=500, detail="Network not found or not unique when trying to delete " + str(numi) )
   try:
      cur.execute(sql_query, data_tuple)
      conn.commit()
      cur.close()
   except Exception as e:
      raise HTTPException(status_code=500, detail="Unable to delete " + str(e) )

def edit(network, oldvrf, newvrf, comment):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (newvrf, comment, first, last, oldvrf)
   sql_query = "UPDATE IPAM SET vrf = %s, comment = %s WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s"
   print("WILL try to run ", sql_query)
   try:
      cur = conn.cursor()
      cur.execute( sql_query, data_tuple)
   except Exception as e:
      raise HTTPException(status_code=500, detail="Unable to update " + str(e) )
   if cur.rowcount == 0:
         raise HTTPException(status_code=500, detail="Unable to update, network not found")
   conn.commit()
   cur.close()
   return
   


def dbexecute(sql_statement, data_tuple):
   try:   
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple) 
      conn.commit() 
      cur.close()
   except Exception as e:
      print(str(sql_statement) + str(data_tuple))
      raise HTTPException(status_code=500, detail="Unable to insert into database " + str(e) )
   return cur.rowcount

def authenticate( username, password):
   try:
      print( "username and password to validate", username, password )
      cur = conn.cursor()
      cur.execute("SELECT PASSWORD FROM users WHERE username = %s", (username,))
      result = cur.fetchone()[0].strip()
      print( result )
      cur.close()
   except:
      return False
   if( result == password ): 
      print("user is authenticated")
      return True 
   else:
      print("no match", result, password )
      return False 


def authorized( username, workspace):

   print( "username and workspace to validate", username, workspace )
   try:
      cur = conn.cursor()
      cur.execute("SELECT NAME FROM workspaces WHERE username = %s AND name = %s", (username, workspace))
      result = cur.fetchone()[0].strip()
      print( result )
      cur.close()
   except Exception as e:
      print("ERROR, ", e )
      return False
   if result : 
      print("user is authorized")
      return True 
   else:
      print("no match", result, workspace )
      return False 
