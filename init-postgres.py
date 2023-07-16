import psycopg2

conn = psycopg2.connect( host="localhost", database="ipam", user="postgres", password="xxx777&")

sql_statement = [] 

#sql_statement.append("DROP TABLE ipam;")
sql_statement.append("DROP TABLE networks CASCADE;")

sql_statement.append("DROP TABLE users;")
sql_statement.append("DROP TABLE workspaces;")
sql_statement.append("DROP TYPE status;")
sql_statement.append("DROP TABLE hosts;")

sql_statement.append("CREATE TYPE status AS ENUM ('reserved','available', 'used', 'capped' );") 
sql_statement.append("CREATE TABLE networks (first INET PRIMARY KEY, last INET, vrf CHAR(50), workspace CHAR(50), comment CHAR(200) , current_status status );")
sql_statement.append("CREATE TABLE hosts (ip INET PRIMARY KEY, first INET, vrf CHAR(50), workspace CHAR(50), hostname CHAR(255), comment CHAR(200) , CONSTRAINT fk_network FOREIGN KEY(first) REFERENCES networks(first) );")


sql_statement.append("CREATE TABLE users (USERNAME CHAR(50), PASSWORD CHAR(50));")
sql_statement.append("CREATE TABLE workspaces (NAME CHAR(50), USERNAME CHAR(50));")

# add admin users
sql_statement.append("INSERT INTO users (USERNAME, PASSWORD) VALUES ('stephan', 'mufflers');")
sql_statement.append("INSERT INTO workspaces (NAME, USERNAME) VALUES ('admin', 'stephan');")

cur = conn.cursor()
for statement in sql_statement:
   print("STATEMENT ", statement) 
   cur.execute( statement)

conn.commit()
cur.close()

print("INIT Complete") 

