import psycopg2
from psycopg2.extras import RealDictCursor
import data

def getdb():
    
    while True:
        try:
            conn = psycopg2.connect(host=data.host,database=data.database,user=data.user,password=data.password,cursor_factory=RealDictCursor)
            
            print("conntion was sussefull")
            break
        except Exception as error:
            print(error) 
            
    return conn
