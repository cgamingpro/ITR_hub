from fastapi import APIRouter
from redis import Redis
from rq import Queue
from rq import Worker
from options import statusCheck, userData
from rediscon import redis_conn


print(redis_conn)
print(redis_conn.ping())

job_queue = Queue(connection=redis_conn)

# handles the queuign of each job   and gives back job id from redidds queuese 


async def pan_status(pan_id,pass_id,job_id,request_id):
    print(f"job processing started")
    job = job_queue.enqueue(statusCheck.demo, pan_id, pass_id,job_id,request_id)
    return job.id

#dummy one to extend
async def pan_userData(pan_id,pass_id,job_id,request_id):
    print(f"job processing started")
    job = job_queue.enqueue(userData.userData, pan_id, pass_id,job_id,request_id)
    return job.id
