import psycopg2
from psycopg2.extras import RealDictCursor

#get's conenciton to the postgress server for now 
def getdb():
    
    while True:
        try:
            conn = psycopg2.connect(host="localhost",database="fastapi",user="postgres",password="Hariom@123",cursor_factory=RealDictCursor)
            
            print("conntion was sussefull")
            break
        except Exception as error:
            print(error) 
            
    return conn
