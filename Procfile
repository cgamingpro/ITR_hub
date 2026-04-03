tasks-api: cd tasks && uvicorn main:app --host 0.0.0.0 --port $PORT
rq-worker: cd tasks && rq worker
frontend-api: cd FrontEnd && uvicorn main:app --host 0.0.0.0 --port 8001
frontend-listener: cd FrontEnd && python listner.py