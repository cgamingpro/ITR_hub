from rediscon import redis_conn
from db import getdb
from openpyxl import Workbook, load_workbook

##depricated now , mixed into the main code , but keeping it here for refrence and future use if needed
##handles all the shit that happens once a job is complterd  , 

##works on reids publish and subscribe
pubsub = redis_conn.pubsub()
pubsub.subscribe("batch_complete")

for message in pubsub.listen():

    if message["type"] != "message":
        continue

    request_id = message["data"]

    con = getdb()
    cursor = con.cursor()

        #---- gotta combien all thesee querery into one shit ig     

    #get the data of hte jobs that just got osmsoelted 
    cursor.execute("""SELECT 
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
    ORDER BY j.created_at ASC;""",
    (request_id,))
    
    job_results = cursor.fetchall()
    
    #get the file to update
    cursor.execute("""SELECT 
    u.filename,
    u.s3_key,
    u.size_bytes,
    u.created_at
    FROM requests r
    JOIN uploads u 
    ON r.upload_id = u.id
    WHERE r.id = %s::uuid;""",
    (request_id,))
    file_info = cursor.fetchone()
    
    #updatiogn the origianl uploaded fiel and then update thee same again 
    wb = load_workbook(file_info['s3_key'])
    ws = wb.active
    for job in job_results:
        row_number = job['row_number']
        #option one is jus that pass status , for rn ain't parsing it , just returing as it is 
        if int(job['job_type']) == 1:
            if job['success']:
                ws.cell(row=row_number, column=3).value = job['output']
            else:
                ws.cell(row=row_number, column=3).value = f"Error: {job['error']}"      
                    
        ##dummy will implemtn other options lateer man     
        elif int(job['job_type']) == 2:
            print("job type 2")
        elif int(job['job_type']) == 3:
            print("job type 3")
                
                

            
    
    #update the job status
    cursor.execute("""
        UPDATE requests
        SET status = 'completed'
        WHERE id = %s::uuid
    """, (request_id,))
    
    con.commit()
    wb.save(file_info['s3_key'])
    wb.close()
    cursor.close()
    con.close()