import os
import shutil
import traceback
import requests
import threading
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook, load_workbook
from fastapi.staticfiles import StaticFiles

# Your internal imports
import data
import util
import auth
from db import getdb
from rediscon import redis_conn
from models.models import Job, user, userLogin

# URL for job queuing api 
api2url = data.API2URL

# Replace with FireBase cloud Storage 
UPLOAD_DIRECTORY = os.getenv("STORAGE_PATH", "local_storage")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


# ==========================================
# 1. THE REDIS BACKGROUND LISTENER
# ==========================================
def run_redis_listener():
    print("Starting background Redis listener...")
    pubsub = redis_conn.pubsub()
    pubsub.subscribe("batch_complete")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue

        # Decode data just in case Redis returns bytes
        raw_data = message["data"]
        request_id = raw_data.decode("utf-8") if isinstance(raw_data, bytes) else raw_data
        print(f"Listener triggered for request_id: {request_id}")

        con = getdb()
        cursor = con.cursor()

        try:
            # Get the data of the jobs that just got completed 
            cursor.execute("""
                SELECT 
                    j.id AS job_id,
                    j.row_number,
                    j.created_at,
                    j.job_type,
                    jr.output,
                    jr.success,
                    jr.error
                FROM jobs j
                LEFT JOIN job_results jr
                ON j.id = jr.job_id
                WHERE j.request_id = %s::uuid
                ORDER BY j.created_at ASC;
            """, (request_id,))
            
            job_results = cursor.fetchall()
            
            # Get the file to update
            cursor.execute("""
                SELECT 
                    u.filename,
                    u.s3_key,
                    u.size_bytes,
                    u.created_at
                FROM requests r
                JOIN uploads u 
                ON r.upload_id = u.id
                WHERE r.id = %s::uuid;
            """, (request_id,))
            file_info = cursor.fetchone()
            
            # Updating the original uploaded file
            if file_info and os.path.exists(file_info['s3_key']):
                wb = load_workbook(file_info['s3_key'])
                ws = wb.active
                
                for job in job_results:
                    row_number = job['row_number']
                    
                    if int(job['job_type']) == 1:
                        if job['success']:
                            ws.cell(row=row_number, column=3).value = job['output']
                        else:
                            ws.cell(row=row_number, column=3).value = f"Error: {job['error']}"      
                    elif int(job['job_type']) == 2:
                        print("job type 2")
                    elif int(job['job_type']) == 3:
                        print("job type 3")

                # Update the job status
                cursor.execute("""
                    UPDATE requests
                    SET status = 'completed'
                    WHERE id = %s::uuid
                """, (request_id,))
                
                con.commit()
                wb.save(file_info['s3_key'])
                wb.close()
                print(f"Successfully processed and updated file for request {request_id}")

        except Exception as e:
            print(f"Error in Redis listener processing: {e}")
            con.rollback()
        finally:
            cursor.close()
            con.close()

# ==========================================
# 2. FASTAPI LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fire up the listener in a daemon thread so it doesn't block the API
    # Daemon=True means it will automatically die when the FastAPI server stops
    listener_thread = threading.Thread(target=run_redis_listener, daemon=True)
    listener_thread.start()
    yield
    # Cleanup logic (if any) would go here when the server shuts down

# Initialize FastAPI with the lifespan
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ==========================================
# 3. YOUR EXISTING ENDPOINTS
# ==========================================

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
    con = getdb()
    cursor = con.cursor()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = os.path.basename(user_file.filename) 
    unique_filename = f"{current_user_id}_{timestamp}_{safe_name}"
    file_location = os.path.join(UPLOAD_DIRECTORY, unique_filename)
    
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(user_file.file, file_object)
            
        file_size_bytes = os.path.getsize(file_location)

        insert_query = """
            INSERT INTO uploads (user_id, filename, s3_key, size_bytes)
            VALUES (%s::uuid, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(insert_query, (current_user_id, unique_filename, file_location, file_size_bytes))
        new_upload_id = cursor.fetchone()['id']
        con.commit()
        
        request_type = await get_combination_id(option1, option2, option3)
        rqest_id = await createRequest(current_user_id, new_upload_id, file_location, request_type)
        
        return {
                "message": "Upload started",
                "request_id": str(rqest_id)
            }
        
    except Exception as e:
        con.rollback()
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    finally:
        cursor.close()
        con.close()

async def createRequest(current_user_id: str, upload_id: str, current_path: str, request_type: str):
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
        await createJobs(current_user_id, new_rquest_id, current_path, request_type)
        
        return new_rquest_id
        
    except Exception as e:
        con.rollback()
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    finally:
        cursor.close()
        con.close()

async def createJobs(current_user_id: str, request_id: str, current_path: str, job_type: str):
    con = getdb()
    cursor = con.cursor()
    try:
        wb = load_workbook(current_path)
        ws = wb.active
        
        count = 2 
        for row in ws.iter_rows(min_row=2, values_only=True):
            pan_id = row[0]
            pass_id = row[1]
            
            insert_query = """INSERT INTO jobs (request_id, row_number ,job_type) 
                            VALUES (%s::uuid, %s , %s)
                            RETURNING id; """
            cursor.execute(insert_query, (request_id, count, job_type))
            new_job_id = cursor.fetchone()['id']
            
            paylod = {
                "job_id": new_job_id,
                "pan_id": pan_id,
                "pass_id": pass_id,
                "job_code": job_type,
                "request_id": request_id
            }
            
            requests.post(api2url, json=paylod)
            count += 1
            
        con.commit()
        
    except Exception as e:
        con.rollback()
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail="Failed to upload and save to database.")
    finally:
        cursor.close()
        con.close()
        wb.close()
        
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

        remaining = redis_conn.get(f"batch:{request_id}:remaining")
        remaining = 0 if remaining is None else int(remaining)
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
async def get_recent_requests(current_user_id = Depends(auth.get_current_user)):
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
async def download_request_file(request_id: str, current_user_id = Depends(auth.get_current_user)):
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
        
@app.post("/userreg")
async def user_registration(user: user):
    con = getdb()
    cursor = con.cursor()
    try:
        password_bytes = len(user.password.encode("utf-8"))
        if password_bytes > 72:
            raise HTTPException(status_code=400, detail="Password too long (max 72 bytes)")
        
        hashed_password = util.hash(user.password)
        
        cursor.execute("""
            INSERT INTO users (email, hashed_password, name)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (user.email, hashed_password, user.name))

        new_user_id = cursor.fetchone()['id']
        con.commit()
        return {"message": "User registered successfully", "user_id": str(new_user_id)}
    except Exception as e:
        con.rollback()
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail="Failed to register user, maybe email already exists.")
    finally:
        cursor.close()
        con.close()
        
@app.get("/users/me")        
async def get_user(user_id = Depends(auth.get_current_user)):
    con = getdb()
    cursor = con.cursor()
    try: 
        cursor.execute("""
            SELECT id, email, name
            FROM users
            WHERE id = %s::uuid
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": str(row["id"]),
            "email": row["email"],
            "name": row["name"]
        }
    finally:
        cursor.close()
        con.close()
        
@app.post('/login')
def login(user_cred: OAuth2PasswordRequestForm = Depends()):
    con = getdb()
    cursor = con.cursor()
    try:
        cursor.execute("""
            SELECT id, email, hashed_password
            FROM users
            WHERE email = %s
        """, (user_cred.username,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        password_valid = util.verify(user_cred.password, row["hashed_password"])
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = auth.create_acess_token(data={"user_id": str(row["id"])})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        cursor.close()
        con.close()
    
async def get_combination_id(opt1, opt2, opt3):
    total = 0
    if opt1: total += 1
    if opt2: total += 2
    if opt3: total += 4
    return total