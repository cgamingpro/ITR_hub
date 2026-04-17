from fastapi import FastAPI
from routers import jobRoutes
from models.models import Job
app = FastAPI()

#Entry point for the job processignf API , just recive the jobs and pass to appropriate function in jobRoutes.py
@app.post("/job")
async def job_post(job_post: Job):
    
    #actual workign one
    if job_post.job_code == 1:
        print("job code 1")
        job_id = await jobRoutes.pan_status(job_post)
        return {"job_id": job_id}
    
    #Dummy one to extend 
    if job_post.job_code == 0:
        print("job code 2")
        job_id = await jobRoutes.pan_userData(job_post)
        return {"job_id": job_id}
        
        
    
