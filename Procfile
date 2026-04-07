# Internal API (tasks) – only accessible by other services
tasks-api: cd tasks && uvicorn main:app --host 0.0.0.0 --port 8000

# Background worker for tasks
rq-worker: cd tasks && rq worker

# Public frontend API – Railway will expose this on $PORT
frontend-api: cd FrontEnd && uvicorn main:app --host 0.0.0.0 --port $PORT

# Listener / background process for frontend
frontend-listener: cd FrontEnd && python listner.py