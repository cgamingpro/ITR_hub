import traceback
from openpyxl import Workbook, load_workbook
from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates
import shutil,os

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
        
        await createRequest(new_upload_id,file_location, request_type)
        

        return {"message": f"Success! Saved as ID: {new_upload_id}"}
        
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
        
        await createJobs(new_rquest_id,current_path, request_type)
        
        
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
                "job_code": job_type
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