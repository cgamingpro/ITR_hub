from pydantic import BaseModel
from typing import Optional
from random import randrange

class Job(BaseModel):
    job_id: str
    pan_id: str
    pass_id: str
    job_code: int
    request_id: str
    
    
    
    
    
