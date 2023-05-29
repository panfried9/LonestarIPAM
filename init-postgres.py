import psycopg2

conn = psycopg2.connect( host="localhost", database="ipam", user="postgres", password="xxx777&")

sql_statement1 = "DROP TABLE ipam;"
sql_statement2 = "DROP TABLE users;"
sql_statement3 = "CREATE TABLE ipam (FIRST INET, LAST INET, OWNER CHAR(50), VRF CHAR(50));"
sql_statement4 = "CREATE TABLE users (USERNAME CHAR(50), PASSWORD CHAR(50));"

# add admin users
sql_statement5 = "INSERT INTO users (USERNAME, PASSWORD) VALUES ('stephan', 'mufflers');"

cur = conn.cursor()
cur.execute( sql_statement1)
cur.execute( sql_statement2)
cur.execute( sql_statement3)
cur.execute( sql_statement4)
cur.execute( sql_statement5)

conn.commit()
cur.close()

