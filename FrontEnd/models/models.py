from pydantic import BaseModel , EmailStr
from typing import Optional
from random import randrange

class Job(BaseModel):
    job_id: str
    pan_id: str
    pass_id: str
    job_code: int
    request_id: str
    
    
    
class user(BaseModel):
    email: EmailStr
    password: str
    name: str
    
class token(BaseModel):
    access_token: str
    token_type: str

class tokenData(BaseModel):
    user_id: Optional[str] = None

class userLogin(BaseModel):
    username: str
    password: str