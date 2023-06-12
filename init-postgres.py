import psycopg2

conn = psycopg2.connect( host="localhost", database="ipam", user="postgres", password="xxx777&")

sql_statement = [] 

sql_statement.append("DROP TABLE ipam;")
sql_statement.append("DROP TABLE users;")
sql_statement.append("DROP TABLE workspaces;")
sql_statement.append("CREATE TABLE ipam (FIRST INET PRIMARY KEY, LAST INET, VRF CHAR(50), WORKSPACE CHAR(50), COMMENT CHAR(200) );")
sql_statement.append("CREATE TABLE users (USERNAME CHAR(50), PASSWORD CHAR(50));")
sql_statement.append("CREATE TABLE workspaces (NAME CHAR(50), USERNAME CHAR(50));")

# add admin users
sql_statement.append("INSERT INTO users (USERNAME, PASSWORD) VALUES ('stephan', 'mufflers');")
sql_statement.append("INSERT INTO workspaces (NAME, USERNAME) VALUES ('admin', 'stephan');")



cur = conn.cursor()
for statement in sql_statement:
   cur.execute( statement)

conn.commit()
cur.close()

