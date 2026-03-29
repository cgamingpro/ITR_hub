from fastapi import FastAPI
from routers import jobRoutes
from models.models import Job
app = FastAPI()


@app.post("/job")
async def job_post(job_post: Job):
    print("job request accuired")
    if job_post.job_code == 1:
        print("job code 1")
        job_id = await jobRoutes.pan_status(job_post.pan_id, job_post.pass_id , job_post.job_id, job_post.request_id)
        return {"job_id": job_id}
    
    if job_post.job_code == 2:
        print("job code 2")
        job_id = await jobRoutes.pan_userData(job_post.pan_id, job_post.pass_id,job_post.request_id)
        return {"job_id": job_id}
        
        
    
