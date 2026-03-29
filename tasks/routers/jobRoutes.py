from fastapi import APIRouter
from redis import Redis
from rq import Queue
from rq import Worker
from options import statusCheck, userData


#fast-api setup
#router = APIRouter()

# redis setup 
redis_conn = Redis(host="localhost", port=6379)  # <-- WSL Redis

print(redis_conn)
print(redis_conn.ping())

job_queue = Queue(connection=redis_conn)

#@router.get("/test")
async def pan_status(pan_id,pass_id,job_id,request_id):
    print(f"job processing started")
    job = job_queue.enqueue(statusCheck.demo, pan_id, pass_id,job_id,request_id)
    return job.id
    
async def pan_userData(pan_id,pass_id,job_id,request_id):
    print(f"job processing started")
    job = job_queue.enqueue(userData.userData, pan_id, pass_id,job_id,request_id)
    return job.id
