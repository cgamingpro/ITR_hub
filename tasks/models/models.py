from pydantic import BaseModel
from typing import Optional
from random import randrange

class Job(BaseModel):
    user_id: str
    request_id: str
    pan_id: str
    pass_id: str
    job_code: int
    
    
    
    
    
