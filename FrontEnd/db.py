import psycopg2
from psycopg2.extras import RealDictCursor

def getdb():
    
    while True:
        try:
            conn = psycopg2.connect(host="localhost",database="fastapi",user="postgres",password="Hariom@123",cursor_factory=RealDictCursor)
            
            print("conntion was sussefull")
            break
        except Exception as error:
            print(error) 
            
    return conn
