from pydantic import BaseModel
from typing import Optional
from random import randrange

class Job(BaseModel):
    job_id: str
    pan_id: str
    pass_id: str
    job_code: int
    request_id: str
    schedule_date: Optional[str] = None
    schedule_time: Optional[str] = None
    rettry_number: Optional[int] = 0
    special_job: Optional[bool] = False
    
    
    
    
    
