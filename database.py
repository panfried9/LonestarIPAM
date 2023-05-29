from fastapi import HTTPException
import sqlite3
import ipaddress
import ipamconvert

conn = sqlite3.connect('ipam.db')
cursor = conn.cursor() 

def count_overlaps(f1, f2, e1, e2, vrf):
    if f2 is None: 
       data_tuple = ( f1, e1, vrf) 
       sql_query = "SELECT COUNT(*) FROM IPAM WHERE first <= ? AND last >= ? AND vrf == ?"
    else:
       # we are dealing with v6
       data_tuple = (f1,f2,e1,e2, vrf)
       sql_query = "SELECT COUNT(*) FROM IPAM WHERE first <= ? AND first6 <= ? AND last >= ? AND last6 >= ? AND vrf == ?"
    try: 
       cursor.execute(sql_query, data_tuple)
       conn.commit()
       numi = cursor.fetchone()[0]  
    except Exception as e:
       print("E:", str(e)) 
       raise HTTPException(status_code=500, detail="Unable to verify overlaps, database issue") 
    return numi 






def add(network, vrf): 
   if type(network) is ipaddress.IPv6Network: 
      f1, f2 = ipamconvert.six2two(network.network_address)
      e1, e2 = ipamconvert.six2two(network.broadcast_address)   
      data_tuple = (f1, f2, e1, e2, vrf)
      sql_query = "INSERT INTO IPAM (FIRST, FIRST6, LAST, LAST6, VRF) VALUES (?,?,?,?,?)"

      try:
         numi = count_overlaps( f1, f2, e1, e2, vrf)
      except Exception as e:
         raise HTTPException(status_code=500,detail="unable to connect to database to check for overlaps")
 
   else: 
      f1 = int(network.network_address)
      e1 = int(network.broadcast_address)
      data_tuple = (f1, e1, vrf)
      sql_query = "INSERT INTO IPAM (FIRST, LAST, VRF) VALUES (?,?,?)"

      try:
         numi = count_overlaps( f1, None, e1, None, vrf)
      except Exception as e:
         raise HTTPException(status_code=500,detail="unable to connect to database to check for overlaps")
   if( numi > 0 ):
      raise HTTPException(status_code=500, detail="overlaps with existing network" )
   try: 
      cursor.execute(sql_query, data_tuple)
      conn.commit()
   except Exception as e:
      print("EEEE:", e) 
      raise HTTPException(status_code=500,detail="unable to connect to database to insert new network") 
   return 




def get(network, vrf):
   if type(network) is ipaddress.IPv6Network:
      f1, f2 = ipamconvert.six2two(network.network_address)
      e1, e2 = ipamconvert.six2two(network.broadcast_address)  
      data_tuple = (f1, f2, e1, e2, vrf)
      sql_query = "SELECT * FROM IPAM WHERE first == ? AND first6 == ? AND last == ? AND last6 == ? AND vrf == ?"
   else:
      f1 = int(network.network_address)
      e1 = int(network.broadcast_address)
      data_tuple = (f1, e1, vrf) 
      sql_query = "SELECT * FROM IPAM WHERE first == ? AND last == ? AND vrf == ?" 
      print("OK lets query")
   try:   
      cursor.execute(sql_query, data_tuple) 
      ipdata = cursor.fetchone()
      print(ipdata) 
   except:
      raise HTTPException(status_code=500, detail="unable to connect to database to get network details") 
   if ipdata is None:
      raise HTTPException(status_code=500, detail="No such network" ) 
   # FIXME, remove the IP addresses. This is redundant info, caller already knows what network was asked for
    
   return ipdata



def delete(network, vrf): 
   if type(network) is ipaddress.IPv6Network:
      f1, f2 = ipamconvert.six2two(network.network_address)
      e1, e2 = ipamconvert.six2two(network.broadcast_address)
      data_tuple = (f1, f2, e1, e2, vrf)
      sql_query_a = "SELECT COUNT(*) FROM IPAM WHERE first == ? AND first6 == ? AND last == ? AND last6 == ? AND vrf == ?"
      sql_query = "DELETE FROM IPAM WHERE first == ? AND first6 == ? AND last == ? AND last6 == ? AND vrf == ?"


   else:
      f1 = int(network.network_address)
      e1 = int(network.broadcast_address)
      data_tuple = (f1, e1, vrf)
      sql_query_a = "SELECT COUNT(*) FROM IPAM WHERE first == ? AND last == ? AND vrf == ?"
      sql_query = "DELETE FROM IPAM WHERE first == ? AND last == ? AND vrf == ?"


   try: 
      cursor.execute(sql_query_a, data_tuple) 
      numi = cursor.fetchone()[0] 
   except Exception as e:
      raise HTTPException(status_code=500,detail="Unable to verify that the network is in the database "+ str(e) )
   if numi != 1:
      raise HTTPException(status_code=500, detail="Network not found or not unique when trying to delete" + str(numi) )
   try: 
      cursor.execute(sql_query, data_tuple)
      conn.commit()
   except Exception as e:
      raise HTTPException(status_code=500, detail="Unable to delete " + str(e) )  




