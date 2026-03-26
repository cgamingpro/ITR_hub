from fastapi import Body, FastAPI,Response,status,HTTPException
from pydantic import BaseModel
from typing import Optional
from random import randrange
import psycopg2
from psycopg2.extras import RealDictCursor


app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    
while True:
    try:
        conn = psycopg2.connect(host="localhost",database="fastapi",user="postgres",password="Hariom@123",cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("conntion was sussefull")
        break
    except Exception as error:
        print(error)  
    
          
  

    
my_posts = [{"title":"first post", "content":"this is my first post","id":1},
            {"title":"second post", "content":"this is my second post","id":2}]


def find_post(id ):
    for p in my_posts:
        if p["id"] == id:
            return p

def find_index_post(id):
    for i,p in enumerate(my_posts):
        if p['id'] == id:
            return i
            
        

#creata a post damm
@app.post("/posts", status_code= status.HTTP_201_CREATED)
def create_post(new_post: Post ): 
    cursor.execute("""insert into posts (title,content) values (%s,%s) RETURNING * """,(new_post.title,new_post.content))
    post = cursor.fetchone()
    conn.commit()
    return {"status":"post created", "post": post }

#return all post 
@app.get("/posts")
def get_posts():
    cursor.execute("""select * from posts""")
    posts = cursor.fetchall()
    return {"data": posts}

#return single post
@app.get("/posts/{id}")
def get_post(id: int, responce: Response):
    cursor.execute("""SELECT * FROM posts WHERE id = %s """,(str(id)))
    post = cursor.fetchone()
    if not post: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id {id} dond't wsit u fuckk ")
    return {"post_id": post} 

#obcous deltee bro
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING * """,(str(id)))
    delted_post = cursor.fetchone()
    conn.commit()
    
    if delted_post == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,detail=F"THIS POST NOT FOUND BOR{id} ")
    
    return  Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int , post: Post):
    cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s where id = %s returning *""",(post.title,post.content,post.published,str(id)))
    updated_post = cursor.fetchone()
    conn.commit()

    
    if updated_post == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,detail=F"THIS POST NOT FOUND BOR{id} ")
    
    
    return{"message":updated_post}
    