# tasks-api (internal)
tasks-api: cd tasks && uvicorn main:app --host 127.0.0.1 --port 8000

# background worker
rq-worker: cd tasks && rq worker

# frontend-api (public)
frontend-api: cd FrontEnd && uvicorn main:app --host 0.0.0.0 --port 8001

# frontend listener (internal)
frontend-listener: cd FrontEnd && python listner.py