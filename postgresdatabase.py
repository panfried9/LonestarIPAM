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

# TRANSACTION SAFE
def add_user(newuser, newpass):
   data_tuple = (newuser, newpass, newuser)
   sql_statement = "INSERT INTO users (username, password) SELECT %s, %s WHERE NOT EXISTS (SELECT username FROM users WHERE username = %s);"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
   except Exception as e:
      conn.rollback()
      cur.close()
      return(0, "Error when trying to add user " + str(e))  
   cur.close()
   return (1,"") 

# TRANSACTION SAFE
def delete_user(currentuser):
   data_tuple = (currentuser,)
   sql_statement = "DELETE FROM users WHERE username = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
   except Exception as e:
      cur.close()
      return(0, "Unable to delete user " + str(e) ) 
   cur.close()
   return(1,"")

# TRANSACTION SAFE
# returns all users from a workspace 
def get_user(workspace):
   data_tuple = (workspace,)
   sql_statement = "SELECT username FROM users WHERE workspace = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      userdata = cur.fetchall()
   except:
      cur.close()
      return (0, "unable to connect to database to get user details" )
   cur.close()
   if userdata is None:
      return (1, [])
   cleandata = [] 
   for user in userdata:
         cleandata.append( user[0].strip())
   return (1,cleandata)

########################################
# workspace functions
########################################
# TRANSACTION SAFE
def add_workspace(name, user):
   # make sure the new user exists
   # this function is used both for adding a brand new workspace 
   # as well as adding a user to the workspace
   # for adding a new workspace, it is a given that the user exists since
   # we are using the callers username
   # but for adding a new users, it is not and must explicitly be checked  
   data_tuple = (user,)
   sql_statement = "SELECT username FROM users WHERE username = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      userdata = cur.fetchone()[0].strip()
   except:
      cur.close()
      return (0, "unable to connect to database to get user details" )
   if userdata != user:
      return (0, "unable to verify new users exists" )

   # make sure there is no such mapping already
   data_tuple_a = (name, user)  
   sql_statement_a = "SELECT COUNT(*) FROM workspaces WHERE name = %s AND username = %s;" 
   try:
     cur.execute( sql_statement_a, data_tuple_a) 
     count = cur.fetchone()[0]
   except Exception as e:
      cur.close()
      return (0, "unable to connect to database to get user workspace details , " +str(e)  )
   if count != 0:
      return (0, "This user/workspace mapping already exists in database " )

   # insert
   data_tuple_b = (name, user)
   sql_statement_b = "INSERT INTO workspaces (name, username) VALUES (%s, %s) ;"
   try:
      cur.execute( sql_statement_b, data_tuple_b)
      conn.commit()
   except Exception as e:
      conn.rollback()
      cur.close()
      return(0,"unable to add workspace " + str(e)) 
   cur.close() 
   return(1,"")

# TRANSACTION SAFE
def get_workspaces(username):
   data_tuple = (username,)
   sql_statement = "SELECT name FROM workspaces WHERE username = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple )
      #conn.commit()
      wsdata = cur.fetchall()
   except Exception as e:
      cur.close()
      return (0, "get workspaces error " + str(e))
   cur.close() 
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
   except Exception as e:
      cur.close()
      return(0,"unable to determine if this is the last user " + str(e) ) 
   if cur.rowcount < 2:
      cur.close()
      return (0, "Can't delete the last user in a workspace")
   data_tuple_b  = (workspacename, username)
   sql_statement_b = "DELETE FROM workspaces WHERE name = %s AND username = %s;"   
   try:
      cur.execute( sql_statement_b, data_tuple_b)
      conn.commit()
   except Exception as e:
      cur.close()
      return(0,"unable to delete from workspace " + str(e))
   cur.close()
   return(1,"")

# TRANSACTION SAFE
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
   except Exception as e:
      cur.close()
      return (0, "unable to determine if objects are present for this workspace, " + str(e))
   if count != 0 :
       cur.close()
       return (0, "Objects are still owned by this workspace, cant delete. Number of objects: "+ count) 
   # is this the last user in the workspace, it must be for it to be deleted
   data_tuple_b = (workspacename,)
   sql_statement_b  = "SELECT * FROM workspaces WHERE name = %s"
   try:
      cur.execute( sql_statement_b, data_tuple_b)
   except Exception as e:
      cur.close()
      return(0,"unable to make sure this is the last user " + str(e))
   if cur.rowcount != 1:
      cur.close()
      return (0, "Can't delete workspace unless only the final user remains, please remove any other users first")
   data_tuple_c  = (workspacename, username)
   sql_statement_c = "DELETE FROM workspaces WHERE name = %s AND username = %s"   
   try:
      cur.execute( sql_statement_c, data_tuple_c)
   except Exception as e:
      conn.rollback() # there is really nothing to roll back but still to be safe
      cur.close()
      return(0, "Unable to insert into database " + str(e) ) 
   conn.commit()
   cur.close()
   return (1, "")

#############################################
# network functions
#############################################

# TRANSACTION SAFE
def add_network(network, vrf, workspace, comment):
   first = str(network.network_address)
   last  = str(network.broadcast_address)    
   data_tuple = (first, last, vrf, workspace, comment )
   sql_statement = "INSERT INTO ipam (first, last, vrf, workspace, comment) VALUES (%s,%s,%s,%s,%s );"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      conn.commit()
   except Exception as e:
      conn.rollback()
      cur.close() 
      return {"status" : 0, "error" : "unable to connect to database to add network , " +str(e) }
   cur.close() 
   return {"status" :1, "error" : ""} 

# TRANSACTION SAFE
def del_then_add_network(oldnets, vrf, workspace, newnets, comment, in_status):
   print("IN STATUS, ", in_status) 
   cur = conn.cursor()
   for oldnet in oldnets:
      print("OLDNET: ", str(oldnet) )  
      first_o = str(oldnet.network_address)
      last_o  = str(oldnet.broadcast_address)
      data_tuple = (first_o, last_o, vrf, workspace)
      sql_query = "DELETE FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace=%s;"
      try:
         cur.execute(sql_query, data_tuple)
      except Exception as e:
         cur.rollback() 
         cur.close()
         return (0,"unable to delete network ," + str(e))  

   for newnet in newnets: 
      first_n = str(newnet.network_address)
      last_n  = str(newnet.broadcast_address)
      data_tuple = (first_n, last_n, vrf, workspace, comment, in_status )
      
      sql_statement = "INSERT INTO ipam (first, last, vrf, workspace, comment, current_status ) VALUES (%s,%s,%s,%s,%s,%s);"
      try:
         cur.execute( sql_statement, data_tuple)
      except Exception as e:
         conn.rollback()
         cur.close()
         return (0, "unable to connect to database to add network , " +str(e)) 
   conn.commit() 
   cur.close()
   return (1,"")  
   


# TRANSACTION SAFE
def get_network(network, vrf, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, vrf, workspace)
   sql_statement = "SELECT * FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_statement, data_tuple)
      ipdata = cur.fetchone()
   except Exception as e:
      cur.close() 
      return {"status" : 0, "error" : "unable to connect to database to get network details, "+str(e) } 
   if ipdata is None:
      cur.close() 
      return {"status" : 0, "error" : "no such network, " + str(network) } 
   cur.close() 
   # FIXME, implement a filter function to remove certain data
   try:
      newnet = first_last_to_net(ipdata[0], ipdata[1])
   except Exception as e: 
      return { "status" : 0, "error" : "Unable to convert database info to network, " + str(e)}  
   return { "status": 1 , "error" : "", "network" : newnet, "vrf" : ipdata[2], "workspace" : ipdata[3], "comment" : ipdata[4], "current_status" : ipdata[5] }

# TRANSACTION SAFE
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
    except Exception as e:
       cur.close() 
       return (0, "Unable to get overlaps from database, " + str(e)  )
    cur.close() 
    for net in overlapping:
      try:
         newnet = first_last_to_net(net[0], net[1]) 
      except:
         return (0,"Unable to create network/mask from one of the found network, database unclean")   
      cleaned_overlapping.append( newnet )
    return (1, cleaned_overlapping)   

# TRANSACTION SAFE
def delete(network, vrf, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (first, last, vrf, workspace)
   sql_query = "DELETE FROM IPAM WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace=%s;"
   try:
      cur = conn.cursor()
      cur.execute(sql_query, data_tuple)
      conn.commit()
   except Exception as e:
      cur.close()
      return (0, "Unable to delete from database, " + str(e))
   cur.close() 
   return(1,"")

# TRANSACTION SAFE
# updates vrf, comment and status for a network in oldvrf in workspace 
def edit_network(network, oldvrf, newvrf, comment, current_status, workspace):
   first = str(network.network_address)
   last  = str(network.broadcast_address)
   data_tuple = (newvrf, comment, current_status, first, last, oldvrf, workspace)
   sql_query = "UPDATE IPAM SET vrf = %s, comment = %s, current_status=%s WHERE first = (inet %s) AND last = (inet %s) AND vrf = %s AND workspace = %s;"
   try:
      cur = conn.cursor()
      cur.execute( sql_query, data_tuple)
      conn.commit()
   except Exception as e:
      cur.close() 
      return (0, "Unable to edit network ," + str(e))
   cur.close() 
   if cur.rowcount == 0:
      return (0, "Unable to edit, network not found")
   return (1,"")

# TRANSACTION SAFE   
def authenticate( username, password):
   try:
      cur = conn.cursor()
      cur.execute("SELECT PASSWORD FROM users WHERE username = %s", (username,))
      result = cur.fetchone()[0].strip()
   except:
      cur.close() 
      return False
   cur.close()
   if( result == password ): 
      return True 
   else:
      return False 

# TRANSACTION SAFE
def authorized( username, workspace):
   try:
      cur = conn.cursor()
      cur.execute("SELECT NAME FROM workspaces WHERE username =%s AND name =%s", (username, workspace))
      result = cur.fetchone()[0].strip()
   except Exception as e:
      cur.close()
      return False
   cur.close() 
   if result: 
      return True 
   else:
      return False 
