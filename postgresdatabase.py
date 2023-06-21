import psycopg2
from fastapi import HTTPException
import ipaddress

conn = psycopg2.connect( host="localhost", database="ipam", user="postgres", password="xxx777&")

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

def add_user(newuser, newpass):
   data_tuple = (newuser, newpass, newuser)
   sql_statement = "INSERT INTO users (username, password) SELECT %s, %s WHERE NOT EXISTS (SELECT username FROM users WHERE username = %s);"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0, "database connection fail while trying to add user " + str(e))  
   return (1,"") 

def delete_user(currentuser):
   data_tuple = (currentuser,)
   sql_statement = "DELETE FROM users WHERE username = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0, "Unable to delete user " + str(e) ) 
   return(1,"")

# returns all users from a workspace 
def get_user(workspace):
   data_tuple = (workspace,)
   sql_statement = "SELECT username FROM users WHERE workspace = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      userdata = cur.fetchall()
      cur.close() 
   except:
      return (0, "unable to connect to database to get user details" )
   if userdata is None:
      return (1, [])
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
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0,"unable to add workspace " + str(e)) 
   return(1,"")

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
   cleandata = []
   for data in wsdata:
      cleandata.append(data[0].strip())
   return (1, cleandata)

def delete_user_from_workspace(username, workspacename):
   # does the user belong to this workspace? 
   if not authorized( username, workspacename):
      return (0, "user not authorized for this workspace")
   # is this the last user in the workspace?
   data_tuple = (workspacename,)
   sql_statement  = "SELECT * FROM workspaces WHERE name = %s"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0,"unable to determine if this is the last user " + str(e) ) 
   if cur.rowcount < 2:
      return (0, "Can't delete the last user in a workspace")
   data_tuple_b  = (workspacename, username)
   sql_statement_b = "DELETE FROM workspaces WHERE name = %s AND username = %s;"   
   try:
      cur = conn.cursor()
      cur.execute( sql_statement_b, data_tuple_b)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0,"unable to delete from workspace " + str(e))
   return(1,"")

def delete_workspace(username, workspacename):
   # does the user belong to this workspace? 
   if not authorized(username, workspacename):
       return (0, "user not authorized for this workspace")
   # does this workspace own objects, if so they need to be deleted first
   data_tuple = ( workspace, )
   sql_query = "SELECT COUNT(*) FROM IPAM WHERE workspace = %s"
   try:
      cur = conn.cursor()
      cur.execute(sql_query, data_tuple)
      count = cur.fetchone()[0]
      cur.close()
   except Exception as e:
      return (0, "unable to determine if objects are present for this workspace, " + str(e))
   if count != 0 :
       return (0, "Objects are still owned by this workspace, cant delete. Number of objects: "+ count) 
   # is this the last user in the workspace, it must be for it to be deleted
   data_tuple_b = (workspacename,)
   sql_statement_b  = "SELECT * FROM workspaces WHERE name = %s"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement_b, data_tuple_b)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0,"unable to make sure this is the last user " + str(e))
   if cur.rowcount != 1:
      return (0, "Can't delete workspace unless only the final user remains, please remove any other users first")
   data_tuple_c  = (workspacename, username)
   sql_statement_c = "DELETE FROM workspaces WHERE name = %s AND username = %s"   
   try:
      cur = conn.cursor()
      cur.execute( sql_statement_c, data_tuple_c)
      conn.commit()
      cur.close()
   except Exception as e:
      return(0, "Unable to insert into database " + str(e) ) 
   return (1, "")

#############################################
# network functions
#############################################

# add network
def add_network(network, vrf, workspace, comment):
   first = str(network.network_address)
   last  = str(network.broadcast_address)    
   data_tuple = (first, last, vrf, workspace, comment)
   sql_statement = "INSERT INTO IPAM (FIRST, LAST, VRF, WORKSPACE, COMMENT) VALUES (%s,%s,%s,%s,%s);"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      cur.close()
   except:
      print("SQL error")
      return {"status" : 0, "error" : "unable to connect to database to add network" }
   return {"status" :1, "error" : ""} 


def get_network(network, vrf, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, vrf, workspace)
   sql_statement = "SELECT * FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
      ipdata = cur.fetchone()
      cur.close() 
   except:
      print("SQL error")
      return {"status" : 0, "error" : "unable to connect to database to get network details" } 
   if ipdata is None:
      print("ip data is none -->", str(sql_statement), str(data_tuple))
      return {"status" : 0, "error" : "no such network " + network } 
   # FIXME, implement a filter function to remove certain data
   try:
      newnet = first_last_to_net(ipdata[0], ipdata[1])
   except Exception as e: 
      return { "status" : 0, "error" : str(e)}  
   return { "status": 1 , "error" : "", "network" : newnet, "vrf" : ipdata[2], "workspace" : ipdata[3], "comment" : ipdata[4] }

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
       return (0, "Unable to get overlaps from database, " + str(e)  )
    for net in overlapping:
      try:
         newnet = first_last_to_net(net[0], net[1]) 
      except:
         return (0,"Unable to create network/mask from one of the found network, database unclean")   
      cleaned_overlapping.append( newnet )
    return (1, cleaned_overlapping)   

def delete(network, vrf, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, vrf, workspace)
   sql_query = "DELETE FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace=%s;"
   try:
      cur = conn.cursor()
      cur.execute(sql_query, data_tuple)
      conn.commit()
      cur.close()
   except Exception as e:
      return (0, "Unable to delete from database, " + str(e))
   return(1,"")


def edit_network(network, oldvrf, newvrf, comment, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (newvrf, comment, first, last, oldvrf, workspace)
   sql_query = "UPDATE IPAM SET vrf = %s, comment = %s WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_query, data_tuple)
      conn.commit()
      cur.close() 
   except Exception as e:
      return (0, "Unable to edit network ," + str(e))
   if cur.rowcount == 0:
      return (0, "Unable to edit, network not found")
   return (1,"")
   
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
