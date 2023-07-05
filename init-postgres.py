import psycopg2

conn = psycopg2.connect( host="localhost", database="ipam", user="postgres", password="xxx777&")

sql_statement = [] 

sql_statement.append("DROP TABLE ipam;")
sql_statement.append("DROP TABLE users;")
sql_statement.append("DROP TABLE workspaces;")
sql_statement.append("DROP TYPE status CASCADE;")
sql_statement.append("CREATE TYPE status AS ENUM ('unassigned','available', 'in-use-set', 'in-use-found', 'reserved', 'capped' );") 
sql_statement.append("CREATE TABLE ipam (first INET PRIMARY KEY, last INET, vrf CHAR(50), workspace CHAR(50), comment CHAR(200) , current_status status );")
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

