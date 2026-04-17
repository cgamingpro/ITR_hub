from fastapi import APIRouter
import pytz
from redis import Redis
from rq import Queue
from rq import Worker
from options import statusCheck, userData
from rediscon import redis_conn
from models.models import Job
from rq_scheduler import Scheduler
from datetime import datetime, timedelta

print(redis_conn)
print(redis_conn.ping())

job_queue = Queue(connection=redis_conn)
scheduler = Scheduler(connection=redis_conn)

IST = pytz.timezone('Asia/Kolkata')

async def pan_status(job_post : Job):
    print("job processing started")
    
    

    if job_post.special_job and job_post.schedule_date and job_post.schedule_time:
        # Time Parsing
        native_dt = datetime.strptime(
            f"{job_post.schedule_date} {job_post.schedule_time}", 
            "%Y-%m-%d %H:%M"
        )
        localized_dt = IST.localize(native_dt)
        scheduled_dt = localized_dt.astimezone(pytz.utc)
        
        job = scheduler.enqueue_at(
            scheduled_dt, 
            statusCheck.demo, 
            job_post.pan_id, 
            job_post.pass_id, 
            job_post.job_id, 
            job_post.request_id
        )
        return job.id
    
    else:
        job = job_queue.enqueue(
            statusCheck.demo, 
            job_post.pan_id, 
            job_post.pass_id,
            job_post.job_id,
            job_post.request_id
        )
        return job.id
        
#dummy one to extend
async def pan_userData(job_post : Job):
    print("job processing started")
    job = job_queue.enqueue(userData.userData, job_post.pan_id, job_post.pass_id,job_post.job_id,job_post.request_id)
    return job.id