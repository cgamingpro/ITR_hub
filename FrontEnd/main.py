from datetime import time
import traceback
from openpyxl import Workbook, load_workbook
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates
import shutil
import os
from rediscon import redis_conn
import requests
from db import getdb
from datetime import datetime
import data
from fastapi.responses import FileResponse, HTMLResponse
from models.models import Job, user ,userLogin
import util , auth
from fastapi.security import  OAuth2PasswordRequestForm


##url for job queuing api 
api2url = data.API2URL

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Replace with FireBase cloud Storage 
UPLOAD_DIRECTORY = os.getenv("STORAGE_PATH", "local_storage")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)





#main end point but i don't give much fkk
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#for the Excel upload and completer job queing , 
@app.post("/upload")
async def handele_upload(
    current_user_id = Depends(auth.get_current_user),
    user_file: UploadFile = File(...),
    option1: bool = Form(False),
    option2: bool = Form(False),
    option3: bool = Form(False),
    option4: bool = Form(False)
):
    print(f"\n=== UPLOAD ENDPOINT CALLED ===")
    print(f"Current user ID: {current_user_id}")
    print(f"Filename: {user_file.filename}")
    print(f"Options - opt1: {option1}, opt2: {option2}, opt3: {option3}, opt4: {option4}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established: {con}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = os.path.basename(user_file.filename) 
    unique_filename = f"{current_user_id}_{timestamp}_{safe_name}"
    print(f"Unique filename generated: {unique_filename}")
    
    file_location = os.path.join(UPLOAD_DIRECTORY, unique_filename)
    print(f"File location: {file_location}")
    
    try:
        
        ## fiel uploaded succkelssy in db and we got acess now 
        print(f"Starting file save process...")
        
        filename = unique_filename
        print(f"Saving file to: {filename}")
        
        # file_location = f"{UPLOAD_DIRECTORY}/{filename}"
    
        # Open a new file on your hard drive and copy the incoming bytes into it
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(user_file.file, file_object)
        print(f"File written successfully to disk")
            
        file_size_bytes = os.path.getsize(file_location)
        print(f"File size: {file_size_bytes} bytes")

        # Just keeps a record of the excel file uploaded, to be used while returing the resutls , and mapping the file in history 
        insert_query = """
            INSERT INTO uploads (user_id, filename, s3_key, size_bytes)
            VALUES (%s::uuid, %s, %s, %s)
            RETURNING id;
        """
        print(f"Executing DB insert for upload...")
        cursor.execute(insert_query, (current_user_id, filename, file_location, file_size_bytes))
        
        new_upload_id = cursor.fetchone()['id']
        print(f"Upload ID created: {new_upload_id}")
        
        con.commit()
        print(f"Database committed successfully")
        
        
    
        ##parsign diffent jobs based on the options selected and queing them in the job queing API
        request_type = await get_combination_id(option1, option2, option3)
        print(f"Request type ID calculated: {request_type}")
        
        
        #genrate requestion based on this shit
        print(f"Creating request with user_id: {current_user_id}, upload_id: {new_upload_id}")
        rqest_id = await createRequest(current_user_id, new_upload_id, file_location, request_type)
        print(f"Request ID created: {rqest_id}")
        
    
    
        print(f"=== UPLOAD ENDPOINT RETURNING ===")
        return {
                "message": "Upload started",
                "request_id": str(rqest_id)
            }
        
    except Exception as e:
        print(f"\n!!! ERROR IN UPLOAD ENDPOINT !!!")
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        
        cursor.close()
        con.close()
        
        

async def createRequest(current_user_id: str, upload_id: str, current_path: str, request_type: str):
    print(f"\n=== CREATE REQUEST CALLED ===")
    print(f"Params - user_id: {current_user_id}, upload_id: {upload_id}, path: {current_path}, type: {request_type}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established in createRequest")
    
    try: 
        ##gettign the number of jobs
        print(f"Loading workbook from: {current_path}")
        wb = load_workbook(current_path)
        ws = wb.active
        print(f"Workbook loaded, active sheet: {ws.title}")

        total_rows = sum(1 for _ in ws.iter_rows(min_row=2, values_only=True))
        print(f"Total rows in workbook: {total_rows}")
        
        #will handle almsot everythign thotught the reqeusts 
        print(f"Inserting request into DB...")
        insert_query = """INSERT INTO requests (user_id, upload_id, name, total_jobs)
                        VALUES (%s::uuid, %s::uuid, %s, %s)
                        RETURNING id;"""
        
        cursor.execute(insert_query, (current_user_id, upload_id, os.path.basename(current_path), total_rows))
        new_rquest_id = cursor.fetchone()['id']
        print(f"New request ID: {new_rquest_id}")
        
        con.commit()
        print(f"Request committed to DB")
        
        ##creatigna a redis varrible with the uuid of reqeust to manage the jobs comletignon 
        print(f"Setting Redis key for batch tracking: batch:{new_rquest_id}:remaining = {total_rows}")
        redis_conn.set(f"batch:{new_rquest_id}:remaining", total_rows)
        print(f"Redis key set successfully")
        
        #creatign the inddviaivdual jobs 
        print(f"Creating individual jobs...")
        await createJobs(current_user_id,new_rquest_id,current_path, request_type)
        print(f"All jobs created successfully")
        
        
        print(f"=== CREATE REQUEST RETURNING: {new_rquest_id} ===")
        return new_rquest_id
        
    except Exception as e:
        print(f"\n!!! ERROR IN CREATE REQUEST !!!")
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        
        cursor.close()
        con.close()
    
    


async def createJobs(current_user_id: str, request_id: str, current_path: str, job_type: str):
    print(f"\n=== CREATE JOBS CALLED ===")
    print(f"Params - user_id: {current_user_id}, request_id: {request_id}, job_type: {job_type}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established in createJobs")
    
    try:
        print(f"Loading workbook for job creation...")
        wb = load_workbook(current_path)
        ws = wb.active
        print(f"Workbook loaded, starting job creation loop...")
        
        count = 2 #becasue of the header row in excel file
        for row in ws.iter_rows(min_row=2, values_only=True):
            print(f"\nProcessing row {count}...")
            pan_id = row[0]
            pass_id = row[1]
            print(f"Row data - PAN: {pan_id}, PASS: {pass_id}")
            
            
            insert_query = """INSERT INTO jobs (request_id, row_number ,job_type) 
                            VALUES (%s::uuid, %s , %s)
                            RETURNING id; """
            print(f"Inserting job to DB...")
            cursor.execute(insert_query, (request_id, count, job_type))
            new_job_id = cursor.fetchone()['id']
            print(f"Job ID created: {new_job_id}")
            
            #callign the 2nd api 
            paylod = {
                "job_id": new_job_id,
                "pan_id": pan_id,
                "pass_id": pass_id,
                "job_code": job_type,
                "request_id": request_id
            }
            print(f"Sending to API2: {api2url} with payload: {paylod}")
            
            response = requests.post(api2url, json=paylod)
            print(f"API2 response status: {response.status_code}")
            
            #just the itteraton yaar, 
            count +=1
            print(f"Moving to next row...")
            
        ##commiting the jobs in db
        print(f"\nAll jobs inserted. Committing to DB...")
        con.commit()
        print(f"All jobs committed successfully")
        
    except Exception as e:
        print(f"\n!!! ERROR IN CREATE JOBS !!!")
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    
    finally:
        print(f"=== CREATE JOBS CLEANUP ===")
        cursor.close()
        con.close()
        wb.close()
        print(f"Resources cleaned up")
        
        
        
## contintulsy pings back to chekc the systaus of the request 
@app.get("/requests/{request_id}/status")
async def request_status(request_id: str):
    print(f"\n=== REQUEST STATUS ENDPOINT CALLED ===")
    print(f"Request ID: {request_id}")

    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established in request_status")

    try:
        print(f"Querying request status from DB...")
        cursor.execute("""
            SELECT id, name, total_jobs, status
            FROM requests
            WHERE id = %s::uuid
        """, (request_id,))

        row = cursor.fetchone()
        print(f"Query result: {row}")

        if not row:
            print(f"Request not found!")
            raise HTTPException(status_code=404, detail="Request not found")

        # check redis progress
        print(f"Checking Redis for batch progress: batch:{request_id}:remaining")
        remaining = redis_conn.get(f"batch:{request_id}:remaining")
        print(f"Redis remaining value: {remaining}")

        if remaining is None:
            remaining = 0
        else:
            remaining = int(remaining)
        print(f"Remaining (int): {remaining}")

        ##using this insted of the compelted jobs in db , cuase that is being updated once the bathc is compelter , and theis acaily proceesd jobs
        #not the compelted jobs ,
        proceessed_job = row["total_jobs"] - remaining
        print(f"Processed jobs: {proceessed_job} out of {row['total_jobs']}")

        print(f"=== RETURNING STATUS ===")
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
        
    
    
#last two day's resquest
@app.get("/requests/recent")
async def get_recent_requests(
    current_user_id = Depends(auth.get_current_user)
):
    print(f"\n=== GET RECENT REQUESTS ENDPOINT ===")
    print(f"User ID: {current_user_id}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established")

    try:
        print(f"Querying recent requests from DB...")
        cursor.execute("""
            SELECT id, name, total_jobs, status, created_at
            FROM requests
            WHERE user_id = %s::uuid
            AND created_at >= NOW() - INTERVAL '2 days'
            ORDER BY created_at ASC
        """, (current_user_id,))

        rows = cursor.fetchall()
        print(f"Found {len(rows)} recent requests")

        results = []
        for r in rows:
            result_item = {
                "id": str(r["id"]),
                "name": r["name"],
                "status": r["status"],
                "total_jobs": r["total_jobs"]
            }
            print(f"Adding result: {result_item['id']} - {result_item['name']}")
            results.append(result_item)

        print(f"=== RETURNING {len(results)} RESULTS ===")
        return results

    finally:
        cursor.close()
        con.close()    
        
        
#downaodl the file connected ot that reqeust , with the updated data in it
@app.get("/requests/{request_id}/download")
async def download_request_file(request_id: str , current_user_id = Depends(auth.get_current_user)):
    print(f"\n=== DOWNLOAD ENDPOINT CALLED ===")
    print(f"Request ID: {request_id}, User ID: {current_user_id}")

    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established")

    try:
        print(f"Querying file for download...")
        cursor.execute("""
            SELECT u.filename, u.s3_key
            FROM requests r
            JOIN uploads u ON r.upload_id = u.id
            WHERE r.id = %s::uuid
            AND r.user_id = %s::uuid
        """, (request_id, current_user_id))

        row = cursor.fetchone()
        print(f"Query result: {row}")

        if not row:
            print(f"File not found!")
            raise HTTPException(status_code=404, detail="File not found")

        print(f"File found: {row['filename']}")
        return FileResponse(
            path=row["s3_key"],
            filename=row["filename"],
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    finally:
        cursor.close()
        con.close()
        
#keep it hidden for now , will be used for user registration and authentication later on , just a dummy one for now
@app.post("/userreg")
async def user_registration(user: user):
    print(f"\n=== USER REGISTRATION ENDPOINT ===")
    print(f"Email: {user.email}, Name: {user.name}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established")

    try:
        
        #pass hashing
        password_bytes = len(user.password.encode("utf-8"))
        print(f"Password length: {password_bytes} bytes")
        
        if password_bytes > 72:
            print(f"!!! Password too long !!!")
            raise HTTPException(
                status_code=400,
                detail="Password too long (max 72 bytes)"
                )
        
        print(f"Hashing password...")
        hashed_password = util.hash(user.password)
        print(f"Password hashed successfully")
        
        print(f"Inserting user into DB...")
        cursor.execute("""
            INSERT INTO users (email, hashed_password, name)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (user.email, hashed_password, user.name))

        new_user_id = cursor.fetchone()['id']
        print(f"New user ID: {new_user_id}")
        
        con.commit()
        print(f"User committed to DB successfully")

        print(f"=== REGISTRATION SUCCESSFUL ===")
        return {"message": "User registered successfully", "user_id": str(new_user_id)}

    except Exception as e:
        print(f"\n!!! ERROR IN USER REGISTRATION !!!")
        con.rollback()
        
        print("\n--- DATABASE ERROR DETAILS ---")
        traceback.print_exc() 
        print("------------------------------\n")
        
        raise HTTPException(status_code=500, detail="Failed to register user., maybe email already exists.")

    finally:
        cursor.close()
        con.close()
        
        
#retriving the user data
@app.get("/users/me")        
async def get_user(user_id = Depends(auth.get_current_user)):
    print(f"\n=== GET USER ENDPOINT ===")
    print(f"User ID: {user_id}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established")

    try: 
        print(f"Querying user from DB...")
        cursor.execute("""
            SELECT id, email, name
            FROM users
            WHERE id = %s::uuid
        """, (user_id,))

        row = cursor.fetchone()
        print(f"Query result: {row}")

        if not row:
            print(f"!!! User not found !!!")
            raise HTTPException(status_code=404, detail="User not found")

        user_data = {
            "id": str(row["id"]),
            "email": row["email"],
            "name": row["name"]
        }
        print(f"=== RETURNING USER DATA ===")
        return user_data

    finally:
        cursor.close()
        con.close()
        

@app.post('/login')
def login(user_cred: OAuth2PasswordRequestForm = Depends()):
    print(f"\n=== LOGIN ENDPOINT CALLED ===")
    print(f"Username/Email: {user_cred.username}")
    
    con = getdb()
    cursor = con.cursor()
    print(f"Database connection established")

    try:
        print(f"Querying user by email...")
        cursor.execute("""
            SELECT id, email, hashed_password
            FROM users
            WHERE email = %s
        """, (user_cred.username,))

        row = cursor.fetchone()
        print(f"User query result: {row}")

        if not row:
            print(f"!!! User not found !!!")
            raise HTTPException(status_code=404, detail="User not found")

        # Verify password
        print(f"Verifying password...")
        password_valid = util.verify(user_cred.password, row["hashed_password"])
        print(f"Password verification result: {password_valid}")
        
        if not password_valid:
            print(f"!!! Invalid credentials !!!")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        
        print(f"Creating access token...")
        access_token = auth.create_acess_token(data={"user_id": str(row["id"])})
        print(f"Access token created successfully")
        
        print(f"=== LOGIN SUCCESSFUL ===")
        return {"access_token": access_token , "token_type": "bearer"}

    finally:
        cursor.close()
        con.close()
    

#job parse
async def get_combination_id(opt1, opt2, opt3):
    print(f"\n=== GET COMBINATION ID CALLED ===")
    print(f"Options: opt1={opt1}, opt2={opt2}, opt3={opt3}")
    
    total = 0
    if opt1:
        total += 1
        print(f"Option 1 selected, adding 1. Total: {total}")
    if opt2:
        total += 2
        print(f"Option 2 selected, adding 2. Total: {total}")
    if opt3:
        total += 4
        print(f"Option 3 selected, adding 4. Total: {total}")
    
    print(f"Final combination ID: {total}")
    return total