import traceback
from openpyxl import Workbook, load_workbook
from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates
import shutil,os
from rediscon import redis_conn
import requests
from db import getdb



api2url = "http://localhost:8000/job"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

#for tsetign only 
UPLOAD_DIRECTORY = "local_storage"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
current_user_id = "9d7d0d52-c450-4cbc-a148-f0fe49e6b3e5" 

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})





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
    
    
    try:
        
        ## fiel uploaded succkelssy in db and we got acess now 
        
        
        file_location = f"{UPLOAD_DIRECTORY}/{user_file.filename}"
    
        # Open a new file on your hard drive and copy the incoming bytes into it
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(user_file.file, file_object)
            
        file_size_bytes = os.path.getsize(file_location)


        insert_query = """
            INSERT INTO uploads (user_id, filename, s3_key, size_bytes)
            VALUES (%s::uuid, %s, %s, %s)
            RETURNING id;
        """
        
        cursor.execute(insert_query, (current_user_id, user_file.filename, file_location, file_size_bytes))
        
        new_upload_id = cursor.fetchone()['id']
        
        con.commit()
        
        
        ##request function call
        request_type = option1
        
        rqest_id = await createRequest(new_upload_id,file_location, request_type)
        

        #return {"message": f"Success! Saved as ID: {new_upload_id}"}
    
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

        wb = load_workbook(current_path)
        ws = wb.active

        total_rows = sum(1 for _ in ws.iter_rows(min_row=2, values_only=True))
        
        insert_query = """INSERT INTO requests (user_id, upload_id, name, total_jobs)
                        VALUES (%s::uuid, %s::uuid, %s, %s)
                        RETURNING id;"""
        
        cursor.execute(insert_query, (current_user_id, upload_id, os.path.basename(current_path), total_rows))
        new_rquest_id = cursor.fetchone()['id']
        con.commit()
        
        redis_conn.set(f"batch:{new_rquest_id}:remaining", total_rows)
        
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
        count = 2
        for row in ws.iter_rows(min_row=2, values_only=True):
            pan_id = row[0]
            pass_id = row[1]
            
            
            
            
            insert_query = """INSERT INTO jobs (request_id, row_number) 
                            VALUES (%s::uuid, %s)
                            RETURNING id; """
            cursor.execute(insert_query, (request_id, count))
            new_job_id = cursor.fetchone()['id']
            con.commit()
            
            paylod = {
                "job_id": new_job_id,
                "pan_id": pan_id,
                "pass_id": pass_id,
                "job_code": job_type,
                "request_id": request_id
            }
            
            response = requests.post(api2url, json=paylod)
            print(response.json())
           
            
            count +=1

        
    except Exception as e:
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        
        cursor.close()
        con.close()
        
        
        

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

        completed = row["total_jobs"] - remaining

        return {
            "request_id": str(row["id"]),
            "name": row["name"],
            "status": row["status"],
            "total_jobs": row["total_jobs"],
            "completed_jobs": completed
        }

    finally:
        cursor.close()
        con.close()