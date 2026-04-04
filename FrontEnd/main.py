from datetime import time
import traceback
from openpyxl import Workbook, load_workbook
from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates
import shutil
import os
from rediscon import redis_conn
import requests
from db import getdb
from datetime import datetime
import data
from fastapi.responses import FileResponse, HTMLResponse


##url for job queuing api 
api2url = data.API2URL

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Replace with FireBase cloud Storage 
UPLOAD_DIRECTORY = "local_storage"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


#Here just for testing , currently esists in DB, manually added
current_user_id = "9d7d0d52-c450-4cbc-a148-f0fe49e6b3e5" 
current_user_mail = "test@mail.com"

#main end point but i don't give much fkk
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#for the Excel upload and completer job queing , 
@app.post("/upload")
async def handele_upload(
    user_file: UploadFile = File(...),
    option1: bool = Form(False),
    option2: bool = Form(False),
    option3: bool = Form(False),
    option4: bool = Form(False)
):
    con = getdb()
    cursor = con.cursor()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = os.path.basename(user_file.filename) 
    unique_filename = f"{current_user_id}_{timestamp}_{safe_name}"
    file_location = os.path.join(UPLOAD_DIRECTORY, unique_filename)
    
    try:
        
        ## fiel uploaded succkelssy in db and we got acess now 
        
        filename = unique_filename
        print(f"Saving file to: {filename}")
        
        # file_location = f"{UPLOAD_DIRECTORY}/{filename}"
    
        # Open a new file on your hard drive and copy the incoming bytes into it
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(user_file.file, file_object)
            
        file_size_bytes = os.path.getsize(file_location)

        # Just keeps a record of the excel file uploaded, to be used while returing the resutls , and mapping the file in history 
        insert_query = """
            INSERT INTO uploads (user_id, filename, s3_key, size_bytes)
            VALUES (%s::uuid, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(insert_query, (current_user_id, filename, file_location, file_size_bytes))
        
        new_upload_id = cursor.fetchone()['id']
        
        con.commit()
        
        
    
        ##parsign diffent jobs based on the options selected and queing them in the job queing API
        request_type = await get_combination_id(option1, option2, option3)
        
        
        #genrate requestion based on this shit
        rqest_id = await createRequest(new_upload_id,file_location, request_type)
        
    
    
        return {
                "message": "Upload started",
                "request_id": str(rqest_id)
            }
        
    except Exception as e:
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        
        cursor.close()
        con.close()
        
        

async def createRequest(upload_id,current_path, request_type):
    con = getdb()
    cursor = con.cursor()   
    try: 
        ##gettign the number of jobs
        wb = load_workbook(current_path)
        ws = wb.active

        total_rows = sum(1 for _ in ws.iter_rows(min_row=2, values_only=True))
        
        #will handle almsot everythign thotught the reqeusts 
        insert_query = """INSERT INTO requests (user_id, upload_id, name, total_jobs)
                        VALUES (%s::uuid, %s::uuid, %s, %s)
                        RETURNING id;"""
        
        cursor.execute(insert_query, (current_user_id, upload_id, os.path.basename(current_path), total_rows))
        new_rquest_id = cursor.fetchone()['id']
        con.commit()
        
        ##creatigna a redis varrible with the uuid of reqeust to manage the jobs comletignon 
        redis_conn.set(f"batch:{new_rquest_id}:remaining", total_rows)
        
        #creatign the inddviaivdual jobs 
        await createJobs(new_rquest_id,current_path, request_type)
        
        
        return new_rquest_id
        
    except Exception as e:
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        
        cursor.close()
        con.close()
    
    


async def createJobs(request_id, current_path,job_type):
    con = getdb()
    cursor = con.cursor()
    
    try:
        wb = load_workbook(current_path)
        ws = wb.active
        count = 2 #becasue of the header row in excel file
        for row in ws.iter_rows(min_row=2, values_only=True):
            pan_id = row[0]
            pass_id = row[1]
            
            
            insert_query = """INSERT INTO jobs (request_id, row_number ,job_type) 
                            VALUES (%s::uuid, %s , %s)
                            RETURNING id; """
            cursor.execute(insert_query, (request_id, count, job_type))
            new_job_id = cursor.fetchone()['id']
            
            #callign the 2nd api 
            paylod = {
                "job_id": new_job_id,
                "pan_id": pan_id,
                "pass_id": pass_id,
                "job_code": job_type,
                "request_id": request_id
            }
            
            requests.post(api2url, json=paylod)
            
            #just the itteraton yaar, 
            count +=1
            
        ##commiting the jobs in db
        con.commit()
        
    except Exception as e:
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        
        cursor.close()
        con.close()
        wb.close()
        
        
        
## contintulsy pings back to chekc the systaus of the request 
@app.get("/requests/{request_id}/status")
async def request_status(request_id: str):

    con = getdb()
    cursor = con.cursor()

    try:
        cursor.execute("""
            SELECT id, name, total_jobs, status
            FROM requests
            WHERE id = %s::uuid
        """, (request_id,))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Request not found")

        # check redis progress
        remaining = redis_conn.get(f"batch:{request_id}:remaining")

        if remaining is None:
            remaining = 0
        else:
            remaining = int(remaining)

        ##using this insted of the compeleted jobs in db , cuase that is being updated once the bathc is compelter , and theis acaily proceesd jobs
        #not the compelted jobs ,
        proceessed_job = row["total_jobs"] - remaining

        return {
            "request_id": str(row["id"]),
            "name": row["name"],
            "status": row["status"],
            "total_jobs": row["total_jobs"],
            "completed_jobs": proceessed_job
        }

    finally:
        cursor.close()
        con.close()
        
    
    
    
@app.get("/requests/recent")
async def get_recent_requests():
    con = getdb()
    cursor = con.cursor()

    try:
        cursor.execute("""
            SELECT id, name, total_jobs, status, created_at
            FROM requests
            WHERE user_id = %s::uuid
            AND created_at >= NOW() - INTERVAL '2 days'
            ORDER BY created_at ASC
        """, (current_user_id,))

        rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append({
                "id": str(r["id"]),
                "name": r["name"],
                "status": r["status"],
                "total_jobs": r["total_jobs"]
            })

        return results

    finally:
        cursor.close()
        con.close()    
        
        

@app.get("/requests/{request_id}/download")
async def download_request_file(request_id: str):

    con = getdb()
    cursor = con.cursor()

    try:
        cursor.execute("""
            SELECT u.filename, u.s3_key
            FROM requests r
            JOIN uploads u ON r.upload_id = u.id
            WHERE r.id = %s::uuid
            AND r.user_id = %s::uuid
        """, (request_id, current_user_id))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=row["s3_key"],
            filename=row["filename"],
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    finally:
        cursor.close()
        con.close()
        
        
#job parse
async def get_combination_id(opt1, opt2, opt3):
    total = 0
    if opt1: total += 1
    if opt2: total += 2
    if opt3: total += 4
    return total